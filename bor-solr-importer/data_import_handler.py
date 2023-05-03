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
from bor_api.services.solr.solr_docs import Entity

from bor_solr_importer import create_app
from bor_solr_importer.utils import collect_colin_data, collect_lear_data, prep_data


def update_solr(base_docs: list[Entity], data_name: str) -> int:
    """Import data into solr."""
    count = 0
    offset = 0
    rows = current_app.config.get('BATCH_SIZE', 1000)
    while count < len(base_docs) and rows > 0 and len(base_docs) - offset > 0:
        count += min(rows, len(base_docs) - offset)
        # send batch to solr
        bor_solr.create_or_replace_docs(base_docs[offset:count])
        offset = count
        current_app.logger.debug(f'Total {data_name} base doc records imported: {count}')
    return count


def load_search_core():  # pylint: disable=too-many-statements
    """Load data from LEAR and COLIN into the search core."""
    try:
        colin_data_cur = collect_colin_data()
        colin_data = colin_data_cur.fetchall()
        current_app.logger.debug('Prepping COLIN data...')
        prepped_colin_data = prep_data(colin_data, colin_data_cur, 'COLIN')
        current_app.logger.debug(f'{len(prepped_colin_data)} COLIN records ready for import.')
        lear_data_cur = collect_lear_data()
        lear_data = lear_data_cur.fetchall()
        current_app.logger.debug('Prepping LEAR data...')
        prepped_lear_data = prep_data(lear_data, lear_data_cur, 'LEAR')
        current_app.logger.debug(f'{len(prepped_lear_data)} LEAR records ready for import.')
        if current_app.config.get('REINDEX_CORE', False):
            # delete existing index
            current_app.logger.debug('REINDEX_CORE set: deleting current solr index...')
            bor_solr.delete_all_docs()
        # execute update to solr in batches
        current_app.logger.debug('Importing records from COLIN...')
        count = update_solr(prepped_colin_data, 'COLIN')
        current_app.logger.debug('COLIN import completed.')
        current_app.logger.debug('Importing records from LEAR...')
        count += update_solr(prepped_lear_data, 'LEAR')
        current_app.logger.debug('LEAR import completed.')
        current_app.logger.debug(f'Total records imported: {count}')

        if not current_app.config.get('PRELOADER_JOB', False):
            try:
                current_app.logger.debug('Resyncing any overwritten docs during import...')
                api_url = f'{current_app.config.get("BOR_API_URL")}{current_app.config.get("BOR_API_V1")}'
                resync_resp = requests.post(url=f'{api_url}/internal/solr/update/resync',
                                            json={'minutesOffset': current_app.config.get('RESYNC_OFFSET', '130')})
                if resync_resp.status_code != HTTPStatus.CREATED:
                    current_app.logger.error('Resync failed with status %s', resync_resp.status_code)
                current_app.logger.debug('Resync complete.')
            except Exception as error:  # noqa: B902
                current_app.logger.debug(error.with_traceback(None))
                current_app.logger.error('Resync failed.')

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
