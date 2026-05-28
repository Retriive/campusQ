import { CampusProvider } from "@/components/campus-q/campus-context"
import { ChatContainer } from "@/components/campus-q/chat-container"

export const metadata = {
  title: "CampusQ — Chat",
}

export default function ChatPage() {
  return (
    <CampusProvider>
      <ChatContainer />
    </CampusProvider>
  )
}
