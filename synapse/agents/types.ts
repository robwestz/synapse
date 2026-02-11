export type AgentId =
  | "discovery_agent"
  | "extraction_agent"
  | "synapse_agent"
  | "cluster_agent"
  | "validation_agent";

export interface AgentContext {
  runId: string;
  ticketId?: string;
  profileVersion?: string;
  nowIso: string;
}

export interface AgentWarning {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface AgentResult<TOutput = unknown> {
  agentId: AgentId;
  ok: boolean;
  output: TOutput;
  warnings: AgentWarning[];
  durationMs: number;
}

export interface BaseAgent<TInput = unknown, TOutput = unknown> {
  readonly id: AgentId;
  validate(input: TInput): AgentWarning[];
  run(input: TInput, ctx: AgentContext): Promise<AgentResult<TOutput>>;
}

export interface CandidateSeed {
  phrase: string;
  market: string;
  language: string;
}

export interface CandidateQuery {
  phrase: string;
  source:
    | "seed"
    | "ahrefs_also_rank"
    | "ahrefs_related"
    | "ahrefs_matching"
    | "ahrefs_suggestions"
    | "serp_metadata"
    | "edge_seeding";
  score?: number;
  tags?: string[];
}

export interface IntentSignatureLite {
  perspective: string;
  intentGradient: number;
  canonicalConcepts: Array<{ token: string; weight: number }>;
  confidence: number;
}

export interface SynapseEdgeLite {
  from: string;
  to: string;
  strength: number;
  family: "EXPANSION" | "TRANSITION" | "BOUNDARY" | "CONTEXTUAL";
  contradiction: boolean;
}

export interface ClusterLite {
  id: string;
  label: string;
  nodeIds: string[];
  cohesion: number;
}
