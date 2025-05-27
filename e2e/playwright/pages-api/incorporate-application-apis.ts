import { test, expect, request } from '@playwright/test';
import { getFormattedDate, utils } from '../helpers/utils';
import dotenv from 'dotenv';
dotenv.config();

export class incorporationApplication{
    businessLegalType: string;
    accountId: number;
    token: string;
    identifier!: string;
    filingId!: string;
    todayDate!: string;
    businessIdentifier!: string;
    legalName!: string;
    firstName!: string;
    lastName!: string;



    constructor(businessLegalType: string, accountId: number,
        token:string
    ) {
        this.businessLegalType = businessLegalType;
        this.accountId = accountId;
        this.token = token;
    }
    async apiCreateDraftIncorporationApplication(){
        
        const legalApiBaseUrl = process.env.LEGALAPI_BASEURL_TEST
        const apiContext = await request.newContext({
            baseURL: legalApiBaseUrl,
            extraHTTPHeaders: {
              'Authorization': `Bearer ${this.token}`,
              'Content-Type': 'application/json',
              
            },
          });
    // Send POST request with JSON body
        const response = await apiContext.post('/api/v2/businesses?draft=true', {
            data: {
                "filing": {
                    "header": {
                        "accountId": this.accountId,
                        "name": "incorporationApplication"
                    },
                    "business": {
                        "legalType": "BC"
                    },
                    "incorporationApplication": {
                        "nameRequest": {
                            "legalType": "BC"
                        }
                    }
                }
            },
            });
        
        // Validate response
        expect(response.status()).toBe(201);
        const json = await response.json();
        console.log(json);
        console.log('Identifier:', json.filing.business.identifier);
        this.identifier = json.filing.business.identifier;
        console.log('Filling ID:', json.filing.header.filingId);
        this.filingId = json.filing.header.filingId;
        }
    async apiFillingIncorporationApplication(officerFirstName: string, officerLastName: string) {
        this.todayDate = getFormattedDate('YYYY-MM-DD')
        this.firstName = officerFirstName;
        this.lastName = officerLastName;
        
        const legalApiBaseUrl = process.env.LEGALAPI_BASEURL_TEST
        // Create a new API request context with headers
        const apiContext2 = await request.newContext({
            baseURL: legalApiBaseUrl,
            extraHTTPHeaders: {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json',
            
            },
        });
        const urlPut = `/api/v2/businesses/${this.identifier}/filings/${this.filingId}`;
        console.log('URL:', urlPut); 
        
        const response2 = await apiContext2.put(urlPut, {
            data: {
            "filing": {
                "header": {
                    "name": "incorporationApplication",
                    "certifiedBy": "API Backend Automation",
                    "date": this.todayDate,
                    "accountId": this.accountId,
                },
                "incorporationApplication": {
                    "nameRequest": {
                        "legalType": "BC"
                    },
                    "nameTranslations": [],
                    "offices": {
                        "registeredOffice": {
                            "deliveryAddress": {
                                "streetAddress": "delivery_address - address line one",
                                "addressCity": "delivery_address city",
                                "addressCountry": "CA",
                                "postalCode": "H0H 0H0",
                                "addressRegion": "BC"
                            },
                            "mailingAddress": {
                                "streetAddress": "mailing_address - address line one",
                                "addressCity": "mailing_address city",
                                "addressCountry": "CA",
                                "postalCode": "H0H 0H0",
                                "addressRegion": "BC"
                            }
                        },
                        "recordsOffice": {
                            "deliveryAddress": {
                                "streetAddress": "delivery_address - address line one",
                                "addressCity": "delivery_address city",
                                "addressCountry": "CA",
                                "postalCode": "H0H 0H0",
                                "addressRegion": "BC"
                            },
                            "mailingAddress": {
                                "streetAddress": "mailing_address - address line one",
                                "addressCity": "mailing_address city",
                                "addressCountry": "CA",
                                "postalCode": "H0H 0H0",
                                "addressRegion": "BC"
                            }
                        }
                    },
                    "contactPoint": {
                        "email": "no_one@never.get",
                        "phone": "123-456-7890"
                    },
                    "parties": [
                        {
                            "officer": {
                                "firstName": "First",
                                "lastName": "Last",
                                "middleName": "",
                                "organizationName": "",
                                "partyType": "person",
                                "email": "first.last@example.com"
                            },
                            "roles": [
                                {
                                    "roleType": "Completing Party",
                                    "appointmentDate": this.todayDate
                                },
                                {
                                    "roleType": "Incorporator",
                                    "appointmentDate": this.todayDate
                                },
                                {
                                    "roleType": "Director",
                                    "appointmentDate": this.todayDate
                                }
                            ],
                            "deliveryAddress": {
                                "streetAddress": "delivery_address - address line one",
                                "addressCity": "delivery_address city",
                                "addressCountry": "CA",
                                "postalCode": "H0H 0H0",
                                "addressRegion": "BC"
                            },
                            "mailingAddress": {
                                "streetAddress": "mailing_address - address line one",
                                "addressCity": "mailing_address city",
                                "addressCountry": "CA",
                                "postalCode": "H0H 0H0",
                                "addressRegion": "BC"
                            }
                        }
                    ],
                    "shareStructure": {
                        "shareClasses": [
                            {
                                "name": "Sample Share Class",
                                "priority": 1,
                                "hasMaximumShares": false,
                                "maxNumberOfShares": null,
                                "hasParValue": false,
                                "parValue": null,
                                "currency": null,
                                "hasRightsOrRestrictions": false,
                                "series": []
                            }
                        ]
                    },
                    "incorporationAgreement": {
                        "agreementType": "sample"
                    }
                }
            }
        },
        });
 
        console.log('Requst URL:', urlPut);

        if (response2.status() !==  202) {
            const body = await response2.json();
            console.log('Validation errors:', body.errors);
        }

        expect(response2.status()).toBe(202);
        const responsejson = await response2.json();
        console.log(responsejson);
    }
    
    async getApiBusinessDetails() {     
        // Create a new API request context with headers
        const legalApiBaseUrl = process.env.LEGALAPI_BASEURL_TEST
        const urlGet = `/api/v2/businesses/${this.identifier}/filings`;
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
     // await new Promise(resolve => setTimeout(resolve, 4000));

      const responsejson2 = await response3.json();
      console.log(responsejson2);
      console.log('Business Identifier:', responsejson2.filing.business.identifier);
      this.businessIdentifier = responsejson2.filing.business.identifier;
      
      this.legalName = responsejson2.filing.business.legalName;
      console.log('Legal Name:', responsejson2.filing.business.legalName);

    }

    getBusinessIdentifier(): string {
        return this.businessIdentifier;
    }
    getLegalName(): string {
        return this.legalName;
    }
}