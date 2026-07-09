"use client"

import * as Sentry from "@sentry/react"
import { useEffect } from "react"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
      Sentry.captureException(error)
    }
  }, [error])

  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col items-center justify-center gap-4 p-6 bg-background text-foreground">
        <h2 className="text-lg font-semibold">Something went wrong</h2>
        <p className="text-sm text-muted-foreground text-center max-w-md">
          CampusQ hit an unexpected error. Try refreshing the page.
        </p>
        <button
          type="button"
          onClick={reset}
          className="rounded-full bg-primary px-5 py-2 text-sm text-primary-foreground"
        >
          Try again
        </button>
      </body>
    </html>
  )
}
