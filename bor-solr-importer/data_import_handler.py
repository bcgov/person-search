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

from bor_solr_importer import create_app, oracle_db
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


def load_search_core():  # pylint: disable=too-many-statements
    """Load data from LEAR and COLIN into the search core."""
    try:
        is_reindex = current_app.config.get('REINDEX_CORE', False)
        is_preload = current_app.config.get('PRELOADER_JOB', False)
        
        if is_reindex:
            reindex_prep(is_preload)

        try:
            current_app.logger.debug('Connecting to Oracle instance...')
            cursor = oracle_db.connection.cursor()
            current_app.logger.debug('Collecting COLIN data...')
            count = 0
            offset = 0
            rows = current_app.config.get('BATCH_SIZE_SQL', 1000)
            while rows > 0:
                current_app.logger.debug(f'Collecting batch from COLIN...')
                colin_data_cur = collect_colin_data(offset, rows, cursor)
                current_app.logger.debug('Fetching rows...')
                colin_data = colin_data_cur.fetchall()
                if not colin_data:
                    current_app.logger.debug('No more rows to fetch.')
                    break
                offset += rows

                current_app.logger.debug('Prepping batch data...')

                prepped_colin_data = prep_data(colin_data, colin_data_cur, 'COLIN')
                current_app.logger.debug(f'{len(prepped_colin_data)} COLIN records ready for import.')
            
                # execute update to solr in batches
                current_app.logger.debug('Importing records from COLIN...')
                count += update_solr(prepped_colin_data, 'COLIN')
                current_app.logger.debug('Records imported.')

            current_app.logger.debug(f'COLIN import completed. COLIN records imported: {count}.')

            lear_data_cur = collect_lear_data()
            lear_data = lear_data_cur.fetchall()

            current_app.logger.debug('Prepping LEAR data...')
            prepped_lear_data = prep_data(lear_data, lear_data_cur, 'LEAR')
            current_app.logger.debug(f'{len(prepped_lear_data)} LEAR records ready for import.')

            # execute update to solr in batches
            current_app.logger.debug('Importing records from LEAR...')
            count += update_solr(prepped_lear_data, 'LEAR')
            current_app.logger.debug('LEAR import completed.')

            current_app.logger.debug(f'Total records imported: {count}')
        except Exception as err:  # noqa: B902
            if is_reindex and not is_preload:
                reindex_recovery()
            raise err  # pass along

        if not is_preload:
            try:
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
