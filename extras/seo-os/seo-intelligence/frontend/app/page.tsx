'use client'

import { useState } from 'react'
import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center space-y-6 py-12">
        <h1 className="text-brutal-xl text-primary">
          OBLITERATE AHREFS
        </h1>

        <p className="text-2xl font-bold max-w-3xl mx-auto">
          Extract <span className="text-primary">EVERY strategic insight</span> hiding in your Ahrefs data
          that they deliberately keep obscured.
        </p>

        <div className="flex justify-center gap-4 mt-8">
          <Link
            href="/upload"
            className="px-8 py-4 bg-primary text-white font-display text-lg shadow-brutal hover:shadow-brutal-lg transition-shadow"
          >
            UPLOAD DATA
          </Link>

          <Link
            href="/modes"
            className="px-8 py-4 bg-secondary text-white font-display text-lg shadow-brutal hover:shadow-brutal-lg transition-shadow"
          >
            VIEW 50+ MODES
          </Link>
        </div>
      </section>

      {/* Value Prop */}
      <section className="grid md:grid-cols-3 gap-8">
        <div className="border-4 border-secondary p-6 shadow-brutal">
          <h3 className="text-brutal-md mb-4">AHREFS</h3>
          <ul className="space-y-2 text-muted">
            <li>❌ Shows you data</li>
            <li>❌ 50 filters that reveal nothing</li>
            <li>❌ $999/month</li>
            <li>❌ Keeps you stupid</li>
            <li>❌ Business model: sell data</li>
          </ul>
        </div>

        <div className="border-4 border-primary p-6 shadow-brutal-lg">
          <h3 className="text-brutal-md text-primary mb-4">US</h3>
          <ul className="space-y-2">
            <li>✅ Shows you WHAT TO DO</li>
            <li>✅ 50+ intelligence modes</li>
            <li>✅ $99/month</li>
            <li>✅ Makes you dangerous</li>
            <li>✅ Business model: sell intelligence</li>
          </ul>
        </div>

        <div className="border-4 border-accent p-6 shadow-brutal">
          <h3 className="text-brutal-md text-accent mb-4">THE DIFFERENCE</h3>
          <ul className="space-y-2">
            <li>🎯 AI-powered insights</li>
            <li>🎯 Strategic recommendations</li>
            <li>🎯 Actionable opportunities</li>
            <li>🎯 Competitive intelligence</li>
            <li>🎯 Predictive analytics</li>
          </ul>
        </div>
      </section>

      {/* Example Modes */}
      <section className="space-y-6">
        <h2 className="text-brutal-lg text-center">SAMPLE INTELLIGENCE MODES</h2>

        <div className="grid md:grid-cols-2 gap-6">
          <ModeCard
            mode="1.1"
            name="Cluster Dominance Matrix"
            description="Identify which parent topics competitors dominate. Find 8x traffic opportunities where they own 81% of keywords and you have 18%."
            impact="HIGH"
          />

          <ModeCard
            mode="1.2"
            name="Longtail Gap Finder"
            description="Find 847 longtail keywords (5+ words) competitors rank for that you're missing. Low competition, high conversion."
            impact="IMMEDIATE"
          />

          <ModeCard
            mode="3.1"
            name="Common Linker Discovery"
            description="87 domains link to your top 3 competitors but not you. Here's TechCrunch (DR 91). Here's the exact pitch."
            impact="HIGH"
          />

          <ModeCard
            mode="8.4"
            name="Competitive Moat Score"
            description="Competitor moat score: 87/100. Breaking their dominance requires 2-3 years + $500K. Instead, target these adjacent keywords..."
            impact="STRATEGIC"
          />
        </div>

        <div className="text-center mt-8">
          <Link
            href="/modes"
            className="inline-block px-6 py-3 border-4 border-secondary shadow-brutal hover:shadow-brutal-lg transition-shadow font-bold"
          >
            VIEW ALL 50+ MODES →
          </Link>
        </div>
      </section>

      {/* Pricing */}
      <section className="space-y-6">
        <h2 className="text-brutal-lg text-center">PRICING</h2>

        <div className="grid md:grid-cols-4 gap-6">
          <PricingCard
            tier="Starter"
            price="$49"
            features={[
              "1 primary site",
              "3 competitors",
              "20 intelligence modes",
              "10 analyses/month",
            ]}
          />

          <PricingCard
            tier="Professional"
            price="$99"
            features={[
              "1 primary site",
              "10 competitors",
              "ALL 50+ modes",
              "Unlimited analyses",
            ]}
            highlight
          />

          <PricingCard
            tier="Enterprise"
            price="$299"
            features={[
              "5 primary sites",
              "50 competitors",
              "Custom modes",
              "White-label reports",
            ]}
          />

          <PricingCard
            tier="FUCK YOU AHREFS"
            price="$999"
            features={[
              "Same price as Ahrefs",
              "Actual intelligence",
              "Unlimited everything",
              "Make them obsolete",
            ]}
            special
          />
        </div>
      </section>

      {/* CTA */}
      <section className="text-center py-12 border-4 border-primary bg-primary/5">
        <h2 className="text-brutal-lg mb-6">READY TO OBLITERATE THE COMPETITION?</h2>
        <p className="text-xl mb-8">Upload your Ahrefs exports. Get insights in seconds.</p>

        <Link
          href="/upload"
          className="inline-block px-12 py-6 bg-primary text-white font-display text-2xl shadow-brutal-lg hover:shadow-brutal transition-shadow"
        >
          START OBLITERATING →
        </Link>
      </section>
    </div>
  )
}

function ModeCard({ mode, name, description, impact }: any) {
  const impactColors = {
    HIGH: 'text-primary',
    IMMEDIATE: 'text-accent',
    STRATEGIC: 'text-secondary',
  }

  return (
    <div className="border-4 border-secondary p-6 hover:shadow-brutal transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <span className="font-mono text-sm text-muted">MODE {mode}</span>
        <span className={`font-bold ${impactColors[impact as keyof typeof impactColors]}`}>
          {impact}
        </span>
      </div>

      <h3 className="font-display text-xl mb-3">{name}</h3>
      <p className="text-sm">{description}</p>
    </div>
  )
}

function PricingCard({ tier, price, features, highlight, special }: any) {
  return (
    <div className={`
      border-4 p-6 space-y-4
      ${highlight ? 'border-primary bg-primary/5 shadow-brutal-lg' : 'border-secondary'}
      ${special ? 'border-accent bg-accent/5' : ''}
    `}>
      <h3 className="font-display text-xl">{tier}</h3>
      <p className="text-brutal-md">{price}<span className="text-base">/mo</span></p>

      <ul className="space-y-2 text-sm">
        {features.map((feature: string, i: number) => (
          <li key={i}>✓ {feature}</li>
        ))}
      </ul>

      <button className={`
        w-full py-3 font-bold
        ${highlight ? 'bg-primary text-white' : 'border-2 border-secondary'}
      `}>
        SELECT
      </button>
    </div>
  )
}
