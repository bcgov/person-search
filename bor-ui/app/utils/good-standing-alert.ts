// Mainframe entity types that never show the "not in good standing" alert.
// Not suppressed (by business decision): PARISHES, COOP, XPRO_COOP.
// Still outstanding: FINANCIAL (waiting on audience confirmation).
const GOOD_STANDING_SUPPRESSED_TYPES: string[] = [
  BusinessType.CEMETERY,
  BusinessType.LIBRARY,
  BusinessType.PENSION_FUND_SOCIETY,
  BusinessType.PRIVATE_ACT,
  BusinessType.RAILWAYS,
  BusinessType.SOCIETY_BRANCH,
  BusinessType.TRAMWAYS
]

/**
 * Whether the "not in good standing" alert should be hidden for this business.
 * TRUST is only suppressed when HISTORICAL (ACTIVE trusts still show it).
 */
export const suppressGoodStandingAlert = (legalType?: string, state?: string): boolean => {
  if (!legalType) {
    return false
  }
  if (legalType === BusinessType.TRUST) {
    return state === EntityState.HISTORICAL
  }
  return GOOD_STANDING_SUPPRESSED_TYPES.includes(legalType)
}
