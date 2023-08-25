# Copyright © 2023 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The BOR solr data import service."""
import sys
from http import HTTPStatus

import requests
from flask import current_app
from bor_api.exceptions import SolrException
from bor_api.services import bor_solr
from bor_api.services.authz import get_bearer_token
from bor_api.services.solr.solr_docs import Entity

from bor_solr_importer import create_app
from bor_solr_importer.utils import (collect_colin_data, collect_lear_data, prep_data,
                                     reindex_post, reindex_prep, reindex_recovery)


def update_solr(base_docs: list[Entity], data_name: str) -> int:
    """Import data into solr."""
    count = 0
    offset = 0
    rows = current_app.config.get('BATCH_SIZE_SOLR', 1000)
    retry_count = 0
    erred_record_count = 0
    while count < len(base_docs) and rows > 0 and len(base_docs) - offset > 0:
        batch_amount = min(rows, len(base_docs) - offset)
        count += batch_amount
        # send batch to solr
        try:
            bor_solr.create_or_replace_docs(base_docs[offset:count])
            retry_count = 0
        except SolrException as err:  # pylint: disable=bare-except;
            current_app.logger.debug(err)
            if retry_count < 3:
                # retry
                current_app.logger.debug('Failed to update solr with batch. Trying again (%s of 3)...', retry_count + 1)
                retry_count += 1
                # set count back
                count -= batch_amount
                continue
            else:
                # log error and skip
                current_app.logger.error('Retry count exceeded for batch. Skipping batch.')
                # add number of records in failed batch to the erred count
                erred_record_count += (count - offset)
        offset = count
        current_app.logger.debug(f'Total {data_name} base doc records imported: {count - erred_record_count}')
    return count


