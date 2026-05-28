"use client"

import { useState, useRef, useEffect } from "react"
import { Sidebar } from "@/components/sidebar"
import { EmptyState } from "@/components/empty-state"
import { ChatMessage, Message } from "@/components/chat-message"
import { ChatInput } from "@/components/chat-input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { FileText, X } from "lucide-react"

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [files, setFiles] = useState<any[]>([]) 
  const [attachment, setAttachment] = useState<File | null>(null) // Holds the pending file
  const scrollRef = useRef<HTMLDivElement>(null)

  const fetchDocuments = async () => {
    try {
      const response = await fetch("https://ai-knowledge-backend-9vf6.onrender.com/api/documents")
      const data = await response.json()
      setFiles(data.documents)
    } catch (error) {
      console.error("Failed to fetch documents:", error)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  const handleNewChat = () => {
    setMessages([])
    setAttachment(null)
  }

  const handleSendMessage = async (content: string) => {
    // Add user message to UI
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: attachment ? `[Attached File: ${attachment.name}]\n\n${content}` : content,
    }
    setMessages((prev) => [...prev, userMessage])

    // Build form data for file + text
    const formData = new FormData()
    formData.append("question", content)
    
    if (attachment) {
      formData.append("file", attachment)
    }

    // 🔴 NEW: Package up the chat history and send it to Python
    const chatHistory = messages.map((msg) => ({
      role: msg.role,
      content: msg.content
    }))
    formData.append("history", JSON.stringify(chatHistory))

    // Clear attachment so UI resets immediately
    setAttachment(null)

    try {
      const response = await fetch("https://ai-knowledge-backend-9vf6.onrender.com/api/chat", {
        method: "POST",
        body: formData, // No Content-Type header needed for FormData!
      })

      if (!response.ok) throw new Error("Network response was not ok")

      const data = await response.json()

      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: data.answer,
        sources: data.sources?.map((s: any, index: number) => ({
          id: `source-${Date.now()}-${index}`,
          fileName: s.doc,
          sectionTitle: s.section,
          snippet: s.snippet,
        })) || [],
      }
      
      setMessages((prev) => [...prev, aiMessage])

    } catch (error) {
      console.error("Error talking to backend:", error)
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: "I couldn't reach the backend server.",
      }
      setMessages((prev) => [...prev, errorMessage])
    }
  }

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar 
        files={files} 
        onNewChat={handleNewChat} 
        onAttachFile={(file) => setAttachment(file)} // Receive file from sidebar
      />

      <main className="flex-1 md:ml-[280px] flex flex-col">
        {messages.length === 0 ? (
          <EmptyState onSuggestionClick={(s) => handleSendMessage(s)} />
        ) : (
          <ScrollArea className="flex-1">
            <div className="mx-auto max-w-3xl px-4 py-8 space-y-6">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              <div ref={scrollRef} />
            </div>
          </ScrollArea>
        )}

        {/* Chat Input Area */}
        <div className="mx-auto w-full max-w-3xl px-4 pb-4">
          {/* Attachment Preview Badge */}
          {attachment && (
            <div className="mb-2 flex items-center gap-2 rounded-lg border bg-muted/50 p-2 w-fit">
              <FileText className="h-4 w-4 text-blue-500" />
              <span className="text-xs font-medium text-muted-foreground">{attachment.name}</span>
              <button 
                onClick={() => setAttachment(null)}
                className="ml-2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}
          <ChatInput onSend={handleSendMessage} />
        </div>
      </main>
    </div>
  )
}