export interface CourseCardData {
  courseCode: string
  courseName: string
  credits: number
  description: string
  prerequisites: string[]
  prerequisiteText?: string
}

export interface Source {
  url: string
  title: string
  section?: string
}

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  courseCards?: CourseCardData[]
  sources?: Source[]
}
