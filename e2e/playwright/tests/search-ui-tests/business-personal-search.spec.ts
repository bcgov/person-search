import { test } from '@playwright/test';
import { LoginPage } from '../../pages-ui/logonPage';
import { BusinessAndPersonSearchPage } from '../../pages-ui/searchPage';
import { RegistriesDashboardPage } from '../../pages-ui/dashboardPage';
import  searchData  from '../../fixtures/search-ui/search-testdata.json';

/*test('Business Search - UI validation', async ({ page }) => {
  const loginPage = new LoginPage(page);
  const businessAndPersonSearchPage = new BusinessAndPersonSearchPage(page);
  const registriesDashboardPage = new RegistriesDashboardPage(page);
  await loginPage.goto();
  await loginPage.login();
  
  await registriesDashboardPage.selectProductAndServices(searchData[1].productAndService);
  await businessAndPersonSearchPage.businessSearch(searchData[1].businessSearchText);
  await businessAndPersonSearchPage.loadMoreResultsClick();
});

test('Person Search - UI validation', async ({ page }) => {
  const loginPage = new LoginPage(page);
  const businessAndPersonSearchPage = new BusinessAndPersonSearchPage(page);
  const registriesDashboardPage = new RegistriesDashboardPage(page);
  
    await loginPage.goto();
    await loginPage.login();
    registriesDashboardPage.selectProductAndServices(searchData[1].productAndService);
    await businessAndPersonSearchPage.personSearch(searchData[1].personalSearchText);
    
  });*/

  test('Business and Person Search - UI validation', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const businessAndPersonSearchPage = new BusinessAndPersonSearchPage(page);
    const registriesDashboardPage = new RegistriesDashboardPage(page);
    
      await loginPage.goto();
      await loginPage.login('bcsc');
      registriesDashboardPage.selectProductAndServices(searchData[0].productAndService);
      await businessAndPersonSearchPage.businessSearch(searchData[0].businessSearchText);
  
      await businessAndPersonSearchPage.personSearch(searchData[0].personalSearchText);
     
    });
