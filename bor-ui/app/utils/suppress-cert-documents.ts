import { DateTime } from 'luxon'

/**
 * Mainframe (non-COLIN) entity types that have been migrated and must not offer
 * the Certificate of Good Standing (CGOOD) and/or Certificate of Status (CSTAT) for purchase.
 *
 * NOTES:
 * - TRUST ('T') needs no handling: the rule is "suppress if Historical, do not suppress if Active", and
 *   the documents are already only offered for ACTIVE businesses.
 * - COOPERATIVE ('CP') is never suppressed. XPRO COOP ('XCP') only has CSTAT suppressed.
 */

/** Always suppress the Certificate of Good Standing. */
const suppressCGoodTypes: BusinessType[] = [
  BusinessType.CEMETERY,
  BusinessType.LIBRARY,
  BusinessType.PENSION_FUND_SOCIETY,
  BusinessType.RAILWAYS,
  BusinessType.SOCIETY_BRANCH,
  BusinessType.TRAMWAYS
]

/** Suppress the Certificate of Good Standing UNLESS the entity filed an AR in the last 12 months. */
const suppressCGoodUnlessRecentArTypes: BusinessType[] = [
  BusinessType.FINANCIAL,
  BusinessType.PRIVATE_ACT
]

/** Always suppress the Certificate of Status. */
const suppressCStatTypes: BusinessType[] = [
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
]

/** Whether the legal type needs the filing history to decide on the Certificate of Good Standing. */
export const certOfGoodStandingDependsOnAr = (legalType?: string): boolean =>
  suppressCGoodUnlessRecentArTypes.includes(legalType as BusinessType)

/**
 * Whether the filing history contains a completed Annual Report filed within the last 12 months.
 * The "filed and paid" date shown in the history is used (payment date, falling back to submitted/effective date).
 */
export const hasFiledArInLast12Months = (filings: BusinessLedgerItem[] = [], now = DateTime.now()): boolean => {
  const cutoff = now.minus({ years: 1 })

  return filings.some((filing) => {
    const isAr = filing.name === FilingType.ANNUAL_REPORT
      || !!filing.data?.legalFilings?.includes(FilingType.ANNUAL_REPORT)
    if (!isAr || filing.status !== FilingStatus.COMPLETED) {
      return false
    }
    // ledger dates are in the form of "Wed, 23 Apr 2025 21:30:40 GMT"
    const filedDate = DateTime.fromRFC2822(filing.paymentDate || filing.submittedDate || filing.effectiveDate)
    return filedDate.isValid && filedDate >= cutoff && filedDate <= now
  })
}
/** Whether the Certificate of Good Standing option should be hidden. */
export const suppressCertOfGoodStanding = (legalType?: string, filedArInLast12Months = false): boolean => {
  if (suppressCGoodTypes.includes(legalType as BusinessType)) {
    return true
  }
  return certOfGoodStandingDependsOnAr(legalType) && !filedArInLast12Months
}

/** Whether the Certificate of Status option should be hidden. */
export const suppressCertOfStatus = (legalType?: string): boolean =>
  suppressCStatTypes.includes(legalType as BusinessType)
