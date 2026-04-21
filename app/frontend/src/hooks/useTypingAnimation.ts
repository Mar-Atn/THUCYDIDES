/**
 * useTypingAnimation — reveals text progressively, word-by-word.
 *
 * Used in MeetingChat to animate incoming messages from the other participant.
 * Speed scales with message length: ~1-2 seconds total regardless of size.
 */

import { useState, useEffect, useRef } from 'react'

interface UseTypingAnimationResult {
  /** The currently visible portion of the text */
  displayedText: string
  /** Whether the animation is still in progress */
  isTyping: boolean
}

/**
 * Progressively reveal text word-by-word.
 *
 * @param text - Full message text to animate
 * @param active - Whether to animate (false = show full text immediately)
 * @param targetDurationMs - Approximate total animation time in ms (default 1500)
 */
export function useTypingAnimation(
  text: string,
  active: boolean = true,
  targetDurationMs: number = 1500,
): UseTypingAnimationResult {
  const words = text.split(/(\s+)/) // preserve whitespace tokens
  const totalWords = words.filter(w => w.trim().length > 0).length
  const [wordIndex, setWordIndex] = useState(active ? 0 : words.length)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!active) {
      setWordIndex(words.length)
      return
    }

    setWordIndex(0)

    // Calculate per-word interval: target duration / number of words
    // Minimum 30ms, maximum 120ms per word
    const interval = totalWords > 0
      ? Math.max(30, Math.min(120, targetDurationMs / totalWords))
      : 0

    if (totalWords === 0) {
      setWordIndex(words.length)
      return
    }

    timerRef.current = setInterval(() => {
      setWordIndex(prev => {
        const next = prev + 1
        if (next >= words.length) {
          if (timerRef.current) clearInterval(timerRef.current)
          return words.length
        }
        return next
      })
    }, interval)

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [text, active]) // eslint-disable-line react-hooks/exhaustive-deps

  const displayedText = words.slice(0, wordIndex).join('')
  const isTyping = wordIndex < words.length

  return { displayedText, isTyping }
}
