import { describe, expect, it } from 'vitest'
import { DateTime } from 'luxon'

import {
  certOfGoodStandingDependsOnAr,
  hasFiledArInLast12Months,
  suppressCertOfGoodStanding,
  suppressCertOfStatus
} from '../../../app/utils/suppress-cert-documents'

const now = DateTime.fromISO('2026-10-20T12:00:00Z')

const makeFiling = (overrides: Partial<BusinessLedgerItem> = {}) => ({
  name: FilingType.ANNUAL_REPORT,
  status: FilingStatus.COMPLETED,
  paymentDate: 'Tue, 20 Jan 2026 18:00:00 GMT',
  submittedDate: 'Tue, 20 Jan 2026 18:00:00 GMT',
  effectiveDate: 'Tue, 20 Jan 2026 18:00:00 GMT',
  ...overrides
}) as BusinessLedgerItem

describe('suppressCertOfGoodStanding', () => {
  it.each([
    BusinessType.CEMETERY,
    BusinessType.LIBRARY,
    BusinessType.PENSION_FUND_SOCIETY,
    BusinessType.RAILWAYS,
    BusinessType.SOCIETY_BRANCH,
    BusinessType.TRAMWAYS
  ])('always suppresses for %s', (legalType) => {
    expect(suppressCertOfGoodStanding(legalType)).toBe(true)
    expect(suppressCertOfGoodStanding(legalType, true)).toBe(true)
  })

  it.each([BusinessType.FINANCIAL, BusinessType.PRIVATE_ACT])(
    'suppresses for %s only when no AR was filed in the last 12 months',
    (legalType) => {
      expect(suppressCertOfGoodStanding(legalType, false)).toBe(true)
      expect(suppressCertOfGoodStanding(legalType, true)).toBe(false)
    }
  )

  it.each([
    BusinessType.PARISHES,
    BusinessType.COOP,
    BusinessType.XPRO_COOP,
    BusinessType.TRUST,
    BusinessType.BC_COMPANY,
    undefined
  ])('does not suppress for %s', (legalType) => {
    expect(suppressCertOfGoodStanding(legalType)).toBe(false)
  })
})

describe('suppressCertOfStatus', () => {
  it.each([
    BusinessType.CEMETERY,
    BusinessType.FINANCIAL,
    BusinessType.LIBRARY,
    BusinessType.PARISHES,
    BusinessType.PENSION_FUND_SOCIETY,
    BusinessType.PRIVATE_ACT,
    BusinessType.RAILWAYS,
    BusinessType.SOCIETY_BRANCH,
    BusinessType.TRAMWAYS,
    BusinessType.XPRO_COOP
  ])('suppresses for %s', (legalType) => {
    expect(suppressCertOfStatus(legalType)).toBe(true)
  })

  it.each([
    BusinessType.COOP,
    BusinessType.TRUST,
    BusinessType.BC_COMPANY,
    undefined
  ])('does not suppress for %s', (legalType) => {
    expect(suppressCertOfStatus(legalType)).toBe(false)
  })
})

describe('certOfGoodStandingDependsOnAr', () => {
  it('is true only for Financial and Private Act', () => {
    expect(certOfGoodStandingDependsOnAr(BusinessType.FINANCIAL)).toBe(true)
    expect(certOfGoodStandingDependsOnAr(BusinessType.PRIVATE_ACT)).toBe(true)
    expect(certOfGoodStandingDependsOnAr(BusinessType.LIBRARY)).toBe(false)
    expect(certOfGoodStandingDependsOnAr(undefined)).toBe(false)
  })
})

describe('hasFiledArInLast12Months', () => {
  it('returns false for no filings', () => {
    expect(hasFiledArInLast12Months(undefined, now)).toBe(false)
    expect(hasFiledArInLast12Months([], now)).toBe(false)
  })

  it('returns true for a completed AR filed within 12 months', () => {
    expect(hasFiledArInLast12Months([makeFiling()], now)).toBe(true)
  })

  it('returns false for an AR filed more than 12 months ago', () => {
    const old = 'Sun, 19 Oct 2025 07:00:00 GMT'
    const filing = makeFiling({ paymentDate: old, submittedDate: old, effectiveDate: old })
    expect(hasFiledArInLast12Months([filing], now)).toBe(false)
  })

  it('uses the payment date over the effective date', () => {
    const filing = makeFiling({
      paymentDate: 'Tue, 20 Jan 2026 18:00:00 GMT',
      effectiveDate: 'Mon, 27 Dec 2021 08:00:00 GMT'
    })
    expect(hasFiledArInLast12Months([filing], now)).toBe(true)
  })

  it('falls back to submitted date when there is no payment date', () => {
    const filing = makeFiling({
      paymentDate: undefined,
      submittedDate: 'Tue, 20 Jan 2026 18:00:00 GMT',
      effectiveDate: 'Mon, 27 Dec 2021 08:00:00 GMT'
    })
    expect(hasFiledArInLast12Months([filing], now)).toBe(true)
  })

  it('ignores filings that are not annual reports', () => {
    const filing = makeFiling({ name: FilingType.CHANGE_OF_DIRECTORS })
    expect(hasFiledArInLast12Months([filing], now)).toBe(false)
  })

  it('ignores annual reports that are not completed', () => {
    const filing = makeFiling({ status: FilingStatus.DRAFT })
    expect(hasFiledArInLast12Months([filing], now)).toBe(false)
  })

  it('ignores filings with an invalid date', () => {
    const filing = makeFiling({ paymentDate: 'not a date', submittedDate: 'not a date' })
    expect(hasFiledArInLast12Months([filing], now)).toBe(false)
  })

  it('finds a recent AR among older filings', () => {
    const old = 'Wed, 22 Jan 2020 18:00:00 GMT'
    const filings = [
      makeFiling({ paymentDate: old, submittedDate: old, effectiveDate: old }),
      makeFiling()
    ]
    expect(hasFiledArInLast12Months(filings, now)).toBe(true)
  })
})
