import { test, expect, request } from '@playwright/test';
import {api, incorporationApplication} from '../../pages-api/incorporate-application-apis';
import { LoginPage } from '../../pages-ui/logonPage';
import { termsOfUse } from '../../pages-ui/termsOfUsePage';
import  fillingData  from '../../fixtures/entity-fillings/incorporation-application-data.json';
import  searchData  from '../../fixtures/search-ui/search-testdata.json';
import { BusinessAndPersonSearchPage } from '../../pages-ui/searchPage';
import { RegistriesDashboardPage } from '../../pages-ui/dashboardPage';

test(' Validate Business Search Operation by creating New Incorporation Application by back end ', async ({ page }) => {
 test.setTimeout(90000);
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  let accessToken: string = await loginPage.loginAndReturnToken('idir');
  loginPage.logout();

 const object = new incorporationApplication('BC', process.env.PLAYWRIGHT_TEST_IDIR_ACCOUNTID, accessToken)
 await object.apiCreateDraftIncorporationApplication(); 
 //await object.apiFillingIncorporationApplication();
await object.apiFillingIncorporationApplication(fillingData[0]["officerFistName"], fillingData[0]["officerLastName"]);
 await new Promise(resolve => setTimeout(resolve, 4000));
 await object.getApiBusinessDetails();
 let businessIdentifier: string = await object.getBusinessIdentifier();
 let legalName: string = await object.getLegalName();

 const loginPage2 = new LoginPage(page);
 const businessAndPersonSearchPage = new BusinessAndPersonSearchPage(page);
 const registriesDashboardPage = new RegistriesDashboardPage(page);
 const termsOfUsepage = new termsOfUse(page);

   await loginPage2.goto();
   await loginPage2.login('bcsc');
   await termsOfUsepage.termsOfUseInput()
   await registriesDashboardPage.selectProductAndServices(searchData[1].productAndService);
   await businessAndPersonSearchPage.businessSearch(businessIdentifier);
   await loginPage2.logout();

  });