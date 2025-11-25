import { Page, Locator } from '@playwright/test';

export class trFillingPage {
  readonly page: Page;

  readonly addIndiviualBtn: Locator;
  readonly declarationMeBtn:Locator;
  readonly declarationParentBtn:Locator;
  readonly declarationNoneBtn:Locator;
  readonly declarationLawyerBtn:Locator;
  readonly fullNameInput:Locator;
  readonly preferredNameCheckbox:Locator;
  readonly preferredNameInput:Locator;
  readonly cOfShareLess25Percentage;
  readonly cOfShare25_50Percentage;
  readonly cOfShare50_75Percentage;
  readonly cOfShareGreater75Percentage;

  readonly cOfShareregisteredOwnerCheckBox;
  readonly cOfSharebeneficialOwnerCheckBox;
  readonly cOfShareindirectControlCheckBox;
  readonly cOfSharehasJointlyOrInConcertCheckBox;
  readonly cOfShareactingJointlyCheckBox;
  readonly cOfShareinConcertControlCheckBox;

  readonly cOfVotes25Percentage;
  readonly cOfVotes25_50Percentage;
  readonly cOfVotes50_75Percentage;
  readonly cOfVotesGreater75Percentage;

  readonly cOfVotesgisteredOwnerCheckBox;
  readonly cOfVotesbeneficialOwnerCheckBox;
  readonly cOfVotesindirectControlCheckBox;
  readonly cOfVoteshasJointlyOrInConcertCheckBox;
  readonly cOfVotesactingJointlyCheckBox;
  readonly cOfVotesinConcertControlCheckBox;

  readonly cOfMajorityDirectControlCheckBox;
  readonly cOfMajorityInDirectControlCheckBox;
  readonly cOfMajoritySigInfluenceControlCheckBox;

  readonly cOfMajorityhasJointlyOrInConcertCheckBox;
  readonly cOfMajorityactingJointlyCheckBox;
  readonly cOfMajorityinConcertControlCheckBox;

  readonly email;
  
  readonly addressCountryButton;  
  readonly addressStreet;
  readonly addressStreetLine2;
  readonly addressCity;
  readonly addressProvince;
  readonly addressPostalCode;

  readonly mailingAddIsDiffCheckbox;
  readonly mailingAddressCountryButton;
  readonly mailingAddressStreet;
  readonly mailingAddressStreetLine2;
  readonly mailingAddressCity;
  readonly mailingAddressProvince;
  readonly mailingAddressPostalCode;

  readonly phoneNumberCountryCodeCombo;
  readonly phoneNumberNumberInput; 
  readonly phoneNumberExtenstionInput;

  readonly citizenshipsCaCitizenRadio;
  readonly citizenshipsCaPrRadio;
  readonly citizenshipsOtherComboButton;

  readonly birthDateDate;

  readonly taxNumberInput;
  readonly noTaxNumberCheckBox ;

  readonly taxResidenceTrueCheckbox;
  readonly taxResidenceFalseCheckboxid;
  
  readonly determinationOfIncapacityCheckbox;
  readonly isUnableToObtainOrConfirmInformationCheckbox ;

  readonly newSIDoneButton;
  readonly newSICancelButton;

  readonly reviewAndConfirmButton;

