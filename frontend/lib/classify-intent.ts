// Mirrors backend classify_intent() for analytics categorization only — never log raw query text.
export function classifyIntent(query: string): string {
  const q = query.toLowerCase()
  if (["prerequisite", "prereq", "before taking", "without taking"].some((k) => q.includes(k))) {
    return "prerequisites"
  }
  if (["deadline", "last day", "when is", "when do", "when does", "what date"].some((k) => q.includes(k))) {
    return "deadlines"
  }
  if (["cgpa", "gpa", "good standing", "fail", "repeat", "withdraw", "ace ", "academic standing"].some((k) => q.includes(k))) {
    return "regulations"
  }
  if (q.includes("engineering") && ["how many times", "attempt", "retake", "try again"].some((k) => q.includes(k))) {
    return "regulations"
  }
  if (["register", "registration", "add a course", "drop", "override", "waitlist", "time ticket"].some((k) => q.includes(k))) {
    return "registration"
  }
  if (["required courses", "graduate", "degree", "program", "stream", "concentration", "minor", "credits to"].some((k) => q.includes(k))) {
    return "program_requirements"
  }
  if (["co-op", "transcript", "financial aid", "bursary", "scholarship", "defer", "enrolment"].some((k) => q.includes(k))) {
    return "services"
  }
  if (/[a-zA-Z]{4}\s*\d{4}/.test(query)) {
    return "course_lookup"
  }
  return "general"
}
