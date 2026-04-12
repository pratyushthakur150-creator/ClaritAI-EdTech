import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Filter,
  Phone,
  Mic,
  GraduationCap,
  BarChart3,
  BookOpen,
  Book,
  Users,
  MessageSquare,
  ChevronLeft,
  Target,
  Calendar,
  Settings,
} from 'lucide-react'

interface NavItem {
  name: string
  href: string
  icon: React.ElementType
  badge?: string
}

interface SidebarProps {
  isCollapsed: boolean
  onToggle: () => void
}

interface NavSection {
  label: string
  items: NavItem[]
}

const navSections: NavSection[] = [
  {
    label: 'Core',
    items: [
      { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
      { name: 'CRM', href: '/dashboard/crm', icon: Target },
      { name: 'Students', href: '/dashboard/students', icon: Users },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { name: 'Teaching Assistant', href: '/dashboard/teaching-assistant', icon: BookOpen },
      { name: 'CRM Voice Agent', href: '/dashboard/assistant', icon: Mic },
      { name: 'Chatbot', href: '/dashboard/chatbot', icon: MessageSquare },
    ],
  },
  {
    label: 'Management',
    items: [
      { name: 'Demos', href: '/dashboard/demos', icon: Calendar },
      { name: 'Calls', href: '/dashboard/calls', icon: Phone },
      { name: 'Enrollments', href: '/dashboard/enrollments', icon: GraduationCap },
      { name: 'Courses', href: '/dashboard/courses', icon: Book },
    ],
  },
  {
    label: 'Analytics & Config',
    items: [
      { name: 'Funnel', href: '/dashboard/funnel', icon: Filter },
      { name: 'Insights', href: '/dashboard/insights', icon: BarChart3 },
      { name: 'Settings', href: '/dashboard/settings', icon: Settings },
    ],
  },
]

function LogoImage({ size = 36, className = '' }: { size?: number; className?: string }) {
  const [failed, setFailed] = React.useState(false)
  if (failed) {
    return (
      <div className={`rounded-lg bg-gradient-to-br from-[#A855F7] to-[#D946EF] flex items-center justify-center text-white text-xs font-bold shadow-lg shadow-purple-500/20 ${className}`} style={{ width: size, height: size }}>
        C
      </div>
    )
  }
  return (
    <img
      src="/logo.png.png"
      alt="ClaritAi"
      width={size}
      height={size}
      className={`object-contain ${className}`}
      onError={() => setFailed(true)}
    />
  )
}

export default function Sidebar({ isCollapsed, onToggle }: SidebarProps) {
  const pathname = usePathname()

  return (
    <div
      className={`
        h-screen flex flex-col transition-all duration-300 ease-out
        ${isCollapsed ? 'w-[72px]' : 'w-[260px]'}
      `}
      style={{
        background: 'rgba(15, 14, 23, 0.85)',
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
        borderRight: '1px solid #1E1D2E',
      }}
    >
      {/* Logo area */}
      <div className={`flex items-center h-16 px-4 border-b border-white/5 ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
        {!isCollapsed && (
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center overflow-hidden shrink-0">
              <LogoImage size={32} className="w-full h-full" />
            </div>
            <div>
              <span className="font-bold text-white text-lg tracking-tight">ClaritAI</span>
              <span className="text-[10px] uppercase tracking-widest text-gray-500/70 block -mt-0.5 font-medium">Premium Plan</span>
            </div>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
          aria-label="Toggle sidebar"
        >
          <ChevronLeft
            className={`w-4 h-4 text-gray-400 transition-transform duration-300 ${isCollapsed ? 'rotate-180' : ''}`}
          />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-6 space-y-1" role="navigation" aria-label="Main navigation">
        {navSections.map((section) => (
          <div key={section.label}>
            {!isCollapsed && (
              <div className="px-4 mb-2 mt-4 first:mt-0">
                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest pl-2 mb-2">
                  {section.label}
                </p>
              </div>
            )}
            {isCollapsed && <div className="my-2 mx-3 border-t border-white/5" />}
            {section.items.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`
                    flex items-center gap-3 px-6 py-3 text-sm font-medium transition-all duration-200
                    ${isCollapsed ? 'justify-center px-3' : ''}
                    ${isActive
                      ? 'text-[#A855F7] bg-gradient-to-r from-[#A855F7]/15 to-[#A855F7]/[0.02] border-l-[3px] border-[#A855F7] shadow-[inset_0_0_15px_rgba(168,85,247,0.05)]'
                      : 'text-gray-400 hover:text-white hover:bg-white/5 border-l-[3px] border-transparent'
                    }
                  `}
                  title={isCollapsed ? item.name : undefined}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon className={`w-[20px] h-[20px] flex-shrink-0 transition-colors ${isActive ? 'text-[#A855F7]' : ''}`} />
                  {!isCollapsed && (
                    <span className="truncate">{item.name}</span>
                  )}
                  {!isCollapsed && item.badge && (
                    <span className="ml-auto bg-[#A855F7]/20 text-[#A855F7] text-[10px] font-semibold px-2 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-white/5 bg-black/20 backdrop-blur-sm">
        {!isCollapsed ? (
          <div className="flex items-center gap-3 px-2 py-2">
            <div className="w-8 h-8 rounded-full overflow-hidden shrink-0 flex items-center justify-center">
              <LogoImage size={32} className="w-full h-full rounded-full" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-white truncate">ClaritAi</p>
              <p className="text-[10px] text-gray-500 truncate">© 2025</p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center">
              <LogoImage size={32} className="w-full h-full rounded-full" />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}