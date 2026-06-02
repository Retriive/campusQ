"use client"

import * as React from "react"
import { track } from "@vercel/analytics"
import { cn } from "@/lib/utils"
import { MessageSquare as MessageSquareIcon, BookOpen as BookOpenIcon, BarChart2 as BarChart2Icon, Calculator as CalculatorIcon, CalendarDays as CalendarDaysIcon } from "lucide-react"
import { Header } from "./header"
import { Sidebar, type View, type ChatSession } from "./sidebar"
import { ChatMessage } from "./chat-message"
import { ChatInput } from "./chat-input"
import { EmptyState } from "./empty-state"
import { CourseCard } from "./course-card"
import { FeedbackModal } from "./feedback-modal"
import { PrereqVisualizer } from "./prereq-visualizer"
import { CourseCompare } from "./course-compare"
import { ProgramExplorer } from "./program-explorer"
import { GpaCalculator } from "./gpa-calculator"
import { DeadlineTracker } from "./deadline-tracker"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const SESSIONS_KEY = "campusq-sessions"
const MAX_SESSIONS = 20

interface CourseCardData {
  courseCode: string
  courseName: string
  credits: number
  description: string
  prerequisites: string[]
}

interface Source {
  url: string
  title: string
}

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  courseCards?: CourseCardData[]
  sources?: Source[]
}

interface Suggestion {
  label: string
  query?: string
  view?: View
}

function getSuggestions(message: Message, courseCodes: string[]): Suggestion[] {
  const suggestions: Suggestion[] = []
  if (courseCodes.length > 0) {
    const code = courseCodes[0]
    suggestions.push({ label: `Prerequisite tree for ${code}`, query: `Show prerequisite chain for ${code}` })
    if (courseCodes.length === 1) {
      suggestions.push({ label: `Compare ${code} with another course`, view: "compare" })
    }
  }
  if (message.content.toLowerCase().includes("program") || message.content.toLowerCase().includes("degree")) {
    suggestions.push({ label: "Browse all programs", view: "programs" })
  }
  return suggestions.slice(0, 3)
}

function extractCourseCodes(text: string): string[] {
  const matches = text.match(/\b[A-Z]{4}\s*\d{4}\b/g) || []
  return [...new Set(matches.map((m) => m.replace(/\s+/, " ").trim()))]
}

