'use client'

import React, { useEffect, useState } from 'react'
import { Settings, Loader2, User, UserCircle } from 'lucide-react'
import apiClient from '@/lib/api'
import { toast } from 'sonner'

interface Voice {
    id: string
    name: string
    description: string
    gender: string
}

interface VoiceSettingsProps {
    onSettingsChange?: (settings: { voiceId: string, speed: number }) => void
}

export default function VoiceSettings({ onSettingsChange }: VoiceSettingsProps) {
    const [voices, setVoices] = useState<Voice[]>([])
    const [loading, setLoading] = useState(true)
    const [selectedVoice, setSelectedVoice] = useState('alloy')
    const [speed, setSpeed] = useState(1.0)

    useEffect(() => {
        fetchVoices()
        const savedVoice = localStorage.getItem('voice_settings_voice')
        const savedSpeed = localStorage.getItem('voice_settings_speed')
        if (savedVoice) setSelectedVoice(savedVoice)
        if (savedSpeed) setSpeed(parseFloat(savedSpeed))
    }, [])

    useEffect(() => {
        localStorage.setItem('voice_settings_voice', selectedVoice)
        localStorage.setItem('voice_settings_speed', speed.toString())
        if (onSettingsChange) {
            onSettingsChange({ voiceId: selectedVoice, speed })
        }
    }, [selectedVoice, speed, onSettingsChange])

    const fetchVoices = async () => {
        try {
            const { data } = await apiClient.get<Voice[]>('/api/v1/voice/voices')
            setVoices(data)
        } catch (error) {
            console.error('Failed to fetch voices:', error)
            setVoices([
                { id: 'alloy', name: 'Alloy', description: 'Balanced, neutral voice', gender: 'neutral' },
                { id: 'echo', name: 'Echo', description: 'Clear, professional voice', gender: 'male' },
                { id: 'fable', name: 'Fable', description: 'Warm, storytelling voice', gender: 'neutral' },
                { id: 'onyx', name: 'Onyx', description: 'Deep, authoritative voice', gender: 'male' },
                { id: 'nova', name: 'Nova', description: 'Bright, energetic voice', gender: 'female' },
                { id: 'shimmer', name: 'Shimmer', description: 'Soft, gentle voice', gender: 'female' },
            ])
            toast.error('Using offline voice list')
        } finally {
            setLoading(false)
        }
    }

    const genderIcon = (gender: string) => {
        if (gender === 'male') return '♂'
        if (gender === 'female') return '♀'
        return '◎'
    }

    return (
        <div className="bg-white rounded-2xl border border-slate-200/80 overflow-hidden flex flex-col">
            {/* Header with subtle gradient */}
            <div className="px-5 py-3.5 border-b border-slate-100 flex items-center gap-2"
                style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.04), rgba(139,92,246,0.04))' }}>
                <div className="w-6 h-6 rounded-lg flex items-center justify-center"
                    style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
                    <Settings size={12} className="text-white" />
                </div>
                <h3 className="text-sm font-semibold text-slate-800">Voice Configuration</h3>
            </div>

            <div className="p-5 space-y-5 flex-1 overflow-y-auto">
                {/* Voice Selection */}
                <div>
                    <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5">
                        AI Voice Model
                    </label>
                    {loading ? (
                        <div className="flex justify-center p-4"><Loader2 className="animate-spin text-slate-300" /></div>
                    ) : (
                        <div className="grid grid-cols-2 gap-2">
                            {voices.map(voice => {
                                const isSelected = selectedVoice === voice.id
                                return (
                                    <button
                                        key={voice.id}
                                        onClick={() => setSelectedVoice(voice.id)}
                                        className={`relative px-3 py-2.5 text-left rounded-xl border transition-all duration-200 group overflow-hidden ${isSelected
                                            ? 'border-indigo-500 bg-indigo-50/80 shadow-sm shadow-indigo-100'
                                            : 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50'
                                            }`}
                                    >
                                        {/* Hover glow */}
                                        {!isSelected && (
                                            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
                                                style={{ background: 'radial-gradient(circle at 50% 50%, rgba(99,102,241,0.06), transparent 70%)' }} />
                                        )}
                                        <div className="flex items-center gap-1.5 relative">
                                            <span className={`text-sm font-semibold ${isSelected ? 'text-indigo-700' : 'text-slate-700'}`}>
                                                {voice.name}
                                            </span>
                                            <span className={`text-[10px] ${isSelected ? 'text-indigo-400' : 'text-slate-300'}`}>
                                                {genderIcon(voice.gender)}
                                            </span>
                                        </div>
                                        <span className="text-[10px] text-slate-400 leading-tight block mt-0.5 relative">
                                            {voice.description}
                                        </span>
                                        {/* Selected indicator dot */}
                                        {isSelected && (
                                            <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-indigo-500" />
                                        )}
                                    </button>
                                )
                            })}
                        </div>
                    )}
                </div>

                {/* Speed Control */}
                <div>
                    <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5">
                        Speaking Rate: <span className="text-indigo-600 font-bold">{speed}x</span>
                    </label>
                    <div className="flex items-center gap-3">
                        <span className="text-[10px] font-semibold text-slate-400 w-7">0.5x</span>
                        <div className="flex-1 relative h-6 flex items-center">
                            <input
                                type="range"
                                min="0.5"
                                max="2"
                                step="0.1"
                                value={speed}
                                onChange={(e) => setSpeed(parseFloat(e.target.value))}
                                className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
                                style={{
                                    background: `linear-gradient(to right, #6366f1 0%, #8b5cf6 ${((speed - 0.5) / 1.5) * 100}%, #e2e8f0 ${((speed - 0.5) / 1.5) * 100}%, #e2e8f0 100%)`,
                                }}
                            />
                        </div>
                        <span className="text-[10px] font-semibold text-slate-400 w-7 text-right">2.0x</span>
                    </div>
                </div>
            </div>

            {/* Inline slider thumb styles */}
            <style dangerouslySetInnerHTML={{
                __html: `
                input[type="range"]::-webkit-slider-thumb {
                    -webkit-appearance: none;
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #6366f1, #8b5cf6);
                    border: 2px solid white;
                    box-shadow: 0 2px 6px rgba(99,102,241,0.4);
                    cursor: pointer;
                    transition: transform 0.15s ease;
                }
                input[type="range"]::-webkit-slider-thumb:hover {
                    transform: scale(1.2);
                }
                input[type="range"]::-moz-range-thumb {
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #6366f1, #8b5cf6);
                    border: 2px solid white;
                    box-shadow: 0 2px 6px rgba(99,102,241,0.4);
                    cursor: pointer;
                }
            ` }} />
        </div>
    )
}
