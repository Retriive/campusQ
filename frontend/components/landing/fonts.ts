import { Instrument_Serif, Source_Sans_3 } from "next/font/google"

export const landDisplay = Instrument_Serif({
  subsets: ["latin"],
  variable: "--font-land-display",
  weight: "400",
  style: ["normal", "italic"],
})

export const landBody = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-land-body",
  weight: ["400", "500", "600", "700"],
})