  constructor(page: Page) {
    this.page = page;

    this.addIndiviualBtn = page.locator('button[data-cy="add-new-btn"]');
    this.declarationMeBtn= page.locator('button[data-cy="declaration-button-me"]');
    this.declarationParentBtn=page.locator('button[data-cy="declaration-button-parent"]');
    this.declarationNoneBtn=page.locator('button[data-cy="declaration-button-none"]');
    this.declarationLawyerBtn=page.locator('button[data-cy="declaration-button-lawyer"]');
    this.fullNameInput=page.locator('input[data-cy="testFullName"]');
    this.preferredNameCheckbox= page.locator('input[data-cy="usePreferredName"]');
    this.preferredNameInput = page.locator('input[data-cy="testPreferredName"]');
    
    this.cOfShareLess25Percentage = page.locator('div[data-cy="controlOfShares.percentage.0"');
    this.cOfShare25_50Percentage= page.locator('div[data-cy="controlOfShares.percentage.1"');
    this.cOfShare50_75Percentage= page.locator('div[data-cy="controlOfShares.percentage.2"')
    this.cOfShareGreater75Percentage = page.locator('div[data-cy="controlOfShares.percentage.3"');

    this.cOfShareregisteredOwnerCheckBox= page.locator('input[data-cy="controlOfShares.registeredOwner"]');
    this.cOfSharebeneficialOwnerCheckBox= page.locator('input[data-cy="controlOfShares.beneficialOwner"]');
    this.cOfShareindirectControlCheckBox = page.locator('input[data-cy="controlOfShares.indirectControl"]');

    this.cOfSharehasJointlyOrInConcertCheckBox=page.locator('input[data-cy="controlOfShares.jointlyOrInConcert.hasJointlyOrInConcert"]');
    this.cOfShareactingJointlyCheckBox = page.locator('input[data-cy="controlOfShares.jointlyOrInConcert.actingJointly"]');
    this.cOfShareinConcertControlCheckBox = page.locator('input[data-cy="controlOfShares.jointlyOrInConcert.inConcertControl"]');

    this.cOfVotes25Percentage = page.locator('div[data-cy="controlOfVotes.percentage.0"]');
    this.cOfVotes25_50Percentage= page.locator('div[data-cy="controlOfVotes.percentage.1"]');
    this.cOfVotes50_75Percentage= page.locator('div[data-cy="controlOfVotes.percentage.2"]');
    this.cOfVotesGreater75Percentage = page.locator('div[data-cy="controlOfVotes.percentage.3"]');

    this.cOfVotesgisteredOwnerCheckBox = page.locator('input[data-cy="controlOfVotes.registeredOwner"]');
    this.cOfVotesbeneficialOwnerCheckBox=page.locator('input[data-cy="controlOfVotes.beneficialOwner"]');
    this.cOfVotesindirectControlCheckBox= page.locator('input[data-cy="controlOfVotes.beneficialOwner"]');

    this.cOfVoteshasJointlyOrInConcertCheckBox=page.locator('input[data-cy="controlOfVotes.jointlyOrInConcert.hasJointlyOrInConcert"]');
    this.cOfVotesactingJointlyCheckBox=page.locator('input[data-cy="controlOfVotes.jointlyOrInConcert.actingJointly"]');
    this.cOfVotesinConcertControlCheckBox= page.locator('input[data-cy="controlOfVotes.jointlyOrInConcert.inConcertControl"]');

    this.cOfMajorityDirectControlCheckBox = page.locator('input[data-cy="controlOfDirectors.directControl"]');
    this.cOfMajorityInDirectControlCheckBox=page.locator('input[data-cy="controlOfDirectors.indirectControl"]');
    this.cOfMajoritySigInfluenceControlCheckBox= page.locator('input[data-cy="controlOfDirectors.significantInfluence"]');

    this.cOfMajorityhasJointlyOrInConcertCheckBox=page.locator('input[data-cy="controlOfDirectors.jointlyOrInConcert.hasJointlyOrInConcert"]');
    this.cOfMajorityactingJointlyCheckBox=page.locator('input[data-cy="controlOfDirectors.jointlyOrInConcert.actingJointly"]');
    this.cOfMajorityinConcertControlCheckBox= page.locator('input[data-cy="controlOfDirectors.jointlyOrInConcert.inConcertControl"]');

    this.email = page.locator('input[data-cy="testEmail"]');

    
    this.addressCountryButton = page.locator('#headlessui-listbox-button-v-0-21[data-cy="address-country"]');

    this.addressStreet= page.locator('#headlessui-combobox-input-v-0-23[data-cy="address-street"]');
    this.addressStreetLine2= page.locator('#v-0-25[data-cy="address-line2"]');
    this.addressCity= page.locator('#v-0-26[data-cy="address-city"]');
    this.addressProvince= page.locator('#v-0-27[data-cy="address-region-input"]');
    this.addressPostalCode= page.locator('#v-0-28[data-cy="address-postal-code"]');

    this.mailingAddIsDiffCheckbox = page.locator('#v-0-30[data-cy="mailingAddressIsDifferent-checkbox"]');

    this.mailingAddressCountryButton=page.locator('#v-0-796[data-cy="address-country"]');
    this.mailingAddressStreet=page.locator('#headlessui-combobox-input-v-0-799[data-cy="address-street"]');
    this.mailingAddressStreetLine2=page.locator('#v-0-801[data-cy="address-line2"]');
    this.mailingAddressCity=page.locator('#v-0-802[data-cy="address-city"]');
    this.mailingAddressProvince=page.locator('#v-0-803[data-cy="address-region-input"]');
    this.mailingAddressPostalCode=page.locator('#v-0-804[data-cy="address-postal-code"]');
  

    this.phoneNumberCountryCodeCombo = page.locator('input[data-cy="phoneNumber.countryCode"]');
    this.phoneNumberNumberInput = page.locator('input[data-cy="phoneNumber.number"]');
    this.phoneNumberExtenstionInput=page.locator('input[data-cy="phoneNumber.extensionCode"]');
    this.birthDateDate = page.locator('[name="birthDate"]') ;

    this.citizenshipsCaCitizenRadio = page.locator('input[data-cy="citizenships-ca-citizen-radio"]');
    this.citizenshipsCaPrRadio = page.locator('input[data-cy="citizenships-ca-pr-radio"]');
    this.citizenshipsOtherComboButton= page.locator('button[data-cy="citizenships.otherComboboxButton"]');

    this.taxNumberInput = page.locator('input[data-cy="tax-number-input"]');
    this.noTaxNumberCheckBox = page.locator('input[data-cy="no-tax-number-checkbox"]');

    this.taxResidenceTrueCheckbox = page.locator('#taxResidency-true');
    this.taxResidenceFalseCheckboxid=page.locator('#taxResidency-false');
    
    this.determinationOfIncapacityCheckbox= page.locator('[name="determinationOfIncapacity"]');
    this.isUnableToObtainOrConfirmInformationCheckbox = page.locator('[name="isUnableToObtainOrConfirmInformation"]');

    this.newSIDoneButton= page.locator('button[data-cy="new-si-done-btn"]');
    this.newSICancelButton = page.locator('button[data-cy="new-si-cancel-btn"]');

    this.reviewAndConfirmButton = page.locator('button[data-cy="button-control-right-button"]');

  }

