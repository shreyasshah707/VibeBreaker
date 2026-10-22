import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'VibeBreaker - Anti-Vibe-Coding Learning Tool',
  description: 'Reconstruct code step by step. Learn by doing, not by copying.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-vibe-bg text-vibe-text antialiased">
        {children}
      </body>
    </html>
  )
}