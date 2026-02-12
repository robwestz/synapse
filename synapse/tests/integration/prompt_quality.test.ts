/**
 * Prompt Quality Test
 *
 * Verifies that the new rich prompts produce correct signatures
 * when the LLM returns realistic (non-trivial) JSON responses.
 *
 * Uses a mock LLM that inspects the system prompt for expected schema
 * guidance and returns realistic Swedish market data.
 */
import test from "node:test";
import assert from "node:assert/strict";
import type { SerpProfile } from "../../kernel/contracts";
import { LlmAdapter, type LlmClient, type LlmMessageInput } from "../../adapters/llm";

/** Mock LLM that returns realistic Swedish market signatures */
class RealisticMockClient implements LlmClient {
  calls: LlmMessageInput[] = [];

  async generate(input: LlmMessageInput): Promise<string> {
    this.calls.push(input);

    // Detect which prompt type based on system message content
    if (input.system.includes("IntentSignature")) {
      return JSON.stringify({
        canonical_concepts: [
          { token: "AGENT", weight: 0.9, evidence: "SERP dominated by real estate agent listings and comparison sites", source_terms: ["mäklare"], confidence: 0.9 },
          { token: "LOCATION", weight: 0.85, evidence: "'stockholm' is a geographic location", source_terms: ["stockholm"], confidence: 0.95 },
          { token: "CHOICE", weight: 0.6, evidence: "SERP shows comparison/listing sites suggesting user wants to choose", source_terms: [], confidence: 0.7 },
        ],
        promises: [
          { token: "CHOICE", weight: 0.7, evidence: "aggregator pages promise comparison of agents", source_terms: ["jämför"], confidence: 0.75 },
        ],
        action_verbs: ["hitta", "jämför", "kontakta"],
        trust_signals: [
          { token: "AUTHORITY", weight: 0.65, evidence: "licensed profession, regulated by FMI", source_terms: ["auktoriserad"], confidence: 0.7 },
        ],
        perspective: {
          primary: "seeker",
          secondary: "advisor",
          confidence: 0.85,
          evidence: "SERP shows aggregator and comparison sites targeting home sellers looking for agents",
        },
        intent_gradient: {
          value: 0.55,
          label: "commercial_investigation",
          confidence: 0.8,
        },
        required_elements: ["agent_list", "ratings", "price_comparison", "area_coverage"],
        format: "comparison_page",
        incompatibility_markers: ["hyresrätt", "bostadsrätt till salu"],
        emergent_meaning: "Home seller in Stockholm seeking to compare and select a real estate agent",
        confidence_by_field: {
          concepts: 0.88,
          perspective: 0.85,
          intent_gradient: 0.8,
          trust_signals: 0.7,
          format: 0.82,
          overall: 0.81,
        },
      });
    }

    if (input.system.includes("relationship classification")) {
      return JSON.stringify({
        family: "EXPANSION",
        subtype: "attribute_expansion",
        explanation: "Both phrases target Stockholm real estate agents, but 'bästa mäklare stockholm' adds a quality qualifier that narrows the search to top-rated agents.",
        actionable_insight: "Create a dedicated 'best agents' page with ratings/reviews data, interlinked from the general Stockholm agents page.",
        contradiction: false,
        risk_notes: "Moderate cannibalization risk — ensure the general page targets broad terms while the 'bästa' page focuses on review-related queries.",
      });
    }

    if (input.system.includes("concept mapping")) {
      return JSON.stringify({
        canonical_concepts: [
          { token: "AGENT", weight: 0.9, evidence: "mäklare = real estate agent → AGENT", source_terms: ["mäklare"], confidence: 0.95 },
          { token: "LOCATION", weight: 0.8, evidence: "stockholm is a location", source_terms: ["stockholm"], confidence: 0.95 },
        ],
      });
    }

    throw new Error(`Unexpected system prompt: ${input.system.slice(0, 50)}`);
  }
}

