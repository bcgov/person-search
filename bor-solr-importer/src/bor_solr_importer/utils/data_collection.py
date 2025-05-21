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
"""Data collection functions."""
import psycopg2
from flask import current_app

from bor_solr_importer import oracle_db


def _get_stringified_list_for_sql(config_value: str) -> str:
    """Return the values from the config in a format usable for the execute statement."""
    if items := current_app.config.get(config_value, []):
        return ",".join([f"'{x}'" for x in items]).replace(")", "")

    return ""


def collect_colin_data(corp_num_min: str, corp_num_max: str | None = None):
    """Collect data from COLIN."""
    max_corp_num_clause = f"and c.corp_num < '{corp_num_max}'" if corp_num_max else ""
    debug_clause = ""
    if debug_identfiers := _get_stringified_list_for_sql(config_value="DEBUG_IDENTIFIERS"):
        # will only select from identifiers we are interested in debugging
        debug_clause = f"and c.corp_num in ({debug_identfiers})"

    current_app.logger.debug("Connecting to Oracle instance...")
    cursor = oracle_db.connection.cursor()

    current_app.logger.debug("Collecting batch from COLIN...")
    cursor.execute(f"""
        SELECT c.corp_num as identifier, c.corp_typ_cd as legal_type, c.bn_15 as tax_id, c.admin_email,
            cn.corp_nme as legal_name, cp.business_nme as organization_name, cp.first_nme as first_name,
            cp.last_nme as last_name, cp.middle_nme as middle_initial, cp.party_typ_cd, cp.corp_party_id as party_id,
            cp.appointment_dt as appointment_date, cp.cessation_dt as cessation_date, cp.start_event_id,
            cp.end_event_id, cp.prev_party_id, cp.delivery_addr_id,
            pt.short_desc as party_type_desc, cpe.event_typ_cd, cpe.event_timestmp, cpef.effective_dt,
            cpa.province as party_region, cpa.country_typ_cd as party_country, cpa.city as party_city,
            cpa.postal_cd as party_postal_code, cpa.addr_line_1 as party_street, cpa.unit_type as party_unit_type,
            cpa.unit_no as party_unit_no, cpa.civic_no as party_civic_no, cpa.civic_no_suffix as party_civic_no_suffix,
            cpa.street_name as party_street_name, cpa.street_type as party_street_type,
            cpa.street_direction as party_street_direction, cpa.address_format_type as party_address_format_type,
            cpa.addr_line_2 as party_street_additional, cpa.addr_line_3 as party_addr_line_3,
            cpa.route_service_type as party_route_service_type, cpa.lock_box_no as party_lock_box_no,
            cpa.route_service_no as party_route_service_no, cpa.installation_type as party_installation_type,
            cpa.installation_name as party_installation_name,
            cpam.province as party_mail_region, cpam.country_typ_cd as party_mail_country,
            cpam.city as party_mail_city, cpam.postal_cd as party_mail_postal_code,
            cpam.addr_line_1 as party_mail_street, cpam.unit_type as party_mail_unit_type,
            cpam.unit_no as party_mail_unit_no, cpam.civic_no as party_mail_civic_no,
            cpam.civic_no_suffix as party_mail_civic_no_suffix, cpam.street_name as party_mail_street_name,
            cpam.street_type as party_mail_street_type, cpam.street_direction as party_mail_street_direction,
            cpam.address_format_type as party_mail_address_format_type,
            cpam.addr_line_2 as party_mail_street_additional, cpam.addr_line_3 as party_mail_addr_line_3,
            cpam.route_service_type as party_mail_route_service_type, cpam.lock_box_no as party_mail_lock_box_no,
            cpam.route_service_no as party_mail_route_service_no,
            cpam.installation_type as party_mail_installation_type,
            cpam.installation_name as party_mail_installation_name,
            a.province as region, a.country_typ_cd as country, a.city, a.postal_cd as postal_code,
            a.addr_line_1 as street, a.addr_line_2 as street_additional, a.addr_line_3, a.unit_type, a.unit_no,
            a.civic_no, a.civic_no_suffix, a.street_name, a.street_type, a.street_direction, a.address_format_type,
            a.route_service_type, a.lock_box_no, a.route_service_no, a.installation_type, a.installation_name,
            CASE cos.op_state_typ_cd
                when 'ACT' then 'ACTIVE' when 'HIS' then 'HISTORICAL'
                else 'ACTIVE' END as state
        FROM corporation c
        join corp_state cs on cs.corp_num = c.corp_num
        join corp_op_state cos on cos.state_typ_cd = cs.state_typ_cd
        join corp_name cn on cn.corp_num = c.corp_num
        join corp_party cp on cp.corp_num = c.corp_num
        join party_type pt on pt.party_typ_cd = cp.party_typ_cd
        left join event cpe on cpe.event_id = cp.start_event_id
        left join filing cpef on cpef.event_id = cp.start_event_id
        left join address cpa on cpa.addr_id = cp.delivery_addr_id
        left join address cpam on cpam.addr_id = cp.mailing_addr_id
        left join office o on o.corp_num = c.corp_num and o.office_typ_cd = 'RG' and o.end_event_id is null
        left join address a on a.addr_id = o.delivery_addr_id
        WHERE c.corp_typ_cd not in ({_get_stringified_list_for_sql('MODERNIZED_LEGAL_TYPES')})
            and cs.end_event_id is null
            and cn.end_event_id is null
            and cn.corp_name_typ_cd in ('CO', 'NB')
            and cp.party_typ_cd not in ('PAS','PDI','PSA','RAD','RAF','RAO','RAS','TAP','TAA','TSP')
            and c.corp_num >= :offset_corp_num
            {max_corp_num_clause}
            {debug_clause}
        """, offset_corp_num=corp_num_min)
    return cursor


