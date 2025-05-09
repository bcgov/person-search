# Copyright © 2025 Province of British Columbia
#
# Licensed under the BSD 3 Clause License, (the "License");
# you may not use this file except in compliance with the License.
# The template for the license can be found here
#    https://opensource.org/license/bsd-3-clause/
#
# Redistribution and use in source and binary forms,
# with or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS”
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
"""Test Suite to ensure the worker routines are working as expected."""
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest
import requests_mock
from flask import Flask
from simple_cloudevent import SimpleCloudEvent, to_queue_message


BEN_BUSINESS = {
    'business': {
        'goodStanding': True,
        'identifier': 'BC1234567',
        'legalName': 'Benefit Company',
        'legalType': 'BEN',
        'state': 'ACTIVE',
        'taxId': '123456789BC0001'
    }
}
BEN_PARTIES = {
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
BEN_ADDRESSES = {
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


@pytest.mark.parametrize('test_name, business, parties, addresses', [
    ('test-ben-company', BEN_BUSINESS, BEN_PARTIES, BEN_ADDRESSES),
])
@patch("bor_solr_updater.resources.worker.verify_gcp_jwt")
@patch("bor_solr_updater.resources.worker.gcp_queue.get_simple_cloud_event")
def test_business_event(mock_get_event: MagicMock, mock_verify: MagicMock, app: Flask, client, test_name, business, parties, addresses):
    """Assert that events can be retrieved and decoded from the Queue."""
    identifier = business['business']['identifier']
    kc_url = app.config['ACCOUNT_SVC_AUTH_URL']
    bus_url = f'{app.config["LEAR_SVC_URL"]}/businesses/{identifier}?slim=True'
    parties_url = f'{app.config["LEAR_SVC_URL"]}/businesses/{identifier}/parties?slim=True'
    addresses_url = f'{app.config["LEAR_SVC_URL"]}/businesses/{identifier}/addresses?slim=True'
    bor_url = f'{app.config["BOR_SVC_URL"]}/internal/solr/update'

    with requests_mock.mock() as m:
        m.post(kc_url, json={'access_token': 'token'})
        m.get(bus_url, json=business)
        m.get(parties_url, json=parties)
        m.get(addresses_url, json=addresses)
        m.put(bor_url)

        msg = SimpleCloudEvent(id=1, type='bc.registry.business.test', data={'identifier': identifier})
        mock_verify.return_value = None
        mock_get_event.return_value = msg
        resp = client.post("/worker", data=to_queue_message(msg))

        assert resp.status_code == HTTPStatus.OK

        assert m.called == True
        assert m.call_count == 5
        assert m.request_history[0].url == kc_url + '/'
        assert m.request_history[1].url == bus_url
        assert m.request_history[2].url == parties_url
        assert m.request_history[3].url == addresses_url
        assert m.request_history[4].url == bor_url
        
        update_payload = m.last_request.json()
        person_parties = [{**x, 'source': 'LEAR'} for x in parties['parties'] if x['officer']['partyType'] == 'person']
        expected_output = {
            'business': {
                'addresses': [addresses['registeredOffice']['deliveryAddress']],
                **business['business']
            },
            'parties': person_parties
        }
        assert update_payload == expected_output
