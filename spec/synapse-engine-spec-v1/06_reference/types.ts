// Minimal TS types that mirror the schemas (useful in plugins)
export type Intent =
  | "informational" | "howto" | "commercial" | "transactional"
  | "navigational" | "local" | "freshness";

export type Perspective = "provider" | "seeker" | "advisor" | "regulator" | "neutral";

export type Provenance =
  | "ads_api" | "gsc" | "serp_paa" | "serp_related" | "autocomplete" | "crawl" | "llm_inferred";

export type SynapseType =
  | "shared_entity" | "facet_transform" | "serp_overlap" | "task_chain"
  | "comparative" | "problem_solution" | "intent_shift" | "perspective_shift" | "bridge";

export interface EvidenceItem {
  source: string;
  kind: string;
  summary: string;
  value?: unknown;
  confidence: number; // 0..1
}

export interface SynapseCard {
  from_id: string;
  to_id: string;
  strength: number; // 0..1
  types: SynapseType[];
  direction: "bidirectional" | "unidirectional";
  intent_shift?: string;
  perspective_shift?: string;
  confidence: number;
  bridge_statement: string;
  evidence: EvidenceItem[];
}

export interface GraphNode {
  id: string;
  phrase: string;
  x: number; // 0..1
  y: number; // 0..1
  cluster_id: string;
  intent: Intent | string;
  perspective: Perspective;
  confidence: number;
  provenance: Provenance | string;
  size: number;
  flags?: string[];
}

export interface Cluster {
  id: string;
  label: string;
  color: string;
  node_ids: string[];
  dominant_intent: Intent | string;
  dominant_perspective: Perspective;
  hub_entities?: string[];
  centroid: { x: number; y: number };
}

export interface GraphEdge {
  from: string;
  to: string;
  strength: number;
  types: SynapseType[] | string[];
  synapse_card: SynapseCard;
}

export interface GraphArtifact {
  meta: { version: string; generated_at: string; language: string; market: string };
  seed: { id: string; phrase: string; x: number; y: number; intent: Intent | string; perspective: Perspective };
  nodes: GraphNode[];
  edges: GraphEdge[];
  clusters: Cluster[];
  legend: { intent_axis: string; perspective_axis: string; strength_buckets: { min: number; max: number; label: string }[] };
  warnings?: string[];
}