def load_search_core():  # pylint: disable=too-many-statements,too-many-locals,too-many-branches; will update
    """Load data from LEAR and COLIN into the search core."""
    try:
        is_reindex = current_app.config.get('REINDEX_CORE', False)
        is_preload = current_app.config.get('PRELOADER_JOB', False)

        if is_reindex:
            current_app.logger.debug('---------- Pre Reindex Actions ----------')
            reindex_prep(is_preload)

        try:
            current_app.logger.debug('---------- Collecting/Importing COLIN Entities ----------')
            # PROD numbers for parties grouped by business number:
            #     - 0        to 0500000  ~3,000,000
            #     - 0500000  to A0000000 ~3,750,000
            #     - A0000000 to S0000000 ~2,350,000
            #     - S0000000 to .        ~3,400,000
            # Split load based on above numbers to keep memory usage lower
            total_colin_count = 0
            corp_num_limits = [
                {'min': '0000000', 'max': '0500000'},
                {'min': '0500000', 'max': 'A0000000'},
                {'min': 'A0000000', 'max': 'S0000000'},
                {'min': 'S0000000', 'max': None}]
            party_batch_rows_max = current_app.config.get('BATCH_SIZE_SQL', 500000)
            colin_data_descs = []
            for corp_num_limit in corp_num_limits:
                current_app.logger.debug(f'********** COLIN Corp Num Batch {corp_num_limit} **********')
                party_batch_count = 0
                party_batch_offset = 0
                colin_data = []
                while party_batch_count < 100:  # sanity check (expecting < 10 batches depending on data)
                    party_batch_count += 1
                    current_app.logger.debug(f'++++++++++ COLIN Party Batch {party_batch_count} ++++++++++')
                    current_app.logger.debug('Collecting party batch data...')
                    colin_data_cur = collect_colin_data(corp_num_limit,
                                                        party_batch_offset,
                                                        party_batch_rows_max*party_batch_count)
                    current_app.logger.debug('Fetching party batch rows...')
                    new_colin_data = colin_data_cur.fetchall()
                    if not colin_data_descs:
                        # just need to do once
                        colin_data_descs = [desc[0].lower() for desc in colin_data_cur.description]
                    if new_colin_data:
                        party_batch_offset += party_batch_rows_max
                        colin_data += new_colin_data
                        current_app.logger.debug(f'Total corp num batch rows fetched so far: {len(colin_data)}')
                        continue

                    # final check for any ids greater than the batch_rows_max*batch_count
                    current_app.logger.debug('No rows to found. Checking for any remaining records...')
                    colin_data_cur = collect_colin_data(corp_num_limit, party_batch_offset)
                    current_app.logger.debug('Fetching remaining rows...')
                    new_colin_data = colin_data_cur.fetchall()
                    colin_data += new_colin_data
                    current_app.logger.debug(f'Total rows fetched: {len(colin_data)}')
                    current_app.logger.debug('No more rows to fetch.')
                    break

                # NB: need full data set under each corp num to collapse parties properly
                current_app.logger.debug('********** Mapping COLIN Entities **********')
                prepped_colin_data = prep_data(colin_data, colin_data_descs, 'COLIN')
                current_app.logger.debug(f'COLIN entities ready for import: {len(prepped_colin_data)}')
                # execute update to solr in batches
                current_app.logger.debug('********** Importing COLIN Entities **********')
                corp_num_batch_count = update_solr(prepped_colin_data, 'COLIN')
                current_app.logger.debug(
                    f'COLIN import completed for corp num batch. Entities imported: {corp_num_batch_count}.')
                total_colin_count += corp_num_batch_count
                current_app.logger.debug(f'Total COLIN entities imported so far: {total_colin_count}.')

            current_app.logger.debug(f'COLIN import completed. Total COLIN entities imported: {total_colin_count}.')

            current_app.logger.debug('---------- Collecting LEAR Entities ----------')
            lear_data_cur = collect_lear_data()
            lear_data = lear_data_cur.fetchall()

            current_app.logger.debug('---------- Mapping LEAR data ----------')
            prepped_lear_data = prep_data(lear_data, [desc[0].lower() for desc in lear_data_cur.description], 'LEAR')
            current_app.logger.debug(f'{len(prepped_lear_data)} LEAR records ready for import.')

            # execute update to solr in batches
            current_app.logger.debug('---------- Importing LEAR entities ----------')
            lear_count = update_solr(prepped_lear_data, 'LEAR')
            current_app.logger.debug(f'LEAR import completed. Total LEAR entities imported: {lear_count}')

            current_app.logger.debug(f'Total entities imported: {total_colin_count + lear_count}')
        except Exception as err:  # noqa: B902
            if is_reindex and not is_preload:
                reindex_recovery()
            raise err  # pass along

        if not is_preload:
            try:
                current_app.logger.debug('---------- Resync ----------')
                current_app.logger.debug('Getting token for Resync...')
                token = get_bearer_token()
                headers = {'Authorization': 'Bearer ' + token}

                current_app.logger.debug('Resyncing any overwritten docs during import...')
                api_url = f'{current_app.config.get("BOR_API_URL")}{current_app.config.get("BOR_API_V1")}'
                resync_resp = requests.post(url=f'{api_url}/internal/solr/update/resync',
                                            headers=headers,
                                            json={'minutesOffset': current_app.config.get('RESYNC_OFFSET', '130')})
                if resync_resp.status_code != HTTPStatus.CREATED:
                    if resync_resp.status_code == HTTPStatus.GATEWAY_TIMEOUT:
                        current_app.logger.debug('Resync timed out -- check api for any individual failures.')
                    else:
                        current_app.logger.error('Resync failed with status %s', resync_resp.status_code)
                else:
                    current_app.logger.debug('Resync complete.')
            except Exception as error:  # noqa: B902
                current_app.logger.debug(error.with_traceback(None))
                current_app.logger.error('Resync failed.')

        if is_reindex and not is_preload:
            current_app.logger.debug('---------- Post Reindex Actions ----------')
            reindex_post()

        current_app.logger.debug('SOLR import finished successfully.')

    except SolrException as err:
        current_app.logger.debug(f'SOLR gave status code: {err.status_code}')
        current_app.logger.error(err.error)
        current_app.logger.debug('SOLR import failed.')
        sys.exit(1)


if __name__ == '__main__':
    print('Starting data importer...')
    app = create_app()  # pylint: disable=invalid-name
    with app.app_context():
        load_search_core()
        sys.exit(0)
