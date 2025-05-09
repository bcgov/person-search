# Copyright © 2024 Province of British Columbia
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
"""Manages processor for updating a business in bor."""
from contextlib import suppress
from time import sleep

from flask import current_app
from simple_cloudevent import SimpleCloudEvent

from bor_solr_updater.exceptions import BusinessException
from bor_solr_updater.services.entity import get_entity_info
from bor_solr_updater.services.bor import update_bor


def process_business_event(ce: SimpleCloudEvent):
    """Process business events."""
    if not ce.type or not "bc.registry.business" in ce.type:
        # expecting bc.registry.business.<anything>
        current_app.logger.debug("skipping event based on ce.type")
        return
    current_app.logger.debug(">>>>>>>process_business_event>>>>>")
    # get identifier
    identifier = ce.data.get("identifier")
    if not identifier:
        raise BusinessException("Unable to parse identifier from message payload.")

    with suppress(Exception):
        if (filings := ce.data.get("filing", {}).get("legalFilings", [])) and "alteration" in filings:
            # if alteration, then give it 5 seconds (lear will still be processing it in some cases)
            sleep(5)
  
    # get extra data from lear
    business_info_path = f"/businesses/{identifier}"
    parties_info_path = f"/businesses/{identifier}/parties"
    address_info_path = f'/businesses/{identifier}/addresses'
    business_resp = get_entity_info(business_info_path)
    parties_resp = get_entity_info(parties_info_path)
    address_resp = get_entity_info(address_info_path)
    parties = []
    for party in parties_resp.json().get('parties'):
        if party.get('officer', {}).get('partyType') != 'person':
            # skip businesses for now until LEAR reworked
            continue
        # bor_api/bor_solr needs to know if its a LEAR party vs COLIN for the unique id
        party['source'] = 'LEAR'
        parties.append(party)

    # update solr via bor-api
    def convert_business(business: dict):
        """Return the business info with the expected legal name."""
        if business['legalType'] in ['SP', 'GP']:
            for name in business.get('alternateNames', []):
                if name['identifier'] == business['identifier']:
                    business['legalName'] = name['name']
                    break
        return business

    update_payload = {'business': convert_business(business_resp.json()['business']), 'parties': parties}
    # if business has a registered office with a deliverty address then add it to the business data
    if ro_delivery_address := address_resp.json().get('registeredOffice', {}).get('deliveryAddress'):
        update_payload['business']['addresses'] = [ro_delivery_address]

    update_bor(update_payload)

    current_app.logger.debug("<<<<<<<process_business_event<<<<<<<<<<")
