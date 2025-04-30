import { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export class RegistriesDashboardPage {
  readonly page: Page;
  readonly businessandPersonSearchButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.businessandPersonSearchButton = page.getByRole('link', { name: 'Business and Person Search' });
   
  }

  async selectProductAndServices(searchInput: string) {
    if (searchInput === 'Business and Person Search') { 
        await this.businessandPersonSearchButton.click();
        } else {
        console.error('Invalid product or service selected');
        }   
    }
   
  }

 
