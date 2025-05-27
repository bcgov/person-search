import { test, expect, request } from '@playwright/test';
import {api, incorporationApplication} from '../../pages-api/incorporate-application-apis';
import { LoginPage } from '../../pages-ui/logonPage';
import  fillingData  from '../../fixtures/entity-fillings/incorporation-application-data.json';
import { changeFilling } from '../../pages-api/change-filling-apis';

test(' Change Director - Add new Director - Backend automation ', async ({ page }) => {
 //const 
 test.setTimeout(90000);
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  let accessToken: string = await loginPage.loginAndReturnToken('idir');
 const object = new incorporationApplication('BC', process.env.PLAYWRIGHT_TEST_IDIR_ACCOUNTID, accessToken)
 await object.apiCreateDraftIncorporationApplication(); 
 await object.apiFillingIncorporationApplication(fillingData[0]["officerFistName"], fillingData[0]["officerLastName"]);
  await new Promise(resolve => setTimeout(resolve, 8000));
  await object.getApiBusinessDetails();
  console.log ('Sucessfully Created Incorporation: ',await object.getBusinessIdentifier());
  let businessIdentifier = await object.getBusinessIdentifier();
  let legalName = await object.getLegalName();
  const changeFillingObject = new changeFilling(accessToken, 'BC');
  await changeFillingObject.addNewDirector(businessIdentifier, legalName, fillingData[0]["addNewOfficerFirstName"], fillingData[0]["addNewOfficerLastName"]);
  await new Promise(resolve => setTimeout(resolve, 8000));
  await changeFillingObject.getApiBusinessParties();
  });


 test(' Change Director - Cease a existing Director - Backend automation ', async ({ page }) => {
 //const 
 test.setTimeout(90000);
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  let accessToken: string = await loginPage.loginAndReturnToken('idir');
 const object = new incorporationApplication('BC', process.env.PLAYWRIGHT_TEST_IDIR_ACCOUNTID, accessToken)
 await object.apiCreateDraftIncorporationApplication(); 
 await object.apiFillingIncorporationApplication(fillingData[0]["officerFistName"], fillingData[0]["officerLastName"]);
  await new Promise(resolve => setTimeout(resolve, 8000));
  await object.getApiBusinessDetails();
  console.log ('Sucessfully Created Incorporation: ',await object.getBusinessIdentifier());
  let businessIdentifier = await object.getBusinessIdentifier();
  let legalName = await object.getLegalName();
  const changeFillingObject = new changeFilling(accessToken, 'BC');
  await changeFillingObject.addNewDirector(businessIdentifier, legalName, fillingData[0]["addNewOfficerFirstName"], fillingData[0]["addNewOfficerLastName"]);
  await new Promise(resolve => setTimeout(resolve, 8000));
 await changeFillingObject.ceaseDirector(businessIdentifier, legalName, fillingData[0]["officerFistName"], fillingData[0]["officerLastName"]);
 await new Promise(resolve => setTimeout(resolve, 8000));
   await changeFillingObject.getApiBusinessParties();
  }); 