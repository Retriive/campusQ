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
      className="inline-flex flex-wrap items-center gap-0.5 rounded-lg border border-line bg-canvas-raised/80 p-0.5"
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
            className={`land-press text-[12.5px] px-2.5 py-1.5 rounded-md transition-[background-color,color,transform] duration-200 ${
              active
                ? "bg-ink text-canvas font-semibold"
                : "text-ink-faint hover:text-ink"
            }`}
          >
            {s.shortName}
            {!s.live && (
              <span className={`ml-1 text-[9px] tracking-wide ${active ? "opacity-60" : "opacity-45"}`}>
                soon
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
