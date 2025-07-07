import posthog from 'posthog-js'

export const initPostHog = () => {
  if (typeof window !== 'undefined') {
    posthog.init(
      process.env.NEXT_PUBLIC_POSTHOG_KEY || 'phc_demo_key', // Replace with your actual PostHog key
      {
        api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://us.i.posthog.com',
        person_profiles: 'identified_only',
        capture_pageview: true,
        capture_pageleave: true,
      }
    )
  }
}

export { posthog } 