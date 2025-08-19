import { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export class termsOfUse {
  readonly page: Page;
 // readonly termsOfUseCheckBox: Locator;
  readonly termsOfUseContinueButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.termsOfUseContinueButton = page.locator('#btnSubmit');

  }

  async termsOfUseInput() {

    await this.page.click('label[for="accept"]');

    await this.termsOfUseContinueButton.click();
    await this.page.waitForTimeout(2000);
    console.info(`[AuthSetup] Logged in successfully`)
    await expect(this.page).toHaveURL(process.env.NUXT_BASE_URL  + 'en-CA/dashboard');
    console.info(`[AuthSetup] Navigated to dashboard page: ${process.env.NUXT_BASE_URL }`)
    await this.page.waitForTimeout(2000);
  }
   
  }

 
