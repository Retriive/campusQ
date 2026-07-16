/**
 * Returns the url only if it's a safe http(s) link, otherwise undefined.
 *
 * Assistant/model output and citation metadata are untrusted, so
 * `javascript:` / `data:` (and any other scheme) must never become a clickable
 * anchor. Relative or malformed values throw in the URL parser and are treated
 * as unsafe.
 */
export function safeHref(url: unknown): string | undefined {
  if (typeof url !== "string") return undefined
  try {
    const proto = new URL(url).protocol
    return proto === "http:" || proto === "https:" ? url : undefined
  } catch {
    return undefined
  }
}
