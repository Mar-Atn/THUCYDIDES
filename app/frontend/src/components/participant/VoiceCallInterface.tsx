/**
 * VoiceCallInterface — ElevenLabs voice call UI for avatar conversations.
 *
 * Designed to look like MeetingChat with added voice controls.
 * Same full-screen layout, same header, same message bubbles.
 *
 * M5.7 Avatar Conversation System
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { useConversation, ConversationProvider } from '@elevenlabs/react'
import { supabase } from '@/lib/supabase'

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

function stripVoiceAnnotations(text: string): string {
  return text.replace(/\[[a-z\s]{1,20}\]/gi, '').replace(/\s{2,}/g, ' ').trim()
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function fmtTime(d: Date): string {
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

async function getToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token ?? null
}

/* ── Outer wrapper (provides ConversationProvider context) ──────────── */

export function VoiceCallInterface(props: VoiceCallProps) {
  return (
    <ConversationProvider>
      <VoiceCallInner {...props} />
    </ConversationProvider>
  )
}

/* ── Inner component ────────────────────────────────────────────────── */

function VoiceCallInner({
  meetingId, simId, voiceAgentId, avatarIdentity, intentNote,
  conversationHistory, counterpartName, counterpartCountry,
  myRoleId, myCountryCode, onEnd,
}: VoiceCallProps) {
  const [status, setStatus] = useState<'connecting' | 'active' | 'ended' | 'error'>('connecting')
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([])
  const [muted, setMuted] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const transcriptRef = useRef<TranscriptEntry[]>([])
  const transcriptEndRef = useRef<HTMLDivElement>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const endingRef = useRef(false)

  // Build prompt override — identity + intent note (which includes counterpart info) + rules
  const fullPrompt = [
    avatarIdentity,
    '',
    '## Meeting Briefing',
    intentNote || '(No specific briefing for this meeting.)',
    '',
    '## Prior Conversation',
    conversationHistory || '(No prior messages — this is the start of the conversation.)',
    '',
    '## Voice Behavior Rules',
    VOICE_RULES,
  ].join('\n')

  /* ── ElevenLabs hook ──────────────────────────────────────────────── */

  const conversation = useConversation({
    onConnect: () => {
      setStatus('active')
      startTimer()
    },
    onDisconnect: () => {
      if (status === 'connecting') {
        setError('Voice agent disconnected during setup. Check ElevenLabs agent configuration.')
        setStatus('error')
        return
      }
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
      writeVoiceMessage(entry)
    },
    onError: (err) => {
      setError(err.message || 'Voice connection error')
      setStatus('error')
    },
  })

  /* ── Timer ────────────────────────────────────────────────────────── */

  function startTimer() {
    timerRef.current = setInterval(() => setElapsed(prev => prev + 1), 1000)
  }

  function stopTimer() {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null }
  }

  /* ── Start session on mount ───────────────────────────────────────── */

  useEffect(() => {
    startSession()
    return () => { stopTimer() }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript])

  async function startSession() {
    console.error('[VOICE-DEBUG] startSession called')
    console.error('[VOICE-DEBUG] avatarIdentity length:', avatarIdentity?.length || 0)
    console.error('[VOICE-DEBUG] intentNote length:', intentNote?.length || 0)
    console.error('[VOICE-DEBUG] intentNote preview:', intentNote?.slice(0, 150) || 'EMPTY')
    console.error('[VOICE-DEBUG] fullPrompt length:', fullPrompt?.length || 0)
    console.error('[VOICE-DEBUG] voiceAgentId:', voiceAgentId)
    try {
      await conversation.startSession({
        agentId: voiceAgentId,
        clientTools: {},
        overrides: {
          agent: { prompt: { prompt: fullPrompt } },
        },
      })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to start voice session')
      setStatus('error')
    }
  }

  /* ── Write voice messages to backend ──────────────────────────────── */

  async function writeVoiceMessage(entry: TranscriptEntry) {
    try {
      const token = await getToken()
      await fetch(`${API_BASE}/api/sim/${simId}/meetings/${meetingId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          role_id: myRoleId,
          country_code: myCountryCode,
          content: entry.text,
          channel: 'voice',
        }),
      })
    } catch {
      // Non-critical
    }
  }

  /* ── End conversation ─────────────────────────────────────────────── */

  const handleEnd = useCallback(async () => {
    if (endingRef.current) return
    endingRef.current = true
    stopTimer()
    setStatus('ended')

    // End the meeting via API (SPEC 5.5: voice ending = meeting ending)
    try {
      const token = await getToken()
      await fetch(`${API_BASE}/api/sim/${simId}/meetings/${meetingId}/end`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ role_id: myRoleId }),
      })
    } catch { /* best effort */ }

    const voiceTranscript = transcriptRef.current
      .map(e => `[${e.speaker === 'ai' ? counterpartName : 'You'}] ${e.text}`)
      .join('\n')
    onEnd(voiceTranscript)
  }, [simId, meetingId, myRoleId, counterpartName, onEnd])

  function endCall() {
    // End ElevenLabs session
    try { conversation.endSession() } catch { /* ignore */ }
    // Stop timer and update UI immediately (don't wait for API)
    stopTimer()
    setStatus('ended')
    // End meeting API + callback — fire and forget
    const voiceTranscript = transcriptRef.current
      .map(e => `[${e.speaker === 'ai' ? counterpartName : 'You'}] ${e.text}`)
      .join('\n')
    // Call end_meeting API in background (don't await)
    const token = getToken()
    token.then(t => {
      fetch(`${API_BASE}/api/sim/${simId}/meetings/${meetingId}/end`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(t ? { 'Authorization': `Bearer ${t}` } : {}) },
        body: JSON.stringify({ role_id: myRoleId }),
      }).catch(() => {})
    }).catch(() => {})
    onEnd(voiceTranscript)
  }

  function toggleMute() {
    setMuted(prev => {
      const next = !prev
      if (next) { conversation.setVolume({ volume: 0 }) }
      else { conversation.setVolume({ volume: 1 }) }
      return next
    })
  }

  /* ── Render: Error ────────────────────────────────────────────────── */

  if (status === 'error') {
    return (
      <div className="fixed inset-0 z-50 bg-white flex items-center justify-center">
        <div className="text-center max-w-md px-6">
          <div className="font-heading text-h2 text-danger mb-2">Voice Connection Failed</div>
          <p className="font-body text-body-sm text-gray-500 mb-6">{error}</p>
          <button onClick={() => onEnd('')}
            className="font-body text-body-sm font-medium bg-danger/10 text-danger px-6 py-2 rounded-lg hover:bg-danger/20 transition-colors">
            Close
          </button>
        </div>
      </div>
    )
  }

  /* ── Render: Main (matches MeetingChat layout) ────────────────────── */

  return (
    <div className="fixed inset-0 z-50 bg-white flex flex-col md:items-center md:justify-center">
      <div className="w-full h-full md:max-w-[600px] md:h-[85vh] md:rounded-xl md:border md:border-gray-200 md:shadow-2xl flex flex-col bg-white overflow-hidden">

        {/* ── Header (matches MeetingChat) ────────────────────────────── */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 bg-gray-50 shrink-0">
          <button onClick={endCall} className="text-gray-500 hover:text-gray-900 transition-colors p-1" aria-label="Back">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
          </button>

          <div className="flex-1 min-w-0">
            <div className="font-heading text-h3 text-gray-900 truncate">
              {counterpartName}
            </div>
            <div className="font-body text-caption text-gray-500 flex items-center gap-2">
              <span className="uppercase tracking-wider">{counterpartCountry}</span>
              <span className="text-gray-300">|</span>
              <span className="text-green-600">
                {status === 'active' ? formatDuration(elapsed) : status === 'connecting' ? 'Connecting...' : 'Ended'}
              </span>
            </div>
          </div>

          <button onClick={endCall}
            className="font-body text-caption text-danger/70 hover:text-danger px-2 py-1 rounded border border-danger/20 hover:border-danger/40 transition-colors">
            End
          </button>
        </div>

        {/* ── Voice status bar ────────────────────────────────────────── */}
        <div className="px-4 py-2 bg-gray-50/50 border-b border-gray-200 shrink-0 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${status === 'active' ? 'bg-green-500' : status === 'connecting' ? 'bg-amber-400 animate-pulse' : 'bg-gray-400'}`} />
            <span className="font-body text-caption text-gray-500">
              {status === 'active'
                ? conversation.isSpeaking ? 'Speaking...' : 'Listening...'
                : status === 'connecting' ? 'Establishing connection...' : 'Call ended'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={toggleMute}
              className={`p-1.5 rounded-full transition-colors ${muted ? 'bg-danger/10 text-danger' : 'text-gray-400 hover:text-gray-600'}`}
              title={muted ? 'Unmute' : 'Mute'}>
              {muted ? <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="1" y1="1" x2="23" y2="23"/><path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"/><path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2c0 .76-.13 1.49-.35 2.17"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
                : <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>}
            </button>
          </div>
        </div>

        {/* ── Transcript (same style as MeetingChat messages) ─────────── */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1" style={{ overscrollBehavior: 'contain' }}>
          {transcript.length === 0 && status === 'active' && (
            <div className="text-center font-body text-body-sm text-gray-500/50 py-8">
              Voice call started. Speak to begin...
            </div>
          )}
          {status === 'connecting' && (
            <div className="text-center font-body text-body-sm text-gray-500/50 py-8">
              Connecting to voice agent...
            </div>
          )}

          {transcript.map((entry, idx) => {
            const isMe = entry.speaker === 'human'
            const prevEntry = idx > 0 ? transcript[idx - 1] : null
            const showSender = !prevEntry || prevEntry.speaker !== entry.speaker

            return (
              <div key={idx} className={`flex flex-col ${isMe ? 'items-end' : 'items-start'} ${showSender ? 'mt-3' : 'mt-0.5'}`}>
                {showSender && (
                  <div className={`font-body text-caption font-medium mb-1 px-2 ${isMe ? 'text-blue-600' : 'text-indigo-600'}`}>
                    {isMe ? 'You' : counterpartName}
                    <span className="text-gray-500/40 font-normal ml-1.5 uppercase tracking-wider text-[10px]">
                      {isMe ? myCountryCode : counterpartCountry}
                    </span>
                  </div>
                )}
                <div className={`max-w-[85%] rounded-2xl px-3.5 py-2 shadow-sm ${
                  isMe
                    ? 'bg-blue-600/20 text-gray-900 rounded-br-md'
                    : 'bg-gray-50 text-gray-900 rounded-bl-md border border-gray-200/50'
                }`}>
                  <div className="font-body text-body-sm whitespace-pre-wrap break-words leading-relaxed">
                    {stripVoiceAnnotations(entry.text)}
                  </div>
                  <div className={`font-data text-[10px] mt-1 ${isMe ? 'text-blue-600/40' : 'text-gray-500/30'}`}>
                    {fmtTime(entry.timestamp)}
                  </div>
                </div>
              </div>
            )
          })}
          <div ref={transcriptEndRef} />
        </div>

        {/* ── End call bar (replaces input area) ─────────────────────── */}
        <div className="px-3 py-3 border-t border-gray-200 bg-gray-50 shrink-0 safe-area-bottom">
          <div className="flex items-center justify-center">
            <button onClick={endCall}
              className="px-8 py-2.5 bg-danger/10 text-danger hover:bg-danger/20 rounded-full font-body text-body-sm font-medium transition-colors border border-danger/20">
              End Voice Call
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
