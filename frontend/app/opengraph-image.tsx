import { ImageResponse } from "next/og"

export const alt = "CampusQ"
export const size = { width: 1200, height: 630 }
export const contentType = "image/png"

export default function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "#fafaf9",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", fontSize: 180, fontWeight: 800, letterSpacing: "-0.04em", color: "#18181b", lineHeight: 1 }}>
          Campus<span style={{ color: "#dc2626" }}>Q</span>
        </div>
        <div style={{ fontSize: 34, color: "#71717a", marginTop: "24px" }}>
          AI academic assistant for Carleton students
        </div>
      </div>
    ),
    { ...size }
  )
}
