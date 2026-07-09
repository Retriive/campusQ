import type { View } from "../sidebar"
import type { Message } from "./types"

export interface Suggestion {
  label: string
  query?: string
  view?: View
}

export function getSuggestions(
  message: Message,
  courseCodes: string[],
): Suggestion[] {
  const suggestions: Suggestion[] = []
  if (courseCodes.length > 0) {
    const code = courseCodes[0]
    suggestions.push({
      label: `Prerequisite tree for ${code}`,
      query: `Show prerequisite chain for ${code}`,
    })
    if (courseCodes.length === 1) {
      suggestions.push({
        label: `Compare ${code} with another course`,
        view: "compare",
      })
    }
  }
  if (
    message.content.toLowerCase().includes("program")
    || message.content.toLowerCase().includes("degree")
  ) {
    suggestions.push({ label: "Browse all programs", view: "programs" })
  }
  return suggestions.slice(0, 3)
}

export function extractCourseCodes(text: string): string[] {
  const matches = text.match(/\b[A-Z]{4}\s*\d{4}\b/g) || []
  return [...new Set(matches.map((match) => match.replace(/\s+/, " ").trim()))]
}
