'use client'

import { useEffect, useRef, useState } from 'react'
import { ChevronDown, Copy, Menu, Mic, MoreHorizontal, PanelLeft, Plus, Send, Square, Volume2 } from 'lucide-react'

type QuerySource = 'text' | 'voice'
type ConversationTurn = {
  id: string
  query: string
  source: QuerySource
  response?: string
  pending?: boolean
}

type VoiceResponse = {
  query?: string
  transcript: string
  input_type?: QuerySource
  response: string
  audio_url?: string | null
  session_id?: string
}

type SessionHistory = {
  session_id: string
  turns: Array<{ query: string; response: string; input_type: QuerySource }>
}

type AuthUser = {
  email: string
  plan: 'free' | 'plus' | 'pro'
  daily_limit: number | null
  used_today: number
  two_factor_enabled: boolean
  guest?: boolean
  trial_enabled?: boolean
  trial_requests_used?: number
  trial_requests_limit?: number
}

type AuthMode = 'login' | 'signup' | 'otp-request' | 'otp-verify' | 'two-factor'

export default function Home() {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [history, setHistory] = useState<ConversationTurn[]>([])
  const [textInput, setTextInput] = useState('')
  const [isReading, setIsReading] = useState(false)
  const [error, setError] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [authReady, setAuthReady] = useState(false)
  const [authMode, setAuthMode] = useState<AuthMode>('login')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authCode, setAuthCode] = useState('')
  const [pendingLoginToken, setPendingLoginToken] = useState('')
  const [user, setUser] = useState<AuthUser | null>(null)
  const [twoFactorSecret, setTwoFactorSecret] = useState('')
  const [twoFactorSetupCode, setTwoFactorSetupCode] = useState('')
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const sessionIdRef = useRef<string | null>(null)

  useEffect(() => () => window.speechSynthesis?.cancel(), [])
  useEffect(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), [history, isProcessing])
  useEffect(() => {
    const savedToken = window.localStorage.getItem('voicegpt-access-token')
    if (!savedToken) { setAuthReady(true); return }
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/me`, { headers: { Authorization: `Bearer ${savedToken}` } })
      .then((result) => result.ok ? result.json() : Promise.reject(new Error('Session expired')))
      .then((currentUser: AuthUser) => { setAccessToken(savedToken); setUser(currentUser) })
      .catch(() => window.localStorage.removeItem('voicegpt-access-token'))
      .finally(() => setAuthReady(true))
  }, [])
  useEffect(() => {
    const savedSessionId = window.localStorage.getItem('voicegpt-session-id')
    if (!savedSessionId) return

    sessionIdRef.current = savedSessionId
    fetch(`${apiUrl()}/api/voice/session/${encodeURIComponent(savedSessionId)}`)
      .then((result) => result.ok ? result.json() : Promise.reject(new Error('Conversation not found')))
      .then((data: SessionHistory) => setHistory(data.turns.map((turn) => ({
        id: createTurnId(), query: turn.query, response: turn.response,
        source: turn.input_type,
      }))))
      .catch(() => window.localStorage.removeItem('voicegpt-session-id'))
  }, [])
  const createTurnId = () => `${Date.now()}-${Math.random().toString(36).slice(2)}`
  const addPendingTurn = (query: string, source: QuerySource) => {
    const id = createTurnId()
    setHistory((previous) => [...previous, { id, query, source, pending: true }])
    return id
  }
  const completeTurn = (id: string, data: VoiceResponse, fallbackSource: QuerySource) => {
    setHistory((previous) => previous.map((turn) => turn.id === id ? {
      ...turn,
      query: data.query || data.transcript,
      source: data.input_type || fallbackSource,
      response: data.response,
      pending: false,
    } : turn))
  }
  const removeTurn = (id: string) => setHistory((previous) => previous.filter((turn) => turn.id !== id))
  const apiUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const rememberSession = (sessionId?: string) => {
    if (!sessionId) return
    sessionIdRef.current = sessionId
    window.localStorage.setItem('voicegpt-session-id', sessionId)
  }
  const finishAuthentication = (data: { access_token: string; user: AuthUser }) => {
    window.localStorage.setItem('voicegpt-access-token', data.access_token)
    setAccessToken(data.access_token)
    setUser(data.user)
    setError('')
  }
  const submitAuthentication = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    const baseUrl = apiUrl()
    try {
      if (authMode === 'otp-request') {
        const result = await fetch(`${baseUrl}/api/auth/login/otp/request`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: authEmail }) })
        const data = await result.json()
        if (!result.ok) throw new Error(data.detail || 'Could not send sign-in code')
        setAuthMode('otp-verify')
        setError(data.development_otp ? `Development sign-in code: ${data.development_otp}` : 'A sign-in code has been sent.')
        return
      }
      const endpoint = authMode === 'signup' ? '/api/auth/register' : authMode === 'otp-verify' ? '/api/auth/login/otp/verify' : authMode === 'two-factor' ? '/api/auth/login/2fa' : '/api/auth/login'
      const payload = authMode === 'otp-verify' ? { email: authEmail, code: authCode } : authMode === 'two-factor' ? { login_token: pendingLoginToken, code: authCode } : { email: authEmail, password: authPassword }
      const result = await fetch(`${baseUrl}${endpoint}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      const data = await result.json()
      if (!result.ok) throw new Error(data.detail || 'Authentication failed')
      if (data.requires_two_factor) { setPendingLoginToken(data.login_token); setAuthMode('two-factor'); return }
      finishAuthentication(data)
    } catch (authError) { setError(authError instanceof Error ? authError.message : 'Authentication failed') }
  }
  const logout = () => { window.localStorage.removeItem('voicegpt-access-token'); window.localStorage.removeItem('voicegpt-session-id'); window.localStorage.removeItem('voicegpt-guest'); sessionIdRef.current = null; setAccessToken(null); setUser(null); setHistory([]) }
  const startTwoFactorSetup = async () => {
    try {
      const result = await fetch(`${apiUrl()}/api/auth/2fa/setup`, { method: 'POST', headers: { Authorization: `Bearer ${accessToken}` } })
      const data = await result.json()
      if (!result.ok) throw new Error(data.detail || 'Could not start two-factor setup')
      setTwoFactorSecret(data.secret)
      setError('')
    } catch (setupError) { setError(setupError instanceof Error ? setupError.message : 'Could not start two-factor setup') }
  }
  const confirmTwoFactorSetup = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    try {
      const result = await fetch(`${apiUrl()}/api/auth/2fa/confirm`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` }, body: JSON.stringify({ code: twoFactorSetupCode }) })
      const data = await result.json()
      if (!result.ok) throw new Error(data.detail || 'Could not enable two-factor authentication')
      setUser((currentUser) => currentUser ? { ...currentUser, two_factor_enabled: true } : currentUser)
      setTwoFactorSecret('')
      setTwoFactorSetupCode('')
    } catch (setupError) { setError(setupError instanceof Error ? setupError.message : 'Could not enable two-factor authentication') }
  }

  const playAudioResponse = (audioUrl: string, baseUrl: string) => {
    if (!audioRef.current) return
    audioRef.current.src = new URL(audioUrl, `${baseUrl}/`).toString()
    audioRef.current.onplay = () => setIsPlaying(true)
    audioRef.current.onended = audioRef.current.onerror = () => setIsPlaying(false)
    audioRef.current.play().catch(() => setIsPlaying(false))
  }
  const processAudio = async (audioBlob: Blob, turnId: string) => {
    try {
      const formData = new FormData(); formData.append('audio', audioBlob)
      if (sessionIdRef.current) formData.append('session_id', sessionIdRef.current)
      const baseUrl = apiUrl(); const result = await fetch(`${baseUrl}/api/voice/process`, { method: 'POST', headers: { Authorization: `Bearer ${accessToken}` }, body: formData })
      if (!result.ok) throw new Error('Failed to process audio')
      const data: VoiceResponse = await result.json(); rememberSession(data.session_id); completeTurn(turnId, data, 'voice')
      if (data.audio_url) playAudioResponse(data.audio_url, baseUrl)
    } catch (err) { removeTurn(turnId); setError('Failed to process audio. Please try again.'); console.error(err) } finally { setIsProcessing(false) }
  }
  const startRecording = async () => {
    try {
      setError(''); const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); const recorder = new MediaRecorder(stream)
      mediaRecorderRef.current = recorder; audioChunksRef.current = []
      recorder.ondataavailable = (event) => { if (event.data.size > 0) audioChunksRef.current.push(event.data) }
      recorder.onstop = async () => {
        const turnId = addPendingTurn('Transcribing your voice message…', 'voice')
        await processAudio(new Blob(audioChunksRef.current, { type: 'audio/webm' }), turnId)
        stream.getTracks().forEach((track) => track.stop())
      }
      recorder.start(); setIsRecording(true)
    } catch (err) { setError('Microphone access was blocked. Please grant permission and try again.'); console.error(err) }
  }
  const stopRecording = () => { if (mediaRecorderRef.current && isRecording) { mediaRecorderRef.current.stop(); setIsRecording(false); setIsProcessing(true) } }
  const processText = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const text = textInput.trim(); if (!text || isProcessing) return
    setError(''); setTextInput(''); setIsProcessing(true)
    const turnId = addPendingTurn(text, 'text')
    try {
      const baseUrl = apiUrl(); const result = await fetch(`${baseUrl}/api/voice/text`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` }, body: JSON.stringify({ text, session_id: sessionIdRef.current }) })
      if (!result.ok) throw new Error('Failed to process text')
      const data: VoiceResponse = await result.json(); rememberSession(data.session_id); completeTurn(turnId, data, 'text')
      if (data.audio_url) playAudioResponse(data.audio_url, baseUrl)
    } catch (err) { removeTurn(turnId); setTextInput(text); setError('Failed to send message. Please try again.'); console.error(err) } finally { setIsProcessing(false) }
  }
  const readResponse = (text: string) => {
    if (!window.speechSynthesis) return
    if (isReading) { window.speechSynthesis.cancel(); setIsReading(false); return }
    const utterance = new SpeechSynthesisUtterance(text); utterance.onstart = () => setIsReading(true); utterance.onend = utterance.onerror = () => setIsReading(false)
    window.speechSynthesis.cancel(); window.speechSynthesis.speak(utterance)
  }
  const newChat = () => { sessionIdRef.current = null; window.localStorage.removeItem('voicegpt-session-id'); setHistory([]); setError(''); setTextInput(''); setSidebarOpen(false) }

  if (!authReady) return <main className="auth-shell"><p>Loading VoiceGPT…</p></main>
  if (!accessToken) return <main className="auth-shell"><section className="auth-card"><div className="welcome-logo">✦</div><h1>{authMode === 'signup' ? 'Create your account' : authMode === 'otp-request' || authMode === 'otp-verify' ? 'Sign in with a code' : authMode === 'two-factor' ? 'Enter your security code' : 'Welcome back'}</h1><p>{authMode === 'two-factor' ? 'Open your authenticator app and enter the six-digit code.' : 'Sign in to use VoiceGPT.'}</p>{error && <p className="error-message">{error}</p>}{authMode === 'login' && <button className="try-button" onClick={async () => { try { const result = await fetch(`${apiUrl()}/api/auth/guest/start`, { method: 'POST' }); const data = await result.json(); if (!result.ok) throw new Error(data.detail || 'Could not start guest session'); window.localStorage.setItem('voicegpt-access-token', data.access_token); window.localStorage.setItem('voicegpt-guest', 'true'); setAccessToken(data.access_token); setUser({ email: 'Guest', plan: 'free', daily_limit: data.requests_limit, used_today: 0, two_factor_enabled: false }); setError('') } catch (guestError) { setError(guestError instanceof Error ? guestError.message : 'Could not start guest session') } }}>Try for Free (No Sign-up Required)</button>}<form className="auth-form" onSubmit={submitAuthentication}>{authMode !== 'two-factor' && <input type="email" value={authEmail} onChange={(event) => setAuthEmail(event.target.value)} placeholder="Email address" autoComplete="email" required />}{(authMode === 'login' || authMode === 'signup') && <input type="password" value={authPassword} onChange={(event) => setAuthPassword(event.target.value)} placeholder="Password (8+ characters)" autoComplete={authMode === 'signup' ? 'new-password' : 'current-password'} minLength={8} required />}{(authMode === 'otp-verify' || authMode === 'two-factor') && <input value={authCode} onChange={(event) => setAuthCode(event.target.value.replace(/\D/g, '').slice(0, 6))} placeholder="Six-digit code" inputMode="numeric" autoComplete="one-time-code" required />}<button type="submit" className="auth-submit">{authMode === 'signup' ? 'Create account' : authMode === 'otp-request' ? 'Send sign-in code' : authMode === 'otp-verify' || authMode === 'two-factor' ? 'Verify code' : 'Sign in'}</button></form>{authMode !== 'two-factor' && <div className="auth-links">{authMode === 'login' && <><button onClick={() => { setAuthMode('signup'); setError('') }}>Create account</button><button onClick={() => { setAuthMode('otp-request'); setError('') }}>Use a sign-in code</button></>}{authMode === 'signup' && <button onClick={() => { setAuthMode('login'); setError('') }}>Already have an account?</button>}{(authMode === 'otp-request' || authMode === 'otp-verify') && <button onClick={() => { setAuthMode('login'); setError('') }}>Use password instead</button>}</div>}<small>Free: 10 requests/day · Plus: 100/day · Pro: unlimited</small></section></main>

  return <main className="chat-shell">
    <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <div className="sidebar-top"><button className="brand" onClick={newChat}><span className="brand-mark">✦</span><span>VoiceGPT</span></button><button className="icon-button close-sidebar" onClick={() => setSidebarOpen(false)}><PanelLeft size={19} /></button></div>
      <button className="new-chat" onClick={newChat}><Plus size={18} /> New chat</button>
      <nav className="chat-list"><p className="nav-label">Today</p><button className="chat-item active"><span>Voice conversation</span><MoreHorizontal size={18} /></button><p className="nav-label">Previous 7 days</p><button className="chat-item"><span>Getting started with AI</span></button><button className="chat-item"><span>Ideas and notes</span></button></nav>
      <div className="sidebar-footer"><div className="account"><span className="avatar">{user?.email.slice(0, 1).toUpperCase()}</span><span className="account-details"><strong>{user?.email}</strong><small>{user?.guest ? 'Guest · 5 free requests' : user?.trial_enabled ? `Trial · ${user.trial_requests_used}/${user.trial_requests_limit} used` : `${user?.plan} · ${user?.daily_limit === null ? 'Unlimited' : `${user?.used_today}/${user?.daily_limit} today`}`}</small></span>{user?.guest ? <button className="logout-button" onClick={() => { logout(); setAuthMode('signup') }}>Sign up</button> : <button className="logout-button" onClick={logout}>Log out</button>}</div>{user && !user.guest && !user.two_factor_enabled && (twoFactorSecret ? <form className="two-factor-setup" onSubmit={confirmTwoFactorSetup}><p>Add this secret to your authenticator app: <code>{twoFactorSecret}</code></p><input value={twoFactorSetupCode} onChange={(event) => setTwoFactorSetupCode(event.target.value.replace(/\D/g, '').slice(0, 6))} placeholder="Six-digit code" inputMode="numeric" required /><button type="submit">Enable 2FA</button></form> : <button className="two-factor-button" onClick={startTwoFactorSetup}>Set up two-factor authentication</button>)}</div>
    </aside>
    {sidebarOpen && <button className="sidebar-scrim" onClick={() => setSidebarOpen(false)} aria-label="Close navigation" />}
    <section className="chat-main">
      <header className="chat-header"><button className="icon-button mobile-menu" onClick={() => setSidebarOpen(true)}><Menu size={21} /></button><button className="model-switcher">VoiceGPT <ChevronDown size={16} /></button></header>
      <div className="conversation">{history.length === 0 ? <div className="welcome"><div className="welcome-logo">✦</div><h1>How can I help you today?</h1><p>Type a message or use the microphone to start a voice conversation.</p></div> : <div className="messages">{history.map((turn) => <div className="turn" key={turn.id}><article className="message user-message"><div className="message-avatar user-avatar">M</div><div className="user-query"><span className="query-source">{turn.source === 'voice' ? 'Spoken query' : 'Typed query'}</span><p>{turn.query}</p></div></article>{turn.response ? <article className="message assistant-message"><div className="message-avatar assistant-avatar">✦</div><div className="message-content"><p>{turn.response}</p><div className="message-actions"><button onClick={() => navigator.clipboard?.writeText(turn.response!)} aria-label="Copy response"><Copy size={15} /></button><button onClick={() => readResponse(turn.response!)} aria-label={isReading ? 'Stop reading' : 'Read response aloud'}><Volume2 className={isReading ? 'speaking' : ''} size={16} /></button></div></div></article> : <article className="message assistant-message"><div className="message-avatar assistant-avatar">✦</div><div className="thinking" aria-label="Generating response"><i /><i /><i /></div></article>}</div>)}<div ref={messagesEndRef} /></div>}</div>
      <div className="composer-area">{error && <p className="error-message">{error}</p>}{isRecording && <p className="recording-status"><span /> Listening… tap stop when you&apos;re done</p>}<form className="composer" onSubmit={processText}><textarea value={textInput} onChange={(event) => setTextInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit() } }} placeholder="Message VoiceGPT" rows={1} disabled={isProcessing} aria-label="Message VoiceGPT" /><div className="composer-actions"><span className="voice-state">{isPlaying ? 'Speaking…' : isProcessing ? 'Thinking…' : ''}</span><button type="button" className={`round-action ${isRecording ? 'recording' : ''}`} onClick={isRecording ? stopRecording : startRecording} disabled={isProcessing} aria-label={isRecording ? 'Stop recording' : 'Start voice recording'}>{isRecording ? <Square size={15} fill="currentColor" /> : <Mic size={19} />}</button><button type="submit" className="send-button" disabled={!textInput.trim() || isProcessing} aria-label="Send message"><Send size={18} /></button></div></form><p className="disclaimer">VoiceGPT can make mistakes. Check important info.</p></div>
    </section><audio ref={audioRef} className="hidden" />
  </main>
}
