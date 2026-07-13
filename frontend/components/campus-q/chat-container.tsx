"use client"

import * as React from "react"
import Link from "next/link"
import { track } from "@vercel/analytics"
import { classifyIntent } from "@/lib/classify-intent"
import { useUser, useAuth } from "@clerk/nextjs"
import { cn } from "@/lib/utils"
import { MessageSquare as MessageSquareIcon, BookOpen as BookOpenIcon, BarChart2 as BarChart2Icon, CalendarDays as CalendarDaysIcon, PenLine } from "lucide-react"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { API_BASE_URL } from "@/lib/api"
import {
  fetchCloudChats,
  mergeChatPayloads,
  pushCloudChats,
  readLocalChatPayload,
  writeLocalChatPayload,
  LOCAL_SESSIONS_KEY,
  MAX_SYNCED_SESSIONS,
} from "@/lib/chat-sync"
import { fetchGuestQuota, guestHeaders, isGuestLimitError, type GuestQuota } from "@/lib/guest-quota"
import { Header } from "./header"
import { Sidebar, type View, type ChatSession } from "./sidebar"
import { ChatMessage } from "./chat-message"
import { ChatInput } from "./chat-input"
import { EmptyState } from "./empty-state"
import { FeedbackModal } from "./feedback-modal"
import { CourseCompare } from "./course-compare"
import { ProgramExplorer } from "./program-explorer"
import { DeadlineTracker } from "./deadline-tracker"
import { SignupNudge } from "./signup-nudge"
import { GuestLimitWall } from "./guest-limit-wall"
import { CoursePills } from "./chat/course-pills"
import { MobileSessionList } from "./chat/mobile-session-list"
import { extractCourseCodes, getSuggestions } from "./chat/suggestions"
import type { CourseCardData, Message } from "./chat/types"

const MAX_SESSIONS = MAX_SYNCED_SESSIONS
const SIGNUP_NUDGE_DISMISS_KEY = "campusq-signup-nudge-dismissed"

function ChatPrivacyNotice({ synced }: { synced: boolean }) {
  return (
    <p className="text-[10px] text-center text-muted-foreground/80 px-4 pt-2 leading-relaxed max-w-2xl mx-auto">
      {synced
        ? "Signed in — chat history syncs to your CampusQ account across devices. "
        : "Guest mode — past chats stay locked until you sign up. "}
      Delete chats in the sidebar or clear site data.{" "}
      <Link href="/privacy" className="underline hover:text-foreground">
        Privacy Policy
      </Link>
    </p>
  )
}

