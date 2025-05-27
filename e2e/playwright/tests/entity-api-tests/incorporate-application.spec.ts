import { test, expect, request } from '@playwright/test';
import {api, incorporationApplication} from '../../pages-api/incorporate-application-apis';
import { LoginPage } from '../../pages-ui/logonPage';
import  fillingData  from '../../fixtures/entity-fillings/incorporation-application-data.json';


test(' Validate New Incorporation Application Process - Backend automation ', async ({ page }) => {
 test.setTimeout(90000);
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  let accessToken: string = await loginPage.loginAndReturnToken('idir');

 const object = new incorporationApplication('BC', process.env.PLAYWRIGHT_TEST_IDIR_ACCOUNTID, accessToken)
 await object.apiCreateDraftIncorporationApplication(); 
 //await object.apiFillingIncorporationApplication();
await object.apiFillingIncorporationApplication(fillingData[0]["officerFistName"], fillingData[0]["officerLastName"]);
 await new Promise(resolve => setTimeout(resolve, 4000));
 await object.getApiBusinessDetails();
 console.log ('Sucessfully Created Incorporation: ',await object.getBusinessIdentifier());
 console.log ('Sucessfully Created Incorporation: ',await object.getLegalName());
 console.log ('Sucessfully Created Incorporation: ',await object.getBusinessIdentifier());

  });