function serpFixture(): SerpProfile {
  return {
    query: "mäklare stockholm",
    market: "se",
    fetched_at: "2026-02-11T00:00:00.000Z",
    source: "ahrefs_cached",
    results: [
      { rank: 1, url: "https://www.maklarstatistik.se/stockholm", title: "Bästa mäklarna i Stockholm 2025", description: "Jämför mäklare i Stockholm", page_type: "aggregator", perspective: "advisor", intent: "commercial", key_concepts: ["AGENT", "LOCATION"] },
      { rank: 2, url: "https://www.hemnet.se/maklare/stockholm", title: "Mäklare Stockholm - Hemnet", description: "Hitta mäklare i Stockholm", page_type: "aggregator", perspective: "advisor", intent: "commercial", key_concepts: ["AGENT", "LOCATION"] },
      { rank: 3, url: "https://www.hittamaklare.se", title: "Hitta Mäklare - Jämför mäklare", description: "Jämför och hitta bästa mäklaren", page_type: "aggregator", perspective: "advisor", intent: "commercial", key_concepts: ["AGENT", "CHOICE"] },
    ],
    intent_distribution_top5: { commercial: 0.8, informational: 0.2 },
    perspective_distribution_top5: { advisor: 0.6, seeker: 0.4 },
    page_type_distribution_top5: { aggregator: 0.6, brand: 0.2, blog: 0.2 },
  };
}

test("intentExtraction with rich prompts produces non-default signature", async () => {
  const client = new RealisticMockClient();
  const adapter = new LlmAdapter(client, { retryMax: 1 });

  const out = await adapter.intentExtraction({
    phrase: "mäklare stockholm",
    market: "se",
    taxonomyTokens: ["AGENT", "LOCATION", "CHOICE", "COST", "AUTHORITY"],
    serpProfile: serpFixture(),
  });

  // Verify non-empty canonical concepts
  assert.ok(out.signature.canonical_concepts.length >= 2, "Should have at least 2 canonical concepts");
  const tokens = out.signature.canonical_concepts.map((c) => c.token);
  assert.ok(tokens.includes("AGENT"), "Should contain AGENT token");
  assert.ok(tokens.includes("LOCATION"), "Should contain LOCATION token");

  // Verify perspective is not default neutral
  assert.notEqual(out.signature.perspective.primary, "neutral", "Perspective should not be default neutral");
  assert.equal(out.signature.perspective.primary, "seeker");
  assert.ok(out.signature.perspective.confidence > 0.6, "Perspective confidence should be meaningful");
  assert.ok(out.signature.perspective.evidence.length > 10, "Perspective evidence should be substantive");

  // Verify intent gradient is not default 0.5
  assert.notEqual(out.signature.intent_gradient.value, 0.5, "Intent gradient should not be default 0.5");
  assert.equal(out.signature.intent_gradient.label, "commercial_investigation");
  assert.ok(out.signature.intent_gradient.confidence > 0.6);

  // Verify non-empty supporting fields
  assert.ok(out.signature.action_verbs.length > 0, "Should have action verbs");
  assert.ok(out.signature.trust_signals.length > 0, "Should have trust signals");
  assert.ok(out.signature.required_elements.length > 0, "Should have required elements");
  assert.notEqual(out.signature.format, "unknown", "Format should not be unknown");
  assert.ok(out.signature.emergent_meaning.length > 10, "Emergent meaning should be substantive");

  // Verify vector fingerprint is computed
  assert.ok(out.signature.vector_fingerprint.length > 0, "Should have vector fingerprint");
  assert.ok(out.signature.vector_fingerprint.some((v) => v > 0), "Fingerprint should have non-zero values");

  // Verify confidence fields are meaningful (not all defaults)
  assert.ok(out.signature.confidence_by_field.overall > 0.7, "Overall confidence should reflect real assessment");

  // Verify prompt version
  assert.equal(out.prompt_version, "3.0");
});

test("system prompt contains schema guidance for IntentSignature", async () => {
  const client = new RealisticMockClient();
  const adapter = new LlmAdapter(client, { retryMax: 1 });

  await adapter.intentExtraction({
    phrase: "test",
    market: "se",
    taxonomyTokens: ["AGENT"],
    serpProfile: serpFixture(),
  });

  const systemPrompt = client.calls[0].system;

  // Verify schema elements are present
  assert.ok(systemPrompt.includes("canonical_concepts"), "System prompt should contain canonical_concepts field");
  assert.ok(systemPrompt.includes("perspective"), "System prompt should contain perspective field");
  assert.ok(systemPrompt.includes("intent_gradient"), "System prompt should contain intent_gradient field");
  assert.ok(systemPrompt.includes("seeker"), "System prompt should list seeker perspective");
  assert.ok(systemPrompt.includes("advisor"), "System prompt should list advisor perspective");
  assert.ok(systemPrompt.includes("provider"), "System prompt should list provider perspective");
  assert.ok(systemPrompt.includes("educator"), "System prompt should list educator perspective");
  assert.ok(systemPrompt.includes("regulator"), "System prompt should list regulator perspective");
  assert.ok(systemPrompt.includes("comparison_page"), "System prompt should list format values");
  assert.ok(systemPrompt.includes("NEW:"), "System prompt should explain NEW: token convention");
  assert.ok(systemPrompt.includes("0.0"), "System prompt should have gradient scale");
  assert.ok(systemPrompt.includes("1.0"), "System prompt should have gradient scale");
});

