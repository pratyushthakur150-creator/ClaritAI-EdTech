'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Phone, PhoneOff, Mic, MicOff, Volume2, VolumeX, Maximize2, Minimize2 } from 'lucide-react'

interface VoiceCallInterfaceProps {
    studentName: string
    isActive: boolean
    onEndCall: () => void
}

export default function VoiceCallInterface({ studentName, isActive, onEndCall }: VoiceCallInterfaceProps) {
    const [duration, setDuration] = useState(0)
    const [isMuted, setIsMuted] = useState(false)
    const [isSpeakerOn, setIsSpeakerOn] = useState(true)
    const [isExpanded, setIsExpanded] = useState(false)

    // Timer effect
    useEffect(() => {
        let interval: NodeJS.Timeout
        if (isActive) {
            interval = setInterval(() => {
                setDuration(prev => prev + 1)
            }, 1000)
        } else {
            setDuration(0)
        }
        return () => clearInterval(interval)
    }, [isActive])

    // Format duration
    const formatTime = (seconds: number) => {
        const hrs = Math.floor(seconds / 3600)
        const mins = Math.floor((seconds % 3600) / 60)
        const secs = seconds % 60

        if (hrs > 0) {
            return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
        }
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }

    if (!isActive) return null

    return (
        <div className={`
      fixed transition-all duration-300 ease-in-out bg-gray-900 text-white shadow-2xl overflow-hidden
      ${isExpanded ? 'inset-0 z-50 rounded-none flex flex-col items-center justify-center' : 'bottom-6 right-6 w-80 rounded-2xl z-40'}
    `}>
            {/* Header controls (expand/minimize) */}
            <div className="absolute top-4 right-4 z-10">
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="p-2 rounded-full hover:bg-white/10 text-gray-300 hover:text-white"
                >
                    {isExpanded ? <Minimize2 size={20} /> : <Maximize2 size={16} />}
                </button>
            </div>

            {/* Main Content */}
            <div className={`flex flex-col items-center ${isExpanded ? 'scale-125' : 'p-6'}`}>

                {/* Avatar / Visualizer Placeholder */}
                <div className="relative mb-6">
                    <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg animate-pulse">
                        <span className="text-3xl font-bold">{studentName.charAt(0)}</span>
                    </div>
                    {/* Ripple effects for active call */}
                    <div className="absolute inset-0 rounded-full border-4 border-blue-500/30 animate-ping"></div>
                </div>

                <h3 className="text-xl font-semibold mb-1">{studentName}</h3>
                <p className="text-blue-200 text-sm mb-6 font-mono">{formatTime(duration)}</p>

                {/* Controls Grid */}
                <div className="grid grid-cols-3 gap-6 w-full max-w-[200px]">
                    {/* Mute Toggle */}
                    <div className="flex flex-col items-center gap-2">
                        <button
                            onClick={() => setIsMuted(!isMuted)}
                            className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${isMuted ? 'bg-white text-gray-900' : 'bg-gray-700 hover:bg-gray-600'
                                }`}
                        >
                            {isMuted ? <MicOff size={20} /> : <Mic size={20} />}
                        </button>
                        <span className="text-xs text-gray-400">Mute</span>
                    </div>

                    {/* End Call (Center, Larger) */}
                    <div className="flex flex-col items-center gap-2 -mt-2">
                        <button
                            onClick={onEndCall}
                            className="w-16 h-16 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center shadow-lg transform hover:scale-105 transition-all"
                        >
                            <PhoneOff size={28} fill="currentColor" />
                        </button>
                        <span className="text-xs text-gray-400">End</span>
                    </div>

                    {/* Speaker Toggle */}
                    <div className="flex flex-col items-center gap-2">
                        <button
                            onClick={() => setIsSpeakerOn(!isSpeakerOn)}
                            className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${!isSpeakerOn ? 'bg-white text-gray-900' : 'bg-gray-700 hover:bg-gray-600'
                                }`}
                        >
                            {!isSpeakerOn ? <VolumeX size={20} /> : <Volume2 size={20} />}
                        </button>
                        <span className="text-xs text-gray-400">Speaker</span>
                    </div>
                </div>
            </div>
        </div>
    )
}
