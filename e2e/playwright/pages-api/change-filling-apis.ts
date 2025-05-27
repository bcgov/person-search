
import { test, expect, request } from '@playwright/test';
import { getFormattedDate, getFormattedUTCDate } from '../helpers/utils';

import dotenv from 'dotenv';
dotenv.config();

export class changeFilling{
    
    token: string;
    identifier!: string;
    legalName!: string;
    legalType: string;
    todayDate!: string;
    effectiveDate!: string;
    officerFirstName!: string;
    officerLastName!: string;
  
   
    constructor( token:string, legalType: string, 
    ) {
        this.legalType = legalType;
        this.token = token;
    }

    async addNewDirector(identifier: string, legalName: string, officerFirstName: string, officerLastName: string) {
        this.officerFirstName = officerFirstName;
        this.officerLastName = officerLastName;
        this.identifier = identifier;
        this.legalName = legalName;
        this.todayDate = getFormattedDate('YYYY-MM-DD')
        this.effectiveDate = getFormattedUTCDate();

        console.log('Identifier:', this.identifier);
        console.log('Legal Name:', this.legalName);
        console.log('Officer First Name:', this.officerFirstName);
        console.log('Officer Last Name:', this.officerLastName);
        console.log('Today Date:', this.todayDate);
        console.log('Effective Date:', this.effectiveDate);
        console.log('Legal Type:', this.legalType);

        const legalApiBaseUrl = process.env.LEGALAPI_BASEURL_TEST
        const apiContext = await request.newContext({
            baseURL: legalApiBaseUrl,
            extraHTTPHeaders: {
              'Authorization': `Bearer ${this.token}`,
              'Content-Type': 'application/json',
              
            },
          });
    // Send POST request with JSON body
        const urlChangeDirectorPost = `/api/v2/businesses/${this.identifier}/filings`;
        
            const response = await apiContext.post(urlChangeDirectorPost, { timeout: 60000,
                data: {
                        "filing": {
                            "header": {
                            "name": "changeOfDirectors",
                            "certifiedBy": "API Tester",
                            "email": "no_one@never.get",
                            "date": this.todayDate,
                            "effectiveDate": this.effectiveDate,
                            "waiveFees": true
                            },
                            "business": {
                            "foundingDate": this.effectiveDate,
                            "identifier": this.identifier,
                            "legalName": this.legalName,
                            "legalType": this.legalType
                            },
                            "changeOfDirectors": {
                            "directors": [
                                {
                                "actions": [
                                    "appointed"
                                ],
                                "id": 2,
                                "isDirectorActionable": true,
                                "isFeeApplied": true,
                                "officer": {
                                    "firstName": this.officerFirstName,
                                    "middleInitial": "",
                                    "lastName": this.officerLastName,
                                    "prevFirstName": this.officerFirstName,
                                    "prevMiddleInitial": "",
                                    "prevLastName": this.officerLastName
                                },
                                "deliveryAddress": {
                                    "streetAddress": "12344 194A St",
                                    "streetAddressAdditional": "",
                                    "addressCity": "Pitt Meadows",
                                    "addressRegion": "BC",
                                    "postalCode": "V3Y 2K3",
                                    "addressCountry": "CA"
                                },
                                "appointmentDate": "2025-05-22",
                                "cessationDate": null,
                                "mailingAddress": {
                                    "streetAddress": "12344 194A St",
                                    "streetAddressAdditional": "",
                                    "addressCity": "Pitt Meadows",
                                    "addressRegion": "BC",
                                    "postalCode": "V3Y 2K3",
                                    "addressCountry": "CA"
                                }
                                }
                            ]
                            }
                        }
                        },
                });
        
        // Validate response
        await new Promise(resolve => setTimeout(resolve, 4000));
        expect(response.status()).toBe(201);
        console.log('Sucessfully added Director Response status:', response.status());
        console.log('Sucessfully added Director Response body:', await response.json());
        }
    async ceaseDirector(identifier: string, legalName: string, officerFirstName: string, officerLastName: string) {
        this.officerFirstName = officerFirstName;
        this.officerLastName = officerLastName;
        this.identifier = identifier;
        this.legalName = legalName;
        this.todayDate = getFormattedDate('YYYY-MM-DD')
        this.effectiveDate = getFormattedUTCDate();

        console.log('Identifier:', this.identifier);
        console.log('Legal Name:', this.legalName);
        console.log('Officer First Name:', this.officerFirstName);
        console.log('Officer Last Name:', this.officerLastName);
        console.log('Today Date:', this.todayDate);
        console.log('Effective Date:', this.effectiveDate);
        console.log('Legal Type:', this.legalType);

        const legalApiBaseUrl = process.env.LEGALAPI_BASEURL_TEST
        const apiContext = await request.newContext({
            baseURL: legalApiBaseUrl,
            extraHTTPHeaders: {
              'Authorization': `Bearer ${this.token}`,
              'Content-Type': 'application/json',
              
            },
          });
    // Send POST request with JSON body
        const urlChangeDirectorPost = `/api/v2/businesses/${this.identifier}/filings`;
        
            const response = await apiContext.post(urlChangeDirectorPost, { timeout: 60000,
                data: {
                        "filing": {
                            "header": {
                            "name": "changeOfDirectors",
                            "certifiedBy": "Api tester",
                            "email": "no_one@never.get",
                            "date": this.todayDate,
                            "effectiveDate": this.effectiveDate,
                            "waiveFees": true
                            },
                            "business": {
                            "foundingDate": this.effectiveDate,
                            "identifier": this.identifier,
                            "legalName": this.legalName,
                            "legalType": "BC"
                            },
                            "changeOfDirectors": {
                            "directors": [
                                {
                                "appointmentDate": this.todayDate,
                                "cessationDate": this.todayDate,
                                "deliveryAddress": {
                                    "addressCity": "delivery_address city",
                                    "addressCountry": "CA",
                                    "addressRegion": "BC",
                                    "deliveryInstructions": "",
                                    "postalCode": "H0H 0H0",
                                    "streetAddress": "delivery_address - address line one",
                                    "streetAddressAdditional": ""
                                },
                                "mailingAddress": {
                                    "addressCity": "mailing_address city",
                                    "addressCountry": "CA",
                                    "addressRegion": "BC",
                                    "deliveryInstructions": "",
                                    "postalCode": "H0H 0H0",
                                    "streetAddress": "mailing_address - address line one",
                                    "streetAddressAdditional": ""
                                },
                                "officer": {
                                    "email": "first.last@example.com",
                                    "firstName": "FIRST",
                                    "id": 714771,
                                    "lastName": "LAST",
                                    "partyType": "person",
                                    "middleInitial": "",
                                    "prevFirstName": "FIRST",
                                    "prevLastName": "LAST",
                                    "prevMiddleInitial": ""
                                },
                                "role": "director",
                                "id": 2,
                                "isFeeApplied": true,
                                "isDirectorActionable": true,
                                "actions": [
                                    "ceased"
                                ]
                                }
                            ]
                            }
                        }
                        }
                    ,
                });
        
        // Validate response
        await new Promise(resolve => setTimeout(resolve, 4000));
        expect(response.status()).toBe(201);
        console.log('Sucessfully Ceased Director Response status:', response.status());
        console.log('Sucessfully Ceased Director Response body:', await response.json());
        }

    async getApiBusinessParties() {     
        // Create a new API request context with headers
        const legalApiBaseUrl = process.env.LEGALAPI_BASEURL_TEST
        const urlGet = `/api/v2/businesses/${this.identifier}/parties`;
        const apiContext3 = await request.newContext({
          baseURL: legalApiBaseUrl,
          extraHTTPHeaders: {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json',
          },
        });
        console.log('Request URL:', urlGet);
      const response3 = await apiContext3.get(urlGet, {
        timeout: 100000 // 60 seconds
        });
     
      console.log(urlGet);
      // Validate response
      expect(response3.status()).toBe(200);
      console.log('Response status:', response3.status());
      const responseBody = await response3.json();
      console.log('Response body:', responseBody.parties);
      

    }

}
