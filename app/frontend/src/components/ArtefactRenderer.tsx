/**
 * ArtefactRenderer — renders classified documents with SEED_H3 styling.
 *
 * Three artefact types:
 *   - classified_report: dark header, classification badge, structured sections
 *   - telegram: monospace, urgent styling, flash priority
 *   - personal_email: informal, from a specific sender (future)
 *
 * Styles are self-contained — no external CSS dependency.
 */

interface ArtefactProps {
  type: string  // classified_report | telegram | personal_email
  title: string
  subtitle?: string | null
  classification: string
  from_entity?: string | null
  date_label?: string | null
  content_html: string
}

export function ArtefactRenderer({ type, title, subtitle, classification, from_entity, date_label, content_html }: ArtefactProps) {
  if (type === 'telegram') return <TelegramArtefact {...{ title, classification, from_entity, date_label, content_html }} />
  return <ClassifiedReport {...{ title, subtitle, classification, from_entity, date_label, content_html }} />
}

/* ── Classified Intelligence Report ─────────────────────────────────── */

function ClassifiedReport({ title, subtitle, classification, from_entity, date_label, content_html }: Omit<ArtefactProps, 'type'>) {
  return (
    <div style={styles.intelReport}>
      {/* Dark header */}
      <div style={styles.intelHeader}>
        <div style={styles.intelClassification}>{classification}</div>
        <div style={styles.intelTitle}>{title}</div>
        {subtitle && <div style={styles.intelSubtitle}>{subtitle}</div>}
      </div>

      {/* Meta bar */}
      <div style={styles.intelMeta}>
        {from_entity && (
          <div style={styles.intelMetaItem}>
            <span style={styles.intelMetaLabel}>From</span>
            <span style={styles.intelMetaValue}>{from_entity}</span>
          </div>
        )}
        {date_label && (
          <div style={styles.intelMetaItem}>
            <span style={styles.intelMetaLabel}>Date</span>
            <span style={styles.intelMetaValue}>{date_label}</span>
          </div>
        )}
        <div style={styles.intelMetaItem}>
          <span style={styles.intelMetaLabel}>Classification</span>
          <span style={styles.intelMetaValue}>{classification}</span>
        </div>
      </div>

      {/* Body */}
      <div
        style={styles.intelBody}
        dangerouslySetInnerHTML={{ __html: content_html }}
      />

      {/* Footer */}
      <div style={styles.intelFooter}>
        <span>This document is classified {classification}</span>
        <span>Unauthorized disclosure subject to penalties</span>
      </div>

      <style>{intelBodyStyles}</style>
    </div>
  )
}

/* ── Telegram / Flash Cable ─────────────────────────────────────────── */

function TelegramArtefact({ title, classification, from_entity, date_label, content_html }: Omit<ArtefactProps, 'type' | 'subtitle'>) {
  return (
    <div style={styles.cable}>
      {/* Header */}
      <div style={styles.cableHeader}>
        <div style={styles.cableRouting}>
          FLASH TRAFFIC — {classification}
        </div>
        <div style={styles.cablePriority}>FLASH</div>
        <div style={styles.cableFields}>
          {from_entity && <div><span style={styles.cableFieldLabel}>FROM: </span><span>{from_entity}</span></div>}
          {date_label && <div><span style={styles.cableFieldLabel}>DTG: </span><span>{date_label}</span></div>}
          <div><span style={styles.cableFieldLabel}>SUBJ: </span><span>{title}</span></div>
        </div>
      </div>

      {/* Body */}
      <div
        style={styles.cableBody}
        dangerouslySetInnerHTML={{ __html: content_html }}
      />

      <style>{intelBodyStyles}</style>
    </div>
  )
}

/* ── Inline Styles (from SEED_H3) ───────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  // Intel Report
  intelReport: {
    background: '#FFFFFF', maxWidth: 680, margin: '0 auto',
    border: '1px solid #D8DCE5', boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
    borderRadius: 4, overflow: 'hidden',
  },
  intelHeader: {
    background: '#1A2332', color: '#D4DEE8', padding: '20px 28px 16px',
  },
  intelClassification: {
    display: 'inline-block', background: '#B03A3A', color: '#fff',
    fontFamily: "'JetBrains Mono', monospace", fontSize: '0.7rem',
    fontWeight: 700, letterSpacing: 2, padding: '3px 10px', borderRadius: 2, marginBottom: 12,
  },
  intelTitle: {
    fontFamily: "'Playfair Display', Georgia, serif", fontSize: '1.3rem',
    fontWeight: 700, color: '#fff', lineHeight: 1.3, marginBottom: 4,
  },
  intelSubtitle: { fontSize: '0.85rem', color: '#7A8FA3' },
  intelMeta: {
    display: 'flex', gap: 24, padding: '12px 28px', background: '#F0F2F5',
    borderBottom: '1px solid #D8DCE5', fontSize: '0.75rem', color: '#4A5568',
  },
  intelMetaItem: { display: 'flex', flexDirection: 'column' as const },
  intelMetaLabel: {
    fontWeight: 600, textTransform: 'uppercase' as const, letterSpacing: 0.5,
    fontSize: '0.65rem', color: '#8494A7', marginBottom: 2,
  },
  intelMetaValue: {
    fontFamily: "'JetBrains Mono', monospace", fontSize: '0.8rem', color: '#1A2332',
  },
  intelBody: {
    padding: '24px 28px', fontSize: '0.9rem', lineHeight: 1.65, color: '#1A2332',
  },
  intelFooter: {
    padding: '12px 28px', background: '#F0F2F5', borderTop: '1px solid #D8DCE5',
    fontSize: '0.7rem', color: '#8494A7', display: 'flex', justifyContent: 'space-between',
  },

  // Telegram/Cable
  cable: {
    background: '#FFFFF5', maxWidth: 620, margin: '0 auto',
    border: '2px solid #C8C0A0', boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
    borderRadius: 2, overflow: 'hidden',
  },
  cableHeader: {
    padding: '16px 24px 12px', borderBottom: '2px solid #C8C0A0',
    fontFamily: "'JetBrains Mono', monospace",
  },
  cableRouting: {
    fontSize: '0.7rem', color: '#8A7A60', letterSpacing: 1,
    textTransform: 'uppercase' as const, marginBottom: 8,
  },
  cablePriority: {
    display: 'inline-block', background: '#B03A3A', color: '#fff',
    fontSize: '0.65rem', fontWeight: 700, letterSpacing: 2, padding: '2px 8px', borderRadius: 2,
  },
  cableFields: {
    marginTop: 10, fontSize: '0.8rem', lineHeight: 1.8,
    fontFamily: "'JetBrains Mono', monospace", color: '#1A2332',
  },
  cableFieldLabel: { color: '#8A7A60', fontWeight: 500 },
  cableBody: {
    padding: '20px 24px', fontFamily: "'JetBrains Mono', monospace",
    fontSize: '0.8rem', lineHeight: 1.7, color: '#1A2332',
  },
}

/* CSS for inner HTML content (h3, p, .highlight, ul, etc.) */
const intelBodyStyles = `
  .highlight { background: #FFF8E8; border-left: 3px solid #C4922A; padding: 8px 12px; margin: 12px 0; font-size: 0.85rem; }
  h3 { font-family: 'DM Sans', sans-serif; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #1A5276; margin: 20px 0 8px; padding-bottom: 4px; border-bottom: 1px solid #E8EBF0; }
  h3:first-child { margin-top: 0; }
  p { margin-bottom: 10px; }
  ul { padding-left: 20px; margin-bottom: 10px; }
  li { margin-bottom: 4px; }
  strong { font-weight: 600; }
`
