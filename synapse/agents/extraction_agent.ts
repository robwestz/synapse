import { AbstractAgent } from "./base_agent";
import type { AgentContext, AgentWarning, CandidateQuery, IntentSignatureLite } from "./types";

export interface ExtractionInput {
  queries: CandidateQuery[];
}

export interface ExtractionOutput {
  signatures: Record<string, IntentSignatureLite>;
}

export class ExtractionAgent extends AbstractAgent<ExtractionInput, ExtractionOutput> {
  readonly id = "extraction_agent" as const;

  validate(input: ExtractionInput): AgentWarning[] {
    const warnings: AgentWarning[] = [];
    if (!input.queries.length) {
      warnings.push({ code: "queries_empty", message: "No queries to extract." });
    }
    return warnings;
  }

  protected async execute(input: ExtractionInput, _ctx: AgentContext): Promise<ExtractionOutput> {
    // Placeholder signature extraction. Ticketed adapters can replace this.
    const signatures: Record<string, IntentSignatureLite> = {};
    for (const q of input.queries) {
      signatures[q.phrase] = {
        perspective: "neutral",
        intentGradient: 0.5,
        canonicalConcepts: [],
        confidence: 0.5,
      };
    }
    return { signatures };
  }
}
