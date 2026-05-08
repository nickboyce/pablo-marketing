import type posthogJs from 'posthog-js'

type PostHog = typeof posthogJs

let instance: PostHog | null = null
let initPromise: Promise<void> | null = null

export const initPostHog = () => {
  if (typeof window === 'undefined') return
  if (initPromise) return initPromise
  initPromise = import('posthog-js').then(({ default: ph }) => {
    instance = ph
    ph.init(
      process.env.NEXT_PUBLIC_POSTHOG_KEY || 'phc_demo_key',
      {
        api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://us.i.posthog.com',
        person_profiles: 'identified_only',
        capture_pageview: true,
        capture_pageleave: true,
      }
    )
  })
  return initPromise
}

export const posthog = {
  capture: (event: string, properties?: Record<string, unknown>) => {
    if (typeof window === 'undefined') return
    if (instance) {
      instance.capture(event, properties)
    } else {
      initPostHog()?.then(() => instance?.capture(event, properties))
    }
  },
}
