"use client"

import { useEffect, useRef, useState } from 'react'
import gsap from 'gsap'
import { Settings as SettingsIcon, Bell, Shield, Puzzle, Palette, Save, Moon, Sun, Globe } from 'lucide-react'

const tabs = [
    { id: 'general', label: 'General', icon: SettingsIcon },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'integrations', label: 'Integrations', icon: Puzzle },
    { id: 'appearance', label: 'Appearance', icon: Palette },
]

export default function SettingsPage() {
    const containerRef = useRef<HTMLDivElement>(null)
    const [activeTab, setActiveTab] = useState('general')
    const [org, setOrg] = useState('ClaritAI EdTech')
    const [email, setEmail] = useState('admin@claritai.com')
    const [timezone, setTimezone] = useState('Asia/Kolkata')
    const [darkMode, setDarkMode] = useState(true)
    const [emailNotif, setEmailNotif] = useState(true)
    const [pushNotif, setPushNotif] = useState(true)
    const [weeklyDigest, setWeeklyDigest] = useState(false)
    const [twoFactor, setTwoFactor] = useState(false)

    useEffect(() => { if (!containerRef.current) return; const ctx = gsap.context(() => { gsap.from('.st-panel', { y: 30, opacity: 0, duration: 0.6, stagger: 0.15, ease: 'power3.out' }) }, containerRef); return () => ctx.revert() }, [])

    const Toggle = ({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) => (
        <button onClick={() => onChange(!checked)} className={`relative w-11 h-6 rounded-full transition-colors ${checked ? 'bg-[#A855F7]' : 'bg-gray-700'}`}>
            <div className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow transition-transform ${checked ? 'left-6' : 'left-1'}`} />
        </button>
    )

    return (
        <div ref={containerRef}>
            <div className="mb-8"><h2 className="text-3xl font-bold text-white mb-1 tracking-tight">Settings</h2><p className="text-sm text-gray-500">Configure your platform preferences</p></div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Tab nav */}
                <div className="st-panel">
                    <div className="bg-[#13121E] border border-[#2A2840] rounded-2xl p-3 shadow-[0_4px_20px_rgba(0,0,0,0.4)]">
                        <div className="space-y-1">{tabs.map(tab => {
                            const Icon = tab.icon; return (
                                <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${activeTab === tab.id ? 'bg-[#A855F7]/15 text-[#A855F7] border border-[#A855F7]/20' : 'text-gray-400 hover:bg-white/5 hover:text-white'}`}>
                                    <Icon className="w-4 h-4" />{tab.label}
                                </button>
                            )
                        })}</div>
                    </div>
                </div>

                {/* Tab content */}
                <div className="st-panel lg:col-span-3 bg-[#13121E] border border-[#2A2840] rounded-2xl p-6 shadow-[0_4px_20px_rgba(0,0,0,0.4)]">
                    {activeTab === 'general' && (
                        <div className="space-y-6">
                            <h3 className="text-sm font-semibold text-white mb-4">General Settings</h3>
                            <div><label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Organization Name</label><input type="text" value={org} onChange={e => setOrg(e.target.value)} className="w-full bg-[#0B0B12] border border-white/10 rounded-xl py-2.5 px-4 text-sm text-gray-300 focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7] transition-all" /></div>
                            <div><label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Admin Email</label><input type="email" value={email} onChange={e => setEmail(e.target.value)} className="w-full bg-[#0B0B12] border border-white/10 rounded-xl py-2.5 px-4 text-sm text-gray-300 focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7] transition-all" /></div>
                            <div><label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Timezone</label><div className="relative"><Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" /><select value={timezone} onChange={e => setTimezone(e.target.value)} className="w-full bg-[#0B0B12] border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-sm text-gray-300 focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7] transition-all appearance-none cursor-pointer"><option value="Asia/Kolkata">Asia/Kolkata (IST)</option><option value="America/New_York">America/New York (EST)</option><option value="Europe/London">Europe/London (GMT)</option><option value="Asia/Tokyo">Asia/Tokyo (JST)</option></select></div></div>
                        </div>
                    )}

                    {activeTab === 'notifications' && (
                        <div className="space-y-6">
                            <h3 className="text-sm font-semibold text-white mb-4">Notification Preferences</h3>
                            <div className="flex items-center justify-between py-3 border-b border-white/5"><div><p className="text-sm text-white font-medium">Email Notifications</p><p className="text-xs text-gray-500 mt-0.5">Receive updates via email</p></div><Toggle checked={emailNotif} onChange={setEmailNotif} /></div>
                            <div className="flex items-center justify-between py-3 border-b border-white/5"><div><p className="text-sm text-white font-medium">Push Notifications</p><p className="text-xs text-gray-500 mt-0.5">Browser push notifications</p></div><Toggle checked={pushNotif} onChange={setPushNotif} /></div>
                            <div className="flex items-center justify-between py-3"><div><p className="text-sm text-white font-medium">Weekly Digest</p><p className="text-xs text-gray-500 mt-0.5">Weekly summary report via email</p></div><Toggle checked={weeklyDigest} onChange={setWeeklyDigest} /></div>
                        </div>
                    )}

                    {activeTab === 'security' && (
                        <div className="space-y-6">
                            <h3 className="text-sm font-semibold text-white mb-4">Security Settings</h3>
                            <div className="flex items-center justify-between py-3 border-b border-white/5"><div><p className="text-sm text-white font-medium">Two-Factor Authentication</p><p className="text-xs text-gray-500 mt-0.5">Add an extra layer of security</p></div><Toggle checked={twoFactor} onChange={setTwoFactor} /></div>
                            <div className="py-3 border-b border-white/5"><p className="text-sm text-white font-medium mb-2">Change Password</p><div className="space-y-3"><input type="password" placeholder="Current password" className="w-full bg-[#0B0B12] border border-white/10 rounded-xl py-2.5 px-4 text-sm text-gray-300 placeholder-gray-600 focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7] transition-all" /><input type="password" placeholder="New password" className="w-full bg-[#0B0B12] border border-white/10 rounded-xl py-2.5 px-4 text-sm text-gray-300 placeholder-gray-600 focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7] transition-all" /></div></div>
                            <p className="text-xs text-gray-500">Last password change: Never</p>
                        </div>
                    )}

                    {activeTab === 'integrations' && (
                        <div className="space-y-6">
                            <h3 className="text-sm font-semibold text-white mb-4">Integrations</h3>
                            {[{ name: 'Google Calendar', desc: 'Sync meetings and demos', connected: true }, { name: 'Webhook', desc: 'Real-time event notifications', connected: false }, { name: 'Zapier', desc: 'Connect with 5000+ apps', connected: false }].map((int, i) => (
                                <div key={i} className="flex items-center justify-between py-3 border-b border-white/5">
                                    <div className="flex items-center gap-3"><div className="w-10 h-10 rounded-xl bg-gray-800 flex items-center justify-center"><Puzzle className="w-5 h-5 text-gray-400" /></div><div><p className="text-sm text-white font-medium">{int.name}</p><p className="text-xs text-gray-500 mt-0.5">{int.desc}</p></div></div>
                                    <button className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${int.connected ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-[#A855F7]/10 text-[#A855F7] border border-[#A855F7]/20 hover:bg-[#A855F7]/20'}`}>{int.connected ? 'Connected' : 'Connect'}</button>
                                </div>
                            ))}
                        </div>
                    )}

                    {activeTab === 'appearance' && (
                        <div className="space-y-6">
                            <h3 className="text-sm font-semibold text-white mb-4">Appearance</h3>
                            <div className="flex items-center justify-between py-3 border-b border-white/5"><div><p className="text-sm text-white font-medium">Dark Mode</p><p className="text-xs text-gray-500 mt-0.5">Toggle dark/light theme</p></div><Toggle checked={darkMode} onChange={setDarkMode} /></div>
                            <div><p className="text-sm text-white font-medium mb-3">Accent Color</p><div className="flex gap-3">{['#A855F7', '#D946EF', '#3B82F6', '#10B981', '#F59E0B', '#EF4444'].map(c => (<button key={c} className="w-8 h-8 rounded-full border-2 border-transparent hover:border-white/50 transition-all shadow-lg" style={{ backgroundColor: c, boxShadow: `0 0 12px ${c}40` }} />))}</div></div>
                        </div>
                    )}

                    <div className="flex justify-end mt-8 pt-6 border-t border-white/5">
                        <button className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#A855F7] to-[#D946EF] text-white font-medium text-sm shadow-lg shadow-purple-900/30 flex items-center gap-2 hover:shadow-purple-900/50 transition-shadow"><Save className="w-4 h-4" /> Save Changes</button>
                    </div>
                </div>
            </div>
        </div>
    )
}
