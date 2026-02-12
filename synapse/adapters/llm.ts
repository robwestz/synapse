import type {
  CanonicalConcept,
  IntentSignature,
  SerpProfile,
  SynapseFamily,
  SynapseSubtype,
} from "../kernel/contracts";
import { buildVectorFingerprint, mapConcept } from "../kernel/taxonomy";

export interface LlmMessageInput {
  system: string;
  user: string;
  model?: string;
  maxTokens?: number;
}

export interface LlmClient {
  generate(input: LlmMessageInput): Promise<string>;
}

export interface LlmPromptVersions {
  intent_extraction: string;
  concept_canonicalization: string;
  synapse_classification: string;
}

export interface IntentExtractionInput {
  phrase: string;
  market: string;
  taxonomyTokens: string[];
  serpProfile: SerpProfile;
}

export interface IntentExtractionOutput {
  phrase: string;
  signature: IntentSignature;
  prompt_version: string;
  raw: unknown;
}

export interface ConceptCanonicalizationInput {
  concepts: string[];
  market: string;
}

export interface SynapseClassificationInput {
  phraseA: string;
  phraseB: string;
  serpOverlap: number;
  conceptOverlap: number;
  perspectiveDelta: number;
  intentDelta: number;
  entityOverlap: number;
  sharedConcepts: string[];
  conceptsOnlyA: string[];
  conceptsOnlyB: string[];
  perspectiveA: string;
  perspectiveB: string;
}

export interface SynapseClassificationOutput {
  family: SynapseFamily;
  subtype: SynapseSubtype;
  explanation: string;
  actionable_insight: string;
  contradiction: boolean;
  risk_notes?: string;
  prompt_version: string;
  raw: unknown;
}

interface LlmAdapterConfig {
  model?: string;
  maxTokens?: number;
  retryMax?: number;
}

const DEFAULT_PROMPT_VERSIONS: LlmPromptVersions = {
  intent_extraction: "3.0",
  concept_canonicalization: "2.0",
  synapse_classification: "2.0",
};

