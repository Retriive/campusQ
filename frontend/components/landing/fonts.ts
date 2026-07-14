import { Syne, Plus_Jakarta_Sans } from "next/font/google"

export const landDisplay = Syne({
  subsets: ["latin"],
  variable: "--font-land-display",
  weight: ["500", "600", "700", "800"],
})

export const landBody = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-land-body",
  weight: ["400", "500", "600", "700"],
})
