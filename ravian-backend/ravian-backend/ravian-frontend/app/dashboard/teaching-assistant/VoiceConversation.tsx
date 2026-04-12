'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Phone, PhoneOff, Mic, Volume2, Loader2 } from 'lucide-react'
import apiClient from '@/lib/api'

interface VoiceConversationProps {
    courseId: string
    studentId: string
    onClose: () => void
}

type ConvState = 'listening' | 'processing' | 'speaking' | 'idle'

interface Turn {
    role: 'user' | 'assistant'
    text: string
}

// Extend Window for SpeechRecognition
interface SpeechRecognitionEvent {
    results: SpeechRecognitionResultList
    resultIndex: number
}

export default function VoiceConversation({ courseId, studentId, onClose }: VoiceConversationProps) {
    const [state, setState] = useState<ConvState>('idle')
    const [turns, setTurns] = useState<Turn[]>([])
    const [liveTranscript, setLiveTranscript] = useState('')
    const [error, setError] = useState<string | null>(null)

    const recognitionRef = useRef<any>(null)
    const audioRef = useRef<HTMLAudioElement | null>(null)
    const turnsEndRef = useRef<HTMLDivElement>(null)
    const isActiveRef = useRef(true)
    const silenceTimerRef = useRef<NodeJS.Timeout | null>(null)

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001'

    // Scroll to bottom when turns update
    useEffect(() => {
        turnsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [turns, liveTranscript])

    // Check browser support
    const getSpeechRecognition = useCallback(() => {
        const w = window as any
        return w.SpeechRecognition || w.webkitSpeechRecognition || null
    }, [])

    // Send question to TA and play response
    const sendAndPlay = useCallback(async (question: string) => {
        if (!isActiveRef.current) return
        setState('processing')
        setTurns(prev => [...prev, { role: 'user', text: question }])
        setLiveTranscript('')

        try {
            const { data } = await apiClient.post<any>('/api/v1/teaching-assistant/query', {
                student_id: studentId,
                course_id: courseId,
                question,
                use_voice: true,
            })

            if (!isActiveRef.current) return

            const answer = data.answer || 'I could not generate an answer.'
            const audioUrl = data.audio_url

            setTurns(prev => [...prev, { role: 'assistant', text: answer }])

            if (audioUrl) {
                setState('speaking')
                const audio = new Audio(`${baseUrl}${audioUrl}`)
                audioRef.current = audio

                audio.onended = () => {
                    audioRef.current = null
                    if (isActiveRef.current) {
                        startListening()
                    }
                }

                audio.onerror = () => {
                    audioRef.current = null
                    if (isActiveRef.current) {
                        startListening()
                    }
                }

                audio.play().catch(() => {
                    // Autoplay blocked — fallback to resume listening
                    if (isActiveRef.current) startListening()
                })
            } else {
                // No audio — just resume listening
                if (isActiveRef.current) startListening()
            }
        } catch (e: any) {
            const detail = e?.response?.data?.detail || e?.message || 'Failed to get answer'
            setTurns(prev => [...prev, { role: 'assistant', text: `⚠️ Error: ${detail}` }])
            setError(detail)
            // Resume listening after error
            if (isActiveRef.current) {
                setTimeout(() => startListening(), 2000)
            }
        }
    }, [courseId, studentId, baseUrl])

    // Start speech recognition
    const startListening = useCallback(() => {
        if (!isActiveRef.current) return

        const SpeechRecognition = getSpeechRecognition()
        if (!SpeechRecognition) {
            setError('Speech Recognition not supported. Use Chrome or Edge.')
            return
        }

        // Clean up previous instance
        if (recognitionRef.current) {
            try { recognitionRef.current.abort() } catch (_) { }
        }

        const recognition = new SpeechRecognition()
        recognition.continuous = true
        recognition.interimResults = true
        recognition.lang = 'en-US'
        recognition.maxAlternatives = 1

        recognitionRef.current = recognition

        recognition.onresult = (event: SpeechRecognitionEvent) => {
            let interim = ''
            let finalTranscript = ''

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result = event.results[i]
                if (result.isFinal) {
                    finalTranscript += result[0].transcript
                } else {
                    interim += result[0].transcript
                }
            }

            if (interim) {
                setLiveTranscript(interim)
            }

            if (finalTranscript.trim()) {
                // Clear any existing silence timer
                if (silenceTimerRef.current) {
                    clearTimeout(silenceTimerRef.current)
                    silenceTimerRef.current = null
                }

                // Set a short timer — if no more speech comes, send it
                const currentTranscript = finalTranscript.trim()
                silenceTimerRef.current = setTimeout(() => {
                    if (isActiveRef.current) {
                        try { recognition.stop() } catch (_) { }
                        sendAndPlay(currentTranscript)
                    }
                }, 1500) // Wait 1.5s of silence after final result before sending
            }
        }

        recognition.onerror = (event: any) => {
            console.warn('SpeechRecognition error:', event.error)
            if (event.error === 'not-allowed') {
                setError('Microphone access denied. Please allow microphone access.')
                return
            }
            if (event.error === 'no-speech') {
                // No speech detected — restart
                if (isActiveRef.current) {
                    setTimeout(() => startListening(), 500)
                }
                return
            }
            // Other errors — try to restart
            if (isActiveRef.current) {
                setTimeout(() => startListening(), 1000)
            }
        }

        recognition.onend = () => {
            // If we're still in listening state and active, restart (browser may auto-stop)
            if (isActiveRef.current && state === 'listening') {
                // Don't restart if a silence timer is pending (about to send)
                if (!silenceTimerRef.current) {
                    setTimeout(() => startListening(), 300)
                }
            }
        }

        try {
            recognition.start()
            setState('listening')
            setError(null)
            setLiveTranscript('')
        } catch (e) {
            console.error('Failed to start recognition:', e)
            setTimeout(() => startListening(), 500)
        }
    }, [getSpeechRecognition, sendAndPlay])

    // Start conversation on mount
    useEffect(() => {
        isActiveRef.current = true
        // Small delay to let the overlay animate in
        const timer = setTimeout(() => startListening(), 500)
        return () => {
            clearTimeout(timer)
            cleanup()
        }
    }, [])

    // Cleanup everything
    const cleanup = useCallback(() => {
        isActiveRef.current = false
        if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current)
            silenceTimerRef.current = null
        }
        if (recognitionRef.current) {
            try { recognitionRef.current.abort() } catch (_) { }
            recognitionRef.current = null
        }
        if (audioRef.current) {
            audioRef.current.pause()
            audioRef.current = null
        }
    }, [])

    const handleEndCall = () => {
        cleanup()
        onClose()
    }

    // Ring color based on state
    const ringColor = {
        idle: 'border-gray-400',
        listening: 'border-blue-500',
        processing: 'border-yellow-500',
        speaking: 'border-green-500',
    }[state]

    const ringPulse = state === 'listening' || state === 'speaking'

    const statusText = {
        idle: 'Starting...',
        listening: 'Listening — speak your question...',
        processing: 'Thinking...',
        speaking: 'Teaching Assistant is speaking...',
    }[state]

    const statusIcon = {
        idle: <Loader2 className="w-6 h-6 animate-spin text-gray-400" />,
        listening: <Mic className="w-6 h-6 text-blue-500" />,
        processing: <Loader2 className="w-6 h-6 animate-spin text-yellow-500" />,
        speaking: <Volume2 className="w-6 h-6 text-green-500" />,
    }[state]

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col" style={{ maxHeight: '85vh' }}>

                {/* Header */}
                <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-4 text-white">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-lg font-bold flex items-center gap-2">
                                <Phone className="w-5 h-5" />
                                Voice Conversation
                            </h2>
                            <p className="text-indigo-200 text-sm mt-0.5">ClariAI Teaching Assistant</p>
                        </div>
                        <div className="flex items-center gap-2 text-xs bg-white/20 px-3 py-1 rounded-full">
                            <span className={`w-2 h-2 rounded-full ${state === 'listening' ? 'bg-blue-400 animate-pulse' : state === 'speaking' ? 'bg-green-400 animate-pulse' : state === 'processing' ? 'bg-yellow-400 animate-pulse' : 'bg-gray-400'}`} />
                            <span>Live</span>
                        </div>
                    </div>
                </div>

                {/* Conversation transcript */}
                <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3 min-h-[200px]">
                    {turns.length === 0 && state === 'listening' && (
                        <div className="text-center text-gray-400 py-8">
                            <Mic className="w-10 h-10 mx-auto mb-3 text-blue-400 animate-pulse" />
                            <p className="text-sm">I&apos;m listening. Ask me anything about your course!</p>
                        </div>
                    )}

                    {turns.map((turn, i) => (
                        <div key={i} className={`flex ${turn.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[85%] rounded-xl px-4 py-2.5 text-sm ${turn.role === 'user'
                                    ? 'bg-indigo-100 text-indigo-900'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                {turn.role === 'assistant' && (
                                    <span className="text-xs font-semibold text-indigo-500 block mb-1">Teaching Assistant</span>
                                )}
                                <p className="whitespace-pre-wrap">{turn.text}</p>
                            </div>
                        </div>
                    ))}

                    {/* Live transcript (interim) */}
                    {liveTranscript && state === 'listening' && (
                        <div className="flex justify-end">
                            <div className="max-w-[85%] rounded-xl px-4 py-2.5 text-sm bg-indigo-50 text-indigo-400 italic border border-indigo-200 border-dashed">
                                {liveTranscript}...
                            </div>
                        </div>
                    )}

                    <div ref={turnsEndRef} />
                </div>

                {/* Status + controls */}
                <div className="border-t px-6 py-5">
                    {error && (
                        <div className="text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2 mb-3">
                            {error}
                        </div>
                    )}

                    <div className="flex flex-col items-center gap-4">
                        {/* Status ring */}
                        <div className="flex items-center gap-3">
                            <div className={`relative flex items-center justify-center w-12 h-12 rounded-full border-3 ${ringColor} transition-colors duration-300`}>
                                {ringPulse && (
                                    <div className={`absolute inset-0 rounded-full ${state === 'listening' ? 'bg-blue-400' : 'bg-green-400'} opacity-20 animate-ping`} />
                                )}
                                {statusIcon}
                            </div>
                            <span className="text-sm text-gray-600 font-medium">{statusText}</span>
                        </div>

                        {/* End call button */}
                        <button
                            onClick={handleEndCall}
                            className="flex items-center gap-2 px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-full font-semibold shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
                        >
                            <PhoneOff className="w-5 h-5" />
                            End Conversation
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