const INTENT_SYSTEM = `You are an SEO analysis agent that produces comparable semantic signatures for search phrases.

Your task: Given a search phrase, market, taxonomy tokens, and optional SERP results, produce an IntentSignature JSON object.

## Output Schema

{
  "canonical_concepts": [                    // REQUIRED: At least 2-3 concepts
    {
      "token": "string",                    // UPPERCASE taxonomy token (from taxonomy_tokens) or "NEW:TOKEN_NAME" for novel concepts
      "weight": 0.0-1.0,                    // Importance of this concept to the phrase
      "evidence": "string",                 // Why this concept applies (cite SERP titles/descriptions if available)
      "source_terms": ["string"],           // Actual words FROM THE INPUT PHRASE (e.g. "mäklare", "bolån") — NEVER taxonomy tokens
      "confidence": 0.0-1.0                 // How confident you are in this mapping
    }
  ],
  "promises": [                              // What the content promises to deliver (same structure as canonical_concepts)
    { "token": "string", "weight": 0.0-1.0, "evidence": "string", "source_terms": ["string"], "confidence": 0.0-1.0 }
  ],
  "action_verbs": ["string"],               // Verbs implying user action: "jämför", "köp", "ansök", "lär dig"
  "trust_signals": [                         // Credibility indicators (same structure as canonical_concepts)
    { "token": "string", "weight": 0.0-1.0, "evidence": "string", "source_terms": ["string"], "confidence": 0.0-1.0 }
  ],
  "perspective": {
    "primary": "enum",                       // One of: "seeker" | "advisor" | "provider" | "educator" | "regulator" | "neutral"
    "secondary": "string|null",              // Optional secondary perspective
    "confidence": 0.0-1.0,
    "evidence": "string"                     // Explain WHY this perspective (cite SERP page types, title patterns)
  },
  "intent_gradient": {
    "value": 0.0-1.0,                       // 0.0 = purely informational → 1.0 = purely transactional
    "label": "string",                       // One of: "informational", "educational", "investigational", "commercial_investigation", "comparison", "navigational", "transactional"
    "confidence": 0.0-1.0
  },
  "required_elements": ["string"],           // Content elements needed: "price_table", "comparison_matrix", "step_by_step", "calculator"
  "format": "string",                        // One of: "comparison_page" | "guide" | "landing_page" | "listicle" | "tool" | "blog_post" | "product_page" | "category_page" | "faq" | "definition"
  "incompatibility_markers": ["string"],     // Terms/concepts that would NOT belong on this page
  "emergent_meaning": "string",              // The implicit need behind the search (not the literal words)
  "confidence_by_field": {
    "concepts": 0.0-1.0,
    "perspective": 0.0-1.0,
    "intent_gradient": 0.0-1.0,
    "trust_signals": 0.0-1.0,
    "format": 0.0-1.0,
    "overall": 0.0-1.0
  }
}

## Perspective Descriptions
- "seeker": Person looking for information, solutions, or answers (e.g., "hur fungerar bolån")
- "advisor": Professional giving guidance/recommendations (e.g., "bästa lånevillkor 2025")
- "provider": Company/service offering products (e.g., "bolån från 2.99%")
- "educator": Teaching/explaining concepts (e.g., "vad är amorteringskrav")
- "regulator": Legal/regulatory context (e.g., "finansinspektionen regler bolån")
- "neutral": Ambiguous or no clear perspective signal

## Intent Gradient Scale
- 0.0-0.15: informational — pure knowledge seeking
- 0.15-0.30: educational — learning a concept or process
- 0.30-0.45: investigational — researching options broadly
- 0.45-0.60: commercial_investigation — evaluating specific options
- 0.60-0.75: comparison — actively comparing to decide
- 0.75-0.85: navigational — seeking specific brand/site
- 0.85-1.0: transactional — ready to act/buy/apply

## Rules
1. Use taxonomy_tokens from input for canonical_concepts. If a concept has no match, use "NEW:CONCEPT_NAME".
2. Always produce at least 2-3 canonical_concepts with meaningful weights.
3. source_terms MUST be actual words or substrings from the input phrase (e.g. "mäklare", "stockholm", "ränta"). NEVER put taxonomy tokens (like "CHOICE", "COST") in source_terms.
4. If SERP results are provided, use them as evidence: page titles indicate intent, page types indicate perspective.
5. When SERP data shows mostly provider/commercial pages → lean toward "provider" perspective and higher intent_gradient.
6. When SERP data shows guides/wikis/forums → lean toward "seeker"/"educator" and lower intent_gradient.
7. Set confidence lower (0.3-0.5) when evidence is weak; higher (0.7-0.9) when SERP data strongly supports your classification.

## Example

Input phrase: "jämför bolån ränta"
Market: se

Output:
{
  "canonical_concepts": [
    {"token": "CHOICE", "weight": 0.9, "evidence": "SERP dominated by comparison tools and listicles", "source_terms": ["jämför"], "confidence": 0.85},
    {"token": "COST", "weight": 0.8, "evidence": "'ränta' directly maps to cost/pricing", "source_terms": ["ränta"], "confidence": 0.9},
    {"token": "FINANCING", "weight": 0.7, "evidence": "'bolån' is mortgage financing", "source_terms": ["bolån"], "confidence": 0.9}
  ],
  "promises": [
    {"token": "CHOICE", "weight": 0.8, "evidence": "comparison implies presenting choices", "source_terms": ["jämför"], "confidence": 0.8}
  ],
  "action_verbs": ["jämför"],
  "trust_signals": [
    {"token": "AUTHORITY", "weight": 0.6, "evidence": "comparison sites need credible rate data", "source_terms": [], "confidence": 0.6}
  ],
  "perspective": {"primary": "seeker", "secondary": "advisor", "confidence": 0.8, "evidence": "User wants to compare rates; SERP shows aggregator/comparison sites"},
  "intent_gradient": {"value": 0.65, "label": "comparison", "confidence": 0.85},
  "required_elements": ["comparison_matrix", "rate_table", "bank_list"],
  "format": "comparison_page",
  "incompatibility_markers": ["ansök", "kreditkort"],
  "emergent_meaning": "User wants to find the best mortgage rate by comparing multiple lenders",
  "confidence_by_field": {"concepts": 0.85, "perspective": 0.8, "intent_gradient": 0.85, "trust_signals": 0.6, "format": 0.8, "overall": 0.78}
}

Respond ONLY with valid JSON. No explanations, no markdown, no wrapping.`;

