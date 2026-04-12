"use client"

import { useEffect, useRef, useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import gsap from 'gsap'
import { Send, BookOpen, Sparkles, Mic, StopCircle, Upload, FileText, Trash2, Image, X, Youtube } from 'lucide-react'

interface Message { role: 'user' | 'assistant'; content: string; audioUrl?: string | null }
interface CourseDoc { document_id: string; title: string; document_type: string; status: string; chunk_count: number; file_size: number; upload_timestamp: string }

const quickPrompts = ['Explain quadratic equations', 'Help with organic chemistry', 'Review my essay structure', 'Solve this physics problem']
const subjects = ['Mathematics', 'Physics', 'Chemistry', 'English', 'Computer Science']
const docTypes = [
  { value: 'pdf', label: 'PDF', accept: '.pdf' },
  { value: 'pptx', label: 'PowerPoint', accept: '.pptx,.ppt' },
  { value: 'text', label: 'Text', accept: '.txt' },
  { value: 'markdown', label: 'Markdown', accept: '.md' },
  { value: 'image', label: 'Image', accept: '.jpg,.jpeg,.png,.webp' },
  { value: 'video', label: 'Video', accept: '.mp4,.mov' },
  { value: 'youtube', label: 'YouTube URL', accept: '' },
]

interface UploadFileEntry {
  file: File
  status: 'queued' | 'uploading' | 'indexed' | 'error'
  error?: string
  preview?: string // data URL for image thumbnails
}

export default function TeachingAssistantPage() {
  const containerRef = useRef<HTMLDivElement>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()
  const [selectedSubject, setSelectedSubject] = useState('Mathematics')
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([{ role: 'assistant', content: 'Hello! I\'m your ClaritAI Teaching Assistant. Select a subject and ask me anything — I\'m here to help you learn!' }])
  const abortControllerRef = useRef<AbortController | null>(null)

  // ── Upload modal state ──
  const [showUpload, setShowUpload] = useState(false)
  const [uploadFiles, setUploadFiles] = useState<UploadFileEntry[]>([])
  const [uploadTitle, setUploadTitle] = useState('')
  const [uploadDocType, setUploadDocType] = useState('pdf')
  const [uploadYoutubeUrl, setUploadYoutubeUrl] = useState('')
  const [uploadDesc, setUploadDesc] = useState('')
  const [isUploading, setIsUploading] = useState(false)

  // ── Image query state (multi-image) ──
  const [imageFiles, setImageFiles] = useState<File[]>([])
  const [imagePreviews, setImagePreviews] = useState<string[]>([])

  // ── Voice recording state ──
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)

  // ── Active tab ──
  const [activeTab, setActiveTab] = useState<'chat' | 'materials'>('chat')

  // ── Fetch documents for selected subject ──
  const courseId = selectedSubject.toLowerCase().replace(' ', '_')
  const { data: docsData, isLoading: docsLoading } = useQuery({
    queryKey: ['course-docs', courseId],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/content/documents/${courseId}`)
      return res.data
    },
    enabled: activeTab === 'materials',
  })

  // ── Multi-file upload handler ──
  const handleUploadAll = async () => {
    if (uploadDocType === 'youtube') {
      // YouTube URL upload (single)
      setIsUploading(true)
      try {
        const formData = new FormData()
        formData.append('course_id', courseId)
        formData.append('title', uploadTitle || 'YouTube Video')
        formData.append('document_type', 'youtube')
        formData.append('description', uploadDesc)
        formData.append('youtube_url', uploadYoutubeUrl)
        const res = await apiClient.post('/api/v1/content/index', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
        setMessages(prev => [...prev, { role: 'assistant', content: `✅ YouTube video "${res.data.title || uploadTitle}" indexed! ${res.data.chunk_count || 0} chunks created.` }])
        resetUploadModal()
        queryClient.invalidateQueries({ queryKey: ['course-docs', courseId] })
      } catch (err: any) {
        setMessages(prev => [...prev, { role: 'assistant', content: `❌ Upload failed: ${err?.response?.data?.detail || 'Unknown error'}` }])
      } finally {
        setIsUploading(false)
      }
      return
    }
    if (uploadFiles.length === 0) return
    setIsUploading(true)
    let successCount = 0
    for (let i = 0; i < uploadFiles.length; i++) {
      const entry = uploadFiles[i]
      if (entry.status === 'indexed') continue
      setUploadFiles(prev => prev.map((f, idx) => idx === i ? { ...f, status: 'uploading' } : f))
      try {
        const formData = new FormData()
        formData.append('course_id', courseId)
        formData.append('title', uploadFiles.length === 1 && uploadTitle ? uploadTitle : entry.file.name)
        formData.append('document_type', uploadDocType)
        formData.append('description', uploadDesc)
        formData.append('file', entry.file)
        const res = await apiClient.post('/api/v1/content/index', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
        setUploadFiles(prev => prev.map((f, idx) => idx === i ? { ...f, status: 'indexed' } : f))
        successCount++
      } catch (err: any) {
        setUploadFiles(prev => prev.map((f, idx) => idx === i ? { ...f, status: 'error', error: err?.response?.data?.detail || 'Failed' } : f))
      }
    }
    setIsUploading(false)
    if (successCount > 0) {
      setMessages(prev => [...prev, { role: 'assistant', content: `✅ ${successCount} file${successCount > 1 ? 's' : ''} indexed successfully! I can now answer questions from this material.` }])
      queryClient.invalidateQueries({ queryKey: ['course-docs', courseId] })
    }
  }

  const resetUploadModal = () => {
    setShowUpload(false)
    setUploadFiles([])
    setUploadTitle('')
    setUploadDocType('pdf')
    setUploadYoutubeUrl('')
    setUploadDesc('')
  }

  const handleFilesSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    const newEntries: UploadFileEntry[] = Array.from(files).map(file => {
      const entry: UploadFileEntry = { file, status: 'queued' }
      // Generate thumbnail preview for image files
      if (file.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onload = (ev) => {
          setUploadFiles(prev => prev.map(f => f.file === file ? { ...f, preview: ev.target?.result as string } : f))
        }
        reader.readAsDataURL(file)
      }
      return entry
    })
    setUploadFiles(prev => [...prev, ...newEntries])
    if (!uploadTitle && files.length === 1) setUploadTitle(files[0].name)
    e.target.value = '' // reset input for re-selection
  }

  // ── Delete document mutation ──
  const deleteMutation = useMutation({
    mutationFn: async (docId: string) => {
      const res = await apiClient.delete(`/api/v1/content/documents/${docId}`)
      return res.data
    },
    onSuccess: (data) => {
      setMessages(prev => [...prev, { role: 'assistant', content: `🗑️ Document "${data.title}" deleted.` }])
      queryClient.invalidateQueries({ queryKey: ['course-docs', courseId] })
    },
  })

  // ── Text ask mutation (with conversation history) ──
  const sendMutation = useMutation({
    mutationFn: async (question: string) => {
      const controller = new AbortController()
      abortControllerRef.current = controller
      // If images are attached, use image-query endpoint (send first image; GPT-4o vision)
      if (imageFiles.length > 0) {
        const formData = new FormData()
        formData.append('image_file', imageFiles[0]) // primary image
        formData.append('student_id', '00000000-0000-0000-0000-000000000000')
        formData.append('course_id', courseId)
        // If multiple images, mention in question
        const imgNote = imageFiles.length > 1 ? ` [+${imageFiles.length - 1} more image(s) attached]` : ''
        formData.append('question', question + imgNote)
        const res = await apiClient.post('/api/v1/teaching-assistant/image-query', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          signal: controller.signal,
        })
        return res.data
      }
      // Build conversation history from current messages (excluding system greeting)
      const history = messages
        .filter((m, i) => i > 0) // skip initial greeting
        .map(m => ({ role: m.role, content: m.content }))
      const res = await apiClient.post('/api/v1/teaching-assistant/ask', {
        question,
        subject: selectedSubject,
        use_voice: true,
        history,
      }, { signal: controller.signal })
      return res.data
    },
    onSuccess: (data) => {
      const audioUrl = data.audio_url ? `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001'}${data.audio_url}` : null
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer || 'I couldn\'t generate a response.', audioUrl }])
      setImageFiles([])
      setImagePreviews([])
    },
    onError: () => { setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' }]) },
  })

  // ── Voice recording mutation ──
  const voiceMutation = useMutation({
    mutationFn: async (audioBlob: Blob) => {
      const formData = new FormData()
      formData.append('audio_file', audioBlob, 'recording.webm')
      formData.append('student_id', '00000000-0000-0000-0000-000000000000')
      formData.append('course_id', courseId)
      formData.append('voice_id', 'nova')
      const res = await apiClient.post('/api/v1/teaching-assistant/voice-query', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return res.data
    },
    onSuccess: (data) => {
      const transcribedQ = data.question || data.transcribed_question || 'Voice question'
      setMessages(prev => [...prev, { role: 'user', content: `🎤 ${transcribedQ}` }])
      const audioUrl = data.audio_url ? `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001'}${data.audio_url}` : null
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer || 'I couldn\'t generate a response.', audioUrl }])
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail || 'Voice processing failed.'
      setMessages(prev => [...prev, { role: 'assistant', content: `Sorry: ${detail}` }])
    },
  })

  const handleSend = () => {
    if (!input.trim() || sendMutation.isPending) return
    const prefix = imageFiles.length > 0 ? '🖼️ ' : ''
    setMessages(prev => [...prev, { role: 'user', content: `${prefix}${input}` }])
    sendMutation.mutate(input)
    setInput('')
  }

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Response stopped by user.' }])
    }
  }

  // ── Image attach (multi-image) ──
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    const newFiles = Array.from(files)
    setImageFiles(prev => [...prev, ...newFiles])
    newFiles.forEach(file => {
      const reader = new FileReader()
      reader.onload = (ev) => {
        setImagePreviews(prev => [...prev, ev.target?.result as string])
      }
      reader.readAsDataURL(file)
    })
    e.target.value = '' // allow re-selection
  }

  const removeImage = (idx: number) => {
    setImageFiles(prev => prev.filter((_, i) => i !== idx))
    setImagePreviews(prev => prev.filter((_, i) => i !== idx))
  }

  // ── Voice recording ──
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      audioChunksRef.current = []
      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data) }
      mediaRecorder.onstop = () => {
        stream.getTracks().forEach(t => t.stop())
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        if (audioBlob.size > 5000) {
          setMessages(prev => [...prev, { role: 'user', content: '🎤 Sending voice message...' }])
          voiceMutation.mutate(audioBlob)
        } else {
          setMessages(prev => [...prev, { role: 'assistant', content: 'Recording too short. Please speak for at least 2 seconds.' }])
        }
      }
      mediaRecorder.start()
      mediaRecorderRef.current = mediaRecorder
      setIsRecording(true)
      setRecordingTime(0)
      recordingTimerRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000)
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Microphone access denied. Please allow microphone in browser settings.' }])
    }
  }, [voiceMutation])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      if (recordingTimerRef.current) { clearInterval(recordingTimerRef.current); recordingTimerRef.current = null }
    }
  }, [isRecording])

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])
  useEffect(() => { if (!containerRef.current) return; const ctx = gsap.context(() => { gsap.from('.ta-panel', { y: 30, opacity: 0, duration: 0.6, stagger: 0.15, ease: 'power3.out' }) }, containerRef); return () => ctx.revert() }, [])

  const isPending = sendMutation.isPending || voiceMutation.isPending
  const documents: CourseDoc[] = docsData?.documents || []
  const isImageType = (type: string) => ['image', 'jpg', 'jpeg', 'png', 'webp'].includes(type.toLowerCase())

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div ref={containerRef}>
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-white mb-1 tracking-tight">Teaching Assistant</h2>
        <p className="text-sm text-gray-500">AI-powered learning support across all subjects</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="ta-panel space-y-4">
          {/* Subject selector */}
          <div className="bg-[#13121E] border border-[#2A2840] rounded-2xl p-5 shadow-[0_4px_20px_rgba(0,0,0,0.4)]">
            <h3 className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-3">Subject</h3>
            <div className="space-y-1">{subjects.map(s => (
              <button key={s} onClick={() => setSelectedSubject(s)} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${selectedSubject === s ? 'bg-[#A855F7]/15 text-[#A855F7] border border-[#A855F7]/20' : 'text-gray-400 hover:bg-white/5 hover:text-white'}`}>
                <BookOpen className="w-4 h-4" />{s}
              </button>
            ))}</div>
          </div>

          {/* Upload Course Material button */}
          <button onClick={() => setShowUpload(true)} className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-[#A855F7] to-[#D946EF] text-white font-medium text-sm shadow-lg shadow-purple-900/30 hover:shadow-purple-900/50 transition-all">
            <Upload className="w-4 h-4" /> Upload Course Material
          </button>

          {/* Quick prompts */}
          <div className="bg-[#13121E] border border-[#2A2840] rounded-2xl p-5 shadow-[0_4px_20px_rgba(0,0,0,0.4)]">
            <h3 className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-3">Quick Prompts</h3>
            <div className="space-y-2">{quickPrompts.map((p, i) => (
              <button key={i} onClick={() => { setInput(p); setActiveTab('chat') }} className="w-full text-left px-3 py-2 rounded-lg text-xs text-gray-400 hover:bg-white/5 hover:text-white transition-colors border border-transparent hover:border-white/5">
                <Sparkles className="w-3 h-3 inline mr-1.5 text-[#D946EF]" />{p}
              </button>
            ))}</div>
          </div>
        </div>

        {/* Main area */}
        <div className="ta-panel lg:col-span-3 bg-[#13121E] border border-[#2A2840] rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.4)] flex flex-col h-[650px]">
          {/* Tabs: Chat | Materials */}
          <div className="px-6 py-3 border-b border-white/5 flex items-center gap-6">
            <button onClick={() => setActiveTab('chat')} className={`flex items-center gap-2 text-sm font-medium py-1 border-b-2 transition-all ${activeTab === 'chat' ? 'text-[#A855F7] border-[#A855F7]' : 'text-gray-500 border-transparent hover:text-gray-300'}`}>
              <Sparkles className="w-4 h-4" /> Chat
            </button>
            <button onClick={() => setActiveTab('materials')} className={`flex items-center gap-2 text-sm font-medium py-1 border-b-2 transition-all ${activeTab === 'materials' ? 'text-[#A855F7] border-[#A855F7]' : 'text-gray-500 border-transparent hover:text-gray-300'}`}>
              <FileText className="w-4 h-4" /> Course Materials
              {documents.length > 0 && <span className="ml-1 text-[10px] bg-[#A855F7]/20 text-[#A855F7] px-1.5 py-0.5 rounded-full">{documents.length}</span>}
            </button>
            <div className="ml-auto flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#A855F7] to-[#D946EF] flex items-center justify-center shadow-lg shadow-purple-900/30"><Sparkles className="w-3.5 h-3.5 text-white" /></div>
              <div><p className="text-xs font-semibold text-white">ClaritAI Assistant</p><p className="text-[10px] text-gray-500">{selectedSubject} • Online</p></div>
            </div>
          </div>

          {activeTab === 'chat' ? (
            <>
              {/* Chat messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.map((m, i) => (
                  <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] ${m.role === 'user' ? 'bg-gradient-to-r from-[#A855F7] to-[#D946EF] text-white rounded-2xl rounded-br-md' : 'bg-[#1A1929] border border-white/5 text-gray-300 rounded-2xl rounded-bl-md'}`}>
                      <div className="px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap">{m.content}</div>
                      {m.audioUrl && (
                        <div className="px-4 pb-3 pt-0">
                          <audio controls className="w-full h-8 opacity-80" src={m.audioUrl}>Your browser does not support audio.</audio>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isPending && <div className="flex justify-start"><div className="bg-[#1A1929] border border-white/5 px-4 py-3 rounded-2xl rounded-bl-md"><div className="flex gap-1.5"><span className="w-2 h-2 bg-[#A855F7] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} /><span className="w-2 h-2 bg-[#A855F7] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} /><span className="w-2 h-2 bg-[#A855F7] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} /></div></div></div>}
                <div ref={chatEndRef} />
              </div>

              {/* Image previews (multi-image) */}
              {imagePreviews.length > 0 && (
                <div className="px-6 py-2 border-t border-white/5 flex items-center gap-3 overflow-x-auto">
                  {imagePreviews.map((preview, idx) => (
                    <div key={idx} className="relative flex-shrink-0">
                      <img src={preview} alt="" className="w-16 h-16 rounded-lg object-cover border border-white/10" />
                      <button onClick={() => removeImage(idx)} className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-red-500 text-white flex items-center justify-center text-[10px] hover:bg-red-400 transition-colors">
                        <X className="w-3 h-3" />
                      </button>
                      <p className="text-[9px] text-gray-500 text-center mt-0.5 w-16 truncate">{imageFiles[idx]?.name}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Input area */}
              <div className="px-6 py-4 border-t border-white/5">
                {isRecording ? (
                  <div className="flex items-center gap-3">
                    <div className="flex-1 flex items-center gap-3 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2.5">
                      <span className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
                      <span className="text-sm text-red-400 font-medium">Recording... {recordingTime}s</span>
                    </div>
                    <button onClick={stopRecording} className="px-4 py-2.5 rounded-xl bg-red-500 text-white font-medium text-sm shadow-lg hover:bg-red-600 transition-colors flex items-center gap-2">
                      <StopCircle className="w-4 h-4" /> Stop
                    </button>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <input type="text" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSend()} placeholder={imageFiles.length > 0 ? `Ask about ${imageFiles.length} image(s)...` : "Ask a question..."} className="flex-1 bg-[#0B0B12] border border-white/10 rounded-xl py-2.5 px-4 text-sm text-gray-300 placeholder-gray-600 focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7] transition-all" disabled={isPending} />
                    {/* Image attach (multi) */}
                    <label className={`px-3 py-2.5 rounded-xl border cursor-pointer transition-all ${imageFiles.length > 0 ? 'bg-[#A855F7]/15 border-[#A855F7]/30 text-[#A855F7]' : 'bg-[#1A1929] border-white/10 text-gray-400 hover:text-[#A855F7] hover:border-[#A855F7]/30'}`} title="Attach images">
                      <Image className="w-4 h-4" />
                      {imageFiles.length > 0 && <span className="text-[10px] ml-0.5">{imageFiles.length}</span>}
                      <input type="file" accept="image/*" multiple className="hidden" onChange={handleImageSelect} />
                    </label>
                    {/* Mic */}
                    <button onClick={startRecording} disabled={isPending} className="px-3 py-2.5 rounded-xl bg-[#1A1929] border border-white/10 text-gray-400 hover:text-[#A855F7] hover:border-[#A855F7]/30 disabled:opacity-50 transition-all" title="Record voice">
                      <Mic className="w-4 h-4" />
                    </button>
                    {/* Send / Stop */}
                    {isPending ? (
                      <button onClick={handleStop} className="px-4 py-2.5 rounded-xl bg-red-500 text-white font-medium text-sm shadow-lg hover:bg-red-600 transition-colors flex items-center gap-2" title="Stop generating">
                        <StopCircle className="w-4 h-4" /> Stop
                      </button>
                    ) : (
                      <button onClick={handleSend} disabled={!input.trim()} className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#A855F7] to-[#D946EF] text-white font-medium text-sm disabled:opacity-50 transition-opacity shadow-lg shadow-purple-900/30 hover:shadow-purple-900/50">
                        <Send className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : (
            /* ── Materials tab ── */
            <div className="flex-1 overflow-y-auto p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-white">Course Materials — {selectedSubject}</h3>
                  <p className="text-xs text-gray-500 mt-1">Upload PDFs, slides, videos, or YouTube links to enhance AI responses</p>
                </div>
                <button onClick={() => setShowUpload(true)} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#A855F7]/10 border border-[#A855F7]/20 text-[#A855F7] text-sm font-medium hover:bg-[#A855F7]/20 transition-all">
                  <Upload className="w-4 h-4" /> Upload
                </button>
              </div>

              {docsLoading ? (
                <div className="flex items-center justify-center py-20"><div className="w-8 h-8 border-2 border-[#A855F7] border-t-transparent rounded-full animate-spin" /></div>
              ) : documents.length === 0 ? (
                <div className="text-center py-20">
                  <FileText className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-400 text-sm">No materials uploaded for {selectedSubject} yet</p>
                  <p className="text-gray-600 text-xs mt-1">Upload PDFs, slides, or videos to enable RAG-powered answers</p>
                  <button onClick={() => setShowUpload(true)} className="mt-4 px-4 py-2 rounded-xl bg-[#A855F7]/10 border border-[#A855F7]/20 text-[#A855F7] text-sm font-medium hover:bg-[#A855F7]/20 transition-all">Upload First Document</button>
                </div>
              ) : (
                <div className="space-y-3">
                  {documents.map((doc: CourseDoc) => (
                    <div key={doc.document_id} className="flex items-center gap-4 p-4 bg-[#1A1929] border border-white/5 rounded-xl hover:border-white/10 transition-all group">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold ${doc.document_type === 'pdf' ? 'bg-red-500/10 text-red-400' :
                          doc.document_type === 'pptx' ? 'bg-orange-500/10 text-orange-400' :
                            doc.document_type === 'video' ? 'bg-blue-500/10 text-blue-400' :
                              doc.document_type === 'youtube' ? 'bg-red-500/10 text-red-400' :
                                isImageType(doc.document_type) ? 'bg-emerald-500/10 text-emerald-400' :
                                  'bg-gray-500/10 text-gray-400'
                        }`}>
                        {doc.document_type === 'youtube' ? <Youtube className="w-5 h-5" /> : isImageType(doc.document_type) ? <Image className="w-5 h-5" /> : <FileText className="w-5 h-5" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">{doc.title}</p>
                        <p className="text-[11px] text-gray-500 mt-0.5">
                          {doc.document_type.toUpperCase()} • {doc.chunk_count} chunks • {formatSize(doc.file_size)} •
                          <span className={`ml-1 ${doc.status === 'indexed' ? 'text-green-400' : doc.status === 'error' ? 'text-red-400' : 'text-yellow-400'}`}>
                            {doc.status}
                          </span>
                        </p>
                      </div>
                      <button onClick={() => deleteMutation.mutate(doc.document_id)} className="opacity-0 group-hover:opacity-100 p-2 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-all" title="Delete">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Upload Modal (multi-file) ── */}
      {showUpload && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => !isUploading && resetUploadModal()}>
          <div className="bg-[#13121E] border border-[#2A2840] rounded-2xl p-6 w-full max-w-lg shadow-2xl max-h-[85vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-white">Upload Course Material</h3>
              <button onClick={() => !isUploading && resetUploadModal()} className="text-gray-500 hover:text-white"><X className="w-5 h-5" /></button>
            </div>

            <div className="space-y-4 overflow-y-auto flex-1 pr-1">
              {/* Document type */}
              <div>
                <label className="text-xs text-gray-400 font-medium block mb-1.5">Document Type</label>
                <div className="grid grid-cols-4 gap-2">
                  {docTypes.map(dt => (
                    <button key={dt.value} onClick={() => { setUploadDocType(dt.value); setUploadFiles([]) }} disabled={isUploading} className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${uploadDocType === dt.value ? 'bg-[#A855F7]/15 text-[#A855F7] border border-[#A855F7]/30' : 'bg-[#1A1929] text-gray-400 border border-white/5 hover:border-white/10'} disabled:opacity-50`}>
                      {dt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Title (shown only for single file or YouTube) */}
              {(uploadFiles.length <= 1 || uploadDocType === 'youtube') && (
                <div>
                  <label className="text-xs text-gray-400 font-medium block mb-1.5">Title</label>
                  <input type="text" value={uploadTitle} onChange={e => setUploadTitle(e.target.value)} placeholder="e.g. Chapter 3 - Thermodynamics" className="w-full bg-[#0B0B12] border border-white/10 rounded-xl py-2.5 px-4 text-sm text-gray-300 placeholder-gray-600 focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7]" disabled={isUploading} />
                </div>
              )}

              {/* YouTube URL or File picker */}
              {uploadDocType === 'youtube' ? (
                <div>
                  <label className="text-xs text-gray-400 font-medium block mb-1.5">YouTube URL</label>
                  <input type="url" value={uploadYoutubeUrl} onChange={e => setUploadYoutubeUrl(e.target.value)} placeholder="https://www.youtube.com/watch?v=..." className="w-full bg-[#0B0B12] border border-white/10 rounded-xl py-2.5 px-4 text-sm text-gray-300 placeholder-gray-600 focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7]" disabled={isUploading} />
                </div>
              ) : (
                <div>
                  <label className="text-xs text-gray-400 font-medium block mb-1.5">Files {uploadFiles.length > 0 && <span className="text-[#A855F7]">({uploadFiles.length} selected)</span>}</label>
                  <label className="flex flex-col items-center justify-center w-full h-20 border-2 border-dashed border-white/10 rounded-xl cursor-pointer hover:border-[#A855F7]/30 transition-all bg-[#0B0B12]">
                    <Upload className="w-5 h-5 text-gray-500 mb-1" />
                    <p className="text-xs text-gray-500">Click to select files (multiple allowed)</p>
                    <p className="text-[10px] text-gray-600">{docTypes.find(d => d.value === uploadDocType)?.accept || 'Any file'}</p>
                    <input type="file" className="hidden" multiple accept={docTypes.find(d => d.value === uploadDocType)?.accept} onChange={handleFilesSelected} disabled={isUploading} />
                  </label>
                </div>
              )}

              {/* File list with status + thumbnails */}
              {uploadFiles.length > 0 && (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {uploadFiles.map((entry, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-2.5 bg-[#1A1929] border border-white/5 rounded-lg">
                      {entry.preview ? (
                        <img src={entry.preview} alt="" className="w-10 h-10 rounded-lg object-cover border border-white/10 flex-shrink-0" />
                      ) : (
                        <div className="w-10 h-10 rounded-lg bg-[#A855F7]/10 flex items-center justify-center flex-shrink-0">
                          <FileText className="w-4 h-4 text-[#A855F7]" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-gray-300 truncate">{entry.file.name}</p>
                        <p className="text-[10px] text-gray-500">{formatSize(entry.file.size)}</p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                          entry.status === 'queued' ? 'bg-gray-500/10 text-gray-400' :
                          entry.status === 'uploading' ? 'bg-yellow-500/10 text-yellow-400' :
                          entry.status === 'indexed' ? 'bg-green-500/10 text-green-400' :
                          'bg-red-500/10 text-red-400'
                        }`}>
                          {entry.status === 'uploading' && <span className="inline-block w-2 h-2 border border-yellow-400 border-t-transparent rounded-full animate-spin mr-1" />}
                          {entry.status}
                        </span>
                        {!isUploading && entry.status === 'queued' && (
                          <button onClick={() => setUploadFiles(prev => prev.filter((_, i) => i !== idx))} className="text-gray-500 hover:text-red-400">
                            <X className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                      {entry.error && <p className="text-[10px] text-red-400 w-full mt-1">{entry.error}</p>}
                    </div>
                  ))}
                </div>
              )}

              {/* Description */}
              <div>
                <label className="text-xs text-gray-400 font-medium block mb-1.5">Description (optional)</label>
                <input type="text" value={uploadDesc} onChange={e => setUploadDesc(e.target.value)} placeholder="Brief description..." className="w-full bg-[#0B0B12] border border-white/10 rounded-xl py-2.5 px-4 text-sm text-gray-300 placeholder-gray-600 focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7]" disabled={isUploading} />
              </div>

              {/* Subject indicator */}
              <div className="flex items-center gap-2 px-3 py-2 bg-[#A855F7]/5 border border-[#A855F7]/10 rounded-lg">
                <BookOpen className="w-4 h-4 text-[#A855F7]" />
                <span className="text-xs text-gray-400">Will be indexed for: <span className="text-[#A855F7] font-medium">{selectedSubject}</span></span>
              </div>

              {/* Upload button */}
              <button
                onClick={handleUploadAll}
                disabled={isUploading || (uploadDocType !== 'youtube' && uploadFiles.length === 0) || (uploadDocType === 'youtube' && !uploadYoutubeUrl.trim())}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-[#A855F7] to-[#D946EF] text-white font-medium text-sm disabled:opacity-50 transition-opacity shadow-lg shadow-purple-900/30 flex items-center justify-center gap-2"
              >
                {isUploading ? (
                  <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Indexing...</>
                ) : (
                  <><Upload className="w-4 h-4" /> Upload & Index {uploadFiles.length > 1 ? `(${uploadFiles.length} files)` : ''}</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
