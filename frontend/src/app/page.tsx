'use client'

import { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Loader2, Volume2 } from 'lucide-react'

export default function Home() {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')
  const [error, setError] = useState('')
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)

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

      // Play audio response if available
      if (data.audio_url) {
        playAudioResponse(data.audio_url)
      }
    } catch (err) {
      setError('Failed to process audio. Please try again.')
      console.error('Error processing audio:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  const playAudioResponse = (audioUrl: string) => {
    if (audioRef.current) {
      audioRef.current.src = audioUrl
      audioRef.current.onplay = () => setIsPlaying(true)
      audioRef.current.onended = () => setIsPlaying(false)
      audioRef.current.play()
    }
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

          {/* Transcript */}
          {transcript && (
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 mb-6 border border-white/20">
              <div className="flex items-start space-x-3">
                <div className="bg-blue-500 rounded-full p-2">
                  <Mic className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-400 mb-1">You said:</p>
                  <p className="text-lg text-white">{transcript}</p>
                </div>
              </div>
            </div>
          )}

          {/* Response */}
          {response && (
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 mb-6 border border-white/20">
              <div className="flex items-start space-x-3">
                <div className="bg-purple-500 rounded-full p-2">
                  <Volume2 className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-400 mb-1">AI responded:</p>
                  <p className="text-lg text-white">{response}</p>
                </div>
              </div>
            </div>
          )}

          {/* Hidden Audio Element */}
          <audio ref={audioRef} className="hidden" />
        </div>
      </div>
    </main>
  )
}
