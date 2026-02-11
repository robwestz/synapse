'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { Play, Loader, CheckCircle, AlertCircle, Download, Eye } from 'lucide-react'
import Link from 'next/link'

interface ExecutionResult {
  mode: string
  status: string
  summary?: any
  ai_insight?: {
    insight: string
    tokens_used: number
    cost_usd: number
  }
  [key: string]: any
}

export default function ExecutePage() {
  const searchParams = useSearchParams()
  const modeParam = searchParams.get('mode')

  const [selectedMode, setSelectedMode] = useState(modeParam || '')
  const [executing, setExecuting] = useState(false)
  const [result, setResult] = useState<ExecutionResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const executeMode = async () => {
    if (!selectedMode) return

    setExecuting(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('http://localhost:8000/api/v1/intelligence/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mode: selectedMode,
          user_id: 'demo-user',
        }),
      })

      if (!response.ok) {
        throw new Error('Execution failed')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Execution failed')
    } finally {
      setExecuting(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="border-4 border-primary p-6 shadow-brutal-lg">
        <h1 className="text-brutal-xl text-primary mb-4">EXECUTE INTELLIGENCE MODE</h1>
        <p className="text-lg">
          Select a mode and execute. AI will analyze your data and deliver strategic insights.
        </p>
      </div>

      {/* Mode Selection */}
      <div className="border-4 border-secondary p-6">
        <label className="block mb-4">
          <span className="text-brutal-md mb-2 block">SELECT MODE</span>
          <select
            value={selectedMode}
            onChange={(e) => setSelectedMode(e.target.value)}
            className="w-full px-4 py-3 border-4 border-secondary shadow-brutal font-mono"
          >
            <option value="">Choose intelligence mode...</option>
            <optgroup label="MODE 1: Cluster Dominance">
              <option value="1.1_cluster_dominance">1.1 - Parent Topic Coverage Map</option>
              <option value="1.2_longtail_gap">1.2 - Longtail Gap Finder</option>
              <option value="1.3_cluster_momentum">1.3 - Cluster Momentum Detector</option>
              <option value="1.4_entity_overlap">1.4 - Entity Overlap Analysis</option>
              <option value="1.5_intent_gap">1.5 - Intent Gap Matrix</option>
            </optgroup>
            <optgroup label="MODE 2: SERP Warfare">
              <option value="2.1_paa_hijack">2.1 - PAA Question Hijack</option>
              <option value="2.2_snippet_vulnerability">2.2 - Featured Snippet Vulnerability</option>
            </optgroup>
            <optgroup label="MODE 3: Backlink Intelligence">
              <option value="3.1_common_linker">3.1 - Common Linker Discovery</option>
              <option value="3.2_anchor_pattern">3.2 - Anchor Text Pattern Mining</option>
            </optgroup>
            <optgroup label="MODE 4: Traffic Potential">
              <option value="4.1_hidden_traffic">4.1 - Hidden Traffic Clusters</option>
              <option value="4.2_low_competition">4.2 - Low-Competition High-Volume</option>
            </optgroup>
            <optgroup label="MODE 5: Semantic Warfare">
              <option value="5.1_cluster_completeness">5.1 - Cluster Completeness Score</option>
              <option value="5.3_cannibalization">5.3 - Keyword Cannibalization Detector</option>
            </optgroup>
            <optgroup label="MODE 6: Evolution Tracking">
              <option value="6.1_momentum_leaders">6.1 - Momentum Leaders</option>
            </optgroup>
            <optgroup label="MODE 7: Multi-Report Synthesis">
              <option value="7.1_competitor_profile">7.1 - Comprehensive Competitor Profile</option>
            </optgroup>
            <optgroup label="MODE 8: Predictive Intelligence">
              <option value="8.2_content_roi">8.2 - Content ROI Forecaster</option>
              <option value="8.4_competitive_moat">8.4 - Competitive Moat Strength</option>
            </optgroup>
            <optgroup label="MODE 9: Fuck Ahrefs Features">
              <option value="9.1_buy_quarterly">9.1 - Buy Quarterly Calculator</option>
              <option value="9.5_preset_intelligence">9.5 - Preset Intelligence Packs</option>
              <option value="9.7_kd_is_bullshit">9.7 - Keyword Difficulty is Bullshit</option>
            </optgroup>
          </select>
        </label>

        <button
          onClick={executeMode}
          disabled={!selectedMode || executing}
          className="w-full py-4 bg-primary text-white font-bold shadow-brutal hover:shadow-brutal-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {executing ? (
            <>
              <Loader className="w-5 h-5 animate-spin" />
              ANALYZING...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              EXECUTE ANALYSIS
            </>
          )}
        </button>
      </div>

      {/* Executing */}
      {executing && (
        <div className="border-4 border-accent p-8 text-center">
          <Loader className="w-12 h-12 mx-auto mb-4 text-accent animate-spin" />
          <p className="text-brutal-md mb-2">ANALYZING YOUR DATA</p>
          <p className="text-muted">Claude AI is extracting strategic insights...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="border-4 border-primary p-6 bg-primary/5">
          <div className="flex items-center gap-3 mb-4">
            <AlertCircle className="w-6 h-6 text-primary" />
            <h3 className="text-brutal-md text-primary">EXECUTION FAILED</h3>
          </div>
          <p className="text-muted">{error}</p>
          <p className="text-sm text-muted mt-4">
            Make sure you've uploaded data first and the backend is running.
          </p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="space-y-6">
          {/* Success Header */}
          <div className="border-4 border-accent p-6 bg-accent/5">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle className="w-6 h-6 text-accent" />
              <h3 className="text-brutal-md text-accent">ANALYSIS COMPLETE</h3>
            </div>
            <p className="text-muted">
              Mode: <span className="font-mono">{result.mode}</span>
            </p>
          </div>

          {/* Summary */}
          {result.summary && (
            <div className="border-4 border-secondary p-6">
              <h3 className="text-brutal-md mb-4">EXECUTIVE SUMMARY</h3>
              <div className="grid md:grid-cols-3 gap-4">
                {Object.entries(result.summary).map(([key, value]) => (
                  <div key={key} className="border-2 border-secondary/30 p-4">
                    <div className="text-sm text-muted mb-1">
                      {key.replace(/_/g, ' ').toUpperCase()}
                    </div>
                    <div className="text-brutal-md">{String(value)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Insight */}
          {result.ai_insight && (
            <div className="border-4 border-primary p-6 shadow-brutal-lg">
              <h3 className="text-brutal-md text-primary mb-4">AI STRATEGIC INSIGHT</h3>

              <div className="prose prose-lg max-w-none mb-6">
                <div className="whitespace-pre-wrap font-mono text-sm">
                  {result.ai_insight.insight}
                </div>
              </div>

              <div className="flex gap-6 text-sm text-muted border-t-2 border-secondary/30 pt-4">
                <div>Tokens: {result.ai_insight.tokens_used?.toLocaleString()}</div>
                <div>Cost: ${result.ai_insight.cost_usd?.toFixed(4)}</div>
                <div>Model: Claude {result.mode.includes('complex') ? 'Opus' : 'Sonnet'}</div>
              </div>
            </div>
          )}

          {/* Raw Data */}
          <details className="border-4 border-secondary p-6">
            <summary className="text-brutal-md cursor-pointer mb-4">
              RAW DATA (JSON)
            </summary>
            <pre className="text-xs font-mono bg-secondary/5 p-4 overflow-auto max-h-96">
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>

          {/* Actions */}
          <div className="flex gap-4">
            <button className="flex-1 py-3 border-4 border-secondary font-bold hover:shadow-brutal transition-shadow flex items-center justify-center gap-2">
              <Download className="w-5 h-5" />
              EXPORT PDF
            </button>
            <button className="flex-1 py-3 border-4 border-secondary font-bold hover:shadow-brutal transition-shadow flex items-center justify-center gap-2">
              <Download className="w-5 h-5" />
              EXPORT CSV
            </button>
            <Link
              href="/modes"
              className="flex-1 py-3 bg-primary text-white font-bold text-center shadow-brutal hover:shadow-brutal-lg transition-shadow"
            >
              RUN ANOTHER MODE
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