export function ChatContainer() {
  const [messages, setMessages] = React.useState<Message[]>([])
  const [sessions, setSessions] = React.useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = React.useState<string>("")
  const [currentView, setCurrentView] = React.useState<View>("chat")
  const [input, setInput] = React.useState("")
  const [isLoading, setIsLoading] = React.useState(false)
  const [isDark, setIsDark] = React.useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false)
  const [showFeedback, setShowFeedback] = React.useState(false)
  const [lastQuery, setLastQuery] = React.useState("")
  const [expandedPrereq, setExpandedPrereq] = React.useState<string | null>(null)
  const messagesEndRef = React.useRef<HTMLDivElement>(null)

  // Load sessions from localStorage
  React.useEffect(() => {
    try {
      const stored = localStorage.getItem(SESSIONS_KEY)
      if (stored) setSessions(JSON.parse(stored))
    } catch {}
  }, [])

  // Auto-scroll
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Dark mode
  React.useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark)
  }, [isDark])

  // Collapse sidebar on small screens on mount
  React.useEffect(() => {
    if (window.innerWidth < 768) setSidebarCollapsed(true)
  }, [])

  const persistSessions = (updated: ChatSession[]) => {
    setSessions(updated)
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(updated))
  }

  const saveCurrentChat = (msgs: Message[], sessionId: string) => {
    if (msgs.length === 0) return
    const title = msgs[0].content.slice(0, 45) + (msgs[0].content.length > 45 ? "…" : "")
    const session: ChatSession = { id: sessionId, title, createdAt: Date.now() }
    persistSessions(
      [session, ...sessions.filter((s) => s.id !== sessionId)].slice(0, MAX_SESSIONS)
    )
  }

  const handleNewChat = () => {
    if (messages.length > 0) saveCurrentChat(messages, currentSessionId)
    setMessages([])
    const newId = Date.now().toString()
    setCurrentSessionId(newId)
    setCurrentView("chat")
    setExpandedPrereq(null)
  }

  const handleSelectSession = (id: string) => {
    if (messages.length > 0) saveCurrentChat(messages, currentSessionId)
    const msgs = JSON.parse(localStorage.getItem(`campusq-msgs-${id}`) || "[]")
    setMessages(msgs)
    setCurrentSessionId(id)
    setCurrentView("chat")
  }

  const handleDeleteSession = (id: string) => {
    persistSessions(sessions.filter((s) => s.id !== id))
    localStorage.removeItem(`campusq-msgs-${id}`)
    if (currentSessionId === id) {
      setMessages([])
      setCurrentSessionId(Date.now().toString())
    }
  }

  const saveMessages = (msgs: Message[], sessionId: string) => {
    localStorage.setItem(`campusq-msgs-${sessionId}`, JSON.stringify(msgs))
  }

  const handleSubmit = async (overrideInput?: string) => {
    const queryText = (overrideInput ?? input).trim()
    if (!queryText || isLoading) return

    // If no session ID yet, create one
    const sessionId = currentSessionId || Date.now().toString()
    if (!currentSessionId) setCurrentSessionId(sessionId)

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: queryText,
    }

    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setLastQuery(queryText)
    if (!overrideInput) setInput("")
    setIsLoading(true)
    setExpandedPrereq(null)

    // Detect prereq-chain queries so we can auto-expand the visualizer
    const isPrereqQuery = /prereq(uisite)?(\s+chain|\s+tree)?|show.*(prereq|chain|tree)|chain for|tree for/i.test(queryText)

    // Track analytics
    try { track("chat_query", { query: queryText.slice(0, 100) }) } catch {}

    const assistantId = (Date.now() + 1).toString()
    const assistantPlaceholder: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      courseCards: [],
    }
    setMessages((prev) => [...prev, assistantPlaceholder])

    const formData = new FormData()
    formData.append("question", queryText)
    formData.append("history", JSON.stringify(messages.map((m) => ({ role: m.role, content: m.content }))))
    formData.append("session_id", sessionId)

    try {
      const response = await fetch(`${API_URL}/api/chat/stream`, {
        method: "POST",
        body: formData,
      })

      if (!response.body) throw new Error("No response body")

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          const jsonStr = line.slice(6)
          if (!jsonStr.trim()) continue
          try {
            const parsed = JSON.parse(jsonStr)
            if (parsed.type === "token") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: m.content + parsed.content } : m
                )
              )
            } else if (parsed.type === "courses") {
              const codes = (parsed.data as CourseCardData[]).map((c) => c.courseCode)
              if (codes.length > 0) {
                try { track("course_lookup", { courses: codes.join(",") }) } catch {}
              }
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, courseCards: parsed.data } : m
                )
              )
              // Auto-expand prereq tree if the user explicitly asked for it
              if (isPrereqQuery && codes.length === 1) {
                setExpandedPrereq(codes[0])
              }
            } else if (parsed.type === "sources") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, sources: parsed.data } : m
                )
              )
            }
          } catch {}
        }
      }

      // Save messages after response
      setMessages((prev) => {
        saveMessages(prev, sessionId)
        saveCurrentChat(prev, sessionId)
        return prev
      })
    } catch (error) {
      console.error("Chat error:", error)
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: "Sorry, CampusQ is having trouble reaching the server. Is the backend running?" }
            : m
        )
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    handleSubmit(suggestion)
  }

  const sendFeedback = (question: string, answer: string, rating: "up" | "down") => {
    try {
      const fd = new FormData()
      fd.append("rating", rating)
      fd.append("question", question)
      fd.append("answer", answer)
      fd.append("session_id", currentSessionId || "none")
      fetch(`${API_URL}/api/feedback`, { method: "POST", body: fd }).catch(() => {})
      track("answer_feedback", { rating })
    } catch {}
  }

  const renderView = () => {
    if (currentView === "programs")  return <ProgramExplorer />
    if (currentView === "compare")   return <CourseCompare />
    if (currentView === "gpa")       return <GpaCalculator />
    if (currentView === "deadlines") return <DeadlineTracker />
    return null
  }

  const isChatView = currentView === "chat"

  return (
    <div className="flex h-dvh bg-background overflow-hidden">
      {/* Sidebar — hidden on mobile unless expanded */}
      <div className={cn(
        "hidden md:flex shrink-0 h-full",
        !sidebarCollapsed && "w-64",
        sidebarCollapsed && "w-16"
      )}>
        <Sidebar
          onNewChat={handleNewChat}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          currentView={currentView}
          onViewChange={(v) => { setCurrentView(v) }}
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
          onOpenFeedback={() => setShowFeedback(true)}
        />
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <Header isDark={isDark} onToggleDark={() => setIsDark(!isDark)} />

        {/* Non-chat views */}
        {!isChatView && (
          <main className="flex-1 overflow-y-auto">
            <div className="max-w-4xl mx-auto px-4 md:px-6 py-8">
              {renderView()}
            </div>
          </main>
        )}

        {/* Chat view */}
        {isChatView && (
          <>
            <main className="flex-1 overflow-y-auto">
              {messages.length === 0 ? (
                <div className="flex flex-col min-h-full">
                  <div className="flex-1 flex flex-col justify-center">
                    <EmptyState
                      onSuggestionClick={handleSuggestionClick}
                      onViewChange={(v) => setCurrentView(v as View)}
                    />
                  </div>
                  {/* Input lives here on home screen, centered with content */}
                  <div className="max-w-2xl mx-auto w-full px-4 pb-6">
                    <ChatInput
                      value={input}
                      onChange={setInput}
                      onSubmit={handleSubmit}
                      disabled={isLoading}
                      isHome
                    />
                  </div>
                </div>
              ) : (
                <div className="max-w-2xl mx-auto px-4 md:px-6 py-10 space-y-10">
                  {messages.map((message, idx) => {
                    const codes = message.role === "assistant" ? extractCourseCodes(message.content) : []
                    const suggestions = message.role === "assistant" && !isLoading
                      ? getSuggestions(message, (message.courseCards || []).map(c => c.courseCode))
                      : []

                    // The question this answer responded to (preceding user message)
                    const precedingQuestion = messages[idx - 1]?.role === "user" ? messages[idx - 1].content : ""
                    const feedbackHandler =
                      message.role === "assistant" && message.content !== "" && !isLoading
                        ? (rating: "up" | "down") => sendFeedback(precedingQuestion, message.content, rating)
                        : undefined

                    return (
                      <div key={message.id}>
                        <ChatMessage role={message.role} content={message.content} sources={message.sources} onFeedback={feedbackHandler}>
                          {message.courseCards && message.courseCards.length > 0 && (
                            <div className="flex flex-col gap-4 mt-3">
                              {message.courseCards.map((card, idx) => (
                                <div key={idx}>
                                  <CourseCard {...card} />
                                  {card.prerequisites.length > 0 && (
                                    <button
                                      onClick={() =>
                                        setExpandedPrereq(
                                          expandedPrereq === card.courseCode ? null : card.courseCode
                                        )
                                      }
                                      className="mt-2 text-xs text-primary hover:underline"
                                    >
                                      {expandedPrereq === card.courseCode
                                        ? "Hide prerequisite tree"
                                        : "View full prerequisite tree →"}
                                    </button>
                                  )}
                                  {expandedPrereq === card.courseCode && (
                                    <PrereqVisualizer courseCode={card.courseCode} />
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </ChatMessage>

                        {suggestions.length > 0 && (
                          <div className="flex flex-wrap gap-2 mt-2 ml-11">
                            {suggestions.map((s) => (
                              <button
                                key={s.label}
                                onClick={() => {
                                  if (s.query) handleSuggestionClick(s.query)
                                  else if (s.view) setCurrentView(s.view)
                                }}
                                className="px-3 py-1.5 rounded-full text-xs border border-primary/30 text-primary hover:bg-primary/10 transition-colors"
                              >
                                {s.label}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })}

                  <div ref={messagesEndRef} />
                </div>
              )}
            </main>

            {messages.length > 0 && (
              <ChatInput
                value={input}
                onChange={setInput}
                onSubmit={handleSubmit}
                disabled={isLoading}
              />
            )}
          </>
        )}

        {/* Mobile bottom nav */}
        <nav className="md:hidden flex items-center justify-around border-t border-border/40 bg-card safe-area-pb px-2">
          {[
            { view: "programs"  as View, label: "Programs",  Icon: BookOpenIcon       },
            { view: "gpa"       as View, label: "GPA",       Icon: CalculatorIcon     },
            { view: "chat"      as View, label: "Chat",      Icon: MessageSquareIcon  },
            { view: "compare"   as View, label: "Compare",   Icon: BarChart2Icon      },
            { view: "deadlines" as View, label: "Dates",     Icon: CalendarDaysIcon   },
          ].map(({ view, label, Icon }) => {
            const active = currentView === view
            return (
              <button
                key={view}
                onClick={() => setCurrentView(view)}
                className="flex-1 flex flex-col items-center pt-2 pb-3 gap-1 transition-colors"
              >
                <div className={cn(
                  "flex items-center justify-center rounded-2xl transition-all duration-200",
                  active
                    ? "bg-primary/10 px-4 py-1.5"
                    : "px-3 py-1.5"
                )}>
                  <Icon className={cn(
                    "transition-all duration-200",
                    active ? "size-5 text-primary" : "size-5 text-muted-foreground/50"
                  )} />
                </div>
                <span className={cn(
                  "text-[10px] font-medium transition-colors",
                  active ? "text-primary" : "text-muted-foreground/40"
                )}>{label}</span>
              </button>
            )
          })}
        </nav>
      </div>

      <FeedbackModal
        open={showFeedback}
        onClose={() => setShowFeedback(false)}
        lastQuery={lastQuery}
      />
    </div>
  )
}

