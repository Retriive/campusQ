import { clerkMiddleware } from '@clerk/nextjs/server'

// Chat is public so students can try CampusQ without hitting a login wall.
// Clerk still runs so signed-in sessions (history sync, account menu) work.
export default clerkMiddleware()

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
}