const CANONICALIZATION_SYSTEM = `You are a concept mapping agent. Your task: map raw concept strings to canonical taxonomy tokens.

## Input
You receive a list of concept strings and a market code.

## Output Schema
{
  "canonical_concepts": [
    {
      "token": "string",         // UPPERCASE taxonomy token or "NEW:TOKEN_NAME"
      "weight": 0.0-1.0,        // Relevance weight
      "evidence": "string",     // Why this mapping was chosen
      "source_terms": ["string"], // The original input concept strings (NOT taxonomy tokens)
      "confidence": 0.0-1.0     // Mapping confidence
    }
  ]
}

## Mapping Rules
1. Exact match in taxonomy → use that token (e.g., "jämför" → "CHOICE")
2. Partial/semantic match → use closest token (e.g., "billigast" → "COST")
3. No match → "NEW:CONCEPT_NAME" in UPPERCASE (e.g., "kryptovaluta" → "NEW:KRYPTOVALUTA")
4. One input term can map to one token only
5. Preserve all input concepts — do not drop any

## Example
Input: {"concepts": ["jämföra", "pris", "blockkedja"], "market": "se"}
Output:
{
  "canonical_concepts": [
    {"token": "CHOICE", "weight": 0.8, "evidence": "jämföra = compare → CHOICE", "source_terms": ["jämföra"], "confidence": 0.9},
    {"token": "COST", "weight": 0.7, "evidence": "pris = price → COST", "source_terms": ["pris"], "confidence": 0.9},
    {"token": "NEW:BLOCKKEDJA", "weight": 0.5, "evidence": "no taxonomy match for blockchain concept", "source_terms": ["blockkedja"], "confidence": 0.7}
  ]
}

Respond ONLY with valid JSON. No explanations, no markdown, no wrapping.`;

