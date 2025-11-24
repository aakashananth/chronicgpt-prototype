import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Health Metrics LLM Dashboard',
  description: 'Ultrahuman + Azure OpenAI prototype',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-black text-white">
          {/* Top Bar */}
          <header className="border-b border-gray-800 bg-gray-900/50">
            <div className="container mx-auto px-4 py-4">
              <h1 className="text-2xl font-bold">Health Metrics LLM Dashboard</h1>
              <p className="text-gray-400 text-sm mt-1">
                Ultrahuman + Azure OpenAI prototype
              </p>
            </div>
          </header>
          {children}
        </div>
      </body>
    </html>
  )
}
