import { SignIn } from "@clerk/nextjs"
import Link from "next/link"

export default function SignInPage() {
  return (
    <div style={{ minHeight: "100vh", background: "#fafaf9", display: "flex", flexDirection: "column", fontFamily: "inherit" }}>

      {/* Nav */}
      <nav style={{ height: 56, display: "flex", alignItems: "center", padding: "0 24px", borderBottom: "1px solid #e4e4e7", background: "#fafaf9" }}>
        <Link href="/" style={{ fontSize: 14, fontWeight: 700, letterSpacing: "-0.01em", color: "#18181b", textDecoration: "none" }}>
          Campus<span style={{ color: "#dc2626" }}>Q</span>
        </Link>
      </nav>

      {/* Center content */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "48px 16px" }}>

        {/* Heading above card */}
        <div style={{ marginBottom: 28, textAlign: "center" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 999, padding: "4px 12px", marginBottom: 16 }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#dc2626", display: "inline-block" }} />
            <span style={{ fontSize: 11, fontWeight: 600, color: "#dc2626", letterSpacing: "0.05em", textTransform: "uppercase" }}>
              Built for Carleton students
            </span>
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: "#18181b", letterSpacing: "-0.02em", margin: 0 }}>
            Welcome to CampusQ
          </h1>
          <p style={{ fontSize: 14, color: "#71717a", marginTop: 6 }}>
            Sign in to sync your chats across devices
          </p>
        </div>

        <SignIn
          signUpUrl="/sign-up"
          forceRedirectUrl="/chat"
          appearance={{
            variables: {
              colorPrimary: "#dc2626",
              colorBackground: "#ffffff",
              colorText: "#18181b",
              colorTextSecondary: "#71717a",
              colorInputBackground: "#ffffff",
              colorInputText: "#18181b",
              colorInputPlaceholder: "#a1a1aa",
              colorDanger: "#dc2626",
              borderRadius: "12px",
              fontFamily: "inherit",
              fontSize: "14px",
              spacingUnit: "16px",
            },
            layout: {
              socialButtonsVariant: "blockButton",
              socialButtonsPlacement: "top",
              showOptionalFields: false,
            },
            elements: {
              rootBox: {
                width: "100%",
                maxWidth: "400px",
              },
              card: {
                boxShadow: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
                border: "1px solid #e4e4e7",
                borderRadius: "16px",
                padding: "32px",
                background: "#ffffff",
              },
              headerTitle: { display: "none" },
              headerSubtitle: { display: "none" },
              logoBox: { display: "none" },
              socialButtonsBlockButton: {
                border: "1px solid #e4e4e7",
                borderRadius: "10px",
                background: "#ffffff",
                color: "#18181b",
                fontWeight: 500,
                fontSize: "14px",
                height: "42px",
                transition: "background 0.15s",
              },
              dividerLine: { background: "#e4e4e7" },
              dividerText: { color: "#a1a1aa", fontSize: "12px" },
              formFieldLabel: {
                fontSize: "12px",
                fontWeight: 500,
                color: "#3f3f46",
                marginBottom: "4px",
              },
              formFieldInput: {
                border: "1px solid #e4e4e7",
                borderRadius: "10px",
                height: "42px",
                padding: "0 12px",
                fontSize: "14px",
                color: "#18181b",
                background: "#ffffff",
                outline: "none",
                transition: "border-color 0.15s",
              },
              formButtonPrimary: {
                background: "#dc2626",
                borderRadius: "10px",
                height: "42px",
                fontWeight: 600,
                fontSize: "14px",
                border: "none",
                cursor: "pointer",
                transition: "background 0.15s",
              },
              footerActionLink: {
                color: "#dc2626",
                fontWeight: 500,
              },
              identityPreviewEditButton: { color: "#dc2626" },
              formFieldErrorText: { color: "#dc2626", fontSize: "12px" },
              footer: {
                background: "transparent",
                borderTop: "none",
                paddingTop: "16px",
              },
            },
          }}
        />

        <p style={{ marginTop: 20, fontSize: 11, color: "#a1a1aa", textAlign: "center", maxWidth: 320, lineHeight: 1.5 }}>
          CampusQ is independent and not affiliated with Carleton University.
          Always verify important decisions with your academic advisor.
        </p>
      </div>

    </div>
  )
}
