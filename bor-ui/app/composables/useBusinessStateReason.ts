import { DateTime } from 'luxon'

/**
 * Provides the reason a business is in its current (historical) state.
 * Mirrors the state badge logic in business-dashboard-ui (businessDetails/Status.vue),
 * using the public business/filing data available to search users.
 */
export const useBusinessStateReason = () => {
  const { $businessApi } = useNuxtApp()
  const t = useNuxtApp().$i18n.t
  const businessStore = useBusinessStore()
  const { business } = storeToRefs(businessStore)

  const enDash = '–' // ALT + 0150

  /** Convert a yyyy-mm-dd string to a Date at midnight Pacific time. */
  const yyyyMmDdToDate = (dateStr?: string): Date | undefined => {
    if (!dateStr || dateStr.length !== 10) {
      return undefined
    }
    const date = DateTime.fromISO(dateStr, { zone: 'America/Vancouver' }).toJSDate()
    return isNaN(date.valueOf()) ? undefined : date
  }

  /** Format a Date as 'Month Day, Year at HH:MM am/pm Pacific time'. */
  const dateToPacificDateTime = (date: Date): string | undefined => {
    const dateStr = dateToPacificDate(date, true)
    const timeStr = dateToPacificTime(date)
    if (!dateStr || !timeStr) {
      return undefined
    }
    return `${dateStr} at ${timeStr} Pacific time`
  }

  /** Fetch the public view of the business state filing. */
  const getPublicStateFiling = async (
    identifier: string,
    stateFilingUrl: string
  ): Promise<PublicStateFilingResponse['filing'] | undefined> => {
    const filingId = stateFilingUrl.split('/').pop()
    if (!filingId) {
      return undefined
    }
    return await $businessApi<PublicStateFilingResponse>(
      `businesses/${identifier}/filings/${filingId}`,
      { query: { public: true } }
    ).then(resp => resp?.filing).catch((error) => {
      console.warn('Error fetching state filing', error)
      return undefined
    })
  }

  /** Return the reason text for the business state (empty when not historical). */
  const getStateReason = async (): Promise<string> => {
    const biz = business.value as (BusinessDataPublic & BusinessStateData) | undefined
    if (!biz || biz.state !== EntityState.HISTORICAL) {
      return ''
    }

    // reason for amalgamation
    if (biz.amalgamatedInto) {
      const name = t('filing.name.amalgamation')
      const amalgamationDate = apiToDate(biz.amalgamatedInto.amalgamationDate)
      const date = amalgamationDate ? dateToPacificDate(amalgamationDate, true) : `[${t('text.unknown')}]`
      const identifier = biz.amalgamatedInto.identifier || t('label.unknownCompany')
      return `${name} ${enDash} ${date} ${enDash} ${identifier}`
    }

    if (!biz.stateFiling) {
      return ''
    }
    const stateFiling = await getPublicStateFiling(biz.identifier, biz.stateFiling)
    const filingType = stateFiling?.header?.name
    if (!filingType) {
      return ''
    }
    const filingData: PublicStateFilingBody
      = (stateFiling as Partial<Record<string, PublicStateFilingBody>>)[filingType] || {}

    // reason for dissolution
    if (filingType === 'dissolution') {
      let reason = t('filing.name.unknown')
      switch (filingData.type) {
        case 'administrative':
          reason = t('filing.reason.dissolutionAdministrative')
          break
        case 'involuntary':
          reason = t('filing.reason.involuntaryDissolution')
          break
        case 'voluntary':
          reason = businessStore.isFirm() ? t('filing.reason.dissolutionFirm') : t('filing.reason.voluntaryDissolution')
      }
      const dissolutionDate = yyyyMmDdToDate(filingData.dissolutionDate)
        || apiToDate(stateFiling.header?.effectiveDate || '')
      const date = dissolutionDate ? dateToPacificDate(dissolutionDate, true) : `[${t('text.unknown')}]`
      return `${reason} ${enDash} ${date}`
    }

    // reason for put back off
    if (filingType === 'putBackOff' && filingData.reason) {
      const expiryDate = yyyyMmDdToDate(filingData.expiryDate)
      const date = expiryDate ? dateToPacificDate(expiryDate, true) : `[${t('text.unknown')}]`
      return `${filingData.reason} on ${date}`
    }

    // reason for continuation out and default 'reason'
    const effectiveDate = apiToDate(stateFiling.header?.effectiveDate || '')
    const date = (effectiveDate && dateToPacificDateTime(effectiveDate)) || `[${t('text.unknown')}]`
    let reason = ''
    if (filingType === 'continuationOut') {
      reason = t('filing.reason.continuationOut')
    } else {
      reason = t(`filing.name.${filingType}`)
      if (reason === `filing.name.${filingType}`) {
        reason = t('filing.name.unknown')
      }
    }
    return `${reason} ${enDash} ${date}`
  }

  /** Append the state reason text beside the state badge in the business tombstone. */
  const setTombstoneStateReason = async (): Promise<void> => {
    const reason = await getStateReason()
    if (reason) {
      const { businessTombstone } = useBusinessTombstone()
      businessTombstone.value.details = [
        ...(businessTombstone.value.details || []),
        { text: reason }
      ]
    }
  }

  return {
    getStateReason,
    setTombstoneStateReason
  }
}
