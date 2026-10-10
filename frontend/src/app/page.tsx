'use client'

import { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Loader2, Volume2 } from 'lucide-react'

type ConversationTurn = {
  transcript: string
  response: string
}

export default function Home() {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')
  const [history, setHistory] = useState<ConversationTurn[]>([])
  const [textInput, setTextInput] = useState('')
  const [isReading, setIsReading] = useState(false)
  const [error, setError] = useState('')
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    return () => {
      // Do not leave speech playing after navigating away from the page.
      window.speechSynthesis?.cancel()
    }
  }, [])

  const startRecording = async () => {
    try {
      setError('')
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorderRef.current = new MediaRecorder(stream)
      audioChunksRef.current = []

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        await processAudio(audioBlob)
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorderRef.current.start()
      setIsRecording(true)
    } catch (err) {
      setError('Failed to access microphone. Please grant permission.')
      console.error('Error accessing microphone:', err)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setIsProcessing(true)
    }
  }

  const processAudio = async (audioBlob: Blob) => {
    try {
      const formData = new FormData()
      formData.append('audio', audioBlob)

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      // Send audio to backend for STT → LLM → TTS
      const response = await fetch(`${apiUrl}/api/voice/process`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to process audio')
      }

      const data = await response.json()
      setTranscript(data.transcript)
      setResponse(data.response)
      setHistory((previous) => [
        ...previous,
        { transcript: data.transcript, response: data.response },
      ])

      // Play audio response if available
      if (data.audio_url) {
        playAudioResponse(data.audio_url, apiUrl)
      }
    } catch (err) {
      setError('Failed to process audio. Please try again.')
      console.error('Error processing audio:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  const processText = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const text = textInput.trim()
    if (!text || isProcessing) return

    setError('')
    setIsProcessing(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const result = await fetch(`${apiUrl}/api/voice/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })

      if (!result.ok) {
        throw new Error('Failed to process text')
      }

      const data = await result.json()
      setTranscript(data.transcript)
      setResponse(data.response)
      setHistory((previous) => [
        ...previous,
        { transcript: data.transcript, response: data.response },
      ])
      setTextInput('')

      if (data.audio_url) {
        playAudioResponse(data.audio_url, apiUrl)
      }
    } catch (err) {
      setError('Failed to send text. Please try again.')
      console.error('Error processing text:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  const playAudioResponse = (audioUrl: string, apiUrl: string) => {
    if (audioRef.current) {
      // The API returns a relative /static/audio URL.
      audioRef.current.src = new URL(audioUrl, `${apiUrl}/`).toString()
      audioRef.current.onplay = () => setIsPlaying(true)
      audioRef.current.onended = () => setIsPlaying(false)
      audioRef.current.onerror = () => setIsPlaying(false)
      audioRef.current.play().catch(() => setIsPlaying(false))
    }
  }

  const readResponse = () => {
    if (!response || typeof window === 'undefined' || !window.speechSynthesis) {
      return
    }

    if (isReading) {
      window.speechSynthesis.cancel()
      setIsReading(false)
      return
    }

    const utterance = new SpeechSynthesisUtterance(response)
    utterance.lang = 'en-US'
    utterance.onstart = () => setIsReading(true)
    utterance.onend = () => setIsReading(false)
    utterance.onerror = () => setIsReading(false)
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utterance)
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-white mb-4">
              AI Voice Agent
            </h1>
            <p className="text-xl text-gray-300">
              Speak naturally and converse with AI
            </p>
          </div>

          {/* Voice Interface */}
          <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 mb-8 border border-white/20">
            <div className="flex flex-col items-center justify-center space-y-8">
              {/* Recording Button */}
              <button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isProcessing}
                className={`relative w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300 ${
                  isRecording
                    ? 'bg-red-500 hover:bg-red-600 scale-110 animate-pulse'
                    : 'bg-blue-500 hover:bg-blue-600 hover:scale-105'
                } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {isProcessing ? (
                  <Loader2 className="w-16 h-16 text-white animate-spin" />
                ) : isRecording ? (
                  <MicOff className="w-16 h-16 text-white" />
                ) : (
                  <Mic className="w-16 h-16 text-white" />
                )}
              </button>

              {/* Status Text */}
              <div className="text-center">
                {isRecording && (
                  <p className="text-2xl text-white font-semibold">
                    Listening...
                  </p>
                )}
                {isProcessing && (
                  <p className="text-2xl text-white font-semibold">
                    Processing...
                  </p>
                )}
                {!isRecording && !isProcessing && (
                  <p className="text-xl text-gray-300">
                    Click to start recording
                  </p>
                )}
              </div>

              {/* Error Message */}
              {error && (
                <div className="w-full bg-red-500/20 border border-red-500 rounded-lg p-4">
                  <p className="text-red-200 text-center">{error}</p>
                </div>
              )}
            </div>
          </div>

          {/* Text input */}
          <form
            onSubmit={processText}
            className="mb-8 flex gap-3 rounded-2xl border border-white/20 bg-white/10 p-4 backdrop-blur-lg"
          >
            <label htmlFor="text-input" className="sr-only">Type a message</label>
            <input
              id="text-input"
              type="text"
              value={textInput}
              onChange={(event) => setTextInput(event.target.value)}
              placeholder="Or type a message..."
              disabled={isProcessing}
              className="min-w-0 flex-1 rounded-xl border border-white/20 bg-slate-900/50 px-4 py-3 text-white placeholder:text-gray-400 focus:border-blue-400 focus:outline-none"
            />
            <button
              type="submit"
              disabled={isProcessing || !textInput.trim()}
              className="rounded-xl bg-blue-500 px-5 py-3 font-semibold text-white transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Send
            </button>
          </form>

          {/* Conversation history */}
          {history.length > 0 && (
            <section className="mb-6 space-y-4" aria-label="Conversation history">
              <h2 className="px-1 text-xl font-semibold text-white">Conversation history</h2>
              {history.map((turn, index) => (
                <div
                  key={`${index}-${turn.transcript}`}
                  className="space-y-3 rounded-2xl border border-white/20 bg-white/10 p-6 backdrop-blur-lg"
                >
                  <div className="flex items-start space-x-3">
                    <div className="rounded-full bg-blue-500 p-2">
                      <Mic className="h-5 w-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <p className="mb-1 text-sm text-gray-400">You said:</p>
                      <p className="text-lg text-white">{turn.transcript}</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3 border-t border-white/10 pt-3">
                    <div className="rounded-full bg-purple-500 p-2">
                      <Volume2 className="h-5 w-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <p className="mb-1 text-sm text-gray-400">AI responded:</p>
                      <p className="text-lg text-white">{turn.response}</p>
                      {index === history.length - 1 && response === turn.response && (
                        <button
                          type="button"
                          onClick={readResponse}
                          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-white/10 px-3 py-2 text-sm text-gray-200 transition hover:bg-white/20"
                          aria-label={isReading ? 'Stop reading response' : 'Read response aloud'}
                        >
                          <Volume2 className={`h-4 w-4 ${isReading ? 'animate-pulse' : ''}`} />
                          {isReading ? 'Stop reading' : 'Read response'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </section>
          )}

          {/* Hidden Audio Element */}
          <audio ref={audioRef} className="hidden" />
        </div>
      </div>
    </main>
  )
}
