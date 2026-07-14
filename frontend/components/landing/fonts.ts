import { Instrument_Serif, Plus_Jakarta_Sans } from "next/font/google"

export const landDisplay = Instrument_Serif({
  subsets: ["latin"],
  variable: "--font-land-display",
  weight: "400",
  style: ["normal", "italic"],
})

export const landBody = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-land-body",
  weight: ["400", "500", "600", "700"],
})