  async selectDeclaration(delarationSIType: string) {
    switch (delarationSIType) {
        case 'SI':
          await this.declarationMeBtn.click();
          break;
        case 'PARENT':
          await this.declarationParentBtn.click;
          break;
        case 'LAWYER':
          await this.declarationLawyerBtn.click()
          break;
        case 'NONE':
            await this.declarationNoneBtn.click;
        default:
          console.log('No matching action found.');
      }
      
  }

  async enterFullName(fullNameInput: string) {
    this.fullNameInput.fill(fullNameInput)
      }
      
  async controlOfSharePercentageSelect(controlOfSharePercentage: string) {
        switch (controlOfSharePercentage) {
            case 'Less25':
                await this.cOfShareLess25Percentage.click()      
              break;
            case '25-50':
                await this.cOfShare25_50Percentage.click
              break;
            case '50-75':
                await this.cOfShare50_75Percentage.click
              break;
            case 'Over75':
                await this.cOfShareGreater75Percentage.click
            default:
              console.log('No matching action found.');
          }
          
      }
      async controlOfVotePercentageSelect(controlOfVotePercentage: string) {
        switch (controlOfVotePercentage) {
            case 'Less25':
                await this.cOfVotes25Percentage.click()      
              break;
            case '25-50':
                await this.cOfVotes25_50Percentage.click
              break;
            case '50-75':
                await this.cOfVotes50_75Percentage.click
              break;
            case 'Over75':
                await this.cOfVotesGreater75Percentage.click
            default:
              console.log('No matching action found.');
          }
          
      }

  }
