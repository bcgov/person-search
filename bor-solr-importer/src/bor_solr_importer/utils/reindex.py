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
"""Manages util methods for reindexing."""
from http import HTTPStatus
from time import sleep

import requests
from flask import current_app
from bor_api.services import bor_solr
from bor_api.services.authz import get_bearer_token


def reindex_prep(is_preload: bool):
    """Execute reindex operations needed before index is reloaded."""
    if not is_preload:
        # backup leader index
        backup = bor_solr.replication('backup', True)
        current_app.logger.debug(backup.json())
        # disable follower polling during reindex
        disable_polling = bor_solr.replication('disablepolling', False)
        current_app.logger.debug(disable_polling.json())
        # await 10 seconds in case a poll was in progress
        sleep(10)
    # delete existing index
    current_app.logger.debug('REINDEX_CORE set: deleting current solr index...')
    bor_solr.delete_all_docs()

    if not is_preload:
        # update the synonym lists
        try:
            current_app.logger.debug('Getting token for synonym lists update...')
            token = get_bearer_token()
            headers = {'Authorization': 'Bearer ' + token}
            current_app.logger.debug('Updating synonym lists...')
            api_url = f'{current_app.config.get("BOR_API_URL")}{current_app.config.get("BOR_API_V1")}'
            update_resp = requests.put(url=f'{api_url}/internal/solr/update/synonyms', headers=headers, json={})
            if update_resp.status_code != HTTPStatus.OK:
                current_app.logger.error('Synonym lists update failed with status %s', update_resp.status_code)
            else:
                current_app.logger.debug('Synonym lists update complete.')
        except Exception as error:  # noqa: B902
            current_app.logger.debug(error.with_traceback(None))
            current_app.logger.error('Synonym lists update failed.')


def reindex_post():
    """Execute post reindex operations on the follower index."""
    # force the follwer to fetch the new index
    fetch_new_idx = bor_solr.replication('fetchindex', False)
    current_app.logger.debug(fetch_new_idx.json())
    # renable polling
    enable_polling = bor_solr.replication('enablepolling', False)
    current_app.logger.debug(enable_polling.json())


def reindex_recovery():
    """Restore the index on the leader and renable polling on the follower."""
    restore = bor_solr.replication('restore', True)
    current_app.logger.debug(restore.json())
    current_app.logger.debug('awaiting restore completion...')
    for i in range(100):
        current_app.logger.debug(f'Checking restore status ({i + 1} of 100)...')
        status = bor_solr.replication('restorestatus', True)
        if (status.json())['status'] == 'success':
            current_app.logger.debug('restore complete.')
            enable_polling = bor_solr.replication('enablepolling', False)
            current_app.logger.debug(enable_polling.json())
            return
        if (status.json())['status'] == 'failed':
            break
        sleep(5)
    current_app.logger.error('Failed to restore leader index. Manual intervention required.')
