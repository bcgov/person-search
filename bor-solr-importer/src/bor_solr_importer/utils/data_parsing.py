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
"""Data parsing functions."""
import re
from datetime import datetime

from bor_api.services.solr.solr_docs import Address, Entity, EntityRole, DateRange

from bor_solr_importer.enums import ColinPartyTypeCode


def get_party_name(item_dict: dict[str, str]) -> str:
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

def get_party_role(type_cd: str, legal_type: str, desc: str) -> str:
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
    return desc or 'unknown'


def get_address(item_dict: dict[str, str], is_party_address: bool) -> Address:
    """Return the address doc for the data."""
    prefix = 'party_' if is_party_address else ''

    address_format_type = f'{prefix}address_format_type'
    street = f'{prefix}street'
    street_add = f'{prefix}street_additional'
    street_add_3 = f'{prefix}addr_line_3'

    unit_type = f'{prefix}unit_type'
    unit_no = f'{prefix}unit_no'
    civic_no = f'{prefix}civic_no'
    civic_no_suffix = f'{prefix}civic_no_suffix'
    street_name = f'{prefix}street_name'
    street_type = f'{prefix}street_type'
    street_direction = f'{prefix}street_direction'

    route_service_type = f'{prefix}route_service_type'
    lock_box_no = f'{prefix}lock_box_no'
    route_service_no = f'{prefix}route_service_no'
    installation_type = f'{prefix}installation_type'
    installation_name = f'{prefix}installation_name'

    city = f'{prefix}city'
    country = f'{prefix}country'
    region = f'{prefix}region'
    postal = f'{prefix}postal_code'
    
    # get the street info based on the address format type
    street_address = ''
    if address_format_type in ['BAS', 'ADV']:
        street_elements = [item_dict[unit_type] or '',
                           item_dict[unit_no] or '',
                           item_dict[civic_no] or '',
                           item_dict[civic_no_suffix] or '',
                           item_dict[street_name] or '',
                           item_dict[street_type] or '',
                           item_dict[street_direction] or '']
        street_address = ' '.join([x.strip() for x in street_elements]).strip()
        if address_format_type == 'ADV':
            street_add_elements = [item_dict[route_service_type] or '',
                                   item_dict[lock_box_no] or '',
                                   item_dict[route_service_no] or '',
                                   item_dict[installation_type] or '',
                                   item_dict[installation_name] or '']
            street_address += ' '.join([x.strip() for x in street_add_elements])
    else:
        # address format type of 'null' or 'FOR'
        street_elements = [item_dict[street] or '',
                           item_dict[street_add] or '',
                           item_dict.get(street_add_3) or '']
        street_address = ' '.join([x.strip() for x in street_elements])
    
    return Address(addressType='DELIVERY',
                   addressCity=(item_dict[city] or '').strip(),
                   addressCountry=(item_dict[country] or '').strip(),
                   addressRegion=(item_dict[region] or '').strip(),
                   postalCode=(item_dict[postal] or '').strip(),
                   streetAddress=street_address.strip())


def needs_bc_prefix(identifier: str, legal_type: str) -> bool:
    """Return if the identifier should have the BC prefix or not."""
    numbers_only_rgx = r'^[0-9]+$'
    # TODO: get legal types from shared enum
    return legal_type in ['BEN', 'BC', 'CC', 'ULC'] and re.search(numbers_only_rgx, identifier)


def prep_data(data: list[dict[str, str]], cur, source: str) -> list[Entity]:  # pylint: disable=too-many-locals
    """Return the list of BusinessDocs for the given raw db data."""
    prepped_data: dict[str, Entity] = {}

    for item in data:
        item_dict = dict(zip([x[0].lower() for x in cur.description], item))
        if needs_bc_prefix(item_dict['identifier'], item_dict['legal_type']):
            item_dict['identifier'] = 'BC' + item_dict['identifier']
        if not item_dict['identifier'] in prepped_data:
            # add entity doc with address
            business_address = get_address(item_dict, False)
            prepped_data[item_dict['identifier']] = Entity(entityAddresses=[business_address],
                                                           entityType='BUSINESS',
                                                           identifier=item_dict['identifier'].strip(),
                                                           legalName=item_dict['legal_name'].strip(),
                                                           legalType=item_dict['legal_type'].strip(),
                                                           state=item_dict['state'].strip(),
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
                item_dict['role'] = get_party_role(item_dict.get('party_typ_cd'), item_dict['legal_type'], item_dict['party_type_desc'])
            item_dict['role'] = item_dict['role'].replace('_', ' ').upper()
            if not item_dict.get('party_type'):
                item_dict['party_type'] = 'organization' if item_dict['organization_name'] else 'person'
            # set party role
            role_date_range = None
            if appointment_date := item_dict['appointment_date']:
                role_date_range = DateRange(start=datetime.isoformat(appointment_date,
                                                                     timespec='seconds').replace('+00:00', 'Z'),
                                            end=item_dict.get('cessation_date', None))
                if role_date_range.end:
                    role_date_range.end = datetime.isoformat(role_date_range.end,
                                                             timespec='seconds').replace('+00:00', 'Z')
            active = not item_dict.get('end_event_id')
            if role_date_range:
                active = not role_date_range.end
            party_role = EntityRole(active=active,
                                    relatedBN=item_dict['tax_id'],
                                    relatedEntityType='BUSINESS',
                                    relatedIdentifier=item_dict['identifier'],
                                    relatedLegalType=item_dict['legal_type'],
                                    relatedName=item_dict['legal_name'],
                                    relatedState=item_dict['state'],
                                    roleDates=[role_date_range] if role_date_range else None,
                                    roleType=item_dict['role'])
            # check if entity record already there
            party_id = item_dict.get('party_identifier') \
                or f"{source}{item_dict['party_id']}{item_dict.get('party_role_id', '')}"
            party_already_added = party_id in prepped_data

        if party_already_added:
            # party already added as entity -- add the new entity role to it
            if not prepped_data[party_id].roles:
                prepped_data[party_id].roles = []
            prepped_data[party_id].roles.append(party_role)

        elif has_party:
            # add new entity doc for party including address and role
            party_address = get_address(item_dict, True)
            party_entity = Entity(entityAddresses=[party_address],
                                  entityType='PERSON' if item_dict['party_type'] == 'person' else 'BUSINESS',
                                  identifier=party_id,
                                  legalName=get_party_name(item_dict),
                                  roles=[party_role])

            prepped_data[party_id] = party_entity

    return [prepped_data[x] for x in prepped_data]