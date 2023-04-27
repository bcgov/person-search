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
"""Test Suite to ensure the worker routines are working as expected."""
import pytest
import requests_mock
from entity_queue_common.service_utils import subscribe_to_queue

from bor_solr_updater.worker import cb_nr_subscription_handler
from .utils import helper_add_event_to_queue


@pytest.mark.asyncio
async def test_events_listener_queue(config, events_stan):
    """Assert that events can be retrieved and decoded from the Queue."""
    identifier = 'FM1234567'
    kc_url = config['KEYCLOAK_AUTH_TOKEN_URL']
    bus_url = f'{config["LEAR_SVC_URL"]}/businesses/{identifier}'
    parties_url = f'{config["LEAR_SVC_URL"]}/businesses/{identifier}/parties'
    addresses_url = f'{config["LEAR_SVC_URL"]}/businesses/{identifier}/addresses'
    search_url = f'{config["BOR_API_URL"]}/internal/solr/update'
    addresses_json = {
        "recordsOffice": {
            "deliveryAddress": {
                "addressCity": "Coquitlam",
                "addressCountry": "CA",
                "addressRegion": "BC",
                "addressType": "delivery",
                "deliveryInstructions": "",
                "id": 2664211,
                "postalCode": "V3K 3V9",
                "streetAddress": "Bc-435 North Rd",
                "streetAddressAdditional": ""
            },
            "mailingAddress": {
                "addressCity": "Coquitlam",
                "addressCountry": "CA",
                "addressRegion": "BC",
                "addressType": "mailing",
                "deliveryInstructions": "",
                "id": 2664210,
                "postalCode": "V3K 3V9",
                "streetAddress": "Bc-435 North Rd",
                "streetAddressAdditional": ""
            }
        },
        "registeredOffice": {
            "deliveryAddress": {
                "addressCity": "Coquitlam",
                "addressCountry": "CA",
                "addressRegion": "BC",
                "addressType": "delivery",
                "deliveryInstructions": "",
                "id": 2664213,
                "postalCode": "V3K 3V9",
                "streetAddress": "Bc-435 North Rd",
                "streetAddressAdditional": ""
            },
            "mailingAddress": {
                "addressCity": "Coquitlam",
                "addressCountry": "CA",
                "addressRegion": "BC",
                "addressType": "mailing",
                "deliveryInstructions": "",
                "id": 2664212,
                "postalCode": "V3K 3V9",
                "streetAddress": "Bc-435 North Rd",
                "streetAddressAdditional": ""
            }
        }
    }
    business_json = {
        'business': {
            'identifier': identifier,
            'legalName': 'test name',
            'legalType': 'BEN',
            'state': 'ACTIVE',
            'taxId': '123456789BC0001'}}
    parties_json = {
        "parties": [
            {
                "deliveryAddress": {
                    "addressCity": "Calgary",
                    "addressCountry": "CA",
                    "addressRegion": "AB",
                    "deliveryInstructions": None,
                    "id": 2664208,
                    "postalCode": "T3J 3Z5",
                    "streetAddress": "1234-4818 Westwinds Dr NE",
                    "streetAddressAdditional": ""
                },
                "mailingAddress": {
                    "addressCity": "Calgary",
                    "addressCountry": "CA",
                    "addressRegion": "AB",
                    "deliveryInstructions": None,
                    "id": 2664209,
                    "postalCode": "T3J 3Z5",
                    "streetAddress": "1234-4818 Westwinds Dr NE",
                    "streetAddressAdditional": ""
                },
                "officer": {
                    "email": "ppr@dev.com",
                    "firstName": "BCREG2 LIANG",
                    "id": 570343,
                    "lastName": "FORTY",
                    "partyType": "person"
                },
                "roles": [
                    {
                        "appointmentDate": "2023-03-06",
                        "cessationDate": None,
                        "roleType": "Director"
                    }
                ]
            },
            {
                "deliveryAddress": {
                    "addressCity": "Québec",
                    "addressCountry": "CA",
                    "addressRegion": "QC",
                    "deliveryInstructions": None,
                    "id": 2669641,
                    "postalCode": "G1N 1C1",
                    "streetAddress": "W-558 Rue Saint-Vallier O",
                    "streetAddressAdditional": ""
                },
                "mailingAddress": {
                    "addressCity": "Québec",
                    "addressCountry": "CA",
                    "addressRegion": "QC",
                    "deliveryInstructions": None,
                    "id": 2669642,
                    "postalCode": "G1N 1C1",
                    "streetAddress": "W-558 Rue Saint-Vallier O",
                    "streetAddressAdditional": ""
                },
                "officer": {
                    "email": None,
                    "firstName": "BLIPPITY",
                    "id": 570721,
                    "lastName": "BOP",
                    "partyType": "person"
                },
                "roles": [
                    {
                        "appointmentDate": "2023-03-20",
                        "cessationDate": None,
                        "roleType": "Director"
                    }
                ]
            },
            {
                "deliveryAddress": {
                    "addressCity": "Calgary",
                    "addressCountry": "CA",
                    "addressRegion": "AB",
                    "deliveryInstructions": None,
                    "id": 2664208,
                    "postalCode": "T3J 3Z5",
                    "streetAddress": "1234-4818 Westwinds Dr NE",
                    "streetAddressAdditional": ""
                },
                "mailingAddress": {
                    "addressCity": "Calgary",
                    "addressCountry": "CA",
                    "addressRegion": "AB",
                    "deliveryInstructions": None,
                    "id": 2664209,
                    "postalCode": "T3J 3Z5",
                    "streetAddress": "1234-4818 Westwinds Dr NE",
                    "streetAddressAdditional": ""
                },
                "officer": {
                    "email": "ppr@dev.com",
                    "oraganizationName": "Org inc",
                    "id": 1234,
                    "partyType": "organization"
                },
                "roles": [
                    {
                        "appointmentDate": "2023-03-06",
                        "cessationDate": None,
                        "roleType": "Director"
                    }
                ]
            }
        ]
    }
    with requests_mock.mock() as m:
        m.post(kc_url, json={'access_token': 'token'})
        m.get(bus_url, json=business_json)
        m.get(parties_url, json=parties_json)
        m.get(addresses_url, json=addresses_json)
        m.put(search_url)

        events_subject = 'test_subject'
        events_queue = 'test_queue'
        events_durable_name = 'test_durable'

        identifier = 'FM1234567'

        # register the handler to test it
        await subscribe_to_queue(events_stan,
                                events_subject,
                                events_queue,
                                events_durable_name,
                                cb_nr_subscription_handler)

        # add an event to queue
        await helper_add_event_to_queue(events_stan, events_subject, identifier)

        assert m.called == True
        assert m.call_count == 5
        assert kc_url in m.request_history[0].url
        assert m.request_history[1].url == bus_url + '?slim=True'
        assert m.request_history[2].url == parties_url + '?slim=True'
        assert m.request_history[3].url == addresses_url + '?slim=True'
        assert m.request_history[4].url == search_url
        update_payload = m.last_request.json()
        assert update_payload['business'] == business_json['business']
        assert update_payload['businessAddresses'] == addresses_json
        # parties will not include orgs and will have an added 'source' value of LEAR
        parties_without_orgs = [{**x, 'source': 'LEAR'} for x in parties_json['parties'] if x['officer']['partyType'] == 'person']
        assert update_payload['parties'] == parties_without_orgs
