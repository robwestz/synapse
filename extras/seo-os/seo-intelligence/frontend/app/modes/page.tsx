'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Search, Zap, TrendingUp, Target, Brain, BarChart, Shield, DollarSign, Flame } from 'lucide-react'

const INTELLIGENCE_MODES = [
  {
    category: 'MODE 1: Cluster Dominance',
    icon: Target,
    color: 'primary',
    modes: [
      { id: '1.1', name: 'Parent Topic Coverage Map', description: 'Find clusters competitors own at 80%+. 8x traffic potential.', impact: 'HIGH', built: true },
      { id: '1.2', name: 'Longtail Gap Finder', description: '847 longtail keywords (5+ words) you\'re missing.', impact: 'IMMEDIATE', built: true },
      { id: '1.3', name: 'Cluster Momentum Detector', description: 'Rising/falling clusters. Urgent threats identified.', impact: 'HIGH', built: true },
      { id: '1.4', name: 'Entity Overlap Analysis', description: 'Entity associations competitors have that you lack.', impact: 'STRATEGIC', built: true },
      { id: '1.5', name: 'Intent Gap Matrix', description: 'Blind spots: informational vs. commercial vs. transactional.', impact: 'HIGH', built: true },
    ]
  },
  {
    category: 'MODE 2: SERP Warfare',
    icon: Search,
    color: 'accent',
    modes: [
      { id: '2.1', name: 'PAA Question Hijack', description: '23 PAA questions clustered. Create comprehensive FAQ.', impact: 'IMMEDIATE', built: true },
      { id: '2.2', name: 'Featured Snippet Vulnerability', description: '47 keywords position 2-5 with NO snippet. Easy wins.', impact: 'IMMEDIATE', built: true },
      { id: '2.3', name: 'SERP Feature Density Score', description: 'Calculate click-through difficulty. Prioritize low-feature keywords.', impact: 'MODERATE', built: false },
      { id: '2.4', name: 'Multi-Intent SERP Detector', description: 'Hybrid SERPs where multiple intents coexist.', impact: 'STRATEGIC', built: false },
      { id: '2.5', name: 'Position Zero Opportunity', description: 'High-volume keywords with NO snippets yet. First-mover advantage.', impact: 'HIGH', built: false },
    ]
  },
  {
    category: 'MODE 3: Backlink Intelligence',
    icon: Shield,
    color: 'secondary',
    modes: [
      { id: '3.1', name: 'Common Linker Discovery', description: '87 domains link to competitors but not you. Warm prospects.', impact: 'HIGH', built: true },
      { id: '3.2', name: 'Anchor Text Pattern Mining', description: 'Competitor anchor themes: "free tool" 34% vs your 2%.', impact: 'STRATEGIC', built: true },
      { id: '3.3', name: 'Link Velocity Anomaly', description: '127 links in one week. What campaign caused it?', impact: 'STRATEGIC', built: false },
      { id: '3.4', name: 'DR-Weighted Gap Score', description: 'Quality over quantity. Weighted link scoring.', impact: 'MODERATE', built: false },
      { id: '3.5', name: 'Content Type Link Magnet', description: '89% of links go to /tools/*. Stop blogging, build tools.', impact: 'HIGH', built: false },
    ]
  },
  {
    category: 'MODE 4: Traffic Potential',
    icon: TrendingUp,
    color: 'primary',
    modes: [
      { id: '4.1', name: 'Hidden Traffic Clusters', description: 'Entire topics where competitor has 80%, you have 10%. 8x opportunity.', impact: 'HIGH', built: true },
      { id: '4.2', name: 'Low-Competition High-Volume', description: '12K volume, KD 28, top 3 all DR <40. Easy win.', impact: 'IMMEDIATE', built: true },
      { id: '4.3', name: 'Branded vs Non-Branded Ratio', description: 'Competitor: 89% branded = vulnerable. Target their non-branded.', impact: 'STRATEGIC', built: false },
      { id: '4.4', name: 'Traffic Concentration Risk', description: 'Competitor gets 67% traffic from 10 keywords. Attack these.', impact: 'HIGH', built: false },
      { id: '4.5', name: 'Growth Trajectory Prediction', description: 'Keywords with accelerating growth. Invest before saturation.', impact: 'STRATEGIC', built: false },
    ]
  },
  {
    category: 'MODE 5: Semantic Warfare',
    icon: Brain,
    color: 'accent',
    modes: [
      { id: '5.1', name: 'Cluster Completeness Score', description: 'You: 18% semantic coverage. Competitor: 81%. Authority gap.', impact: 'HIGH', built: true },
      { id: '5.2', name: 'Sub-Cluster Discovery', description: 'Within "digital marketing", find sub-clusters via embeddings.', impact: 'STRATEGIC', built: false },
      { id: '5.3', name: 'Keyword Cannibalization Detector', description: 'You rank for "SEO tools" with 7 URLs. Consolidate.', impact: 'HIGH', built: true },
      { id: '5.4', name: 'Topic Authority Transfer', description: 'Link from strong topics to weak for authority boost.', impact: 'MODERATE', built: false },
      { id: '5.5', name: 'Content Depth Gap', description: 'Competitor covers topic with 187 keywords. You have 23.', impact: 'HIGH', built: false },
    ]
  },
  {
    category: 'MODE 6: Evolution Tracking',
    icon: BarChart,
    color: 'secondary',
    modes: [
      { id: '6.1', name: 'Momentum Leaders', description: 'Competitor improved 247 keywords. What strategy works?', impact: 'STRATEGIC', built: true },
      { id: '6.2', name: 'Ranking Volatility Map', description: 'Volatile SERPs = opportunity. No dominant player yet.', impact: 'MODERATE', built: false },
      { id: '6.3', name: 'Zero to Hero Keywords', description: 'NEW content ranked #4 for 47 keywords in 3 months.', impact: 'STRATEGIC', built: false },
      { id: '6.4', name: 'Falling Giants', description: 'DR 84 competitor dropped -12 positions. Outdated content.', impact: 'IMMEDIATE', built: false },
      { id: '6.5', name: 'Seasonal Pattern Detection', description: '"tax software" peaks Q1. Publish NOW for Jan rankings.', impact: 'STRATEGIC', built: false },
    ]
  },
  {
    category: 'MODE 7: Multi-Report Synthesis',
    icon: Zap,
    color: 'primary',
    modes: [
      { id: '7.1', name: 'Comprehensive Competitor Profile', description: 'Complete strategic teardown. Content + Links + SERP + Growth.', impact: 'HIGH', built: true },
      { id: '7.2', name: 'Strategic Blind Spots', description: 'Topics where ALL competitors are weak. Blue ocean.', impact: 'HIGH', built: false },
      { id: '7.3', name: 'Winner Pattern Extraction', description: 'Top 3 competitors share traits. Match these benchmarks.', impact: 'STRATEGIC', built: false },
      { id: '7.4', name: 'Your Unique Advantage Finder', description: 'What you do BETTER than all competitors.', impact: 'STRATEGIC', built: false },
      { id: '7.5', name: 'Ahrefs Exposure Score', description: 'Ahrefs shows 0.3% of available intelligence. We show 100%.', impact: 'MARKETING', built: false },
    ]
  },
  {
    category: 'MODE 8: Predictive Intelligence',
    icon: Brain,
    color: 'accent',
    modes: [
      { id: '8.1', name: 'Time-to-Rank Predictor', description: 'With 20 DR 50+ links, rank top 10 in 4-6 months.', impact: 'STRATEGIC', built: false },
      { id: '8.2', name: 'Content ROI Forecaster', description: 'Ranking #3 = 847 visitors × 2.3% × $49 = $956/mo. ROI: 380%.', impact: 'HIGH', built: true },
      { id: '8.3', name: 'Link Acquisition Velocity', description: 'Need 47 DR 50+ links. Current rate: 16 months. Accelerate.', impact: 'STRATEGIC', built: false },
      { id: '8.4', name: 'Competitive Moat Score', description: 'Moat: 87/100. $500K + 2-3 years to break. Target adjacent.', impact: 'HIGH', built: true },
      { id: '8.5', name: 'Market Saturation Detector', description: '7 domains hold 92% of top 10. Saturated. Niche down.', impact: 'STRATEGIC', built: false },
    ]
  },
  {
    category: 'MODE 9: "Fuck Ahrefs" Features',
    icon: Flame,
    color: 'primary',
    modes: [
      { id: '9.1', name: 'Buy Quarterly Calculator', description: '88% stable. Download quarterly, save $9,000/year.', impact: 'IMMEDIATE', built: true },
      { id: '9.2', name: 'Filter Futility Exposer', description: '89% of Ahrefs filter combinations yield NO insights.', impact: 'MARKETING', built: false },
      { id: '9.5', name: 'Preset Intelligence Packs', description: 'E-commerce, SaaS, Local, Content packs. One-click.', impact: 'HIGH', built: true },
      { id: '9.7', name: 'Keyword Difficulty is Bullshit', description: 'KD 70+ but you ranked #3. Prove KD doesn\'t work.', impact: 'MARKETING', built: true },
    ]
  },
]

