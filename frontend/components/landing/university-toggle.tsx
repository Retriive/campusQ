"use client"

import { SCHOOL_LIST, type SchoolId } from "@/lib/landing-schools"

export function UniversityToggle({
  activeId,
  onSelect,
}: {
  activeId: SchoolId
  onSelect: (id: SchoolId) => void
}) {
  return (
    <div
      role="tablist"
      aria-label="University"
      className="inline-flex flex-wrap items-center gap-1"
    >
      {SCHOOL_LIST.map((s) => {
        const active = activeId === s.id
        return (
          <button
            key={s.id}
            type="button"
            role="tab"
            aria-selected={active}
            data-school={s.id}
            onClick={() => onSelect(s.id)}
            className={`land-press text-[13px] px-3 py-1.5 rounded-md transition-[background-color,color,transform] duration-200 ${
              active
                ? "bg-ink text-canvas font-semibold"
                : "text-ink-faint hover:text-ink hover:bg-canvas-raised"
            }`}
          >
            {s.shortName}
            {!s.live && (
              <span className={`ml-1 text-[10px] tracking-wide ${active ? "opacity-60" : "opacity-45"}`}>
                soon
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
