'use client'

import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import {
  Search,
  LayoutDashboard,
  Target,
  Users,
  BookOpen,
  Mic,
  MessageSquare,
  Calendar,
  Phone,
  GraduationCap,
  Book,
  Filter,
  BarChart3,
  Settings,
  ArrowRight,
  Command,
  X,
} from 'lucide-react'

/* ── Searchable items ────────────────────────────────────────────── */

interface SearchItem {
  id: string
  name: string
  description: string
  href: string
  section: string
  icon: React.ElementType
  keywords: string[]  // extra terms for fuzzy matching
}

const SEARCH_ITEMS: SearchItem[] = [
  // Core
  { id: 'overview', name: 'Overview', description: 'Dashboard overview & KPIs', href: '/dashboard', section: 'Core', icon: LayoutDashboard, keywords: ['home', 'dashboard', 'metrics', 'kpi'] },
  { id: 'crm', name: 'CRM', description: 'Manage leads & pipeline', href: '/dashboard/crm', section: 'Core', icon: Target, keywords: ['leads', 'pipeline', 'contacts', 'sales'] },
  { id: 'students', name: 'Students', description: 'Student records & profiles', href: '/dashboard/students', section: 'Core', icon: Users, keywords: ['learners', 'profiles', 'records'] },
  // Intelligence
  { id: 'ta', name: 'Teaching Assistant', description: 'AI-powered doubt solving', href: '/dashboard/teaching-assistant', section: 'Intelligence', icon: BookOpen, keywords: ['ai', 'rag', 'doubt', 'voice', 'whisper'] },
  { id: 'voice', name: 'CRM Voice Agent', description: 'Outbound AI voice calls', href: '/dashboard/assistant', section: 'Intelligence', icon: Mic, keywords: ['call', 'vapi', 'outbound', 'agent'] },
  { id: 'chatbot', name: 'Chatbot', description: 'Website chatbot & lead capture', href: '/dashboard/chatbot', section: 'Intelligence', icon: MessageSquare, keywords: ['chat', 'widget', 'bot', 'lead capture'] },
  // Management
  { id: 'demos', name: 'Demos', description: 'Schedule & track demo sessions', href: '/dashboard/demos', section: 'Management', icon: Calendar, keywords: ['schedule', 'session', 'meeting', 'demo'] },
  { id: 'calls', name: 'Calls', description: 'Call logs & recordings', href: '/dashboard/calls', section: 'Management', icon: Phone, keywords: ['call log', 'recording', 'history'] },
  { id: 'enrollments', name: 'Enrollments', description: 'Student enrollment records', href: '/dashboard/enrollments', section: 'Management', icon: GraduationCap, keywords: ['enroll', 'admission', 'registration'] },
  { id: 'courses', name: 'Courses', description: 'Course catalog & content', href: '/dashboard/courses', section: 'Management', icon: Book, keywords: ['course', 'program', 'curriculum', 'content'] },
  // Analytics & Config
  { id: 'funnel', name: 'Funnel', description: 'Conversion funnel analytics', href: '/dashboard/funnel', section: 'Analytics & Config', icon: Filter, keywords: ['conversion', 'analytics', 'pipeline', 'funnel'] },
  { id: 'insights', name: 'Insights', description: 'Performance reports & trends', href: '/dashboard/insights', section: 'Analytics & Config', icon: BarChart3, keywords: ['report', 'analytics', 'trends', 'performance'] },
  { id: 'settings', name: 'Settings', description: 'API keys & chatbot configuration', href: '/dashboard/settings', section: 'Analytics & Config', icon: Settings, keywords: ['config', 'api key', 'embed', 'tenant'] },
]

/* ── Fuzzy match helper ──────────────────────────────────────────── */

function matchesQuery(item: SearchItem, query: string): boolean {
  const q = query.toLowerCase()
  if (item.name.toLowerCase().includes(q)) return true
  if (item.description.toLowerCase().includes(q)) return true
  if (item.section.toLowerCase().includes(q)) return true
  return item.keywords.some(k => k.includes(q))
}

/* ── Component ───────────────────────────────────────────────────── */

interface SearchPaletteProps {
  open: boolean
  onClose: () => void
}

