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
import time
from http import HTTPStatus

import requests
from flask import current_app
from bor_api.exceptions import SolrException
from bor_api.services.authz import get_bearer_token


def _get_headers() -> dict[str, str]:
    """Return the headers including the new or cached token required for the solr import."""
    start = time.time()
    current_app.logger.debug('Getting token for Import...')
    token = get_bearer_token()
    current_app.logger.debug('Token set.')
    headers = {'Authorization': 'Bearer ' + token}
    current_app.config['TIME_WAITED_AUTH_TOKEN_CALL'] += time.time() - start
    return headers


def _get_wait_interval(err: Exception):
    """Return the base wait interval for the exception."""
    if isinstance(err.args, (tuple, list)) and err.args and isinstance(err.args[0], dict):
        if (error := err.args[0].get('error')) and isinstance(error, dict):
            if '408' in error.get('detail', ''):
                # increased base wait time for solr 408 error
                return 60
    return 20


def update_solr(docs: list[dict], data_name: str, partial=False) -> int:  # pylint: disable=too-many-locals;
    """Import data into solr."""
    # TODO: break into smaller pieces
    headers = _get_headers()
    api_url = f'{current_app.config.get("BOR_API_URL")}{current_app.config.get("BOR_API_V1")}'
    count = 0
    offset = 0
    rows = current_app.config.get('BATCH_SIZE_SOLR', 1000)
    if data_name == 'BTR':
        rows = current_app.config.get('BATCH_SIZE_SOLR_SI', 1000)
    retry_count = 0
    while count < len(docs) and rows > 0 and len(docs) - offset > 0:
        start = time.time()
        batch_amount = int(min(rows, len(docs) - offset) / (retry_count + 1))
        count += batch_amount
        # call bor-api import endpoint
        try:
            current_app.logger.debug('Importing batch...')
            import_resp = requests.put(url=f'{api_url}/internal/solr/import',
                                       headers=headers,
                                       json={'entities': docs[offset:count],
                                             'timeout': '60',
                                             'type': 'partial' if partial else 'full'},
                                       timeout=90)

            if import_resp.status_code != HTTPStatus.CREATED:
                error_json = 'Unable to parse error response json'
                try:
                    error_json = import_resp.json()
                except Exception as err:  # noqa: B902; Needs to catch any exception, don't care which
                    # log and continue
                    current_app.logger.debug('Error parsing resp json: %s', err)
                # try again
                raise Exception(  # pylint: disable=broad-exception-raised; Don't care about the type for this script
                    {'error': error_json, 'status_code': import_resp.status_code})
            retry_count = 0
        except Exception as err:  # noqa: B902; Needs to catch any exception, don't care which
            current_app.logger.debug(err)
            if retry_count < 5:
                # retry
                current_app.logger.debug('Failed to update solr with batch. Trying again (%s of 5)...', retry_count + 1)
                retry_count += 1
                # await some time before trying again
                base_wait_time = _get_wait_interval(err)
                current_app.logger.debug('Awaiting %s seconds before trying again...', base_wait_time * retry_count)
                time.sleep(base_wait_time * retry_count)
                # renew token for next try
                headers = _get_headers()
                # set count back
                count -= batch_amount
                # add time to error wait
                current_app.config['TIME_WAITED_IMPORT_API_CALL_ERROR'] += time.time() - start
                continue

            if retry_count == 5:
                # wait x minutes and then try one more time
                current_app.logger.debug(
                    'Max retries for batch exceeded. Awaiting 2 mins before trying one more time...')
                time.sleep(120)
                # renew token for next try
                headers = _get_headers()
                # try again
                retry_count += 1
                count -= batch_amount
                # add time to error wait
                current_app.config['TIME_WAITED_IMPORT_API_CALL_ERROR'] += time.time() - start
                continue

            # log and raise error
            current_app.logger.error('Retry count exceeded for batch.')
            raise SolrException('Retry count exceeded for updating SOLR. Aborting import.') from err

        offset = count
        current_app.logger.debug(f'Total batch {data_name} doc records imported: {count}')
        # add time to import wait
        import_type = 'PARTIAL' if partial else 'FULL'
        current_app.config[f'TIME_WAITED_IMPORT_API_CALL_{import_type}'] += time.time() - start
    return count
