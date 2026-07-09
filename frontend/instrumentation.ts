export async function register() {
  if (process.env.NEXT_RUNTIME !== "nodejs") return

  const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN
  if (!dsn) return

  const Sentry = await import("@sentry/node")
  Sentry.init({
    dsn,
    environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || "development",
    tracesSampleRate: Number(process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || "0.1"),
    sendDefaultPii: false,
  })
}
