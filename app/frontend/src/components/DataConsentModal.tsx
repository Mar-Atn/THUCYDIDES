/**
 * Data Consent Modal — GDPR-compliant privacy notice.
 * Adapted from KING SIM's DataConsentModal for TTT context.
 */

import { useState } from 'react'

interface DataConsentModalProps {
  onAccept: () => void | Promise<void>
  onCancel: () => void
}

export function DataConsentModal({ onAccept, onCancel }: DataConsentModalProps) {
  const [agreed, setAgreed] = useState(false)
  const [processing, setProcessing] = useState(false)

  const handleAccept = async () => {
    setProcessing(true)
    await onAccept()
    setProcessing(false)
  }

  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-4 py-8">
      <div className="bg-card border border-border rounded-lg p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <h2 className="font-heading text-h2 text-text-primary mb-1">
          Privacy Notice &amp; Informed Consent
        </h2>
        <p className="font-body text-caption text-text-secondary mb-1">
          Pursuant to the General Data Protection Regulation (EU) 2016/679
          (GDPR)
        </p>
        <p className="font-body text-caption text-text-secondary mb-4">
          Data Controller: MetaGames LAB Ltd. (Limassol, Cyprus;
          info@metagames.academy)
        </p>

        <hr className="border-border mb-4" />

        {/* Section 1 */}
        <h3 className="font-heading text-h3 text-text-primary mb-2">
          1. Purpose and Strict Limitation of Processing
        </h3>
        <ul className="font-body text-body-sm text-text-secondary mb-4 space-y-1.5 list-disc list-inside">
          <li>
            <strong>Core Simulation Mechanics:</strong> Processing your actions,
            decisions, and AI interactions during the simulation.
          </li>
          <li>
            <strong>General Analytics:</strong> Anonymized aggregate report for
            event analysis and simulation improvement.
          </li>
          <li>
            <strong>Personal Analytics (Optional):</strong> Individual
            performance report for your personal use only.
          </li>
        </ul>

        {/* Section 2 */}
        <h3 className="font-heading text-h3 text-text-primary mb-2">
          2. Data Categories Collected
        </h3>
        <ul className="font-body text-body-sm text-text-secondary mb-4 space-y-1.5 list-disc list-inside">
          <li>
            <strong>Identity Data:</strong> Display name, email address.
          </li>
          <li>
            <strong>Application Data:</strong> Actions, decisions, votes,
            transactions, and all inputs submitted during the simulation.
          </li>
          <li>
            <strong>AI Interaction Audio:</strong> Voice recordings during AI
            interactions and public speeches (if applicable).
          </li>
        </ul>

        {/* Section 3 */}
        <h3 className="font-heading text-h3 text-text-primary mb-2">
          3. Strict Confidentiality and Data Sharing
        </h3>
        <ul className="font-body text-body-sm text-text-secondary mb-4 space-y-1.5 list-disc list-inside">
          <li>
            <strong>Personal Report:</strong> Exclusive to you — not shared with
            any third party.
          </li>
          <li>
            <strong>General Report:</strong> Aggregated, anonymized team-level
            data only.
          </li>
          <li>
            <strong>Third-Party Processors:</strong> Anthropic (Claude AI),
            Google (Gemini AI), ElevenLabs (voice) — under strict data
            processing agreements.
          </li>
        </ul>

        {/* Section 4 */}
        <h3 className="font-heading text-h3 text-text-primary mb-2">
          4. Data Retention Periods
        </h3>
        <ul className="font-body text-body-sm text-text-secondary mb-4 space-y-1.5 list-disc list-inside">
          <li>
            <strong>Raw Audio Recordings:</strong> Deleted within 7 days after
            the simulation event.
          </li>
          <li>
            <strong>Transcripts and Reports:</strong> Deleted within 30 days
            after the simulation event.
          </li>
        </ul>

        {/* Section 5 */}
        <h3 className="font-heading text-h3 text-text-primary mb-2">
          5. Your Rights
        </h3>
        <p className="font-body text-body-sm text-text-secondary mb-4">
          Under GDPR, you have the right to access, rectify, or request erasure
          of your personal data at any time. Contact:{' '}
          <a
            href="mailto:info@metagames.academy"
            className="text-action hover:underline"
          >
            info@metagames.academy
          </a>
        </p>

        <hr className="border-border mb-4" />

        {/* Declaration */}
        <h3 className="font-heading text-h3 text-text-primary mb-2">
          Declaration of Consent
        </h3>
        <ol className="font-body text-body-sm text-text-secondary mb-4 space-y-1.5 list-decimal list-inside">
          <li>
            I have read and understand the terms described above regarding data
            processing during the Thucydides Trap simulation.
          </li>
          <li>
            I consent to the processing of my personal data, including
            application data and voice recordings, for the purposes described.
          </li>
          <li>
            I understand that I may withdraw my consent at any time by
            contacting the Data Controller.
          </li>
        </ol>

        {/* Checkbox */}
        <label className="flex items-start gap-2 cursor-pointer mb-4">
          <input
            type="checkbox"
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
            className="mt-1 accent-action"
          />
          <span className="font-body text-body-sm text-text-primary font-medium">
            I have read and agree to the terms described above
          </span>
        </label>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 bg-base text-text-secondary border border-border font-body text-body-sm font-medium py-2.5 px-4 rounded hover:bg-border/30 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleAccept}
            disabled={!agreed || processing}
            className="flex-1 bg-action text-white font-body text-body-sm font-medium py-2.5 px-4 rounded hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {processing ? 'Processing...' : 'Consent and Continue'}
          </button>
        </div>
      </div>
    </div>
  )
}
