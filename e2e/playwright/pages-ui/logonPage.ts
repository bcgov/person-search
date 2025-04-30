import { Page, Locator } from '@playwright/test';
import { defineConfig } from '@playwright/test';
import dotenv from 'dotenv';
dotenv.config();
import { expect } from '@playwright/test';
export class LoginPage {
  readonly page: Page;
  readonly loginServiceCardButton: Locator;
  readonly loginTestButton: Locator;
  readonly continueButton: Locator;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  

  constructor(page: Page) {
    this.page = page;
    this.loginServiceCardButton = page.getByRole('button', { name: 'Login with BC Services Card' });
    this.loginTestButton = page.getByRole('button', { name: 'Log in with Test with username and password' });
    this.usernameInput = page.locator('#username');
    this.passwordInput = page.locator('#password');
    this.continueButton = page.getByRole('button', { name: 'Continue' });
  }

  async goto() {
    console.info(`[AuthSetup] Navigating to login page: ${process.env.NUXT_BASE_URL }`)
    await this.page.goto(process.env.NUXT_BASE_URL  + 'en-CA/login', { waitUntil: 'load', timeout: 360000 })

  }

  async login() {
    await this.loginServiceCardButton.click();
    await this.loginTestButton.click();   
    await this.usernameInput.fill(process.env.PLAYWRIGHT_TEST_BCSC_USERNAME);
    await this.passwordInput.fill(process.env.PLAYWRIGHT_TEST_BCSC_PASSWORD);
    await this.continueButton.click();
    await expect(this.page).toHaveTitle('BC Registries Dashboard - BC Registries and Online Services') 
    console.info(`[AuthSetup] Logged in successfully`)
    await expect(this.page).toHaveURL(process.env.NUXT_BASE_URL  + 'en-CA/dashboard');
    console.info(`[AuthSetup] Navigated to dashboard page: ${process.env.NUXT_BASE_URL }`)
  }
}
