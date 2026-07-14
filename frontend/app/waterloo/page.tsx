import type { Metadata } from "next"
import { LandingPage } from "@/components/landing/landing-page"
import { SCHOOLS } from "@/lib/landing-schools"

const school = SCHOOLS.waterloo

export const metadata: Metadata = {
  title: `CampusQ for ${school.shortName} — join the waitlist`,
  description: `CampusQ is coming to ${school.name}. Join the waitlist for official-calendar course, program, and deadline answers.`,
  openGraph: {
    title: `CampusQ for ${school.shortName}`,
    description: `Join the waitlist — CampusQ is indexing ${school.shortName}'s academic calendar next.`,
  },
}

export default function Page() {
  return <LandingPage defaultSchool="waterloo" />
}