export function ChatContainer() {
  const { user, isSignedIn, isLoaded } = useUser()
  const { getToken } = useAuth()

  // Build the Authorization header from the current Clerk session token.
  // Returns {} when signed out so calls still work while backend auth is off.
  // Guests also send a stable X-Guest-Id for the daily free-question quota.
  const authHeader = async (): Promise<HeadersInit> => {
    const headers: Record<string, string> = { ...guestHeaders() as Record<string, string> }
    try {
      const token = await getToken()
      if (token) headers.Authorization = `Bearer ${token}`
    } catch {}
    return headers
  }
  const [messages, setMessages] = React.useState<Message[]>([])
  const [sessions, setSessions] = React.useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = React.useState<string>("")
  const [currentView, setCurrentView] = React.useState<View>("chat")
  const [input, setInput] = React.useState("")
  const [isLoading, setIsLoading] = React.useState(false)
  const [isDark, setIsDark] = React.useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false)
  const [showFeedback, setShowFeedback] = React.useState(false)
  const [showHistory, setShowHistory] = React.useState(false)
  const [lastQuery, setLastQuery] = React.useState("")
  const [expandedPrereq, setExpandedPrereq] = React.useState<string | null>(null)
  const [nudgeDismissed, setNudgeDismissed] = React.useState(true)
  const [gotFirstAnswer, setGotFirstAnswer] = React.useState(false)
  const [guestQuota, setGuestQuota] = React.useState<GuestQuota | null>(null)
  const [guestLimitReached, setGuestLimitReached] = React.useState(false)
  const messagesEndRef = React.useRef<HTMLDivElement>(null)
  const syncReadyRef = React.useRef(false)
  const syncTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null)
  const getTokenRef = React.useRef(getToken)
  getTokenRef.current = getToken

  const scheduleCloudPush = React.useCallback(() => {
    if (!isSignedIn) return
    if (syncTimerRef.current) clearTimeout(syncTimerRef.current)
    syncTimerRef.current = setTimeout(() => {
      const payload = readLocalChatPayload()
      pushCloudChats(() => getTokenRef.current(), payload).catch(() => {})
    }, 800)
  }, [isSignedIn])

  // Load local sessions; if signed in, merge with cloud and pull history across devices.
  React.useEffect(() => {
    try {
      const local = readLocalChatPayload()
      setSessions(local.sessions)
      setNudgeDismissed(localStorage.getItem(SIGNUP_NUDGE_DISMISS_KEY) === "1")
    } catch {}

    if (!isLoaded) return

    if (!isSignedIn) {
      syncReadyRef.current = true
      fetchGuestQuota().then((q) => {
        if (!q) return
        setGuestQuota(q)
        setGuestLimitReached(q.remaining <= 0)
      })
      return
    }

    setGuestLimitReached(false)
    setGuestQuota(null)

    let cancelled = false
    ;(async () => {
      try {
        const cloud = await fetchCloudChats(() => getTokenRef.current())
        if (cancelled) return
        const local = readLocalChatPayload()
        if (!cloud) {
          syncReadyRef.current = true
          return
        }
        const merged = mergeChatPayloads(local, cloud)
        writeLocalChatPayload(merged)
        setSessions(merged.sessions)
        await pushCloudChats(() => getTokenRef.current(), merged)
        try { track("chat_sync_hydrated", { sessions: merged.sessions.length }) } catch {}
      } catch {
        // Stay on local history if cloud sync is unavailable.
      } finally {
        if (!cancelled) syncReadyRef.current = true
      }
    })()

    return () => {
      cancelled = true
    }
  }, [isLoaded, isSignedIn])

  const dismissSignupNudge = React.useCallback(() => {
    setNudgeDismissed(true)
    try {
      localStorage.setItem(SIGNUP_NUDGE_DISMISS_KEY, "1")
      track("signup_nudge_dismiss")
    } catch {}
  }, [])

  const showSignupNudge =
    isLoaded &&
    !isSignedIn &&
    !nudgeDismissed &&
    !guestLimitReached &&
    gotFirstAnswer &&
    !isLoading &&
    messages.some((m) => m.role === "assistant" && m.content.trim().length > 0)

  const guestQuestionsLeft =
    !isSignedIn && guestQuota ? guestQuota.remaining : null

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
    localStorage.setItem(LOCAL_SESSIONS_KEY, JSON.stringify(updated))
    if (syncReadyRef.current) scheduleCloudPush()
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
    // Guests don't get recent-chat access — signup unlocks history.
    if (!isSignedIn) {
      setShowHistory(true)
      return
    }
    if (messages.length > 0) saveCurrentChat(messages, currentSessionId)
    const msgs = JSON.parse(localStorage.getItem(`campusq-msgs-${id}`) || "[]")
    setMessages(msgs)
    setCurrentSessionId(id)
    setCurrentView("chat")
  }

  const handleRenameSession = (id: string, newTitle: string) => {
    const trimmed = newTitle.trim()
    if (!trimmed) return
    persistSessions(sessions.map((s) => s.id === id ? { ...s, title: trimmed } : s))
  }

  const handleDeleteSession = (id: string) => {
    persistSessions(sessions.filter((s) => s.id !== id))
    localStorage.removeItem(`campusq-msgs-${id}`)
    if (syncReadyRef.current) scheduleCloudPush()
    if (currentSessionId === id) {
      setMessages([])
      setCurrentSessionId(Date.now().toString())
    }
  }

  const saveMessages = (msgs: Message[], sessionId: string) => {
    localStorage.setItem(`campusq-msgs-${sessionId}`, JSON.stringify(msgs))
    if (syncReadyRef.current) scheduleCloudPush()
  }

  const handleSubmit = async (overrideInput?: string) => {
    const queryText = (overrideInput ?? input).trim()
    if (!queryText || isLoading) return

    if (!isSignedIn && guestLimitReached) {
      try { track("guest_limit_blocked_submit") } catch {}
      return
    }

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

    // Track analytics — intent only, not raw query text
    try { track("chat_query", { intent: classifyIntent(queryText) }) } catch {}

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
    formData.append("history", JSON.stringify(messages.map((m) => {
      // When assistant replied with course cards but no text, synthesize content
      // so follow-up questions like "tell me about it" have context
      if (m.role === "assistant" && !m.content && m.courseCards?.length) {
        const summary = m.courseCards.map((c) =>
          `${c.courseCode} — ${c.courseName} (${c.credits} credits). Prerequisites: ${c.prerequisites.join(", ") || "None"}. ${c.description}`
        ).join("\n\n")
        return { role: m.role, content: `[Course details]\n${summary}` }
      }
      return { role: m.role, content: m.content }
    })))
    formData.append("session_id", sessionId)
    formData.append("user_id", user?.id ?? "anonymous")

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: "POST",
        body: formData,
        headers: await authHeader(),
      })

      if (!response.ok) {
        let detail: unknown = null
        try { detail = await response.json() } catch {}
        const limitDetail = (detail as { detail?: unknown } | null)?.detail ?? detail
        if (isGuestLimitError(response.status, limitDetail)) {
          const limit = typeof limitDetail === "object" && limitDetail && "limit" in limitDetail
            ? Number((limitDetail as { limit: number }).limit) || 10
            : 10
          setGuestQuota({ used: limit, limit, remaining: 0 })
          setGuestLimitReached(true)
          try { track("guest_limit_hit") } catch {}
          setMessages((prev) => prev.filter((m) => m.id !== assistantId && m.id !== userMessage.id))
          return
        }
        throw new Error(`Chat failed: ${response.status}`)
      }

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
            if (parsed.type === "quota") {
              const next: GuestQuota = {
                used: Number(parsed.used) || 0,
                limit: Number(parsed.limit) || 10,
                remaining: Number(parsed.remaining) || 0,
              }
              setGuestQuota(next)
              setGuestLimitReached(next.remaining <= 0)
            } else if (parsed.type === "token") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: m.content + parsed.content } : m
                )
              )
            } else if (parsed.type === "courses") {
              const codes = (parsed.data as CourseCardData[]).map((c) => c.courseCode)
              if (codes.length > 0) {
                try { track("course_lookup", { intent: "course_lookup", course_count: codes.length }) } catch {}
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
      // Soft signup push: ask after the student has already gotten value
      setGotFirstAnswer(true)
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
      fetch(`${API_BASE_URL}/api/feedback`, { method: "POST", body: fd }).catch(() => {})
      track("answer_feedback", { rating })
    } catch {}
  }

  const renderView = () => {
    if (currentView === "programs")  return <ProgramExplorer />
    if (currentView === "compare")   return <CourseCompare />
    if (currentView === "deadlines") return <DeadlineTracker onAsk={(q) => { setCurrentView("chat"); handleSubmit(q) }} />
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
          sessions={isSignedIn ? sessions : []}
          currentSessionId={currentSessionId}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
          onRenameSession={handleRenameSession}
          onOpenFeedback={() => setShowFeedback(true)}
          historyLocked={!isSignedIn}
        />
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <Header isDark={isDark} onToggleDark={() => setIsDark(!isDark)} onOpenHistory={() => setShowHistory(true)} onHome={handleNewChat} />

        {/* Non-chat views */}
        {!isChatView && (
          <main className="flex-1 overflow-y-auto scroll-touch">
            <div className="max-w-4xl mx-auto px-4 md:px-6 py-8">
              {renderView()}
            </div>
          </main>
        )}

        {/* Chat view */}
        {isChatView && (
          <>
            <main className="flex-1 overflow-y-auto scroll-touch">
              {messages.length === 0 ? (
                <div className="flex flex-col min-h-full">
                  <div className="flex-1 flex flex-col justify-center">
                    <EmptyState
                      onSuggestionClick={handleSuggestionClick}
                      onViewChange={(v) => setCurrentView(v as View)}
                    />
                  </div>
                  {/* Input lives here on home screen, centered with content */}
                  <div className="max-w-2xl mx-auto w-full px-4 pb-3 md:pb-6">
                    {guestLimitReached && !isSignedIn ? (
                      <GuestLimitWall limit={guestQuota?.limit ?? 10} />
                    ) : (
                      <ChatInput
                        value={input}
                        onChange={setInput}
                        onSubmit={handleSubmit}
                        disabled={isLoading || (!!isLoaded && !isSignedIn && guestLimitReached)}
                        isHome
                      />
                    )}
                    {guestQuestionsLeft !== null && !guestLimitReached && (
                      <p className="text-[10px] text-center text-muted-foreground/70 pt-2">
                        {guestQuestionsLeft} free {guestQuestionsLeft === 1 ? "question" : "questions"} left today
                      </p>
                    )}
                    <div className="hidden sm:block">
                      <ChatPrivacyNotice synced={!!isSignedIn} />
                    </div>
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
                            <CoursePills
                              cards={message.courseCards}
                              expandedPrereq={expandedPrereq}
                              onTogglePrereq={(code) => setExpandedPrereq(expandedPrereq === code ? null : code)}
                            />
                          )}
                        </ChatMessage>

                        {suggestions.length > 0 && (
                          <div className="flex flex-wrap gap-2 mt-2 ml-11">
                            {suggestions.map((s, i) => (
                              <button
                                key={s.label}
                                onClick={() => {
                                  if (s.query) handleSuggestionClick(s.query)
                                  else if (s.view) setCurrentView(s.view)
                                }}
                                style={{ animationDelay: `${i * 45}ms` }}
                                className="stagger-item px-3.5 py-2 md:py-1.5 rounded-full text-xs border border-primary/30 text-primary hover:bg-primary/10 hover:border-primary/50 transition-[background-color,border-color,transform] duration-150 ease-[var(--ease-out)] active:scale-[0.97]"
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
              <div className="max-w-2xl mx-auto w-full">
                {showSignupNudge && <SignupNudge onDismiss={dismissSignupNudge} />}
                {guestLimitReached && !isSignedIn ? (
                  <GuestLimitWall limit={guestQuota?.limit ?? 10} />
                ) : (
                  <ChatInput
                    value={input}
                    onChange={setInput}
                    onSubmit={handleSubmit}
                    disabled={isLoading || (!!isLoaded && !isSignedIn && guestLimitReached)}
                  />
                )}
                {guestQuestionsLeft !== null && !guestLimitReached && (
                  <p className="text-[10px] text-center text-muted-foreground/70 px-4 pt-1.5">
                    {guestQuestionsLeft} free {guestQuestionsLeft === 1 ? "question" : "questions"} left today
                  </p>
                )}
                <div className="hidden sm:block">
                  <ChatPrivacyNotice synced={!!isSignedIn} />
                </div>
              </div>
            )}
          </>
        )}

        {/* Mobile bottom nav — lives in the comfortable thumb zone */}
        <nav
          aria-label="Primary"
          className="md:hidden flex items-stretch justify-around border-t border-border/40 bg-card/95 backdrop-blur-sm safe-area-pb px-2"
        >
          {[
            { view: "programs"  as View, label: "Programs",  Icon: BookOpenIcon       },
            { view: "chat"      as View, label: "Chat",      Icon: MessageSquareIcon  },
            { view: "compare"   as View, label: "Compare",   Icon: BarChart2Icon      },
            { view: "deadlines" as View, label: "Dates",     Icon: CalendarDaysIcon   },
          ].map(({ view, label, Icon }) => {
            const active = currentView === view
            return (
              <button
                key={view}
                onClick={() => setCurrentView(view)}
                aria-label={label}
                aria-current={active ? "page" : undefined}
                className="flex-1 flex flex-col items-center justify-center pt-2 pb-2.5 gap-1 min-h-[56px] transition-transform duration-150 ease-[var(--ease-out)] active:scale-95"
              >
                <div className={cn(
                  "flex items-center justify-center rounded-2xl transition-[background-color,padding] duration-200 ease-[var(--ease-out)]",
                  active
                    ? "bg-primary/10 px-4 py-1.5"
                    : "px-3 py-1.5"
                )}>
                  <Icon className={cn(
                    "size-[22px] transition-colors duration-200",
                    active ? "text-primary" : "text-muted-foreground/50"
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

      {/* Mobile history drawer */}
      <Sheet open={showHistory} onOpenChange={setShowHistory}>
        <SheetContent side="left" className="w-72 p-0 flex flex-col">
          <SheetHeader className="px-4 pt-5 pb-3 border-b border-border/40">
            <SheetTitle className="text-sm">Chat History</SheetTitle>
          </SheetHeader>
          <div className="px-3 py-3">
            <button
              onClick={() => { handleNewChat(); setShowHistory(false) }}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium bg-foreground text-background hover:bg-foreground/90 transition-colors"
            >
              <PenLine className="size-3.5 shrink-0" />
              <span>New Chat</span>
            </button>
          </div>
          {!isSignedIn ? (
            <div className="px-4 py-2 flex flex-col gap-3">
              <p className="text-xs text-muted-foreground leading-relaxed">
                Sign up free to reopen past chats and keep them across devices.
              </p>
              <SignUpButton mode="redirect">
                <button
                  type="button"
                  className="w-full text-sm font-semibold px-3 py-2.5 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  Unlock chat history
                </button>
              </SignUpButton>
            </div>
          ) : (
            <MobileSessionList
              sessions={sessions}
              currentSessionId={currentSessionId}
              onSelect={(id) => { handleSelectSession(id); setShowHistory(false) }}
              onDelete={handleDeleteSession}
              onRename={handleRenameSession}
            />
          )}
        </SheetContent>
      </Sheet>

      <FeedbackModal
        open={showFeedback}
        onClose={() => setShowFeedback(false)}
        lastQuery={lastQuery}
      />
    </div>
  )
}
