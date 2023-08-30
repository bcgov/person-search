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
import gc
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
        batch_amount = min(rows, len(base_docs) - offset) / (retry_count + 1)
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
            # PROD numbers for parties grouped by business identifier:
            #     - 0        to 0250000  ~1,200,000
            #     - 0250000  to 0500000  ~1,800,000
            #     - 0500000  to 0750000  ~2,000,000
            #     - 0750000  to 0950000  ~1,500,000
            #     - 0950000  to A0000000 ~2,150,000
            #     - A0000000 to S0000000 ~500,000
            #     - S0000000 to S0025000 ~1,400,000
            #     - S0025000 to *        ~2,000,000
            # Split load based on above numbers to keep memory usage lower
            total_colin_count = 0
            corp_num_limits = [
                {'min': '0000000', 'max': '0250000'},
                {'min': '0250000', 'max': '0500000'},
                {'min': '0500000', 'max': '0750000'},
                {'min': '0750000', 'max': '0950000'},
                {'min': '0950000', 'max': 'A0000000'},
                {'min': 'A0000000', 'max': 'S0000000'},
                {'min': 'S0000000', 'max': 'S0025000'},
                {'min': 'S0025000', 'max': None}]
            colin_data_descs = []
            start = current_app.config.get('CORP_NUM_LIMITS_START')
            end = current_app.config.get('CORP_NUM_LIMITS_END')
            for corp_num_limit in corp_num_limits[start:end]:
                range_str = f"{corp_num_limit['min']} to {corp_num_limit['max'] or '*'}"
                current_app.logger.debug(f'********** COLIN Corp Batch {range_str} **********')
                colin_data_cur = collect_colin_data(corp_num_limit['min'], corp_num_limit['max'])
                current_app.logger.debug('Fetching corp batch rows...')
                colin_data = colin_data_cur.fetchall()
                if not colin_data_descs:
                    # just need to do once
                    colin_data_descs = [desc[0].lower() for desc in colin_data_cur.description]
                colin_data_cur.close()
                # NB: need full data set under each corp num to collapse parties properly
                current_app.logger.debug('********** Mapping COLIN Entities **********')
                prepped_colin_data = prep_data(colin_data, colin_data_descs, 'COLIN')
                current_app.logger.debug(f'COLIN entities ready for import: {len(prepped_colin_data)}')
                # execute update to solr in batches
                current_app.logger.debug('********** Importing COLIN Entities **********')
                corp_num_batch_count = update_solr(prepped_colin_data, 'COLIN')
                current_app.logger.debug(
                    f'COLIN Corp Batch import completed. Entities imported: {corp_num_batch_count}.')
                total_colin_count += corp_num_batch_count
                current_app.logger.debug(f'Total COLIN entities imported so far: {total_colin_count}.')
                # free up memory
                del colin_data, prepped_colin_data
                gc.collect()

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