export default function ModesPage() {
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [showBuiltOnly, setShowBuiltOnly] = useState(false)

  const filteredModes = INTELLIGENCE_MODES.map(category => ({
    ...category,
    modes: category.modes.filter(mode => {
      const matchesSearch = mode.name.toLowerCase().includes(search.toLowerCase()) ||
        mode.description.toLowerCase().includes(search.toLowerCase())
      const matchesCategory = !selectedCategory || category.category === selectedCategory
      const matchesBuilt = !showBuiltOnly || mode.built
      return matchesSearch && matchesCategory && matchesBuilt
    })
  })).filter(category => category.modes.length > 0)

  const totalBuilt = INTELLIGENCE_MODES.reduce((acc, cat) =>
    acc + cat.modes.filter(m => m.built).length, 0
  )
  const totalModes = INTELLIGENCE_MODES.reduce((acc, cat) => acc + cat.modes.length, 0)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="border-4 border-primary p-6 shadow-brutal-lg">
        <h1 className="text-brutal-xl text-primary mb-4">INTELLIGENCE MODES</h1>
        <p className="text-lg mb-4">
          {totalBuilt} operational modes. {totalModes - totalBuilt} coming soon.
        </p>
        <div className="flex gap-2">
          <div className="px-3 py-1 bg-accent text-white text-sm font-bold">
            {totalBuilt} BUILT
          </div>
          <div className="px-3 py-1 border-2 border-secondary text-sm font-bold">
            {totalModes - totalBuilt} PLANNED
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex gap-4">
        <input
          type="text"
          placeholder="Search modes..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 px-4 py-3 border-4 border-secondary shadow-brutal focus:shadow-brutal-lg outline-none"
        />
        <label className="flex items-center gap-2 px-4 border-4 border-secondary cursor-pointer hover:shadow-brutal">
          <input
            type="checkbox"
            checked={showBuiltOnly}
            onChange={(e) => setShowBuiltOnly(e.target.checked)}
            className="w-4 h-4"
          />
          <span className="font-bold">BUILT ONLY</span>
        </label>
      </div>

      {/* Category Filter */}
      <div className="flex gap-3 flex-wrap">
        <button
          onClick={() => setSelectedCategory(null)}
          className={`px-4 py-2 font-bold transition-shadow ${
            !selectedCategory
              ? 'bg-primary text-white shadow-brutal-lg'
              : 'border-2 border-secondary'
          }`}
        >
          ALL CATEGORIES
        </button>
        {INTELLIGENCE_MODES.map(cat => (
          <button
            key={cat.category}
            onClick={() => setSelectedCategory(cat.category)}
            className={`px-4 py-2 font-bold transition-shadow ${
              selectedCategory === cat.category
                ? 'bg-primary text-white shadow-brutal-lg'
                : 'border-2 border-secondary'
            }`}
          >
            {cat.category.split(':')[0]}
          </button>
        ))}
      </div>

      {/* Modes */}
      <div className="space-y-8">
        {filteredModes.map(category => (
          <div key={category.category} className="border-4 border-secondary p-6">
            <div className="flex items-center gap-4 mb-6">
              <category.icon className="w-8 h-8 text-primary" />
              <h2 className="text-brutal-lg">{category.category}</h2>
              <div className="text-sm text-muted">
                {category.modes.filter(m => m.built).length}/{category.modes.length} built
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              {category.modes.map(mode => (
                <ModeCard key={mode.id} mode={mode} />
              ))}
            </div>
          </div>
        ))}
      </div>

      {filteredModes.length === 0 && (
        <div className="text-center py-12 border-4 border-secondary/50">
          <p className="text-muted">No modes found matching your filters</p>
        </div>
      )}
    </div>
  )
}

