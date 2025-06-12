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
import time
from http import HTTPStatus

import requests
from flask import current_app

from bor_solr_importer import create_app
from bor_solr_importer.bor_api.exceptions import SolrException
from bor_solr_importer.bor_api.services.authz import get_bearer_token
from bor_solr_importer.utils import (
    collect_btr_data,
    collect_colin_data,
    collect_lear_data,
    prep_data,
    prep_data_btr,
    reindex_post,
    reindex_prep,
    reindex_recovery,
    update_solr,
)


def load_search_core():  # noqa: PLR0915, PLR0912
    """Load data from LEAR and COLIN into the search core."""
    # TODO: fix noqa
    try:
        is_reindex = current_app.config.get("REINDEX_CORE")
        is_preload = current_app.config.get("PRELOADER_JOB")
        include_btr_load = current_app.config.get("INCLUDE_BTR_LOAD")
        include_colin_load = current_app.config.get("INCLUDE_COLIN_LOAD")
        include_lear_load = current_app.config.get("INCLUDE_LEAR_LOAD")

        if is_reindex and current_app.config.get("IS_PARTIAL_IMPORT"):
            current_app.logger.error("Attempted reindex on partial data set.")
            current_app.logger.debug("Setting reindex to False to prevent potential data loss.")
            is_reindex = False

        if is_reindex:
            current_app.logger.debug("---------- Pre Reindex Actions ----------")
            reindex_prep(is_preload)

        try:
            btr_id_links: dict = {}
            total_btr_count = 0
            if include_btr_load:
                current_app.logger.debug("---------- Collecting/Importing BTR Data ----------")
                btr_fetch_count = 0
                batch_limit = current_app.config.get("BTR_BATCH_LIMIT")
                loop_count = 0
                while loop_count < 100:  # noqa: PLR2004
                    # NOTE: should never get to this condition
                    loop_count += 1
                    current_app.logger.debug("********** Collecting BTR data **********")
                    start_time_btr = time.time()
                    btr_data_cur = collect_btr_data(batch_limit, btr_fetch_count)
                    btr_data = btr_data_cur.fetchall()
                    current_app.config["TIME_WAITED_DATA_PARSING_BTR"] += time.time() - start_time_btr
                    btr_fetch_count += len(btr_data)
                    btr_data_cur.close()
                    if not btr_data:
                        # this should be the condition that breaks the loop (BTR_BATCH_LIMIT should be set high enough)
                        break

                    current_app.logger.debug("********** Mapping BTR data **********")
                    prepped_btr_data, batch_btr_id_links = prep_data_btr(btr_data, btr_data_cur.keys())
                    btr_id_links = {**btr_id_links, **batch_btr_id_links}
                    current_app.logger.debug(f"{len(prepped_btr_data)} BTR records ready for import.")

                    current_app.logger.debug("********** Importing BTR entities **********")
                    total_btr_count += update_solr(prepped_btr_data, "BTR")
                    current_app.logger.debug(f"BTR batch import completed. Records imported: {total_btr_count}.")
                    del btr_data, prepped_btr_data, batch_btr_id_links

                current_app.logger.debug(f"BTR import completed. Total BTR records imported: {total_btr_count}")

            total_colin_count = 0
            if include_colin_load:
                current_app.logger.debug("---------- Collecting/Importing COLIN Entities ----------")
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
                    {"min": "0000000", "max": "0250000"},
                    {"min": "0250000", "max": "0500000"},
                    {"min": "0500000", "max": "0750000"},
                    {"min": "0750000", "max": "0950000"},
                    {"min": "0950000", "max": "A0000000"},
                    {"min": "A0000000", "max": "S0000000"},
                    {"min": "S0000000", "max": "S0025000"},
                    {"min": "S0025000", "max": None}
                ]
                colin_data_descs = []
                start = current_app.config.get("CORP_NUM_LIMITS_START")
                end = current_app.config.get("CORP_NUM_LIMITS_END")
                for corp_num_limit in corp_num_limits[start:end]:
                    range_str = f"{corp_num_limit['min']} to {corp_num_limit['max'] or '*'}"
                    current_app.logger.debug(f"********** COLIN Corp Batch {range_str} **********")
                    start_time_colin = time.time()
                    colin_data_cur = collect_colin_data(corp_num_limit["min"], corp_num_limit["max"])
                    current_app.logger.debug("Fetching corp batch rows...")
                    colin_data = colin_data_cur.fetchall()
                    current_app.config["TIME_WAITED_DATA_DB_SELECT_COLIN"] += time.time() - start_time_colin
                    if not colin_data_descs:
                        # just need to do once
                        colin_data_descs = [desc[0].lower() for desc in colin_data_cur.description]
                    colin_data_cur.close()
                    # NB: need full data set under each corp num to collapse parties properly
                    current_app.logger.debug("********** Mapping COLIN Entities **********")
                    prepped_colin_data, partial_btr_updates = prep_data(colin_data,
                                                                        colin_data_descs,
                                                                        "COLIN",
                                                                        btr_id_links)
                    current_app.logger.debug(f"COLIN entities ready for import: {len(prepped_colin_data)}")
                    # execute update to solr in batches
                    current_app.logger.debug("********** Importing COLIN Entities **********")
                    corp_num_batch_count = update_solr(prepped_colin_data, "COLIN")
                    current_app.logger.debug(
                        f"COLIN Corp Batch import completed. Entities imported: {corp_num_batch_count}.")
                    total_colin_count += corp_num_batch_count
                    current_app.logger.debug(f"Total COLIN entities imported so far: {total_colin_count}.")

                    current_app.logger.debug(f"COLIN partial entities ready for import: {len(partial_btr_updates)}")
                    colin_btr_update_count = update_solr(partial_btr_updates, "COLIN-BTR Business Update", True)
                    current_app.logger.debug(f"COLIN partial entities imported: {colin_btr_update_count}")

                    # free up memory
                    del colin_data, prepped_colin_data, partial_btr_updates
                    gc.collect()
                    if corp_num_batch_count < 50000:  # noqa: PLR2004
                        # should only happen in dev/test
                        current_app.logger.debug("Waiting 1 min to give time for ORA connection closure.")
                        time.sleep(60)

                current_app.logger.debug(f"COLIN import completed. Total COLIN entities imported: {total_colin_count}.")

            lear_count = 0
            if include_lear_load:
                current_app.logger.debug("---------- Collecting LEAR Entities ----------")
                start_time_lear = time.time()
                lear_data_cur = collect_lear_data()
                lear_data = lear_data_cur.fetchall()
                current_app.config["TIME_WAITED_DATA_DB_SELECT_LEAR"] += time.time() - start_time_lear

                current_app.logger.debug("---------- Mapping LEAR data ----------")
                prepped_lear_data, partial_btr_updates = prep_data(
                    data=lear_data,
                    data_descs=lear_data_cur.keys(),
                    source="LEAR",
                    btr_id_links=btr_id_links
                )
                current_app.logger.debug(f"{len(prepped_lear_data)} LEAR records ready for import.")

                # execute update to solr in batches
                current_app.logger.debug("---------- Importing LEAR entities ----------")
                lear_count = update_solr(prepped_lear_data, "LEAR")
                current_app.logger.debug(f"LEAR import completed. Total LEAR entities imported: {lear_count}")

                current_app.logger.debug(f"LEAR partial entities ready for import: {len(partial_btr_updates)}")
                lear_btr_update_count = update_solr(partial_btr_updates, "LEAR-BTR Business Update", True)
                current_app.logger.debug(f"LEAR partial entities imported: {lear_btr_update_count}")

            current_app.logger.debug(f"Total entities imported: {total_btr_count + total_colin_count + lear_count}")
        except Exception as err:
            if is_reindex and not is_preload:
                reindex_recovery()
            raise err  # pass along

        try:
            current_app.logger.debug("---------- Resync ----------")
            current_app.logger.debug("Getting token for Resync...")
            token = get_bearer_token()
            headers = {"Authorization": "Bearer " + token}

            current_app.logger.debug("Resyncing any overwritten docs during import...")
            api_url = f'{current_app.config.get("BOR_API_URL")}{current_app.config.get("BOR_API_V1")}'
            resync_resp = requests.post(url=f"{api_url}/internal/solr/update/resync",
                                        headers=headers,
                                        json={"minutesOffset": current_app.config.get("RESYNC_OFFSET")},
                                        timeout=120)
            if resync_resp.status_code != HTTPStatus.CREATED:
                if resync_resp.status_code == HTTPStatus.GATEWAY_TIMEOUT:
                    current_app.logger.debug("Resync timed out -- check api for any individual failures.")
                else:
                    current_app.logger.error("Resync failed: %s, %s", resync_resp.status_code, resync_resp.json())
            else:
                current_app.logger.debug("Resync complete.")
        except Exception as error:
            current_app.logger.debug(error.with_traceback(None))
            current_app.logger.error("Resync failed.")

        try:
            current_app.logger.debug("---------- Final Commit ----------")
            current_app.logger.debug("Triggering final commit on leader to make changes visible to search...")
            update_solr([prepped_lear_data[-1]], "LEAR")
            current_app.logger.debug("Final commit complete.")

        except Exception as error:
            current_app.logger.debug(error.with_traceback(None))
            current_app.logger.error("Final commit failed. (This will only effect DEV).")

        if is_reindex and not is_preload:
            current_app.logger.debug("---------- Post Reindex Actions ----------")
            reindex_post()

        current_app.logger.debug("SOLR import finished successfully.")
        current_app.logger.debug("Time waited for getting auth token: %s",
                                 current_app.config["TIME_WAITED_AUTH_TOKEN_CALL"])
        current_app.logger.debug("Time waited for BTR data select: %s",
                                 current_app.config["TIME_WAITED_DATA_DB_SELECT_BTR"])
        current_app.logger.debug("Time waited for BTR data parse: %s",
                                 current_app.config["TIME_WAITED_DATA_PARSING_BTR"])
        current_app.logger.debug("Time waited for COLIN data select: %s",
                                 current_app.config["TIME_WAITED_DATA_DB_SELECT_COLIN"])
        current_app.logger.debug("Time waited for COLIN data parse: %s",
                                 current_app.config["TIME_WAITED_DATA_PARSING_COLIN"])
        current_app.logger.debug("Time waited for LEAR data select: %s",
                                 current_app.config["TIME_WAITED_DATA_DB_SELECT_LEAR"])
        current_app.logger.debug("Time waited for LEAR data parse: %s",
                                 current_app.config["TIME_WAITED_DATA_PARSING_LEAR"])
        current_app.logger.debug("Time waited for full import calls: %s",
                                 current_app.config["TIME_WAITED_IMPORT_API_CALL_FULL"])
        current_app.logger.debug("Time waited for partial import calls: %s",
                                 current_app.config["TIME_WAITED_IMPORT_API_CALL_PARTIAL"])
        current_app.logger.debug("Time waited for error import calls: %s",
                                 current_app.config["TIME_WAITED_IMPORT_API_CALL_ERROR"])

        total_data_select = (current_app.config["TIME_WAITED_DATA_DB_SELECT_BTR"] +
                             current_app.config["TIME_WAITED_DATA_DB_SELECT_COLIN"] +
                             current_app.config["TIME_WAITED_DATA_DB_SELECT_LEAR"])
        total_data_parse = (current_app.config["TIME_WAITED_DATA_PARSING_BTR"] +
                            current_app.config["TIME_WAITED_DATA_PARSING_COLIN"] +
                            current_app.config["TIME_WAITED_DATA_PARSING_LEAR"])
        total_import = (current_app.config["TIME_WAITED_IMPORT_API_CALL_FULL"] +
                        current_app.config["TIME_WAITED_IMPORT_API_CALL_PARTIAL"] +
                        current_app.config["TIME_WAITED_IMPORT_API_CALL_ERROR"])
        current_app.logger.debug("Total time waited for data selects: %s", total_data_select)
        current_app.logger.debug("Total time waited for data parsing: %s", total_data_parse)
        current_app.logger.debug("Total time waited for import calls: %s", total_import)

    except SolrException as err:
        current_app.logger.debug(f"SOLR gave status code: {err.status_code}")
        current_app.logger.error(err.error)
        current_app.logger.debug("SOLR import failed.")
        sys.exit(1)


if __name__ == "__main__":
    print("Starting data importer...")  # noqa: T201
    app = create_app()
    with app.app_context():
        start_time = time.time()
        load_search_core()
        print(f"Total importer run time: {time.time() - start_time}")  # noqa: T201
        sys.exit(0)
