/**
 * Amalgamation info returned in the business slim/public json when the
 * business has been amalgamated into another company.
 */
export interface BusinessAmalgamatedInto {
  amalgamationDate: string
  amalgamationType?: string
  courtApproval?: boolean
  identifier?: string
  legalName?: string
}

/**
 * Extra state fields returned by the business public endpoint that are not
 * (yet) declared on BusinessDataPublic in the business base layer.
 */
export interface BusinessStateData {
  amalgamatedInto?: BusinessAmalgamatedInto
  stateFiling?: string
}

/** Filing body values returned by GET businesses/{id}/filings/{filingId}?public=true */
export interface PublicStateFilingBody {
  type?: string
  reason?: string
  expiryDate?: string
  dissolutionDate?: string
}

/** Response from GET businesses/{id}/filings/{filingId}?public=true */
export interface PublicStateFilingResponse {
  filing?: {
    header?: {
      name?: string
      effectiveDate?: string
    }
  } & Partial<Record<string, PublicStateFilingBody>>
}
