/**
 * MeetingChat — Telegram-style bilateral meeting chat.
 *
 * Full-screen on mobile, max-width panel on desktop.
 * Supports Human-Human, Human-AI, and AI-AI (observable) conversations.
 * Messages from the other participant animate in word-by-word.
 *
 * M6 Sprint: Meeting Chat UI
 */

import { useEffect, useState, useRef, useCallback } from 'react'
import { supabase } from '@/lib/supabase'
import {
  getMeetingDetail,
  sendMeetingMessage,
  endMeeting,
  type MeetingData,
  type MeetingMessage,
} from '@/lib/queries'
import { useTypingAnimation } from '@/hooks/useTypingAnimation'

/* ── Props ─────────────────────────────────────────────────────────────── */

interface MeetingChatProps {
  meetingId: string
  simId: string
  myRoleId: string
  myCountryCode: string
  myCharacterName: string
  onClose: () => void
}

/* ── Helpers ───────────────────────────────────────────────────────────── */

/** Format timestamp to short time (HH:MM). */
function fmtTime(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

/* ── Animated Message Bubble ──────────────────────────────────────────── */

function AnimatedMessage({ text, animate }: { text: string; animate: boolean }) {
  const { displayedText, isTyping } = useTypingAnimation(text, animate)
  return (
    <span>
      {animate ? displayedText : text}
      {isTyping && <span className="inline-block w-1 h-4 bg-current opacity-60 animate-pulse ml-0.5 align-text-bottom" />}
    </span>
  )
}

/* ── Main Component ───────────────────────────────────────────────────── */

export function MeetingChat({
  meetingId,
  simId,
  myRoleId,
  myCountryCode,
  myCharacterName,
  onClose,
}: MeetingChatProps) {
  const [meeting, setMeeting] = useState<MeetingData | null>(null)
  const [messages, setMessages] = useState<MeetingMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [inputText, setInputText] = useState('')
  const [sending, setSending] = useState(false)
  const [ending, setEnding] = useState(false)
  const [showEndConfirm, setShowEndConfirm] = useState(false)

  // Track which message IDs should be animated (new arrivals from the other side)
  const [animatingIds, setAnimatingIds] = useState<Set<string>>(new Set())
  const knownIdsRef = useRef<Set<string>>(new Set())

  // Voice call state
  // Participant info lookup (loaded from roles table)
  const [roleNames, setRoleNames] = useState<Record<string, { name: string; country: string }>>({})

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  /** Determine the other participant's display info. */
  const otherName = meeting
    ? (meeting.participant_a_role_id === myRoleId
        ? roleNames[meeting.participant_b_role_id]?.name ?? meeting.participant_b_role_id
        : roleNames[meeting.participant_a_role_id]?.name ?? meeting.participant_a_role_id)
    : '...'

  const otherCountry = meeting
    ? (meeting.participant_a_role_id === myRoleId
        ? meeting.participant_b_country
        : meeting.participant_a_country)
    : ''

  const isActive = meeting?.status === 'active'
  const turnsLeft = meeting ? meeting.max_turns - meeting.turn_count : 0

  /* ── Load meeting data ───────────────────────────────────────────────── */

  const loadMeeting = useCallback(async () => {
    try {
      const data = await getMeetingDetail(simId, meetingId)
      setMeeting(data.meeting)
      setMessages(data.messages)
      // Mark all initially loaded messages as known (don't animate)
      const ids = new Set(data.messages.map(m => m.id))
      knownIdsRef.current = ids
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load meeting')
    } finally {
      setLoading(false)
    }
  }, [simId, meetingId])

  /** Load role names + voice agent IDs for both participants. */
  const loadRoleNames = useCallback(async () => {
    if (!meeting) return
    const roleIds = [meeting.participant_a_role_id, meeting.participant_b_role_id]
    const otherRoleId = meeting.participant_a_role_id === myRoleId
      ? meeting.participant_b_role_id
      : meeting.participant_a_role_id
    const { data: roles } = await supabase
      .from('roles')
      .select('id,character_name,country_code')
      .in('id', roleIds)
    if (roles) {
      const map: Record<string, { name: string; country: string }> = {}
      for (const r of roles) {
        map[r.id as string] = {
          name: (r.character_name as string) || (r.id as string),
          country: (r.country_code as string) || '',
        }
      }
      setRoleNames(map)
    }
  }, [meeting?.participant_a_role_id, meeting?.participant_b_role_id, myRoleId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { loadMeeting() }, [loadMeeting])
  useEffect(() => { loadRoleNames() }, [loadRoleNames])

  /* ── Realtime subscription for new messages ──────────────────────────── */

  useEffect(() => {
    if (!meetingId) return

    // Realtime subscription — no server-side filter (UUID filters unreliable),
    // client-side filter by meeting_id instead
    const channel = supabase
      .channel(`meeting-chat:${meetingId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'meeting_messages',
        },
        (payload) => {
          const row = payload.new as unknown as MeetingMessage
          // Client-side filter
          if (row.meeting_id !== meetingId) return

          setMessages(prev => {
            if (prev.some(m => m.id === row.id)) return prev
            return [...prev, row]
          })

          // If message is from the other person, animate it
          if (row.role_id !== myRoleId && !knownIdsRef.current.has(row.id)) {
            setAnimatingIds(prev => new Set(prev).add(row.id))
            const wordCount = row.content.split(/\s+/).length
            const duration = Math.max(800, Math.min(2500, wordCount * 80))
            setTimeout(() => {
              setAnimatingIds(prev => {
                const next = new Set(prev)
                next.delete(row.id)
                return next
              })
            }, duration + 500)
          }
          knownIdsRef.current.add(row.id)
        },
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'meetings',
        },
        (payload) => {
          const row = payload.new as unknown as MeetingData
          if (row.id !== meetingId) return
          if (row.status) {
            setMeeting(prev => prev ? { ...prev, status: row.status, turn_count: row.turn_count ?? prev.turn_count } : prev)
          }
        },
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [meetingId, myRoleId])

  /* ── Polling fallback — fetch new messages every 2s ─────────────────── */

  useEffect(() => {
    if (!meetingId || !isActive) return
    const interval = setInterval(async () => {
      try {
        const data = await getMeetingDetail(simId, meetingId)
        if (data.messages.length > messages.length) {
          setMessages(prev => {
            const prevIds = new Set(prev.map(m => m.id))
            const newMsgs = data.messages.filter(m => !prevIds.has(m.id) && !m.id.startsWith('optimistic-'))
            if (newMsgs.length === 0) return prev
            // Mark new messages from other side for animation
            for (const nm of newMsgs) {
              if (nm.role_id !== myRoleId && !knownIdsRef.current.has(nm.id)) {
                setAnimatingIds(p => new Set(p).add(nm.id))
                const wc = nm.content.split(/\s+/).length
                const dur = Math.max(800, Math.min(2500, wc * 80))
                setTimeout(() => setAnimatingIds(p => { const n = new Set(p); n.delete(nm.id); return n }), dur + 500)
              }
              knownIdsRef.current.add(nm.id)
            }
            // Also remove optimistic messages that now have real counterparts
            const realContents = new Set(data.messages.map(m => m.content))
            const cleaned = prev.filter(m => !m.id.startsWith('optimistic-') || !realContents.has(m.content))
            return [...cleaned, ...newMsgs].sort((a, b) =>
              new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
            )
          })
          // Update meeting status too
          if (data.meeting.status !== meeting?.status) {
            setMeeting(data.meeting)
          }
        }
      } catch { /* ignore polling errors */ }
    }, 2000)
    return () => clearInterval(interval)
  }, [meetingId, simId, isActive, myRoleId, messages.length, meeting?.status])

  /* ── Auto-scroll on new messages ─────────────────────────────────────── */

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  /* ── Auto-close when meeting ended by counterpart ───────────────────── */

  const prevActiveRef = useRef(true)
  useEffect(() => {
    if (prevActiveRef.current && !isActive && !loading) {
      // Meeting just became inactive — ended by the other side
      // Brief delay so user sees "Meeting ended" before closing
      const timer = setTimeout(() => onClose(), 2000)
      return () => clearTimeout(timer)
    }
    prevActiveRef.current = isActive
  }, [isActive, loading, onClose])

  /* ── Focus input on mount ────────────────────────────────────────────── */

  useEffect(() => {
    if (!loading && isActive) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [loading, isActive])

  /* ── Send message ────────────────────────────────────────────────────── */

  const handleSend = async () => {
    const text = inputText.trim()
    if (!text || sending || !isActive) return
    setSending(true)
    setInputText('')
    // Optimistic: show own message immediately
    const optimisticMsg: MeetingMessage = {
      id: `optimistic-${Date.now()}`,
      meeting_id: meetingId,
      role_id: myRoleId,
      country_code: myCountryCode,
      content: text,
      channel: 'text',
      turn_number: messages.length + 1,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, optimisticMsg])
    knownIdsRef.current.add(optimisticMsg.id)
    try {
      await sendMeetingMessage(simId, meetingId, myRoleId, myCountryCode, text)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to send')
      setInputText(text) // Restore on failure
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  /* ── End meeting ─────────────────────────────────────────────────────── */

  const handleEndMeeting = async () => {
    setEnding(true)
    try {
      await endMeeting(simId, meetingId, myRoleId)
      setShowEndConfirm(false)
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to end meeting')
    } finally {
      setEnding(false)
    }
  }

  /* ── Render ──────────────────────────────────────────────────────────── */

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 bg-white flex items-center justify-center">
        <div className="text-gray-500 font-body text-body">Loading meeting...</div>
      </div>
    )
  }

  if (error && !meeting) {
    return (
      <div className="fixed inset-0 z-50 bg-white flex flex-col items-center justify-center gap-4">
        <div className="text-danger font-body text-body">{error}</div>
        <button onClick={onClose} className="text-blue-600 font-body text-body-sm hover:underline">
          Go back
        </button>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 bg-white flex flex-col md:items-center md:justify-center">
      {/* Container: full-screen mobile, centered panel desktop */}
      <div className="w-full h-full md:max-w-[600px] md:h-[85vh] md:rounded-xl md:border md:border-gray-200 md:shadow-2xl flex flex-col bg-white overflow-hidden">

        {/* ── Header ──────────────────────────────────────────────────── */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 bg-gray-50 shrink-0">
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-900 transition-colors p-1"
            aria-label="Back"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
          </button>

          <div className="flex-1 min-w-0">
            <div className="font-heading text-h3 text-gray-900 truncate">
              {otherName}
            </div>
            <div className="font-body text-caption text-gray-500 flex items-center gap-2">
              <span className="uppercase tracking-wider">{otherCountry}</span>
              {meeting?.round_num != null && (
                <>
                  <span className="text-dark-border">|</span>
                  <span>Round {meeting.round_num}</span>
                </>
              )}
            </div>
          </div>

          {isActive && (
            <button
              onClick={() => setShowEndConfirm(true)}
              className="font-body text-caption text-danger/70 hover:text-danger px-2 py-1 rounded border border-danger/20 hover:border-danger/40 transition-colors"
            >
              End
            </button>
          )}
        </div>

        {/* ── End Meeting Confirmation ────────────────────────────────── */}
        {showEndConfirm && (
          <div className="px-4 py-3 bg-danger/5 border-b border-danger/20 flex items-center gap-3 shrink-0">
            <span className="font-body text-body-sm text-gray-900 flex-1">
              End this meeting?
            </span>
            <button
              onClick={handleEndMeeting}
              disabled={ending}
              className="font-body text-caption font-medium bg-danger/10 text-danger px-3 py-1 rounded hover:bg-danger/20 disabled:opacity-50 transition-colors"
            >
              {ending ? 'Ending...' : 'Yes, end'}
            </button>
            <button
              onClick={() => setShowEndConfirm(false)}
              className="font-body text-caption text-gray-500 px-2 py-1 hover:text-gray-900 transition-colors"
            >
              Cancel
            </button>
          </div>
        )}

        {/* ── Agenda banner ───────────────────────────────────────────── */}
        {meeting?.agenda && (
          <div className="px-4 py-2 bg-gray-50/50 border-b border-gray-200 shrink-0">
            <div className="font-body text-caption text-gray-500">
              Agenda: <span className="text-gray-900">{meeting.agenda}</span>
            </div>
          </div>
        )}

        {/* ── Messages ────────────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1" style={{ overscrollBehavior: 'contain' }}>
          {messages.length === 0 && (
            <div className="text-center font-body text-body-sm text-gray-500/50 py-8">
              No messages yet. Say hello!
            </div>
          )}

          {messages.map((msg, idx) => {
            const isMe = msg.role_id === myRoleId
            const isSystem = msg.channel === 'system'
            const shouldAnimate = animatingIds.has(msg.id)

            // Show sender name if first message or different sender from previous
            const prevMsg = idx > 0 ? messages[idx - 1] : null
            const showSender = !isSystem && (!prevMsg || prevMsg.role_id !== msg.role_id || prevMsg.channel === 'system')

            if (isSystem) {
              return (
                <div key={msg.id} className="flex justify-center py-2">
                  <span className="font-body text-caption text-gray-500/50 bg-gray-50/30 px-3 py-1 rounded-full">
                    {msg.content}
                  </span>
                </div>
              )
            }

            const senderName = isMe
              ? myCharacterName
              : (roleNames[msg.role_id]?.name ?? msg.role_id)
            const senderCountry = isMe
              ? myCountryCode
              : (roleNames[msg.role_id]?.country ?? msg.country_code)

            return (
              <div key={msg.id} className={`flex flex-col ${isMe ? 'items-end' : 'items-start'} ${showSender ? 'mt-3' : 'mt-0.5'}`}>
                {showSender && (
                  <div className={`font-body text-caption font-medium mb-1 px-2 ${isMe ? 'text-blue-600' : 'text-indigo-600'}`}>
                    {senderName}
                    <span className="text-gray-500/40 font-normal ml-1.5 uppercase tracking-wider text-[10px]">
                      {senderCountry}
                    </span>
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2 shadow-sm ${
                    isMe
                      ? 'bg-blue-600/20 text-gray-900 rounded-br-md'
                      : 'bg-gray-50 text-gray-900 rounded-bl-md border border-gray-200/50'
                  }`}
                >
                  <div className="font-body text-body-sm whitespace-pre-wrap break-words leading-relaxed">
                    {shouldAnimate
                      ? <AnimatedMessage text={msg.content} animate={true} />
                      : msg.content}
                  </div>
                  <div className={`font-data text-[10px] mt-1 ${isMe ? 'text-blue-600/40' : 'text-gray-500/30'}`}>
                    {fmtTime(msg.created_at)}
                  </div>
                </div>
              </div>
            )
          })}
          <div ref={messagesEndRef} />
        </div>

        {/* ── Error banner ────────────────────────────────────────────── */}
        {error && (
          <div className="px-4 py-2 bg-danger/10 border-t border-danger/20 shrink-0">
            <div className="font-body text-caption text-danger flex items-center justify-between">
              <span>{error}</span>
              <button onClick={() => setError(null)} className="text-danger/50 hover:text-danger ml-2">&times;</button>
            </div>
          </div>
        )}

        {/* ── Meeting ended banner ────────────────────────────────────── */}
        {!isActive && (
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 shrink-0 text-center">
            <div className="font-body text-body-sm text-gray-500">
              Meeting ended — returning to game...
            </div>
          </div>
        )}

        {/* ── Input area ──────────────────────────────────────────────── */}
        {isActive && (
          <div className="px-3 py-3 border-t border-gray-200 bg-gray-50 shrink-0 safe-area-bottom">
            <div className="flex items-end gap-2">
              {/* Text input */}
              <textarea
                ref={inputRef}
                value={inputText}
                onChange={e => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message..."
                rows={1}
                maxLength={2000}
                className="flex-1 bg-white border border-gray-200 rounded-2xl px-4 py-2.5 font-body text-body-sm text-gray-900 resize-none focus:border-dark-action/50 focus:outline-none transition-colors placeholder-dark-text-secondary/40 max-h-32 overflow-y-auto"
                style={{ minHeight: '42px' }}
              />

              {/* Send button */}
              <button
                onClick={handleSend}
                disabled={!inputText.trim() || sending}
                className="shrink-0 p-2.5 bg-blue-600 text-dark-base rounded-full hover:bg-blue-600/80 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                aria-label="Send"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m22 2-7 20-4-9-9-4z"/>
                  <path d="M22 2 11 13"/>
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Voice mode is handled by ParticipantDashboard (mode popup before chat) */}
      </div>
    </div>
  )
}
