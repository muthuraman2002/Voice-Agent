'use client'

import { useEffect, useRef, useState } from 'react'
import { ChevronDown, Copy, Menu, Mic, MoreHorizontal, PanelLeft, Plus, Send, Square, Volume2 } from 'lucide-react'

type ConversationTurn = { transcript: string; response: string }

export default function Home() {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [history, setHistory] = useState<ConversationTurn[]>([])
  const [textInput, setTextInput] = useState('')
  const [isReading, setIsReading] = useState(false)
  const [error, setError] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => () => window.speechSynthesis?.cancel(), [])
  useEffect(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), [history, isProcessing])
  const addTurn = (transcript: string, response: string) => setHistory((previous) => [...previous, { transcript, response }])
  const apiUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const playAudioResponse = (audioUrl: string, baseUrl: string) => {
    if (!audioRef.current) return
    audioRef.current.src = new URL(audioUrl, `${baseUrl}/`).toString()
    audioRef.current.onplay = () => setIsPlaying(true)
    audioRef.current.onended = audioRef.current.onerror = () => setIsPlaying(false)
    audioRef.current.play().catch(() => setIsPlaying(false))
  }
  const processAudio = async (audioBlob: Blob) => {
    try {
      const formData = new FormData(); formData.append('audio', audioBlob)
      const baseUrl = apiUrl(); const result = await fetch(`${baseUrl}/api/voice/process`, { method: 'POST', body: formData })
      if (!result.ok) throw new Error('Failed to process audio')
      const data = await result.json(); addTurn(data.transcript, data.response)
      if (data.audio_url) playAudioResponse(data.audio_url, baseUrl)
    } catch (err) { setError('Failed to process audio. Please try again.'); console.error(err) } finally { setIsProcessing(false) }
  }
  const startRecording = async () => {
    try {
      setError(''); const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); const recorder = new MediaRecorder(stream)
      mediaRecorderRef.current = recorder; audioChunksRef.current = []
      recorder.ondataavailable = (event) => { if (event.data.size > 0) audioChunksRef.current.push(event.data) }
      recorder.onstop = async () => { await processAudio(new Blob(audioChunksRef.current, { type: 'audio/webm' })); stream.getTracks().forEach((track) => track.stop()) }
      recorder.start(); setIsRecording(true)
    } catch (err) { setError('Microphone access was blocked. Please grant permission and try again.'); console.error(err) }
  }
  const stopRecording = () => { if (mediaRecorderRef.current && isRecording) { mediaRecorderRef.current.stop(); setIsRecording(false); setIsProcessing(true) } }
  const processText = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const text = textInput.trim(); if (!text || isProcessing) return
    setError(''); setTextInput(''); setIsProcessing(true)
    try {
      const baseUrl = apiUrl(); const result = await fetch(`${baseUrl}/api/voice/text`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) })
      if (!result.ok) throw new Error('Failed to process text')
      const data = await result.json(); addTurn(data.transcript, data.response)
      if (data.audio_url) playAudioResponse(data.audio_url, baseUrl)
    } catch (err) { setTextInput(text); setError('Failed to send message. Please try again.'); console.error(err) } finally { setIsProcessing(false) }
  }
  const readResponse = (text: string) => {
    if (!window.speechSynthesis) return
    if (isReading) { window.speechSynthesis.cancel(); setIsReading(false); return }
    const utterance = new SpeechSynthesisUtterance(text); utterance.onstart = () => setIsReading(true); utterance.onend = utterance.onerror = () => setIsReading(false)
    window.speechSynthesis.cancel(); window.speechSynthesis.speak(utterance)
  }
  const newChat = () => { setHistory([]); setError(''); setTextInput(''); setSidebarOpen(false) }

  return <main className="chat-shell">
    <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <div className="sidebar-top"><button className="brand" onClick={newChat}><span className="brand-mark">✦</span><span>VoiceGPT</span></button><button className="icon-button close-sidebar" onClick={() => setSidebarOpen(false)}><PanelLeft size={19} /></button></div>
      <button className="new-chat" onClick={newChat}><Plus size={18} /> New chat</button>
      <nav className="chat-list"><p className="nav-label">Today</p><button className="chat-item active"><span>Voice conversation</span><MoreHorizontal size={18} /></button><p className="nav-label">Previous 7 days</p><button className="chat-item"><span>Getting started with AI</span></button><button className="chat-item"><span>Ideas and notes</span></button></nav>
      <div className="sidebar-footer"><button className="account"><span className="avatar">M</span><span>My account</span><MoreHorizontal size={18} /></button></div>
    </aside>
    {sidebarOpen && <button className="sidebar-scrim" onClick={() => setSidebarOpen(false)} aria-label="Close navigation" />}
    <section className="chat-main">
      <header className="chat-header"><button className="icon-button mobile-menu" onClick={() => setSidebarOpen(true)}><Menu size={21} /></button><button className="model-switcher">VoiceGPT <ChevronDown size={16} /></button></header>
      <div className="conversation">{history.length === 0 ? <div className="welcome"><div className="welcome-logo">✦</div><h1>How can I help you today?</h1><p>Type a message or use the microphone to start a voice conversation.</p></div> : <div className="messages">{history.map((turn, index) => <div className="turn" key={`${index}-${turn.transcript}`}><article className="message user-message"><div className="message-avatar user-avatar">M</div><p>{turn.transcript}</p></article><article className="message assistant-message"><div className="message-avatar assistant-avatar">✦</div><div className="message-content"><p>{turn.response}</p><div className="message-actions"><button onClick={() => navigator.clipboard?.writeText(turn.response)} aria-label="Copy response"><Copy size={15} /></button><button onClick={() => readResponse(turn.response)} aria-label={isReading ? 'Stop reading' : 'Read response aloud'}><Volume2 className={isReading ? 'speaking' : ''} size={16} /></button></div></div></article></div>)}{isProcessing && <article className="message assistant-message"><div className="message-avatar assistant-avatar">✦</div><div className="thinking"><i /><i /><i /></div></article>}<div ref={messagesEndRef} /></div>}</div>
      <div className="composer-area">{error && <p className="error-message">{error}</p>}{isRecording && <p className="recording-status"><span /> Listening… tap stop when you&apos;re done</p>}<form className="composer" onSubmit={processText}><textarea value={textInput} onChange={(event) => setTextInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit() } }} placeholder="Message VoiceGPT" rows={1} disabled={isProcessing} aria-label="Message VoiceGPT" /><div className="composer-actions"><span className="voice-state">{isPlaying ? 'Speaking…' : isProcessing ? 'Thinking…' : ''}</span><button type="button" className={`round-action ${isRecording ? 'recording' : ''}`} onClick={isRecording ? stopRecording : startRecording} disabled={isProcessing} aria-label={isRecording ? 'Stop recording' : 'Start voice recording'}>{isRecording ? <Square size={15} fill="currentColor" /> : <Mic size={19} />}</button><button type="submit" className="send-button" disabled={!textInput.trim() || isProcessing} aria-label="Send message"><Send size={18} /></button></div></form><p className="disclaimer">VoiceGPT can make mistakes. Check important info.</p></div>
    </section><audio ref={audioRef} className="hidden" />
  </main>
}
