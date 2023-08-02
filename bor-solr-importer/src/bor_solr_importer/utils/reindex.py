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
from datetime import datetime, timezone
from http import HTTPStatus
from time import sleep

import requests
from flask import current_app
from bor_api.exceptions import SolrException
from bor_api.services import bor_solr
from bor_api.services.authz import get_bearer_token


def get_replication_detail(field: str, leader: bool):
    """Verify the replication detail for the core."""
    resp = bor_solr.replication('details', leader)
    if leader:
        return resp.json()['details'][field]
    return resp.json()['details']['follower'][field]


def reindex_prep(is_preload: bool):
    """Execute reindex operations needed before index is reloaded."""
    if not is_preload:
        # backup leader index
        backup_trigger_time = (datetime.utcnow()).replace(tzinfo=timezone.utc)
        backup = bor_solr.replication('backup', True)
        current_app.logger.debug(backup.json())
        # disable follower polling during reindex
        disable_polling = bor_solr.replication('disablepoll', False)
        current_app.logger.debug(disable_polling.json())
        # await 10 seconds in case a poll was in progress
        sleep(10)
        # disable leader replication for reindex duration
        disable_replication = bor_solr.replication('disablereplication', True)
        current_app.logger.debug(disable_replication.json())
        # verify current backup is from just now and was successful in case of failure
        backup_detail = get_replication_detail('backup', True)
        backup_start_time = datetime.fromisoformat(backup_detail['startTime'])
        if not (backup_detail['status'] == 'success' and backup_trigger_time < backup_start_time):
            current_app.logger.debug('Backup detail: %s', backup_detail)
            raise SolrException('Failed to backup leader index', str(backup_detail), HTTPStatus.INTERNAL_SERVER_ERROR)
        # verify follower polling disabled so it doesn't update until reindex is complete
        is_polling_disabled = get_replication_detail('isPollingDisabled', False)
        if not bool(is_polling_disabled):
            current_app.logger.debug('is_polling_disabled: %s', is_polling_disabled)
            raise SolrException('Failed disable polling on follower',
                                str(is_polling_disabled),
                                HTTPStatus.INTERNAL_SERVER_ERROR)

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
    # reenable leader replication
    enable_replication = bor_solr.replication('enablereplication', True)
    current_app.logger.debug(enable_replication.json())
    sleep(5)
    # force the follwer to fetch the new index
    fetch_new_idx = bor_solr.replication('fetchindex', False)
    current_app.logger.debug(fetch_new_idx.json())
    sleep(10)
    # renable polling
    enable_polling = bor_solr.replication('enablepoll', False)
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
            enable_replication = bor_solr.replication('enablereplication', True)
            current_app.logger.debug(enable_replication.json())
            sleep(5)
            enable_polling = bor_solr.replication('enablepolling', False)
            current_app.logger.debug(enable_polling.json())
            return
        if (status.json())['status'] == 'failed':
            break
        sleep(5)
    current_app.logger.error('Failed to restore leader index. Manual intervention required.')