const CLASSIFICATION_SYSTEM = `You are a relationship classification agent. Your task: classify the semantic relationship between two search phrases based on their overlap metrics.

## Input
You receive two phrases with their perspectives, plus computed overlap metrics:
- serp_overlap: Jaccard similarity of top SERP URLs (0-1)
- concept_overlap: Shared canonical concepts ratio (0-1)
- perspective_delta: Perspective distance (0-1, higher = more different)
- intent_delta: Intent gradient difference (0-1, higher = more different)
- entity_overlap: Shared named entities ratio (0-1)
- shared_concepts, concepts_only_a, concepts_only_b: Concept token lists

## Output Schema
{
  "family": "EXPANSION | TRANSITION | BOUNDARY | CONTEXTUAL",
  "subtype": "string",       // See subtype list below
  "explanation": "string",   // 1-2 sentence explanation of the relationship
  "actionable_insight": "string",  // SEO recommendation based on this relationship
  "contradiction": false,    // true if phrases would confuse users if on same page
  "risk_notes": "string|null"  // Cannibalization or anchor text risks
}

## Family Definitions
- EXPANSION: Same core topic, one phrase adds detail or variation. High concept overlap, low intent/perspective delta.
- TRANSITION: Topic shifts in intent or procedure. Moderate concept overlap, intent_delta > 0.3 typically.
- BOUNDARY: Different perspectives on same topic. Perspective_delta > 0.4, may share entities but not SERP results.
- CONTEXTUAL: Loosely related topics, low direct overlap but topically relevant. Low concept overlap, different SERP results.

## Subtypes
EXPANSION family:
  - "attribute_expansion": Adds a qualifier/attribute (e.g., "bolån" → "bolån utan kontantinsats")
  - "facet_transform": Different facet of same entity (e.g., "bolån ränta" → "bolån amortering")
  - "taxonomic": Parent-child or sibling relationship (e.g., "lån" → "bolån")

TRANSITION family:
  - "intent_shift": Same topic but different intent level (e.g., "vad är bolån" → "ansök bolån")
  - "procedural_chain": Sequential steps in a process (e.g., "jämför bolån" → "ansök bolån")
  - "perspective_shift": Same topic from different actor viewpoint

BOUNDARY family:
  - "perspective_inversion": Opposite perspectives (seeker↔provider) on same topic
  - "problem_solution": Problem statement ↔ solution (e.g., "hög ränta" → "byta bank bolån")
  - "domain_boundary": Related but different professional domains

CONTEXTUAL family:
  - "contextual_bridge": Topically adjacent, useful for content strategy
  - "topical_authority": Supports authority on broader topic
  - "entity_association": Shared entities but different topics

## Decision Guide
1. concept_overlap > 0.6 AND intent_delta < 0.2 AND perspective_delta < 0.2 → EXPANSION
2. concept_overlap > 0.3 AND intent_delta > 0.3 → TRANSITION (likely intent_shift)
3. perspective_delta > 0.4 → BOUNDARY (check if perspective_inversion or problem_solution)
4. concept_overlap < 0.3 AND serp_overlap < 0.2 → CONTEXTUAL
5. If shared_concepts exist but SERPs are very different → BOUNDARY or CONTEXTUAL

## Example
Input: phrase_a="jämför bolån", phrase_b="ansök bolån online", serp_overlap=0.15, concept_overlap=0.5, perspective_delta=0.1, intent_delta=0.4, entity_overlap=0.7
Output:
{
  "family": "TRANSITION",
  "subtype": "procedural_chain",
  "explanation": "Both are about mortgages but 'jämför' is comparison (mid-funnel) while 'ansök online' is application (bottom-funnel), forming a natural conversion sequence.",
  "actionable_insight": "Link from comparison content to application page with clear CTA. These represent sequential steps in the user journey.",
  "contradiction": false,
  "risk_notes": "Low cannibalization risk due to distinct intent, but ensure comparison page doesn't compete for 'ansök' keywords."
}

Respond ONLY with valid JSON. No explanations, no markdown, no wrapping.`;

function extractJsonCandidate(text: string): string {
  const raw = text.trim();
  if (!raw) throw new Error("Empty LLM response");
  const fence = raw.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fence?.[1]) return fence[1].trim();
  const firstBrace = raw.indexOf("{");
  const lastBrace = raw.lastIndexOf("}");
  if (firstBrace >= 0 && lastBrace > firstBrace) return raw.slice(firstBrace, lastBrace + 1);
  return raw;
}

function parseJson(text: string): unknown {
  return JSON.parse(extractJsonCandidate(text));
}