export default function SearchPalette({ open, onClose }: SearchPaletteProps) {
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const router = useRouter()

  // Filtered results
  const results = useMemo(() => {
    if (!query.trim()) return SEARCH_ITEMS
    return SEARCH_ITEMS.filter(item => matchesQuery(item, query.trim()))
  }, [query])

  // Reset state when opening
  useEffect(() => {
    if (open) {
      setQuery('')
      setActiveIndex(0)
      requestAnimationFrame(() => inputRef.current?.focus())
    }
  }, [open])

  // Keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex(i => Math.min(i + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex(i => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && results[activeIndex]) {
      e.preventDefault()
      navigate(results[activeIndex].href)
    } else if (e.key === 'Escape') {
      e.preventDefault()
      onClose()
    }
  }, [results, activeIndex, onClose])

  // Scroll active item into view
  useEffect(() => {
    const container = listRef.current
    if (!container) return
    const active = container.querySelector(`[data-index="${activeIndex}"]`) as HTMLElement
    if (active) active.scrollIntoView({ block: 'nearest' })
  }, [activeIndex])

  // Reset active index when results change
  useEffect(() => { setActiveIndex(0) }, [results])

  const navigate = (href: string) => {
    onClose()
    router.push(href)
  }

  // Global Ctrl+K / Cmd+K + Escape shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        if (open) onClose()
      }
      if (e.key === 'Escape' && open) {
        e.preventDefault()
        onClose()
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  // Group results by section
  const grouped = results.reduce<Record<string, SearchItem[]>>((acc, item) => {
    if (!acc[item.section]) acc[item.section] = []
    acc[item.section].push(item)
    return acc
  }, {})

  // Flat index tracker for keyboard nav
  let flatIdx = 0

  return (
    <>
      {/* Backdrop */}
      <div
        style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(8px)',
          zIndex: 100, animation: 'fadeIn 0.15s ease',
        }}
        onClick={onClose}
      />

      {/* Palette */}
      <div style={{ position: 'fixed', inset: 0, zIndex: 101, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', paddingTop: '15vh' }}>
        <div
          style={{
            width: '100%', maxWidth: 520, maxHeight: '70vh', overflow: 'hidden',
            background: '#13121E', border: '1px solid #2A2840', borderRadius: 16,
            boxShadow: '0 25px 60px rgba(0,0,0,0.5), 0 0 40px rgba(168,85,247,0.1)',
            animation: 'scaleIn 0.2s ease',
          }}
        >
          {/* Search input */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px 20px', borderBottom: '1px solid #2A2840' }}>
            <Search size={18} color="#6B7280" style={{ flexShrink: 0 }} />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search pages, features, settings..."
              style={{
                flex: 1, background: 'transparent', outline: 'none', border: 'none',
                fontSize: 14, color: '#E5E7EB', fontFamily: 'inherit',
              }}
              autoComplete="off"
              spellCheck={false}
            />
            {query && (
              <button
                onClick={() => { setQuery(''); inputRef.current?.focus() }}
                style={{ padding: 4, borderRadius: 8, background: 'transparent', border: 'none', cursor: 'pointer', display: 'flex' }}
              >
                <X size={16} color="#6B7280" />
              </button>
            )}
            <kbd style={{
              padding: '3px 8px', background: '#1F2937', borderRadius: 6,
              border: '1px solid #374151', fontSize: 10, color: '#6B7280', fontWeight: 600,
            }}>ESC</kbd>
          </div>

          {/* Results */}
          <div ref={listRef} style={{ overflowY: 'auto', maxHeight: 'calc(70vh - 72px)' }}>
            {results.length === 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '48px 0', color: '#6B7280' }}>
                <Search size={32} style={{ opacity: 0.4, marginBottom: 12 }} />
                <p style={{ fontSize: 14, fontWeight: 500 }}>No results found</p>
                <p style={{ fontSize: 12, marginTop: 4, opacity: 0.7 }}>Try a different search term</p>
              </div>
            ) : (
              Object.entries(grouped).map(([section, items]) => (
                <div key={section}>
                  <div style={{ padding: '8px 20px', background: 'rgba(255,255,255,0.02)' }}>
                    <span style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1.5, color: '#6B7280' }}>{section}</span>
                  </div>
                  {items.map(item => {
                    const idx = flatIdx++
                    const Icon = item.icon
                    const isActive = idx === activeIndex

                    return (
                      <button
                        key={item.id}
                        data-index={idx}
                        onClick={() => navigate(item.href)}
                        onMouseEnter={() => setActiveIndex(idx)}
                        style={{
                          width: '100%', display: 'flex', alignItems: 'center', gap: 12,
                          padding: '12px 20px', textAlign: 'left', border: 'none', cursor: 'pointer',
                          transition: 'background 0.15s',
                          background: isActive ? 'rgba(168,85,247,0.1)' : 'transparent',
                          fontFamily: 'inherit',
                        }}
                      >
                        <div style={{
                          width: 36, height: 36, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                          background: isActive ? 'rgba(168,85,247,0.2)' : '#1F2937',
                          border: isActive ? '1px solid rgba(168,85,247,0.3)' : '1px solid #374151',
                          transition: 'all 0.15s',
                        }}>
                          <Icon size={18} color={isActive ? '#A855F7' : '#9CA3AF'} />
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <p style={{ fontSize: 14, fontWeight: 500, color: isActive ? '#E5E7EB' : '#D1D5DB', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', margin: 0 }}>{item.name}</p>
                          <p style={{ fontSize: 12, color: isActive ? '#A78BFA' : '#6B7280', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', margin: '2px 0 0 0' }}>{item.description}</p>
                        </div>
                        {isActive && (
                          <ArrowRight size={16} color="#A855F7" style={{ flexShrink: 0 }} />
                        )}
                      </button>
                    )
                  })}
                </div>
              ))
            )}
          </div>

          {/* Footer hint */}
          <div style={{
            padding: '10px 20px', borderTop: '1px solid #2A2840', background: 'rgba(255,255,255,0.02)',
            display: 'flex', alignItems: 'center', gap: 16, fontSize: 10, color: '#6B7280',
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <kbd style={{ padding: '2px 6px', background: '#1F2937', borderRadius: 4, border: '1px solid #374151', fontWeight: 600 }}>↑↓</kbd>
              navigate
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <kbd style={{ padding: '2px 6px', background: '#1F2937', borderRadius: 4, border: '1px solid #374151', fontWeight: 600 }}>↵</kbd>
              select
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <kbd style={{ padding: '2px 6px', background: '#1F2937', borderRadius: 4, border: '1px solid #374151', fontWeight: 600 }}>esc</kbd>
              close
            </span>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0 } to { opacity: 1 } }
        @keyframes scaleIn { from { opacity: 0; transform: scale(0.95) } to { opacity: 1; transform: scale(1) } }
      `}</style>
    </>
  )
}
