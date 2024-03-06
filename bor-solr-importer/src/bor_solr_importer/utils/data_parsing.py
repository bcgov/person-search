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
from dataclasses import asdict
from datetime import datetime

from flask import current_app
from bor_api.services.bor_solr.doc_models import Address, Entity, EntityRole, DateRange
from bor_api.utils.data_converters import get_btr_owner

from bor_solr_importer.enums import ColinPartyTypeCode


def get_party_name(item_dict: dict[str, str]) -> str:
    """Return the parsed name of the party in the given doc info."""
    if item_dict.get('organization_name', None):
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


def get_address(item_dict: dict[str, str], is_party_address: bool, is_mail: bool) -> Address:  # noqa: E501; pylint: disable=too-many-locals;
    """Return the address doc for the data."""
    prefix = 'party_' if is_party_address else ''
    if is_mail:
        prefix += 'mail_'

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

    return Address(addressType='MAILING' if is_mail else 'DELIVERY',
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


def set_business_entity(item_dict: dict[str, str], prepped_data: dict[str, Entity]):
    """Set the business entity in the prepped data."""
    if not item_dict['identifier'] in prepped_data:
        # add entity doc with address
        prepped_data[item_dict['identifier']] = Entity(entityAddresses=[],
                                                       entityType='BUSINESS',
                                                       id=item_dict['identifier'].strip(),
                                                       identifier=item_dict['identifier'].strip(),
                                                       legalName=item_dict['legal_name'].strip(),
                                                       legalType=item_dict['legal_type'].strip(),
                                                       state=item_dict['state'].strip(),
                                                       bn=item_dict.get('tax_id'),
                                                       email=item_dict.get('admin_email'))

    elif not prepped_data[item_dict['identifier']].identifier:
        # if business was added as a party then it won't have the identifier, legal_type, state, or bn set
        prepped_data[item_dict['identifier']].identifier = item_dict['identifier'].strip()
        prepped_data[item_dict['identifier']].legalType = item_dict['legal_type'].strip()
        prepped_data[item_dict['identifier']].state = item_dict['state'].strip()
        prepped_data[item_dict['identifier']].bn = item_dict.get('tax_id')


def set_party_entity(item_dict: dict[str, str],
                     prepped_data: dict[str, Entity],
                     source: str,
                     is_debug_identifier=False) -> Entity:
    """Set the party entity in the prepped data."""
    has_party = item_dict.get('party_id')
    party_already_added = False
    party_role: EntityRole = None
    if not has_party:
        return None
    # prep party fields
    if not item_dict.get('role'):
        item_dict['role'] = get_party_role(item_dict.get('party_typ_cd'),
                                           item_dict['legal_type'],
                                           item_dict['party_type_desc'])

    if not item_dict.get('party_type'):
        item_dict['party_type'] = 'person'
        if item_dict.get('organization_name', None):
            item_dict['party_type'] = 'organization'

    if item_dict['party_type'] != 'person':
        # ignoring business parties for now
        return None

    # set party role
    role_date_range = DateRange(start=None, end=None)
    # NOTE: removes tzinfo due to incorrect time values stored in db
    if appointment_date := item_dict['appointment_date']:
        role_date_range.start = datetime.isoformat(appointment_date,
                                                   timespec='seconds').replace('+00:00', '')
    if cessation_date := item_dict.get('cessation_date', None):
        role_date_range.end = datetime.isoformat(cessation_date,
                                                 timespec='seconds').replace('+00:00', '')
        role_date_range.active = False

    party_id = item_dict.get('party_identifier') \
        or f"{source}{item_dict['party_id']}{item_dict['identifier']}" \
           f"{item_dict['role'].replace(' ', '_')}".upper()

    party_role = EntityRole(id=party_id + '/roles0',
                            relatedBN=item_dict['tax_id'],
                            relatedEmail=item_dict.get('admin_email'),
                            relatedEntityType='BUSINESS',
                            relatedIdentifier=item_dict['identifier'],
                            relatedLegalType=item_dict['legal_type'],
                            relatedName=item_dict['legal_name'],
                            relatedState=item_dict['state'],
                            roleDates=[role_date_range],
                            roleType=item_dict['role'])

    # check if entity record already there (should not be as we are adding 1 record per role)
    party_already_added = party_id in prepped_data

    if party_already_added:
        # party already added as entity -- add the new entity role to it
        if not prepped_data[party_id].roles:
            prepped_data[party_id].roles = []
        prepped_data[party_id].roles.append(party_role)

    elif has_party:
        # add new entity doc for party including address and role
        use_mailing = not item_dict.get('delivery_addr_id', None) and source == 'COLIN'
        party_address = get_address(item_dict, True, use_mailing)
        is_party = item_dict['party_type'] == 'person'
        party_entity = Entity(entityAddresses=[party_address] if party_address.address_q else None,
                              entityType='PERSON' if is_party else 'BUSINESS',
                              id=party_id,
                              identifier=None if is_party else party_id,
                              legalName=get_party_name(item_dict),
                              roles=[party_role])

        prepped_data[party_id] = party_entity

    if is_debug_identifier:
        current_app.logger.debug(f'party_role: {party_role}')
        current_app.logger.debug(f'party_id: {party_id}')
        current_app.logger.debug(f'party_already_added: {party_already_added}')
        current_app.logger.debug(f'has_party: {has_party}')
        current_app.logger.debug(f'is_party: {is_party}')
        current_app.logger.debug(f'party_entity: {party_entity}')

    return prepped_data.get(party_id, None)


def party_cleanup(prepped_data: dict[str, Entity], party_links: dict[str, dict[str, str]]):
    """Add relevant data to the current party entry and remove older versions of the party."""
    skipped_ids = []
    for corp_num in party_links:
        for current_id in party_links[corp_num]:
            if current_id not in prepped_data:
                skipped_ids.append(current_id)
                continue

            # get start date from the last party record (expects oldest record to be last in the list)
            prev_id = party_links[corp_num][current_id]

            if prev_id in prepped_data:
                if not prepped_data[current_id].roles[0].roleDates[0].start:
                    # parent appointment date not there so use child appointment date
                    prepped_data[current_id].roles[0].roleDates[0].start = \
                        prepped_data[prev_id].roles[0].roleDates[0].start
                # remove child record from prepped data
                del prepped_data[prev_id]
    current_app.logger.debug(f'skipped_ids {skipped_ids}')


def update_party_links(prepped_data: dict[str, Entity],  # pylint: disable=too-many-arguments
                       child_link: dict[str, dict[str, str]],
                       parent_link: dict[str, dict[str, str]],
                       event_link: dict[str, str],
                       dupes: list,
                       corp_num: str,
                       new_id: str,
                       prev_id: str,
                       start_event_id: str,
                       is_debug_identifier=False):
    """Update/Create links between current party record and original party record."""
    # NOTE: could get multiple records out of order
    parent_id = new_id
    child_id = prev_id
    if corp_num in child_link:
        if prev_id in child_link[corp_num]:
            # two records had the same prev_id (data issue?)
            if prev_id not in dupes:
                dupes.append(prev_id)
            # use record with highest start event id
            dupe_parent_id = child_link[corp_num][prev_id]

            if event_link[dupe_parent_id] > start_event_id:
                # remove this middle record and move on
                if is_debug_identifier:
                    current_app.logger.debug(f'skipping new_id: {new_id}')
                    current_app.logger.debug(f'skipped record: {prepped_data[new_id]}')
                del prepped_data[new_id]
                return

            # remove dupe values (it is a middle record)
            del child_link[corp_num][prev_id]
            del parent_link[corp_num][dupe_parent_id]
            del prepped_data[dupe_parent_id]
            del event_link[dupe_parent_id]

        if new_id in child_link[corp_num]:
            # get top level parent id
            parent_id = child_link[corp_num][new_id]
            del parent_link[corp_num][parent_id]
            # cleanup old values
            del child_link[corp_num][new_id]
            # remove the new party record from response (its an unused middle record)
            del prepped_data[new_id]

        if prev_id in parent_link[corp_num]:
            # get bottom level child and cleanup old values
            child_id = parent_link[corp_num][prev_id]
            del parent_link[corp_num][prev_id]
            # remove the previous party record from response (its an unused middle record)
            del prepped_data[prev_id]

    # set bottom level child to top level parent
    child_link.setdefault(corp_num, {})
    child_link[corp_num][child_id] = parent_id
    # set top level parent to bottom level child
    parent_link.setdefault(corp_num, {})
    parent_link[corp_num][parent_id] = child_id
    # save start event id for later -- if it already exists do NOT update it
    event_link.setdefault(parent_id, start_event_id)
    if is_debug_identifier:
        current_app.logger.debug(f'child_link: {child_link[corp_num]}')
        current_app.logger.debug(f'parent_link: {parent_link[corp_num]}')
        current_app.logger.debug(f'parent_id: {parent_id}')
        current_app.logger.debug(f'event_link: {event_link[parent_id]}')


def get_entities(prepped_data: dict[str, Entity]) -> list[dict]:
    """Return the entities within the prepped data and log info on data issues."""
    missing_data: dict[str, list[Entity]] = {'address': [], 'appointment_date': []}
    entities = []
    for identifier_key in prepped_data:
        entity = prepped_data[identifier_key]
        if entity.entityAddresses and not entity.entityAddresses[0].address_q:
            missing_data['address'].append(entity)
        # elif entity.roles and not entity.roles[0].roleDates[0].start:
        #     missing_data['appointment_date'].append(entity)
        # add 1 entity per role in (UI doesn't handle multiple roles per entity yet)
        for index, role in enumerate(entity.roles):
            single_role_entity = Entity(
                id=entity.id + str(index),
                entityAddresses=entity.entityAddresses,
                entityType=entity.entityType,
                legalName=entity.legalName,
                bn=entity.bn,
                email=entity.email,
                identifier=entity.identifier,
                legalType=entity.legalType,
                roles=[role],
                state=entity.state
            )
            entities.append(asdict(single_role_entity))

    current_app.logger.debug(f"entities with missing address: {len(missing_data['address'])}")
    # current_app.logger.debug(f"entities with missing appointment date: {len(missing_data['appointment_date'])}")
    return entities


def prep_data(data: list[dict[str, str]],  # pylint: disable=too-many-locals
              data_descs: list[str],
              source: str,
              btr_id_links: list[dict[str, list[str]]]) -> tuple[list[dict], list[dict]]:
    """Return the list of Entity docs for the given raw db data."""
    prepped_data: dict[str, Entity] = {}
    child_link: dict[str, dict[str, str]] = {}  # corp_num -> child -> parent
    parent_link: dict[str, dict[str, str]] = {}  # corp_num -> parent -> child
    event_link: dict[str, str] = {}
    dupes = []
    partial_btr_updates = []

    debug_identfiers = current_app.config.get('DEBUG_IDENTIFIERS', [])

    for item in data:
        item_dict = dict(zip(data_descs, item))

        is_debug_identifier = item_dict['identifier'] in debug_identfiers

        if needs_bc_prefix(item_dict['identifier'], item_dict['legal_type']):
            item_dict['identifier'] = 'BC' + item_dict['identifier']

        if is_debug_identifier:
            current_app.logger.debug(f'item_dict: {item_dict}')

        # add partial business update to BTR SI record if applicable
        if (identifier := item_dict['identifier']) in btr_id_links:  # pylint: disable=superfluous-parens
            for btr_id in btr_id_links[identifier]:
                # add the business info to a partial role doc
                partial_btr_updates.append({
                    '_root_': btr_id,
                    'id': btr_id + identifier + 'SIGNIFICANT_INDIVIDUAL',
                    'relatedBN': {'set': item_dict['tax_id']},
                    'relatedEmail': {'set': item_dict.get('admin_email')},
                    'relatedLegalType': {'set': item_dict['legal_type']},
                    'relatedName': {'set': item_dict['legal_name']},
                    'relatedState': {'set': item_dict['state']}
                })

            del btr_id_links[identifier]

        if is_debug_identifier:
            current_app.logger.debug(f'partial_btr_updates: {partial_btr_updates}')

        # NB: for now business entities aren't needed in director search
        # set_business_entity(item_dict, prepped_data)
        party_entity = set_party_entity(item_dict, prepped_data, source, is_debug_identifier)

        if is_debug_identifier:
            current_app.logger.debug(f'item_dict: {item_dict}')
            current_app.logger.debug(f'party_entity: {party_entity}')

        if party_entity and item_dict.get('prev_party_id', None):
            update_party_links(prepped_data=prepped_data,
                               child_link=child_link,
                               parent_link=parent_link,
                               event_link=event_link,
                               dupes=dupes,
                               corp_num=party_entity.roles[0].relatedIdentifier,
                               new_id=party_entity.id,
                               prev_id=f"{source}{item_dict['prev_party_id']}",
                               start_event_id=item_dict['start_event_id'],
                               is_debug_identifier=is_debug_identifier)

        elif party_entity and not party_entity.roles[0].roleDates[0].start:
            # no older records to pull appointment date from so use filing_date
            if item_dict.get('event_typ_cd', None) in ['CONVICORP', 'CONVAMAL', 'CONVCIN']:
                # event date does not correspond to appointment date of party for these
                # appointment date is unknown in this case (so keep it as None)
                continue
            if filing_date := item_dict.get('effective_dt', None) or item_dict.get('event_timestmp', None):
                party_entity.roles[0].roleDates[0].start = datetime.isoformat(filing_date,
                                                                              timespec='seconds').replace('+00:00', 'Z')

    if source == 'COLIN':
        party_cleanup(prepped_data, parent_link)

    current_app.logger.debug(f'multiple prev party ids {len(dupes)}')
    return get_entities(prepped_data), partial_btr_updates


def prep_data_btr(data: list[dict]) -> tuple[dict, dict]:
    """Return the list of Entity docsn and the party/business id links from the btr db data."""
    prepped_data: list[Entity] = []
    id_links: dict[str, list[str]] = {}

    debug_identfiers = current_app.config.get('DEBUG_IDENTIFIERS', [])

    for item in data:
        submission = item[0]
        identifier = submission['businessIdentifier']

        if identifier in debug_identfiers:
            current_app.logger.debug(f'submission: {submission}')

        # minimal business record. Will be updated with full details later.
        business = Entity(id=identifier,
                          identifier=identifier,
                          entityType='BUSINESS',
                          entityAddresses=None,
                          legalName=submission.get('entityStatement', {}).get('name', ''))

        # collect current parties.
        # TODO: handle same party across submissions (not needed until collapsing people into 1 record)
        parties = {}
        for person in submission.get('personStatements', []):
            person_id = person['statementID']
            parties[person_id] = person

        # combine ownership details and parties
        for ownership_info in submission.get('ownershipOrControlStatements', []):
            party_id = ownership_info['interestedParty']['describedByPersonStatement']
            ownership_info['interestedParty'] = {
                'describedByPersonStatement': party_id,
                **parties[party_id]
            }
            parsed_owner = asdict(get_btr_owner(ownership_info, business))
            prepped_data.append(parsed_owner)
            id_links.setdefault(business.id, []).append(party_id)

            if identifier in debug_identfiers:
                current_app.logger.debug(f'entity parsed: {parsed_owner}')

    return prepped_data, id_links