function clamp01(n: number): number {
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

function normalizeConcept(item: any, market: string): CanonicalConcept {
  const tokenIn = typeof item?.token === "string" ? item.token : "";
  const mapped = tokenIn.startsWith("NEW:") || tokenIn.toUpperCase() === tokenIn
    ? tokenIn
    : mapConcept(tokenIn, market).token;
  return {
    token: mapped || "NEW:UNKNOWN",
    weight: clamp01(Number(item?.weight ?? 0.5)),
    evidence: typeof item?.evidence === "string" ? item.evidence : "no_evidence",
    source_terms: Array.isArray(item?.source_terms) ? item.source_terms.filter((x: unknown) => typeof x === "string") : [],
    confidence: clamp01(Number(item?.confidence ?? 0.6)),
  };
}

function normalizeIntentSignature(payload: any, market: string): IntentSignature {
  const concepts = Array.isArray(payload?.canonical_concepts) ? payload.canonical_concepts.map((c: unknown) => normalizeConcept(c, market)) : [];
  const promises = Array.isArray(payload?.promises) ? payload.promises.map((c: unknown) => normalizeConcept(c, market)) : [];
  const trust = Array.isArray(payload?.trust_signals) ? payload.trust_signals.map((c: unknown) => normalizeConcept(c, market)) : [];
  const sig: IntentSignature = {
    canonical_concepts: concepts,
    promises,
    action_verbs: Array.isArray(payload?.action_verbs) ? payload.action_verbs.filter((x: unknown) => typeof x === "string") : [],
    trust_signals: trust,
    perspective: {
      primary: (payload?.perspective?.primary ?? "neutral") as IntentSignature["perspective"]["primary"],
      secondary: typeof payload?.perspective?.secondary === "string" ? payload.perspective.secondary : undefined,
      confidence: clamp01(Number(payload?.perspective?.confidence ?? 0.6)),
      evidence: typeof payload?.perspective?.evidence === "string" ? payload.perspective.evidence : "no_evidence",
    },
    intent_gradient: {
      value: clamp01(Number(payload?.intent_gradient?.value ?? 0.5)),
      label: typeof payload?.intent_gradient?.label === "string" ? payload.intent_gradient.label : "unknown",
      confidence: clamp01(Number(payload?.intent_gradient?.confidence ?? 0.6)),
    },
    required_elements: Array.isArray(payload?.required_elements) ? payload.required_elements.filter((x: unknown) => typeof x === "string") : [],
    format: typeof payload?.format === "string" ? payload.format : "unknown",
    incompatibility_markers: Array.isArray(payload?.incompatibility_markers) ? payload.incompatibility_markers.filter((x: unknown) => typeof x === "string") : [],
    emergent_meaning: typeof payload?.emergent_meaning === "string" ? payload.emergent_meaning : "",
    confidence_by_field: {
      concepts: clamp01(Number(payload?.confidence_by_field?.concepts ?? 0.6)),
      perspective: clamp01(Number(payload?.confidence_by_field?.perspective ?? 0.6)),
      intent_gradient: clamp01(Number(payload?.confidence_by_field?.intent_gradient ?? 0.6)),
      trust_signals: clamp01(Number(payload?.confidence_by_field?.trust_signals ?? 0.6)),
      format: clamp01(Number(payload?.confidence_by_field?.format ?? 0.6)),
      overall: clamp01(Number(payload?.confidence_by_field?.overall ?? 0.6)),
    },
    vector_fingerprint: [],
  };
  sig.vector_fingerprint = buildVectorFingerprint(sig.canonical_concepts);
  return sig;
}

export class LlmAdapter {
  private readonly model: string;
  private readonly maxTokens: number;
  private readonly retryMax: number;
  private readonly promptVersions: LlmPromptVersions;

  constructor(
    private readonly client: LlmClient,
    config: LlmAdapterConfig = {},
    promptVersions: Partial<LlmPromptVersions> = {},
  ) {
    this.model = config.model ?? process.env.LLM_MODEL ?? "claude-sonnet-4-20250514";
    this.maxTokens = config.maxTokens ?? Number(process.env.LLM_MAX_TOKENS ?? 4000);
    this.retryMax = config.retryMax ?? 3;
    this.promptVersions = { ...DEFAULT_PROMPT_VERSIONS, ...promptVersions };
  }

  getPromptVersions(): LlmPromptVersions {
    return { ...this.promptVersions };
  }

  private async callJson(system: string, user: string): Promise<unknown> {
    let promptUser = user;
    let lastErr: unknown = null;
    for (let attempt = 1; attempt <= this.retryMax; attempt++) {
      try {
        const text = await this.client.generate({
          system,
          user: promptUser,
          model: this.model,
          maxTokens: this.maxTokens,
        });
        return parseJson(text);
      } catch (err) {
        lastErr = err;
        promptUser = `${user}\n\nIMPORTANT: Respond ONLY with valid JSON. No explanations, no markdown fences.`;
      }
    }
    throw new Error(`LLM JSON parse failed after ${this.retryMax} attempts: ${String(lastErr)}`);
  }

  async intentExtraction(input: IntentExtractionInput): Promise<IntentExtractionOutput> {
    const userData = JSON.stringify({
      phrase: input.phrase,
      market: input.market,
      taxonomy_tokens: input.taxonomyTokens,
      serp_top: input.serpProfile.results.slice(0, 10),
    }, null, 2);
    const json = await this.callJson(
      INTENT_SYSTEM,
      `Analyze this search phrase and produce an IntentSignature.\nThe taxonomy_tokens list contains all valid concept tokens — use them for canonical_concepts.\nUse SERP results as evidence for perspective and intent classification.\n\n${userData}`,
    );
    const payload = json as any;
    return {
      phrase: input.phrase,
      signature: normalizeIntentSignature(payload.signature ?? payload, input.market),
      prompt_version: this.promptVersions.intent_extraction,
      raw: json,
    };
  }

  async conceptCanonicalization(input: ConceptCanonicalizationInput): Promise<{ canonical_concepts: CanonicalConcept[]; prompt_version: string; raw: unknown }> {
    const json = await this.callJson(
      CANONICALIZATION_SYSTEM,
      JSON.stringify({
        concepts: input.concepts,
        market: input.market,
      }),
    );
    const payload = json as any;
    const list = Array.isArray(payload?.canonical_concepts)
      ? payload.canonical_concepts.map((c: unknown) => normalizeConcept(c, input.market))
      : input.concepts.map((c) => normalizeConcept({ token: mapConcept(c, input.market).token, weight: 0.5, confidence: 0.6 }, input.market));
    return {
      canonical_concepts: list,
      prompt_version: this.promptVersions.concept_canonicalization,
      raw: json,
    };
  }

  async synapseClassification(input: SynapseClassificationInput): Promise<SynapseClassificationOutput> {
    const userData = JSON.stringify({
      phrase_a: input.phraseA,
      phrase_b: input.phraseB,
      serp_overlap: input.serpOverlap,
      concept_overlap: input.conceptOverlap,
      perspective_delta: input.perspectiveDelta,
      intent_delta: input.intentDelta,
      entity_overlap: input.entityOverlap,
      shared_concepts: input.sharedConcepts,
      concepts_only_a: input.conceptsOnlyA,
      concepts_only_b: input.conceptsOnlyB,
      perspective_a: input.perspectiveA,
      perspective_b: input.perspectiveB,
    }, null, 2);
    const json = await this.callJson(
      CLASSIFICATION_SYSTEM,
      `Classify the relationship between these two search phrases based on the provided metrics.\n\n${userData}`,
    );
    const payload = json as any;
    return {
      family: (payload.family ?? "TRANSITION") as SynapseFamily,
      subtype: (payload.subtype ?? "contextual_bridge") as SynapseSubtype,
      explanation: typeof payload.explanation === "string" ? payload.explanation : "",
      actionable_insight: typeof payload.actionable_insight === "string" ? payload.actionable_insight : "",
      contradiction: Boolean(payload.contradiction),
      risk_notes: typeof payload.risk_notes === "string" ? payload.risk_notes : undefined,
      prompt_version: this.promptVersions.synapse_classification,
      raw: json,
    };
  }
}
