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


def collect_colin_data(offset: int, max_rows: int, cursor):
    """Collect data from COLIN."""
    cursor.execute("""
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
        WHERE c.corp_typ_cd not in ('BEN','CP','GP','SP')
            and cs.end_event_id is null
            and cn.end_event_id is null
            and cn.corp_name_typ_cd in ('CO', 'NB')
            and cp.party_typ_cd not in ('PAS','PDI','PSA','RAD','RAF','RAO','RAS','TAP','TAA','TSP')
        OFFSET :offset ROWS FETCH NEXT :max_rows ROWS ONLY
        """, offset=offset, max_rows=max_rows)
    return cursor


def collect_lear_data():
    """Collect data from LEAR."""
    current_app.logger.debug('Connecting to Postgres instance...')
    conn = psycopg2.connect(host=current_app.config.get('DB_HOST'),
                            port=current_app.config.get('DB_PORT'),
                            database=current_app.config.get('DB_NAME'),
                            user=current_app.config.get('DB_USER'),
                            password=current_app.config.get('DB_PASSWORD'))
    cur = conn.cursor()
    current_app.logger.debug('Collecting LEAR data...')
    cur.execute("""
        SELECT b.identifier,b.legal_name,b.legal_type,b.tax_id,
            pr.id as party_role_id,pr.role,pr.appointment_date,pr.cessation_date,
            p.first_name,p.middle_initial,p.last_name,p.organization_name,p.party_type,
            p.id as party_id,p.identifier as party_identifier,
            p_a.street as party_street,p_a.street_additional as party_street_additional,
            p_a.city as party_city,p_a.country as party_country,p_a.region as party_region,
            p_a.postal_code as party_postal_code,
            CASE when b.state = 'LIQUIDATION' then 'ACTIVE' else b.state END state
        FROM businesses b
            LEFT JOIN party_roles pr on pr.business_id = b.id
            LEFT JOIN parties p on p.id = pr.party_id
            LEFT JOIN addresses p_a ON p_a.id = p.delivery_address_id
        WHERE b.legal_type in ('BEN', 'CP', 'SP', 'GP')
        """)
    return cur
