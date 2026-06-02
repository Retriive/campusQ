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
          alignItems: "center",
          justifyContent: "center",
          background: "#fafaf9",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", fontSize: 340, fontWeight: 800, letterSpacing: "-0.04em", color: "#18181b", lineHeight: 1 }}>
          Q<span style={{ color: "#dc2626" }}>.</span>
        </div>
      </div>
    ),
    { ...size }
  )
}
