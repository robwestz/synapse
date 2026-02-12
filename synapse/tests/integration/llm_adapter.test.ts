import test from "node:test";
import assert from "node:assert/strict";
import type { SerpProfile } from "../../kernel/contracts";
import { LlmAdapter, type LlmClient, type LlmMessageInput } from "../../adapters/llm";

class QueueClient implements LlmClient {
  constructor(private readonly responses: string[]) {}
  calls: LlmMessageInput[] = [];

  async generate(input: LlmMessageInput): Promise<string> {
    this.calls.push(input);
    const next = this.responses.shift();
    if (next == null) throw new Error("No mock response left");
    return next;
  }
}

function serpFixture(): SerpProfile {
  return {
    query: "mäklare stockholm",
    market: "se",
    fetched_at: "2026-02-11T00:00:00.000Z",
    source: "ahrefs_cached",
    results: [
      {
        rank: 1,
        url: "https://example.com",
        title: "Mäklare Stockholm",
        description: "Beskrivning",
        page_type: "other",
        perspective: "advisor",
        intent: "commercial",
        key_concepts: [],
      },
    ],
    intent_distribution_top5: { commercial: 1 },
    perspective_distribution_top5: { advisor: 1 },
    page_type_distribution_top5: { other: 1 },
  };
}

test("intentExtraction retries invalid JSON then parses valid JSON", async () => {
  const client = new QueueClient([
    "NOT JSON",
    JSON.stringify({
      signature: {
        canonical_concepts: [{ token: "CHOICE", weight: 0.8, evidence: "3/5 titlar", source_terms: ["val"] }],
        promises: [],
        action_verbs: ["jämför"],
        trust_signals: [],
        perspective: { primary: "advisor", confidence: 0.8, evidence: "2/5" },
        intent_gradient: { value: 0.7, label: "commercial_investigation", confidence: 0.8 },
        required_elements: ["pris"],
        format: "landing_page",
        incompatibility_markers: ["forum"],
        emergent_meaning: "Kommersiell jämförelse.",
        confidence_by_field: {
          concepts: 0.8,
          perspective: 0.8,
          intent_gradient: 0.8,
          trust_signals: 0.7,
          format: 0.8,
          overall: 0.8,
        },
      },
    }),
  ]);

  const adapter = new LlmAdapter(client, { retryMax: 3 });
  const out = await adapter.intentExtraction({
    phrase: "mäklare stockholm",
    market: "sv",
    taxonomyTokens: ["CHOICE"],
    serpProfile: serpFixture(),
  });

  assert.equal(client.calls.length, 2);
  assert.equal(out.signature.canonical_concepts[0].token, "CHOICE");
  assert.equal(out.prompt_version, "3.0");
  assert.ok(Array.isArray(out.signature.vector_fingerprint));
});

test("synapseClassification parses typed result and tracks prompt version", async () => {
  const client = new QueueClient([
    JSON.stringify({
      family: "TRANSITION",
      subtype: "intent_shift",
      explanation: "Skift i intent.",
      actionable_insight: "Använd partiell ankartext.",
      contradiction: false,
      risk_notes: "Låg risk",
    }),
  ]);
  const adapter = new LlmAdapter(client);
  const out = await adapter.synapseClassification({
    phraseA: "mäklare",
    phraseB: "värdera bostad",
    serpOverlap: 0.3,
    conceptOverlap: 0.4,
    perspectiveDelta: 0.7,
    intentDelta: 0.6,
    entityOverlap: 0.2,
    sharedConcepts: ["CHOICE"],
    conceptsOnlyA: ["AGENT"],
    conceptsOnlyB: ["VALUATION"],
    perspectiveA: "advisor",
    perspectiveB: "seeker",
  });

  assert.equal(out.family, "TRANSITION");
  assert.equal(out.subtype, "intent_shift");
  assert.equal(out.prompt_version, "2.0");
});
