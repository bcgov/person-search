# Copyright © 2022 Province of British Columbia
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
from datetime import datetime
from dataclasses import asdict
from http import HTTPStatus

import psycopg2
import requests
from flask import current_app
from bor_api.exceptions import SolrException
from bor_api.services import bor_solr
from bor_api.services.solr.solr_docs import Address, Entity, EntityRole, DateRange

from bor_solr_importer import create_app, oracle_db
from bor_solr_importer.enums import ColinPartyTypeCode


def collect_colin_data():
    """Collect data from COLIN."""
    current_app.logger.debug('Connecting to Oracle instance...')
    cursor = oracle_db.connection.cursor()
    current_app.logger.debug('Collecting COLIN data...')
    cursor.execute("""
        SELECT c.corp_num as identifier, c.corp_typ_cd as legal_type, c.bn_15 as tax_id,
            cn.corp_nme as legal_name, cp.business_nme as organization_name, cp.first_nme as first_name,
            cp.last_nme as last_name, cp.middle_nme as middle_initial, cp.party_typ_cd, cp.corp_party_id as party_id,
            CASE cos.op_state_typ_cd
                when 'ACT' then 'ACTIVE' when 'HIS' then 'HISTORICAL'
                else 'ACTIVE' END as state
        FROM corporation c
        join corp_state cs on cs.corp_num = c.corp_num
        join corp_op_state cos on cos.state_typ_cd = cs.state_typ_cd
        join corp_name cn on cn.corp_num = c.corp_num
        left join (select business_nme, first_nme, last_nme, middle_nme, corp_num, party_typ_cd, corp_party_id
                from corp_party
                where end_event_id is null and party_typ_cd in ('FIO','FBO')
            ) cp on cp.corp_num = c.corp_num
        WHERE c.corp_typ_cd not in ('BEN','CP','GP','SP')
            and cs.end_event_id is null
            and cn.end_event_id is null
            and cn.corp_name_typ_cd in ('CO', 'NB')
        """)
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
            a.street,a.street_additional,a.city,a.country,a.region,a.postal_code,
            pr.id as party_role_id,pr.role,pr.appointment_date,pr.cessation_date,
            p.first_name,p.middle_initial,p.last_name,p.organization_name,p.party_type,
            p.id as party_id,p.identifier as party_identifier,
            p_a.street as party_street,p_a.street_additional as party_street_additional,
            p_a.city as party_city,p_a.country as party_country,p_a.region as party_region,
            p_a.postal_code as party_postal_code,
            CASE when b.state = 'LIQUIDATION' then 'ACTIVE' else b.state END state
        FROM businesses b
            LEFT JOIN offices o ON o.business_id = b.id
            LEFT JOIN addresses a ON a.office_id = o.id
            LEFT JOIN party_roles pr on pr.business_id = b.id
            LEFT JOIN parties p on p.id = pr.party_id
            LEFT JOIN addresses p_a ON p_a.id = p.delivery_address_id
        WHERE b.legal_type in ('BEN', 'CP', 'SP', 'GP')
            AND o.office_type='registeredOffice'
            AND a.address_type='delivery'
        """)
    return cur


def prep_data(data: list[dict[str,str]], cur, source: str) -> list[Entity]:
    """Return the list of BusinessDocs for the given raw db data."""
    prepped_data: dict[str,Entity] = {}

    def get_party_name(item_dict: dict[str,str]) -> str:
        """Return the parsed name of the party in the given doc info."""
        if item_dict['organization_name']:
            return item_dict['organization_name'].strip()
        person_name = ''
        if item_dict['first_name']:
            person_name += item_dict['first_name'].strip()
        if item_dict['middle_initial']:
            person_name += ' ' + item_dict['middle_initial'].strip()
        if item_dict['last_name']:
            person_name += ' ' + item_dict['last_name'].strip()
        return person_name.strip()

    def get_party_role(type_cd: str, legal_type: str) -> str:
        """Return the lear party_type given the colin party type code."""
        if type_cd == ColinPartyTypeCode.DIRECTOR:
            return 'director'
        if type_cd == ColinPartyTypeCode.FIRM_COMP_PARTY:
            return 'completing_party'
        if type_cd == ColinPartyTypeCode.INCORPORATOR:
            return 'incorporator'
        if type_cd in [ColinPartyTypeCode.FIRM_BUS_OWNER.value, ColinPartyTypeCode.FIRM_IND_OWNER.value]:
            if legal_type == 'SP':
                return 'proprietor'
            return 'partner'
        return 'unknown'

    for item in data:
        item_dict = dict(zip([x[0].lower() for x in cur.description], item))
        if not item_dict['identifier'] in prepped_data:
            # add entity doc with address
            street = f"{item_dict['street']} {item_dict.get('street_additional', '')}"
            business_address = Address(addressType='DELIVERY',
                                       addressCity=item_dict['city'],
                                       addressCountry=item_dict['country'],
                                       addressRegion=item_dict['region'],
                                       streetAddress=street,
                                       postalCode=item_dict['postal_code'])

            prepped_data[item_dict['identifier']] = Entity(entityAddresses=[business_address],
                                                           entityType='BUSINESS',
                                                           identifier=item_dict['identifier'],
                                                           legalName=item_dict['legal_name'],
                                                           legalType=item_dict['legal_type'],
                                                           state=item_dict['state'],
                                                           bn=item_dict.get('tax_id'))

        elif not prepped_data[item_dict['identifier']].legalType:
            # if business was added as a party then it won't have the legal_type, state, or bn set
            prepped_data[item_dict['identifier']].legalType = item_dict['legal_type']
            prepped_data[item_dict['identifier']].state = item_dict['state']
            prepped_data[item_dict['identifier']].bn = item_dict['tax_id']

        has_party = item_dict.get('party_id')
        party_already_added = False
        party_role: EntityRole = None
        if has_party:
            # prep party fields
            if not item_dict.get('role'):
                item_dict['role'] = get_party_role(item_dict.get('party_typ_cd'), item_dict['legal_type'])
            item_dict['role'] = item_dict['role'].replace('_', ' ').upper()
            if not item_dict.get('party_type'):
                item_dict['party_type'] = 'organization' if item_dict['organization_name'] else 'person'
            # set party role
            role_date_range = DateRange(start=datetime.isoformat(item_dict['appointment_date'], timespec='seconds').replace('+00:00', 'Z'),
                                        end=item_dict.get('cessation_date', None))
            if role_date_range.end:
                role_date_range.end = datetime.isoformat(role_date_range.end, timespec='seconds').replace('+00:00', 'Z')
            party_role = EntityRole(active=False if role_date_range.end else True,
                                    relatedBN=item_dict['tax_id'],
                                    relatedEntityType='BUSINESS',
                                    relatedIdentifier=item_dict['identifier'],
                                    relatedLegalType=item_dict['legal_type'],
                                    relatedName=item_dict['legal_name'],
                                    relatedState=item_dict['state'],
                                    roleDates=[role_date_range],
                                    roleType=item_dict['role'])
            # check if entity record already there
            party_id = item_dict.get('party_identifier') or f"{source}{item_dict['party_id']}{item_dict['party_role_id']}"
            party_already_added = party_id in prepped_data
            

        if party_already_added:
            # party already added as entity -- add the new entity role to it
            roles = prepped_data[party_id].get('roles', [])
            prepped_data[party_id].roles = roles.append(party_role)

        elif has_party:
            # add new entity doc for party including address and role
            street = f"{item_dict['party_street']} {item_dict.get('party_street_additional', '')}"
            party_address = Address(addressType='DELIVERY',
                                    addressCity=item_dict['party_city'],
                                    addressCountry=item_dict['party_country'],
                                    addressRegion=item_dict['party_region'],
                                    streetAddress=street,
                                    postalCode=item_dict['party_postal_code'])
            
            party_entity = Entity(entityAddresses=[party_address],
                                  entityType='PERSON' if item_dict['party_type'] == 'person' else 'BUSINESS',
                                  identifier=party_id,
                                  legalName=get_party_name(item_dict),
                                  roles=[party_role])

            prepped_data[party_id] = party_entity
            

    return [prepped_data[x] for x in prepped_data]


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
        # colin_data_cur = collect_colin_data()
        # colin_data = colin_data_cur.fetchall()
        # current_app.logger.debug('Prepping COLIN data...')
        # prepped_colin_data = prep_data(colin_data, colin_data_cur, 'COLIN')
        # current_app.logger.debug(f'{len(prepped_colin_data)} COLIN records ready for import.')
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
        # current_app.logger.debug('Importing records from COLIN...')
        # count = update_solr(prepped_colin_data, 'COLIN')
        # current_app.logger.debug('COLIN import completed.')
        current_app.logger.debug('Importing records from LEAR...')
        count = update_solr(prepped_lear_data, 'LEAR')
        current_app.logger.debug('LEAR import completed.')
        current_app.logger.debug(f'Total records imported: {count}')

        if not current_app.config.get('PRELOADER_JOB', False):
            try:
                current_app.logger.debug('Resyncing any overwritten docs during import...')
                api_url = f'{current_app.config.get("BOR_API_URL")}{current_app.config.get("BOR_API_V1")}'
                resync_resp = requests.post(url=f'{api_url}/internal/solr/update/resync',
                                            json={'minutesOffset': 60})
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
