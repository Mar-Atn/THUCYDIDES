/**
 * VoiceCallInterface — ElevenLabs voice call UI for avatar conversations.
 *
 * Allows a human participant to speak with an AI avatar via ElevenLabs
 * Conversational AI. Text chat history and avatar identity are injected
 * as prompt overrides so the voice agent stays in character.
 *
 * M5.7 Avatar Conversation System
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { useConversation } from '@elevenlabs/react'
import { supabase } from '@/lib/supabase'
import {
  Mic, MicOff, Phone, PhoneOff, Eye, EyeOff, Volume2, Smartphone,
} from 'lucide-react'

/* ── Constants ────────────────────────────────────────────────────────── */

const VOICE_RULES = `You are speaking via voice in a live conversation. You are a head of state, not an AI.
- 1-2 sentences per response. Conversation, not lecture.
- Start some responses mid-thought: "Well..." / "Look, the thing is..."
- React emotionally BEFORE logic.
- Use filler naturally: "I mean...", "sort of"
- Vary energy. Whispered confidences, sharp retorts.
- NEVER say "That's a great question" or "Let me elaborate."
- Speak as a real human: messy, emotional, imperfect.
Voice expressions (sparingly): [laughs] [sighs] [whispers] [pauses]`

const API_BASE = import.meta.env.VITE_API_URL ?? ''

/* ── Types ────────────────────────────────────────────────────────────── */

export interface VoiceCallProps {
  meetingId: string
  simId: string
  voiceAgentId: string
  avatarIdentity: string
  intentNote: string
  conversationHistory: string
  counterpartName: string
  counterpartCountry: string
  myRoleId: string
  myCountryCode: string
  onEnd: (voiceTranscript: string) => void
}

interface TranscriptEntry {
  speaker: 'ai' | 'human'
  text: string
  timestamp: Date
}

/* ── Helpers ──────────────────────────────────────────────────────────── */

/** Strip ElevenLabs voice annotations like [slow], [laugh] from display text. */
function stripVoiceAnnotations(text: string): string {
  return text.replace(/\[[a-z\s]{1,20}\]/gi, '').replace(/\s{2,}/g, ' ').trim()
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

async function getToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token ?? null
}

/* ── Component ────────────────────────────────────────────────────────── */

