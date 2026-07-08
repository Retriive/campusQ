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
    <div className="inline-flex flex-wrap items-center gap-1 p-1 rounded-full border border-night-line bg-night-raised">
      {SCHOOL_LIST.map((s) => (
        <button
          key={s.id}
          onClick={() => onSelect(s.id)}
          className={`text-xs px-3.5 py-1.5 rounded-full transition-colors duration-200 active:scale-[0.97] ${
            activeId === s.id
              ? "bg-white text-black font-[550]"
              : "text-zinc-400 hover:text-white"
          }`}
        >
          {s.shortName}
          {!s.live && (
            <span className={`ml-1.5 text-[9px] uppercase tracking-[0.72px] ${activeId === s.id ? "opacity-60" : "opacity-50"}`}>
              soon
            </span>
          )}
        </button>
      ))}
    </div>
  )
}
