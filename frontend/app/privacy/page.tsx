import Link from "next/link"
import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Privacy Policy — CampusQ",
  description: "How CampusQ collects, uses, and protects your information.",
}

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between gap-4">
          <Link href="/" className="text-sm font-medium hover:underline">
            ← CampusQ
          </Link>
          <Link href="/chat" className="text-sm text-muted-foreground hover:text-foreground">
            Open app
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12 prose prose-neutral dark:prose-invert prose-sm">
        <h1>Privacy Policy</h1>
        <p className="text-muted-foreground">Last updated: July 2026</p>

        <p>
          CampusQ is operated by Retriive. This policy explains what we collect, how we use it,
          and your choices. CampusQ is an independent tool and is not affiliated with any university.
        </p>

        <h2>What we collect</h2>
        <ul>
          <li><strong>Account info</strong> — If you sign in, authentication is handled by Clerk (email, profile basics).</li>
          <li><strong>Chat questions</strong> — Questions you submit are processed to generate answers. Server logs store a truncated copy (up to 300 characters) with a pseudonymized user identifier — never your raw Clerk ID.</li>
          <li><strong>Chat history on your device</strong> — Conversations are stored in your browser&apos;s <code>localStorage</code> on the device you use.</li>
          <li><strong>Synced chat history (signed-in only)</strong> — If you create an account, we store your recent chat sessions on our servers so you can open them on another device. Guests are not synced.</li>
          <li><strong>Waitlist</strong> — Email address and school interest when you join a waitlist (with your consent).</li>
          <li><strong>Usage analytics</strong> — Anonymous page views and event categories (e.g. question intent type, not full question text).</li>
          <li><strong>Feedback</strong> — Thumbs up/down and optional problem reports you submit.</li>
        </ul>

        <h2>How we use data</h2>
        <ul>
          <li>Provide and improve the academic assistant</li>
          <li>Monitor answer quality and identify data gaps for university staff (aggregated, anonymized reports)</li>
          <li>Send waitlist updates about your selected school (only if you opted in)</li>
          <li>Protect the service (rate limiting, abuse prevention)</li>
        </ul>

        <h2>Data retention</h2>
        <p>
          Server-side logs are automatically deleted after <strong>90 days</strong>. Browser chat history
          remains until you clear it or delete individual chats in the app. Synced account chat history
          remains until you delete chats in the app or request account deletion.
        </p>

        <h2>Who can access data</h2>
        <ul>
          <li><strong>Retriive team</strong> — Operational access to logs and internal dashboards (admin-protected).</li>
          <li><strong>University partners</strong> — Aggregated advisor reports only; no individual student identities.</li>
          <li><strong>Subprocessors</strong> — See list below. They process data on our behalf under their own terms.</li>
        </ul>

        <h2>Subprocessors</h2>
        <ul>
          <li>OpenAI — language model inference</li>
          <li>Pinecone — vector search over public university data</li>
          <li>Cohere — search reranking (optional)</li>
          <li>Clerk — authentication</li>
          <li>Vercel — frontend hosting and analytics</li>
          <li>Render — backend API hosting</li>
          <li>Resend — transactional email</li>
          <li>Sentry — error monitoring (when enabled)</li>
        </ul>

        <h2>Your choices</h2>
        <ul>
          <li><strong>Clear chat history</strong> — Delete chats in the sidebar or clear site data in your browser. If you are signed in, deleting a chat also removes it from synced account storage.</li>
          <li><strong>Deletion requests</strong> — Email <a href="mailto:hello@retriive.com">hello@retriive.com</a> with the email used to sign in or join the waitlist. We will delete matching server-side records within 30 days.</li>
          <li><strong>Waitlist</strong> — Reply to any waitlist email to unsubscribe.</li>
        </ul>

        <h2>Contact</h2>
        <p>
          Questions about this policy: <a href="mailto:hello@retriive.com">hello@retriive.com</a>
        </p>
      </main>
    </div>
  )
}
