export type SchoolId =
  | "carleton"
  | "uottawa"
  | "uoft"
  | "waterloo"
  | "western"
  | "mcgill"

// Accent colors live in globals.css as [data-school] token themes.
// Components render with token classes (bg-primary, text-primary-ink, …)
// and the landing root's data-school attribute swaps the palette.
export interface SchoolConfig {
  id: SchoolId
  name: string
  shortName: string
  live: boolean
  badge: string
  path: string
  demoMessages: { role: "user" | "assistant"; text: string }[]
  stats: { value: string; label: string }[]
}

export const SCHOOLS: Record<SchoolId, SchoolConfig> = {
  carleton: {
    id: "carleton",
    name: "Carleton University",
    shortName: "Carleton",
    live: true,
    badge: "Live for Carleton students",
    path: "/",
    demoMessages: [
      { role: "user", text: "Can I take COMP 2401 without finishing COMP 1405?" },
      { role: "assistant", text: "No — COMP 2401 requires either COMP 1405 or COMP 1406 as a prerequisite. You'll need to complete one of those first before registering." },
      { role: "user", text: "What's the last day to drop a course this fall?" },
      { role: "assistant", text: "For Fall 2026, the last day to withdraw from a full fall course without academic notation is November 15th." },
    ],
    stats: [
      { value: "3,782", label: "courses indexed" },
      { value: "84", label: "programs covered" },
      { value: "498", label: "degree variants" },
      { value: "0", label: "advisor queues" },
    ],
  },
  uottawa: {
    id: "uottawa",
    name: "University of Ottawa",
    shortName: "uOttawa",
    live: false,
    badge: "Waitlist open for uOttawa students",
    path: "/uottawa",
    demoMessages: [
      { role: "user", text: "What's the prerequisite for ITI 1121?" },
      { role: "assistant", text: "uOttawa's course catalog isn't indexed yet — join the waitlist and you'll be first to ask when it opens." },
      { role: "user", text: "Does CSI 2110 count toward a Software Engineering degree?" },
      { role: "assistant", text: "Not live for uOttawa yet. Drop your email — we'll notify you the day program requirements are searchable." },
    ],
    stats: [
      { value: "Soon", label: "catalog indexing" },
      { value: "Soon", label: "programs covered" },
      { value: "Soon", label: "deadlines tracked" },
      { value: "0", label: "advisor queues" },
    ],
  },
  uoft: {
    id: "uoft",
    name: "University of Toronto",
    shortName: "UofT",
    live: false,
    badge: "Waitlist open for UofT students",
    path: "/uoft",
    demoMessages: [
      { role: "user", text: "What are the prereqs for CSC236?" },
      { role: "assistant", text: "UofT's Arts & Science calendar isn't in CampusQ yet — join the waitlist to get notified when course lookup goes live." },
      { role: "user", text: "Can I take PSY100 and CSC108 in the same term as a first-year?" },
      { role: "assistant", text: "We'll answer that from the official calendar once UofT is indexed. Join the waitlist to be first in line." },
    ],
    stats: [
      { value: "Soon", label: "calendar indexing" },
      { value: "Soon", label: "programs covered" },
      { value: "Soon", label: "deadlines tracked" },
      { value: "0", label: "advisor queues" },
    ],
  },
  waterloo: {
    id: "waterloo",
    name: "University of Waterloo",
    shortName: "Waterloo",
    live: false,
    badge: "Waitlist open for Waterloo students",
    path: "/waterloo",
    demoMessages: [
      { role: "user", text: "Is CS 135 a prereq for CS 136?" },
      { role: "assistant", text: "Waterloo's Undergraduate Calendar isn't indexed yet — join the waitlist and we'll email you when CS course lookup is ready." },
      { role: "user", text: "What's the drop deadline for a Fall co-op study term?" },
      { role: "assistant", text: "Not live for Waterloo yet. Get on the waitlist and you'll hear the moment term deadlines are searchable." },
    ],
    stats: [
      { value: "Soon", label: "calendar indexing" },
      { value: "Soon", label: "co-op rules covered" },
      { value: "Soon", label: "deadlines tracked" },
      { value: "0", label: "advisor queues" },
    ],
  },
  western: {
    id: "western",
    name: "Western University",
    shortName: "Western",
    live: false,
    badge: "Waitlist open for Western students",
    path: "/western",
    demoMessages: [
      { role: "user", text: "What are the prerequisites for CS 2210?" },
      { role: "assistant", text: "Western's academic calendar isn't in CampusQ yet — join the waitlist to get notified when course requirements go live." },
      { role: "user", text: "Do I need Calculus for a Computer Science Major?" },
      { role: "assistant", text: "We'll answer from Western's official program pages once indexing finishes. Join the waitlist to be notified first." },
    ],
    stats: [
      { value: "Soon", label: "catalog indexing" },
      { value: "Soon", label: "programs covered" },
      { value: "Soon", label: "deadlines tracked" },
      { value: "0", label: "advisor queues" },
    ],
  },
  mcgill: {
    id: "mcgill",
    name: "McGill University",
    shortName: "McGill",
    live: false,
    badge: "Waitlist open for McGill students",
    path: "/mcgill",
    demoMessages: [
      { role: "user", text: "What's the prereq for COMP 206?" },
      { role: "assistant", text: "McGill's eCalendar isn't indexed yet — join the waitlist and you'll be first to ask when CampusQ opens for McGill." },
      { role: "user", text: "Can I take MATH 133 without CEGEP math?" },
      { role: "assistant", text: "Not live for McGill yet. Drop your email — we'll notify you the day program and course rules are searchable." },
    ],
    stats: [
      { value: "Soon", label: "eCalendar indexing" },
      { value: "Soon", label: "programs covered" },
      { value: "Soon", label: "deadlines tracked" },
      { value: "0", label: "advisor queues" },
    ],
  },
}

export const SCHOOL_LIST = Object.values(SCHOOLS)

export function schoolPath(id: SchoolId): string {
  return SCHOOLS[id].path
}