def collect_lear_data():
    """Collect data from LEAR."""
    debug_clause = ""
    if debug_identfiers := _get_stringified_list_for_sql("DEBUG_IDENTIFIERS"):
        # will only select from identifiers we are interested in debugging
        debug_clause = f"and b.identifier in ({debug_identfiers})"

    current_app.logger.debug("Connecting to LEAR OCP Postgres instance...")
    conn = psycopg2.connect(host=current_app.config.get("DB_HOST"),
                            port=current_app.config.get("DB_PORT"),
                            database=current_app.config.get("DB_NAME"),
                            user=current_app.config.get("DB_USER"),
                            password=current_app.config.get("DB_PASSWORD"))
    cur = conn.cursor()
    current_app.logger.debug("Collecting LEAR data...")
    cur.execute(f"""
        SELECT b.identifier,b.legal_name,b.legal_type,b.tax_id,
            pr.id as party_role_id,pr.role,pr.appointment_date,pr.cessation_date,
            p.first_name,p.middle_initial,p.last_name,p.organization_name,p.party_type,
            p.id as party_id,p.identifier as party_identifier,
            p_a.street as party_street,p_a.street_additional as party_street_additional,
            p_a.city as party_city,p_a.country as party_country,p_a.region as party_region,
            p_a.postal_code as party_postal_code, p_a.delivery_instructions as party_delivery_instructions,
            a.street,a.street_additional,a.city,a.country,a.region,a.postal_code,a.delivery_instructions,
            CASE when b.state = 'LIQUIDATION' then 'ACTIVE' else b.state END state
        FROM businesses b
            JOIN party_roles pr on pr.business_id = b.id
            JOIN parties p on p.id = pr.party_id
            LEFT JOIN addresses p_a ON p_a.id = p.delivery_address_id
            LEFT JOIN offices o ON o.business_id = b.id AND o.office_type in ('registeredOffice')
            LEFT JOIN addresses a ON a.office_id = o.id AND a.address_type='delivery'
        WHERE b.legal_type in ({_get_stringified_list_for_sql('MODERNIZED_LEGAL_TYPES')})
            AND pr.role != ''
            {debug_clause}
        """)
    return cur


def collect_btr_data(limit: int | None = None, offset: int | None = None):
    """Collect data from BTR."""
    limit_clause = ""
    if limit:
        limit_clause = f"LIMIT {limit}"
    if offset:
        limit_clause += f" OFFSET {offset}"
    if limit_clause:
        # NOTE: needed in order to make sure we get every record when doing batch loads
        limit_clause = f"ORDER BY p.id {limit_clause}"

    debug_clause = ""
    if debug_identfiers := _get_stringified_list_for_sql("DEBUG_IDENTIFIERS"):
        # will only select from identifiers we are interested in debugging
        debug_clause = f"WHERE s.business_identifier IN ({debug_identfiers})"

    current_app.logger.debug("Connecting to BTR GCP Postgres instance...")
    conn = psycopg2.connect(host=current_app.config.get("BTR_DB_HOST"),
                            port=current_app.config.get("BTR_DB_PORT"),
                            database=current_app.config.get("BTR_DB_NAME"),
                            user=current_app.config.get("BTR_DB_USER"),
                            password=current_app.config.get("BTR_DB_PASSWORD"))
    cur = conn.cursor()
    current_app.logger.debug("Collecting BTR data...")
    cur.execute(f"""
                SELECT s.business_identifier, o.ownership_json, p.person_json
                FROM submission s
                JOIN ownership o on s.id = o.submission_id
                JOIN person p on p.id = o.person_id
                {debug_clause} {limit_clause}
                """)
    return cur