function ModeCard({ mode }: { mode: any }) {
  const impactColors = {
    IMMEDIATE: 'text-accent',
    HIGH: 'text-primary',
    STRATEGIC: 'text-secondary',
    MODERATE: 'text-muted',
    MARKETING: 'text-accent',
  }

  return (
    <div className={`
      border-2 p-4 transition-all
      ${mode.built
        ? 'border-secondary hover:shadow-brutal cursor-pointer'
        : 'border-secondary/30 opacity-60'
      }
    `}>
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-muted">MODE {mode.id}</span>
          {mode.built && (
            <span className="px-2 py-0.5 bg-accent text-white text-xs font-bold">
              LIVE
            </span>
          )}
          {!mode.built && (
            <span className="px-2 py-0.5 border border-secondary text-xs">
              SOON
            </span>
          )}
        </div>
        <span className={`text-xs font-bold ${impactColors[mode.impact as keyof typeof impactColors]}`}>
          {mode.impact}
        </span>
      </div>

      <h3 className="font-display text-lg mb-2">{mode.name}</h3>
      <p className="text-sm text-muted">{mode.description}</p>

      {mode.built && (
        <Link
          href={`/execute?mode=${mode.id}`}
          className="mt-4 block text-center py-2 border-2 border-primary text-primary font-bold hover:bg-primary hover:text-white transition-colors"
        >
          EXECUTE →
        </Link>
      )}
    </div>
  )
}
