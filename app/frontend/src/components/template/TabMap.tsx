/**
 * TabMap — Map viewer embedded from the test-interface map editor.
 * Shows the full hex map with all 3 views (global + 2 theaters),
 * unit deployments, chokepoints, and editing capabilities.
 *
 * Uses iframe to embed the existing map viewer/editor which has:
 * - SVG pointy-top hex rendering with country colors
 * - Unit icons (naval, ground, tactical air, air defense, strategic missile)
 * - Click-to-inspect any hex
 * - Global ↔ theater drill-down
 * - Full edit mode with drag/place/undo/redo/save
 */

import { useState } from 'react'

interface TabMapProps {
  templateId: string
}

// Served from Vite public/map/ (API proxied to test-interface:8888)
const MAP_VIEWER_URL = '/map/viewer.html'
const MAP_FULL_EDITOR_URL = 'http://localhost:8888/map'  // full editor still on test-interface for now

export function TabMap({ templateId: _templateId }: TabMapProps) {
  const [showEditor, setShowEditor] = useState(false)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-heading text-h3 text-text-primary">Map</h3>
          <p className="font-body text-caption text-text-secondary mt-1">
            Pointy-top hex grid — Global (10×20) + Eastern Ereb (10×10) + Mashriq (10×10).
            Click hexes to inspect. Use Edit Layout for deployment changes.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowEditor(!showEditor)}
            className={`font-body text-body-sm font-medium py-2 px-4 rounded transition-opacity ${
              showEditor
                ? 'bg-warning/20 text-warning hover:opacity-90'
                : 'bg-action text-white hover:opacity-90'
            }`}
          >
            {showEditor ? 'Hide Map' : 'Show Map'}
          </button>
          <a
            href={MAP_VIEWER_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="font-body text-body-sm font-medium py-2 px-4 rounded bg-base border border-border text-text-secondary hover:text-action transition-colors"
          >
            Open in New Tab
          </a>
        </div>
      </div>

      {showEditor && (
        <div className="border border-border rounded-lg overflow-hidden bg-card">
          <iframe
            src={MAP_VIEWER_URL}
            title="TTT Map Editor"
            className="w-full border-0"
            style={{ height: '75vh', minHeight: '600px' }}
          />
        </div>
      )}

      {!showEditor && (
        <div className="bg-base border border-border rounded-lg p-8 text-center">
          <p className="font-body text-body text-text-secondary mb-2">
            Click "Show Map" to load the interactive hex map viewer.
          </p>
          <p className="font-body text-caption text-text-secondary">
            The map shows all countries, military deployments, chokepoints, and theater drill-downs.
            Use Edit Layout mode to adjust unit positions.
          </p>
        </div>
      )}
    </div>
  )
}
