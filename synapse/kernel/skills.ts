export type SkillId =
  | "serp_overlap"
  | "concept_overlap"
  | "intent_distance"
  | "perspective_distance"
  | "synapse_strength"
  | "mmr_selection"
  | "community_detection"
  | "cluster_signature_aggregation";

export interface SkillDefinition {
  id: SkillId;
  version: string;
  description: string;
  input: string[];
  output: Record<string, string>;
  constraints?: Record<string, unknown>;
}

export const SKILLS: Record<SkillId, SkillDefinition> = {
  serp_overlap: {
    id: "serp_overlap",
    version: "1.0",
    description: "Jaccard overlap between two SERP URL lists.",
    input: ["serp_urls_a[]", "serp_urls_b[]"],
    output: { overlap: "0..1", shared_urls: "string[]" },
    constraints: { normalization: "jaccard_on_urls", min_results_per_serp: 3 },
  },
  concept_overlap: {
    id: "concept_overlap",
    version: "1.0",
    description: "Weighted Jaccard for canonical concept sets.",
    input: ["concepts_a[]", "concepts_b[]"],
    output: { overlap: "0..1", shared: "string[]", only_a: "string[]", only_b: "string[]" },
    constraints: { weighting: "by_weight", min_concepts: 2 },
  },
  intent_distance: {
    id: "intent_distance",
    version: "1.0",
    description: "Absolute distance in intent gradient.",
    input: ["intent_a", "intent_b"],
    output: { distance: "0..1", proximity: "0..1" },
  },
  perspective_distance: {
    id: "perspective_distance",
    version: "1.0",
    description: "Perspective alignment and inversion check.",
    input: ["perspective_a", "perspective_b"],
    output: { alignment: "0..1", is_inversion: "boolean" },
  },
  synapse_strength: {
    id: "synapse_strength",
    version: "1.0",
    description: "Composite synapse strength with contradiction handling.",
    input: [
      "serp_overlap",
      "concept_overlap",
      "perspective_alignment",
      "entity_overlap",
      "intent_proximity",
    ],
    output: { strength: "0..1", contradiction: "boolean", signals_present: "number" },
  },
  mmr_selection: {
    id: "mmr_selection",
    version: "1.0",
    description: "Maximum marginal relevance selection.",
    input: ["candidates[]", "k", "lambda"],
    output: { selected_ids: "string[]", dropped_ids: "string[]" },
  },
  community_detection: {
    id: "community_detection",
    version: "1.0",
    description: "Community clustering from adjacency matrix.",
    input: ["adjacency_matrix", "node_ids[]"],
    output: { clusters: "string[][]", modularity: "number" },
  },
  cluster_signature_aggregation: {
    id: "cluster_signature_aggregation",
    version: "1.0",
    description: "Aggregates node signatures into a cluster signature.",
    input: ["node_signatures[]"],
    output: { cluster_signature: "object" },
  },
};
