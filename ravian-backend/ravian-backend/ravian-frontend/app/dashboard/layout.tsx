"use client"

import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Sidebar from '../../components/Sidebar'
import Header from '../../components/Header'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-[#0B0B12] text-[#F1F0FF]">
        {/* Ambient background glows */}
        <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-[10%] -left-[10%] w-[50vw] h-[50vw] bg-[radial-gradient(circle,rgba(168,85,247,0.12)_0%,rgba(11,11,18,0)_70%)] blur-[60px]" />
          <div className="absolute top-[20%] left-[30%] w-[40vw] h-[40vw] bg-[radial-gradient(circle,rgba(217,70,239,0.08)_0%,rgba(11,11,18,0)_70%)] blur-[80px]" />
        </div>

        {/* Mobile overlay */}
        {mobileMenuOpen && (
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 md:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}

        {/* Sidebar — fixed */}
        <div className={`
          fixed inset-y-0 left-0 z-50 transform transition-all duration-300 ease-out
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
          md:translate-x-0
        `}>
          <Sidebar
            isCollapsed={sidebarCollapsed}
            onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          />
        </div>

        {/* Main area — offset by sidebar width */}
        <div className={`
          min-h-screen flex flex-col transition-all duration-300 ease-out relative z-10
          ${sidebarCollapsed ? 'md:ml-[72px]' : 'md:ml-[260px]'}
        `}>
          <Header onMenuToggle={() => setMobileMenuOpen(!mobileMenuOpen)} />

          <main className="flex-1 overflow-y-auto">
            <div className="p-6 lg:p-8">
              {children}
            </div>
          </main>
        </div>
      </div>
    </QueryClientProvider>
  )
}