export function VoiceCallInterface({
  meetingId,
  simId,
  voiceAgentId,
  avatarIdentity,
  intentNote,
  conversationHistory,
  counterpartName,
  counterpartCountry,
  myRoleId,
  myCountryCode,
  onEnd,
}: VoiceCallProps) {
  const [status, setStatus] = useState<'connecting' | 'active' | 'ended' | 'error'>('connecting')
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([])
  const [muted, setMuted] = useState(false)
  const [phoneMode, setPhoneMode] = useState(false)
  const [showTranscript, setShowTranscript] = useState(true)
  const [elapsed, setElapsed] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const transcriptRef = useRef<TranscriptEntry[]>([])
  const transcriptEndRef = useRef<HTMLDivElement>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const endingRef = useRef(false)

  // Build the full prompt override: avatar identity + intent + history + voice rules
  const fullPrompt = [
    avatarIdentity,
    '',
    '## Conversation Intent',
    intentNote,
    '',
    '## Prior Text Conversation',
    conversationHistory || '(No prior messages — this is the start of the conversation.)',
    '',
    '## Voice Behavior Rules',
    VOICE_RULES,
  ].join('\n')

  /* ── ElevenLabs hook ─────────────────────────────────────────────────── */

  const conversation = useConversation({
    onConnect: () => {
      setStatus('active')
      startTimer()
    },
    onDisconnect: () => {
      handleEnd()
    },
    onMessage: (message) => {
      const entry: TranscriptEntry = {
        speaker: message.source === 'ai' ? 'ai' : 'human',
        text: message.message,
        timestamp: new Date(),
      }
      transcriptRef.current = [...transcriptRef.current, entry]
      setTranscript(transcriptRef.current)

      // Write voice message to meeting_messages via backend
      writeVoiceMessage(entry)
    },
    onError: (err) => {
      setError(err.message || 'Voice connection error')
      setStatus('error')
    },
  })

  /* ── Timer ───────────────────────────────────────────────────────────── */

  function startTimer() {
    timerRef.current = setInterval(() => {
      setElapsed(prev => prev + 1)
    }, 1000)
  }

  function stopTimer() {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  /* ── Start session on mount ──────────────────────────────────────────── */

  useEffect(() => {
    startSession()
    return () => {
      stopTimer()
    }
  }, [])

  /** Auto-scroll transcript. */
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript])

  async function startSession() {
    try {
      await conversation.startSession({
        agentId: voiceAgentId,
        clientTools: {},
        overrides: {
          agent: {
            prompt: {
              prompt: fullPrompt,
            },
          },
        },
      })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to start voice session'
      setError(msg)
      setStatus('error')
    }
  }

  /* ── Write voice messages to backend ──────────────────────────────── */

  async function writeVoiceMessage(entry: TranscriptEntry) {
    try {
      const token = await getToken()
      const roleId = entry.speaker === 'human' ? myRoleId : undefined
      await fetch(`${API_BASE}/api/sim/${simId}/meetings/${meetingId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          role_id: roleId ?? myRoleId,
          country_code: myCountryCode,
          content: entry.text,
          channel: 'voice',
        }),
      })
    } catch {
      // Non-critical — transcript is still captured locally
    }
  }

  /* ── End conversation ────────────────────────────────────────────────── */

  const handleEnd = useCallback(async () => {
    if (endingRef.current) return
    endingRef.current = true

    stopTimer()
    setStatus('ended')

    // Build full transcript string
    const voiceTranscript = transcriptRef.current
      .map(e => `[${e.speaker === 'ai' ? counterpartName : 'You'}] ${e.text}`)
      .join('\n')

    onEnd(voiceTranscript)
  }, [counterpartName, onEnd])

  async function endCall() {
    if (conversation.status === 'connected') {
      await conversation.endSession()
      // handleEnd will fire via onDisconnect
    } else {
      handleEnd()
    }
  }

  /* ── Mute toggle ─────────────────────────────────────────────────────── */

  function toggleMute() {
    setMuted(prev => {
      const next = !prev
      if (next) {
        conversation.setVolume({ volume: 0 })
      } else {
        conversation.setVolume({ volume: 1 })
      }
      return next
    })
  }

  /* ── Phone mode (earpiece / speaker switch) ──────────────────────────── */

  async function togglePhoneMode() {
    setPhoneMode(prev => !prev)
    // setSinkId is only available on some browsers — best-effort
    try {
      const audioElements = document.querySelectorAll('audio')
      for (const el of audioElements) {
        if ('setSinkId' in el) {
          await (el as HTMLAudioElement & { setSinkId: (id: string) => Promise<void> })
            .setSinkId(phoneMode ? '' : 'default')
        }
      }
    } catch {
      // Not supported — ignore
    }
  }

  /* ── Render: Error ───────────────────────────────────────────────────── */

  if (status === 'error') {
    return (
      <div className="fixed inset-0 z-50 bg-[#0A0E1A] flex items-center justify-center p-6 md:relative md:inset-auto md:rounded-xl md:border md:border-red-500/30">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
            <PhoneOff className="w-8 h-8 text-red-400" />
          </div>
          <h2 className="font-['Playfair_Display'] text-2xl text-red-400 mb-2">
            Voice Connection Failed
          </h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => onEnd('')}
            className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    )
  }

  /* ── Render: Main ────────────────────────────────────────────────────── */

  return (
    <div className="fixed inset-0 z-50 bg-[#0A0E1A] flex flex-col md:relative md:inset-auto md:rounded-xl md:border md:border-white/10 md:max-h-[700px]">

      {/* Header: counterpart name + timer */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-[#0A0E1A]/80 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 font-['Playfair_Display'] font-bold text-lg">
            {counterpartName.charAt(0)}
          </div>
          <div>
            <div className="text-white font-['Playfair_Display'] text-lg leading-tight">
              {counterpartName}
            </div>
            <div className="text-gray-500 text-xs">
              {counterpartCountry}
              {status === 'active' && (
                <span className="ml-2 text-green-400">
                  {formatDuration(elapsed)}
                </span>
              )}
              {status === 'connecting' && (
                <span className="ml-2 text-amber-400 animate-pulse">Connecting...</span>
              )}
            </div>
          </div>
        </div>
        <button
          onClick={endCall}
          className="w-10 h-10 rounded-full bg-red-600 hover:bg-red-700 flex items-center justify-center transition-colors"
          title="End call"
        >
          <PhoneOff className="w-5 h-5 text-white" />
        </button>
      </div>

      {/* Center: waveform indicator */}
      <div className="flex-1 flex flex-col items-center justify-center min-h-0">
        {!showTranscript ? (
          <div className="flex flex-col items-center gap-6">
            <div className="w-28 h-28 rounded-full bg-amber-500/10 border-2 border-amber-500/30 flex items-center justify-center">
              <div className={`flex items-end gap-1 h-12 ${status === 'active' ? '' : 'opacity-30'}`}>
                {[1, 2, 3, 4, 5].map(i => (
                  <div
                    key={i}
                    className="w-1.5 bg-amber-400 rounded-full"
                    style={{
                      height: status === 'active' ? `${12 + Math.random() * 36}px` : '8px',
                      transition: 'height 0.15s ease',
                      animation: status === 'active' ? `pulse ${0.4 + i * 0.1}s ease-in-out infinite alternate` : 'none',
                    }}
                  />
                ))}
              </div>
            </div>
            <div className="text-gray-400 font-['DM_Sans'] text-sm">
              {status === 'active'
                ? conversation.isSpeaking ? 'Speaking...' : 'Listening...'
                : status === 'connecting' ? 'Establishing connection...' : 'Call ended'}
            </div>
          </div>
        ) : (
          /* Transcript view */
          <div className="w-full flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-0">
            {transcript.length === 0 && status === 'active' && (
              <p className="text-center text-gray-500 text-sm mt-8">
                Conversation starting...
              </p>
            )}
            {transcript.map((entry, i) => (
              <div
                key={i}
                className={`flex ${entry.speaker === 'human' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] px-3 py-2 rounded-lg text-sm font-['DM_Sans'] ${
                    entry.speaker === 'ai'
                      ? 'bg-white/5 border border-white/10 text-gray-200'
                      : 'bg-blue-600/20 border border-blue-500/20 text-blue-100'
                  }`}
                >
                  <div className="text-[10px] text-gray-500 mb-0.5">
                    {entry.speaker === 'ai' ? counterpartName : 'You'}
                    <span className="ml-2">
                      {entry.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p>{stripVoiceAnnotations(entry.text)}</p>
                </div>
              </div>
            ))}
            <div ref={transcriptEndRef} />
          </div>
        )}
      </div>

      {/* Controls bar */}
      <div className="flex items-center justify-center gap-4 px-4 py-4 border-t border-white/10 bg-[#0A0E1A]/80 backdrop-blur">
        {/* Mute */}
        <button
          onClick={toggleMute}
          className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
            muted
              ? 'bg-red-500/20 text-red-400 border border-red-500/30'
              : 'bg-white/10 text-white border border-white/10 hover:bg-white/20'
          }`}
          title={muted ? 'Unmute' : 'Mute'}
        >
          {muted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
        </button>

        {/* Phone mode */}
        <button
          onClick={togglePhoneMode}
          className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
            phoneMode
              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
              : 'bg-white/10 text-white border border-white/10 hover:bg-white/20'
          }`}
          title={phoneMode ? 'Speaker mode' : 'Phone mode'}
        >
          {phoneMode ? <Smartphone className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
        </button>

        {/* Show/hide transcript */}
        <button
          onClick={() => setShowTranscript(prev => !prev)}
          className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
            showTranscript
              ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
              : 'bg-white/10 text-white border border-white/10 hover:bg-white/20'
          }`}
          title={showTranscript ? 'Hide transcript' : 'Show transcript'}
        >
          {showTranscript ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
        </button>

        {/* End voice call */}
        <button
          onClick={endCall}
          className="w-14 h-14 rounded-full bg-red-600 hover:bg-red-700 flex items-center justify-center transition-colors shadow-lg shadow-red-600/30"
          title="End voice call"
        >
          <Phone className="w-6 h-6 text-white rotate-[135deg]" />
        </button>
      </div>
    </div>
  )
}
