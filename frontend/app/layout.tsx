import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import { ClerkProvider } from '@clerk/nextjs'
import { SentryInit } from '@/components/sentry-init'
import './globals.css'

const _geist = Geist({ subsets: ["latin"] });
const _geistMono = Geist_Mono({ subsets: ["latin"] });

export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
}

export const metadata: Metadata = {
  metadataBase: new URL('https://try-campusq.vercel.app'),
  title: 'CampusQ',
  description: 'CampusQ is an AI-powered academic assistant for Carleton University students. Look up courses, prerequisites, program requirements, and university policies instantly.',
  keywords: ['Carleton University', 'course lookup', 'prerequisites', 'academic assistant', 'degree planner'],
  icons: {
    icon: '/favicon.svg',
    shortcut: '/favicon.svg',
  },
  openGraph: {
    title: 'CampusQ — AI Academic Assistant',
    description: 'Your AI academic assistant, available 24/7. Instant answers from the Carleton academic calendar.',
    type: 'website',
    siteName: 'CampusQ',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'CampusQ — AI Academic Assistant',
    description: 'Your AI academic assistant, available 24/7. Instant answers from the Carleton academic calendar.',
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <ClerkProvider>
      <html lang="en" className="bg-background">
        <head>
          <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        </head>
        <body className="font-sans antialiased" suppressHydrationWarning>
          <SentryInit />
          {children}
          <Analytics />
        </body>
      </html>
    </ClerkProvider>
  )
}
