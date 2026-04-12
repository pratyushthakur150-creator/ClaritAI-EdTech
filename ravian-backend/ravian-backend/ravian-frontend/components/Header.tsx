'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  Search,
  Bell,
  Settings,
  User,
  LogOut,
  Menu,
  Grid3X3,
  Mail
} from 'lucide-react'
import SearchPalette from './SearchPalette'

interface HeaderProps {
  onMenuToggle: () => void
}

export default function Header({ onMenuToggle }: HeaderProps) {
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showNotifications, setShowNotifications] = useState(false)
  const [showSearch, setShowSearch] = useState(false)
  const router = useRouter()
  const userMenuRef = useRef<HTMLDivElement>(null)
  const notifRef = useRef<HTMLDivElement>(null)

  const handleLogout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      router.push('/login')
    }
  }

  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
      setShowUserMenu(false)
    }
    if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
      setShowNotifications(false)
    }
  }, [])

  const handleEscape = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      setShowUserMenu(false)
      setShowNotifications(false)
    }
  }, [])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setShowSearch(prev => !prev)
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [handleClickOutside, handleEscape])

  return (
    <>
      <header className="sticky top-0 z-30 h-16 border-b border-white/5 bg-[#0F0E17]/60 backdrop-blur-md">
        <div className="flex items-center justify-between h-full px-6 lg:px-8">
          {/* Left — mobile menu + breadcrumb */}
          <div className="flex items-center gap-3">
            <button
              onClick={onMenuToggle}
              className="md:hidden p-2 rounded-xl hover:bg-white/5 transition-colors"
              aria-label="Toggle menu"
            >
              <Menu className="w-5 h-5 text-gray-400" />
            </button>

            <div className="hidden md:flex items-center gap-2 text-sm text-gray-500">
              <span className="text-[16px]">🏠</span>
              <span>/</span>
              <span>Overview</span>
              <span>/</span>
              <span className="text-white font-medium">Dashboard</span>
            </div>
          </div>

          {/* Right — search + actions */}
          <div className="flex items-center gap-4">
            {/* Search */}
            <div className="hidden md:block">
              <button
                onClick={() => setShowSearch(true)}
                className="relative flex items-center w-64 bg-[#13121E] border border-white/10 rounded-lg px-3 py-2 text-left hover:border-[#A855F7]/50 transition-all group"
                aria-label="Search"
              >
                <Search className="w-4 h-4 text-gray-500 mr-3 shrink-0 group-focus-within:text-[#A855F7] transition-colors" />
                <span className="text-sm text-gray-600">Search data scheduled...</span>
              </button>
            </div>

            <div className="flex items-center gap-2 text-gray-400">
              {/* Mail */}
              <div className="relative" ref={notifRef}>
                <button
                  onClick={() => { setShowNotifications(!showNotifications); setShowUserMenu(false); }}
                  className="hover:text-white transition-colors relative w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/5"
                  aria-label="Notifications"
                >
                  <Mail className="w-[18px] h-[18px]" />
                  <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#D946EF] rounded-full border-2 border-[#0F0E17]" />
                </button>

                {showNotifications && (
                  <div className="absolute right-0 mt-2 w-80 bg-[#13121E] rounded-2xl shadow-xl border border-[#2A2840] z-50 overflow-hidden">
                    <div className="px-5 py-4 border-b border-white/5">
                      <h3 className="text-sm font-semibold text-white">Notifications</h3>
                    </div>
                    <div className="p-4 space-y-3 max-h-80 overflow-y-auto">
                      <div className="flex items-start gap-3 p-2 rounded-xl hover:bg-white/5 transition-colors">
                        <div className="w-2 h-2 bg-[#A855F7] rounded-full mt-2 shrink-0" />
                        <div>
                          <p className="text-sm text-white font-medium">New student enrolled</p>
                          <p className="text-xs text-gray-500 mt-0.5">2 minutes ago</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3 p-2 rounded-xl hover:bg-white/5 transition-colors">
                        <div className="w-2 h-2 bg-green-500 rounded-full mt-2 shrink-0" />
                        <div>
                          <p className="text-sm text-white font-medium">Call completed successfully</p>
                          <p className="text-xs text-gray-500 mt-0.5">1 hour ago</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Grid */}
              <button className="hover:text-white transition-colors w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/5">
                <Grid3X3 className="w-[18px] h-[18px]" />
              </button>

              {/* User avatar */}
              <div className="relative" ref={userMenuRef}>
                <button
                  onClick={() => { setShowUserMenu(!showUserMenu); setShowNotifications(false); }}
                  className="w-9 h-9 rounded-full bg-gray-600 overflow-hidden border border-white/10 ring-2 ring-transparent hover:ring-[#A855F7]/50 transition-all"
                  aria-label="User menu"
                >
                  <div className="w-full h-full bg-gradient-to-br from-[#A855F7] to-[#D946EF] flex items-center justify-center">
                    <span className="text-white text-xs font-bold">PS</span>
                  </div>
                </button>

                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-52 bg-[#13121E] rounded-2xl shadow-xl border border-[#2A2840] z-50 overflow-hidden">
                    <div className="p-1.5">
                      <button onClick={() => { setShowUserMenu(false); router.push('/dashboard/profile'); }} className="flex items-center gap-2.5 w-full px-3 py-2.5 text-sm text-gray-300 hover:bg-white/5 rounded-xl transition-colors">
                        <User className="w-4 h-4 text-gray-500" />
                        <span className="font-medium">Profile</span>
                      </button>
                      <button onClick={() => { setShowUserMenu(false); router.push('/dashboard/settings'); }} className="flex items-center gap-2.5 w-full px-3 py-2.5 text-sm text-gray-300 hover:bg-white/5 rounded-xl transition-colors">
                        <Settings className="w-4 h-4 text-gray-500" />
                        <span className="font-medium">Settings</span>
                      </button>
                      <hr className="my-1 border-white/5" />
                      <button onClick={handleLogout} className="flex items-center gap-2.5 w-full px-3 py-2.5 text-sm text-red-400 hover:bg-red-500/10 rounded-xl transition-colors">
                        <LogOut className="w-4 h-4" />
                        <span className="font-medium">Sign out</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      <SearchPalette open={showSearch} onClose={() => setShowSearch(false)} />
    </>
  )
}