import { Page, Locator } from '@playwright/test';
import { defineConfig } from '@playwright/test';
import dotenv from 'dotenv';
dotenv.config();
import { expect } from '@playwright/test';
export class LoginPage {
  readonly page: Page;
  readonly loginBcscButton: Locator;

  readonly loginIdirButton: Locator;
  readonly loginIdirUserName: Locator;
  readonly loginIdirPassword: Locator;
  readonly loginIdirContinueButton: Locator;

  readonly loginBcscTestButton: Locator;
  readonly loginBcscContinueButton: Locator;
  readonly loginBcscUsernameInput: Locator;
  readonly loginBcscPasswordInput: Locator;
  readonly termsOfUseCheckBox: Locator;
  readonly termsOfUseContinueButton: Locator;
  readonly staffBusinessSearchLink: Locator;
  readonly logOutMenu: Locator;
  readonly logOutItem: Locator;
  
  

  constructor(page: Page) {
    this.page = page;
    this.loginBcscButton = page.getByRole('button', { name: 'Login with BC Services Card' });
    this.loginBcscTestButton = page.getByRole('button', { name: 'Log in with Test with username and password' });
    this.loginBcscUsernameInput = page.locator('#username');
    this.loginBcscPasswordInput = page.locator('#password');
    this.loginBcscContinueButton = page.getByRole('button', { name: 'Continue' });

    this.loginIdirButton = page.getByRole('button', { name: 'Login with IDIR' });
    this.loginIdirUserName = page.locator('#user');
    this.loginIdirPassword = page.locator('#password');
    this.loginIdirContinueButton = page.getByRole('button', { name: 'Continue' });

    this.termsOfUseCheckBox = page.locator('#accept');
    this.termsOfUseContinueButton = page.locator('#btnSubmit');
    this.staffBusinessSearchLink = page.getByText('Business Search');

    this.logOutMenu=page.locator('[aria-label="my account"]')
    this.logOutItem=page.getByText('Log out')
  
  }

  async goto() {
    console.info(`[AuthSetup] Navigating to login page: ${process.env.NUXT_BASE_URL }`)
    await this.page.goto(process.env.NUXT_BASE_URL  + 'en-CA/login', { waitUntil: 'load', timeout: 360000 })

  }

  async login(loginType: string) {
    if(loginType === 'bcsc') {
      console.info(`[AuthSetup] Logging in with BCSC`)
    await this.loginBcscButton.click();
    await this.loginBcscTestButton.click();   
    await this.loginBcscUsernameInput.fill(process.env.PLAYWRIGHT_TEST_BCSC_USERNAME);
    await this.loginBcscPasswordInput.fill(process.env.PLAYWRIGHT_TEST_BCSC_PASSWORD);
    await this.loginBcscContinueButton.click();
  } else if (loginType === 'idir') {
    console.info(`[AuthSetup] Logging in with IDIR`)
    await this.loginIdirButton.click();
    await this.loginIdirUserName.fill(process.env.PLAYWRIGHT_TEST_IDIR_USERNAME);
    await this.loginIdirPassword.fill(process.env.PLAYWRIGHT_TEST_IDIR_PASSWORD);
    await this.loginIdirContinueButton.click();
  } else {
    console.error('Invalid logi n type selected');  
  }
    await this.page.waitForTimeout(5000);
   // await this.page.getByRole('checkbox', { name: 'accept' }).check();
    //await this.page.check('name=accept');
    //await this.page.c('#accept');
   // await this.page.click('#btnSubmit')

   // await this.termsOfUseCheckBox.check();
   // await this.termsOfUseContinueButton.click();
    
  }
  async logout() {
    await this.logOutMenu.click();
    this.logOutItem.click();
    await this.page.waitForTimeout(5000);
   // await this.page.getByRole('checkbox', { name: 'accept' }).check();
    //await this.page.check('name=accept');
    //await this.page.c('#accept');
   // await this.page.click('#btnSubmit')

   // await this.termsOfUseCheckBox.check();
   // await this.termsOfUseContinueButton.click();
    
  }
  async loginAndReturnToken(loginType: string): Promise<string> {
    if (loginType === 'idir') {
      console.info(`[AuthSetup] Logging in with IDIR`)
      await this.loginIdirButton.click();
      await this.page.waitForTimeout(5000); 
      await this.loginIdirUserName.fill(process.env.PLAYWRIGHT_TEST_IDIR_USERNAME);
      await this.loginIdirPassword.fill(process.env.PLAYWRIGHT_TEST_IDIR_PASSWORD);
      await this.loginIdirContinueButton.click();
      
    } else {
      console.info(`[AuthSetup] Logging in with BCSC`)
      await this.loginBcscButton.click();
      await this.loginBcscTestButton.click();   
      await this.loginBcscUsernameInput.fill(process.env.PLAYWRIGHT_TEST_BCSC_USERNAME);
      await this.loginBcscPasswordInput.fill(process.env.PLAYWRIGHT_TEST_BCSC_PASSWORD);
      await this.loginBcscContinueButton.click();
    }
    await this.page.waitForTimeout(5000);
  
    console.info(`[AuthSetup] Logged in successfully`)
    //console.info(`[AuthSetup] Navigated to dashboard page: ${process.env.NUXT_BASE_URL }`)
    // Extract token from localStorage
    //const token = await this.page.evaluate(() => {
    //  return localStorage.getItem('access_token'); // Replace with the actual key your app uses
    //});
   // console.log('Token from localStorage:', token);
    const tokenSessionStorage = await this.page.evaluate(() => {
      return sessionStorage.getItem('KEYCLOAK_TOKEN'); // Adjust key if needed
    });
    console.log('Token from sessionStorage:', tokenSessionStorage);
    
    if (tokenSessionStorage) {
      return tokenSessionStorage;
    } 
      throw new Error('No token found in localStorage or sessionStorage');
    }
  }

