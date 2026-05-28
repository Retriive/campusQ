"use client"

import * as React from "react"

export type Campus = "carleton" | "uottawa" | "mcgill"

interface CampusTheme {
  name: string
  primaryColor: string
  bgClass: string
  hoverBgClass: string
  borderClass: string
  textClass: string
}

export const campusThemes: Record<Campus, CampusTheme> = {
  carleton: {
    name: "Carleton University",
    primaryColor: "bg-red-700",
    bgClass: "bg-red-700",
    hoverBgClass: "hover:bg-red-800",
    borderClass: "border-red-700",
    textClass: "text-red-700",
  },
  uottawa: {
    name: "uOttawa",
    primaryColor: "bg-red-600",
    bgClass: "bg-red-600",
    hoverBgClass: "hover:bg-red-700",
    borderClass: "border-red-600",
    textClass: "text-red-600",
  },
  mcgill: {
    name: "McGill",
    primaryColor: "bg-red-800",
    bgClass: "bg-red-800",
    hoverBgClass: "hover:bg-red-900",
    borderClass: "border-red-800",
    textClass: "text-red-800",
  },
}

interface CampusContextType {
  selectedCampus: Campus
  setSelectedCampus: (campus: Campus) => void
  theme: CampusTheme
}

const CampusContext = React.createContext<CampusContextType | undefined>(undefined)

export function CampusProvider({ children }: { children: React.ReactNode }) {
  const [selectedCampus, setSelectedCampus] = React.useState<Campus>("carleton")
  const theme = campusThemes[selectedCampus]

  return (
    <CampusContext.Provider value={{ selectedCampus, setSelectedCampus, theme }}>
      {children}
    </CampusContext.Provider>
  )
}

export function useCampus() {
  const context = React.useContext(CampusContext)
  if (context === undefined) {
    throw new Error("useCampus must be used within a CampusProvider")
  }
  return context
}
