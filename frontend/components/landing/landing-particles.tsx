"use client"

import { useEffect, useRef } from "react"

type Particle = {
  x: number
  y: number
  vx: number
  vy: number
  r: number
  a: number
}

/**
 * Decorative hero particle field — soft dots + faint links.
 * Marketing / first-visit only. Pauses on reduced-motion + hidden tabs.
 */
export function LandingParticles({ className = "" }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const parent = canvas.parentElement
    if (!parent) return

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)")
    if (reduce.matches) return

    const ctx = canvas.getContext("2d", { alpha: true })
    if (!ctx) return

    let raf = 0
    let running = true
    let w = 0
    let h = 0
    let dpr = 1
    let particles: Particle[] = []
    const mouse = { x: -9999, y: -9999, active: false }

    const readAccent = () => {
      const styles = getComputedStyle(parent.closest("[data-school]") ?? parent)
      // Primary token is usually oklch(...) — canvas can use it via CSS color when supported.
      return styles.getPropertyValue("--primary").trim() || "#0d9488"
    }

    let accent = readAccent()

    const countFor = (area: number) => {
      // Sparse enough to feel premium, dense enough to read as a field.
      const n = Math.round(area / 14000)
      return Math.max(28, Math.min(90, n))
    }

    const seed = () => {
      const n = countFor(w * h)
      particles = Array.from({ length: n }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.28,
        vy: (Math.random() - 0.5) * 0.28,
        r: 1.1 + Math.random() * 1.8,
        a: 0.25 + Math.random() * 0.45,
      }))
    }

    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2)
      w = parent.clientWidth
      h = parent.clientHeight
      canvas.width = Math.floor(w * dpr)
      canvas.height = Math.floor(h * dpr)
      canvas.style.width = `${w}px`
      canvas.style.height = `${h}px`
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      accent = readAccent()
      seed()
    }

    const onMove = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect()
      mouse.x = e.clientX - rect.left
      mouse.y = e.clientY - rect.top
      mouse.active = true
    }
    const onLeave = () => {
      mouse.active = false
    }

    const linkDist = () => Math.min(140, Math.max(90, w * 0.11))

    const frame = () => {
      if (!running) return
      ctx.clearRect(0, 0, w, h)
      accent = readAccent()
      const maxLink = linkDist()

      for (const p of particles) {
        // Soft mouse attraction — decorative spring-ish drift, not sticky.
        if (mouse.active) {
          const dx = mouse.x - p.x
          const dy = mouse.y - p.y
          const d2 = dx * dx + dy * dy
          if (d2 < 220 * 220 && d2 > 1) {
            const d = Math.sqrt(d2)
            const force = (1 - d / 220) * 0.035
            p.vx += (dx / d) * force
            p.vy += (dy / d) * force
          }
        }

        p.x += p.vx
        p.y += p.vy
        // Damping keeps velocity from accumulating.
        p.vx *= 0.992
        p.vy *= 0.992

        if (p.x < -20) p.x = w + 20
        if (p.x > w + 20) p.x = -20
        if (p.y < -20) p.y = h + 20
        if (p.y > h + 20) p.y = -20
      }

      // Links first (under dots)
      for (let i = 0; i < particles.length; i++) {
        const a = particles[i]
        for (let j = i + 1; j < particles.length; j++) {
          const b = particles[j]
          const dx = a.x - b.x
          const dy = a.y - b.y
          const dist = Math.hypot(dx, dy)
          if (dist > maxLink) continue
          const t = 1 - dist / maxLink
          ctx.beginPath()
          ctx.strokeStyle = accent
          ctx.globalAlpha = t * t * 0.22
          ctx.lineWidth = 1
          ctx.moveTo(a.x, a.y)
          ctx.lineTo(b.x, b.y)
          ctx.stroke()
        }
      }

      for (const p of particles) {
        ctx.beginPath()
        ctx.fillStyle = accent
        ctx.globalAlpha = p.a
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.globalAlpha = 1

      raf = requestAnimationFrame(frame)
    }

    const onVisibility = () => {
      if (document.hidden) {
        running = false
        cancelAnimationFrame(raf)
      } else if (!reduce.matches) {
        running = true
        raf = requestAnimationFrame(frame)
      }
    }

    const onReduce = () => {
      if (reduce.matches) {
        running = false
        cancelAnimationFrame(raf)
        ctx.clearRect(0, 0, w, h)
      } else {
        running = true
        raf = requestAnimationFrame(frame)
      }
    }

    resize()
    raf = requestAnimationFrame(frame)

    const ro = new ResizeObserver(resize)
    ro.observe(parent)
    window.addEventListener("pointermove", onMove, { passive: true })
    canvas.addEventListener("pointerleave", onLeave)
    parent.addEventListener("pointerleave", onLeave)
    document.addEventListener("visibilitychange", onVisibility)
    reduce.addEventListener("change", onReduce)

    // Re-seed when school accent swaps (data-school attribute changes).
    const mo = new MutationObserver(() => {
      accent = readAccent()
    })
    const schoolRoot = parent.closest("[data-school]")
    if (schoolRoot) {
      mo.observe(schoolRoot, { attributes: true, attributeFilter: ["data-school"] })
    }

    return () => {
      running = false
      cancelAnimationFrame(raf)
      ro.disconnect()
      mo.disconnect()
      window.removeEventListener("pointermove", onMove)
      canvas.removeEventListener("pointerleave", onLeave)
      parent.removeEventListener("pointerleave", onLeave)
      document.removeEventListener("visibilitychange", onVisibility)
      reduce.removeEventListener("change", onReduce)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className={`pointer-events-none absolute inset-0 ${className}`}
    />
  )
}
