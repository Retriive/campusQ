import { Metadata } from "next"
import { AboutContent } from "@/components/landing/about-content"

export const metadata: Metadata = {
  title: "About — CampusQ",
  description: "CampusQ is an AI academic assistant for Canadian university students.",
}

export default function AboutPage() {
  return <AboutContent />
}
