"use client"

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react"
import { SCHOOL_LIST, type SchoolId } from "@/lib/landing-schools"

export function UniversityToggle({
  activeId,
  onSelect,
}: {
  activeId: SchoolId
  onSelect: (id: SchoolId) => void
}) {
  const listRef = useRef<HTMLDivElement>(null)
  const btnRefs = useRef(new Map<SchoolId, HTMLButtonElement>())
  const [pill, setPill] = useState({ x: 0, y: 0, w: 0, h: 0, ready: false })

  const measure = useCallback(() => {
    const list = listRef.current
    const btn = btnRefs.current.get(activeId)
    if (!list || !btn) return
    const lr = list.getBoundingClientRect()
    const br = btn.getBoundingClientRect()
    // Track the full rect (x, y, w, h) so the pill lands on the active
    // button even when the toggle wraps onto multiple rows on narrow screens.
    setPill({
      x: br.left - lr.left,
      y: br.top - lr.top,
      w: br.width,
      h: br.height,
      ready: true,
    })
  }, [activeId])

  useLayoutEffect(() => {
    measure()
  }, [measure])

  useEffect(() => {
    window.addEventListener("resize", measure)
    return () => window.removeEventListener("resize", measure)
  }, [measure])

  return (
    <div
      ref={listRef}
      role="tablist"
      aria-label="University"
      className="relative inline-flex flex-wrap items-center gap-0.5 rounded-full border border-line bg-canvas p-1"
    >
      <span
        aria-hidden
        className="land-toggle-pill pointer-events-none absolute top-0 left-0 rounded-full bg-ink"
        style={{
          width: pill.w,
          height: pill.h,
          transform: `translate(${pill.x}px, ${pill.y}px)`,
          opacity: pill.ready ? 1 : 0,
        }}
      />
      {SCHOOL_LIST.map((s) => {
        const active = activeId === s.id
        return (
          <button
            key={s.id}
            type="button"
            role="tab"
            aria-selected={active}
            ref={(el) => {
              if (el) btnRefs.current.set(s.id, el)
              else btnRefs.current.delete(s.id)
            }}
            onClick={() => onSelect(s.id)}
            className={`relative z-[1] whitespace-nowrap land-press text-[12px] px-3 py-1.5 rounded-full transition-colors duration-200 ${
              active ? "text-canvas font-semibold" : "text-ink-faint hover:text-ink"
            }`}
          >
            {s.shortName}
            {!s.live && (
              <span className={`ml-1 text-[9px] tracking-wide ${active ? "opacity-55" : "opacity-40"}`}>
                soon
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