test("user prompt contains task framing before JSON data", async () => {
  const client = new RealisticMockClient();
  const adapter = new LlmAdapter(client, { retryMax: 1 });

  await adapter.intentExtraction({
    phrase: "mäklare stockholm",
    market: "se",
    taxonomyTokens: ["AGENT", "LOCATION"],
    serpProfile: serpFixture(),
  });

  const userPrompt = client.calls[0].user;

  // Verify task framing prefix
  assert.ok(userPrompt.startsWith("Analyze this search phrase"), "User prompt should start with task framing");
  assert.ok(userPrompt.includes("taxonomy_tokens"), "User prompt should mention taxonomy_tokens");
  assert.ok(userPrompt.includes("SERP"), "User prompt should mention SERP evidence");

  // Verify JSON data is included and pretty-printed
  assert.ok(userPrompt.includes('"mäklare stockholm"'), "User prompt should contain the phrase");
  assert.ok(userPrompt.includes('"AGENT"'), "User prompt should contain taxonomy tokens");
});

test("synapseClassification with rich prompts produces non-default classification", async () => {
  const client = new RealisticMockClient();
  const adapter = new LlmAdapter(client, { retryMax: 1 });

  const out = await adapter.synapseClassification({
    phraseA: "mäklare stockholm",
    phraseB: "bästa mäklare stockholm",
    serpOverlap: 0.45,
    conceptOverlap: 0.8,
    perspectiveDelta: 0.1,
    intentDelta: 0.15,
    entityOverlap: 0.9,
    sharedConcepts: ["AGENT", "LOCATION"],
    conceptsOnlyA: [],
    conceptsOnlyB: ["CHOICE"],
    perspectiveA: "seeker",
    perspectiveB: "seeker",
  });

  assert.equal(out.family, "EXPANSION");
  assert.equal(out.subtype, "attribute_expansion");
  assert.ok(out.explanation.length > 20, "Explanation should be substantive");
  assert.ok(out.actionable_insight.length > 20, "Actionable insight should be substantive");
  assert.equal(out.contradiction, false);
  assert.ok(typeof out.risk_notes === "string" && out.risk_notes.length > 0, "Risk notes should be present");
  assert.equal(out.prompt_version, "2.0");
});

test("classification system prompt contains all families and subtypes", async () => {
  const client = new RealisticMockClient();
  const adapter = new LlmAdapter(client, { retryMax: 1 });

  await adapter.synapseClassification({
    phraseA: "a",
    phraseB: "b",
    serpOverlap: 0.5,
    conceptOverlap: 0.5,
    perspectiveDelta: 0.5,
    intentDelta: 0.5,
    entityOverlap: 0.5,
    sharedConcepts: [],
    conceptsOnlyA: [],
    conceptsOnlyB: [],
    perspectiveA: "seeker",
    perspectiveB: "provider",
  });

  const systemPrompt = client.calls[0].system;

  // Verify all families
  for (const family of ["EXPANSION", "TRANSITION", "BOUNDARY", "CONTEXTUAL"]) {
    assert.ok(systemPrompt.includes(family), `System prompt should contain family ${family}`);
  }

  // Verify all subtypes
  for (const subtype of [
    "attribute_expansion", "facet_transform", "taxonomic",
    "intent_shift", "procedural_chain", "perspective_shift",
    "perspective_inversion", "problem_solution", "domain_boundary",
    "contextual_bridge", "topical_authority", "entity_association",
  ]) {
    assert.ok(systemPrompt.includes(subtype), `System prompt should contain subtype ${subtype}`);
  }

  // Verify user prompt has task framing
  const userPrompt = client.calls[0].user;
  assert.ok(userPrompt.startsWith("Classify the relationship"), "User prompt should start with task framing");
});
