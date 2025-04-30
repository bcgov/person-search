import { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export class BusinessAndPersonSearchPage {
  readonly page: Page;
  readonly searchInput: Locator;
  readonly businessRadioInput: Locator;
  readonly personRadioInput: Locator;
  readonly searchResultsTable: Locator;
  readonly searchResults: Locator;
  readonly searchPersonalResults: Locator;
  readonly loadMoreResults: Locator;
  

  constructor(page: Page) {
    this.page = page;
    this.searchInput = page.locator('input[data-cy="search-textfield"]');
    this.businessRadioInput = page.locator('input[value="business"]');
    this.personRadioInput = page.locator('input[value="person"]');
    this.searchResultsTable = page.locator('div[data-cy="search-results-table"]');
    this.searchResults = page.locator('div.business-results.rounded-t.search-table > div > div > div.grow > h2');
    this.searchPersonalResults = page.locator('div:nth-child(1) > div > div > div > div.grow > h2')
    this.loadMoreResults = page.getByRole('button', { name: 'Load More Results' });
    
  }


  async businessSearch(searchInput: string) {
    await this.businessRadioInput.check();
    await this.searchInput.fill(searchInput);
    await this.searchInput.press('Enter');
    await this.page.waitForTimeout(5000); 
    await expect(this.searchResultsTable).toBeVisible()
    await this.searchResults.allInnerTexts().then((texts) => {
      console.log('Search Results:', texts);
    }
    );
    
  }
  async personSearch(searchInput: string) {
    await this.personRadioInput.check();
    await this.searchInput.fill(searchInput);
    await this.searchInput.press('Enter');
    await this.page.waitForTimeout(5000);  
    await expect(this.searchResultsTable).toBeVisible()
    await this.searchPersonalResults.allInnerTexts().then((texts) => {
      console.log('Search Results:', texts);
    }
    );
  }
  async loadMoreResultsClick() {
    await this.loadMoreResults.click();
    await this.page.waitForTimeout(5000); 
    await expect(this.searchResultsTable).toBeVisible()
    await this.searchResults.allInnerTexts().then((texts) => {
      console.log('Search More Results:', texts);
    }
    );
  }
}
