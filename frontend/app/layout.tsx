import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import { ClerkProvider } from '@clerk/nextjs'
import './globals.css'

const _geist = Geist({ subsets: ["latin"] });
const _geistMono = Geist_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: 'CampusQ — Your AI academic advisor, available 24/7',
  description: 'CampusQ is an AI-powered academic assistant for Carleton University students. Look up courses, prerequisites, program requirements, and university policies instantly.',
  keywords: ['Carleton University', 'course lookup', 'prerequisites', 'academic advisor', 'degree planner'],
  icons: {
    icon: '/favicon.svg',
    shortcut: '/favicon.svg',
  },
  openGraph: {
    title: 'CampusQ — AI Academic Advisor',
    description: 'Your AI academic advisor, available 24/7. Instant answers from the Carleton academic calendar.',
    type: 'website',
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
        <body className="font-sans antialiased">
          {children}
          <Analytics />
        </body>
      </html>
    </ClerkProvider>
  )
}
