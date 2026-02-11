import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'

export const metadata: Metadata = {
  title: 'Competitive Intelligence Maximizer - Obliterate Ahrefs',
  description: 'Extract EVERY strategic insight hiding in your Ahrefs data. 20+ AI-powered intelligence modes.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased bg-background text-secondary">
        {/* Header */}
        <header className="border-b-4 border-secondary bg-background sticky top-0 z-50">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <Link href="/" className="text-brutal-lg hover:text-primary transition-colors">
                C.I.M.
              </Link>

              <nav className="flex gap-6">
                <NavLink href="/upload">UPLOAD</NavLink>
                <NavLink href="/modes">MODES</NavLink>
                <NavLink href="/execute">EXECUTE</NavLink>
              </nav>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-6 py-12">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t-4 border-secondary bg-secondary text-white mt-24">
          <div className="container mx-auto px-6 py-12">
            <div className="grid md:grid-cols-4 gap-8">
              <div>
                <h3 className="text-brutal-md mb-4">ABOUT</h3>
                <p className="text-sm text-white/80">
                  We extract strategic intelligence from Ahrefs data.
                  They sell data. We sell insights.
                </p>
              </div>

              <div>
                <h3 className="text-brutal-md mb-4">FEATURES</h3>
                <ul className="space-y-2 text-sm text-white/80">
                  <li>→ 20+ Intelligence Modes</li>
                  <li>→ AI-Powered Insights</li>
                  <li>→ No API Required</li>
                  <li>→ Upload & Analyze</li>
                </ul>
              </div>

              <div>
                <h3 className="text-brutal-md mb-4">MODES</h3>
                <ul className="space-y-2 text-sm text-white/80">
                  <li>→ Cluster Dominance</li>
                  <li>→ SERP Warfare</li>
                  <li>→ Backlink Intelligence</li>
                  <li>→ Traffic Potential</li>
                </ul>
              </div>

              <div>
                <h3 className="text-brutal-md mb-4">STATUS</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-accent rounded-full animate-pulse"></div>
                    <span className="text-white/80">20/55 Modes Built</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-accent rounded-full animate-pulse"></div>
                    <span className="text-white/80">Alpha Ready</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-12 pt-8 border-t-2 border-white/20 text-center text-sm text-white/60">
              <p>
                Built to <span className="text-primary">OBLITERATE</span> the Ahrefs business model.
              </p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}

function NavLink({
  href,
  children,
}: {
  href: string
  children: React.ReactNode
}) {
  return (
    <Link
      href={href}
      className="font-bold hover:text-primary transition-colors"
    >
      {children}
    </Link>
  )
}
