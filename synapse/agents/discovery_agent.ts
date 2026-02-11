import { AbstractAgent } from "./base_agent";
import type { AgentContext, AgentWarning, CandidateQuery, CandidateSeed } from "./types";

export interface DiscoveryInput {
  seed: CandidateSeed;
  candidates: CandidateQuery[];
  target: number;
}

export interface DiscoveryOutput {
  selected: CandidateQuery[];
  droppedCount: number;
}

export class DiscoveryAgent extends AbstractAgent<DiscoveryInput, DiscoveryOutput> {
  readonly id = "discovery_agent" as const;

  validate(input: DiscoveryInput): AgentWarning[] {
    const warnings: AgentWarning[] = [];
    if (!input.seed.phrase?.trim()) {
      warnings.push({ code: "seed_missing", message: "Seed phrase is empty." });
    }
    if (input.target < 1) {
      warnings.push({ code: "target_invalid", message: "Target must be >= 1." });
    }
    return warnings;
  }

  protected async execute(input: DiscoveryInput, _ctx: AgentContext): Promise<DiscoveryOutput> {
    // Placeholder strategy: dedupe by phrase and keep highest score.
    const byPhrase = new Map<string, CandidateQuery>();
    for (const c of input.candidates) {
      const key = c.phrase.trim().toLowerCase();
      const existing = byPhrase.get(key);
      if (!existing || (c.score ?? 0) > (existing.score ?? 0)) {
        byPhrase.set(key, c);
      }
    }

    const selected = [...byPhrase.values()]
      .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
      .slice(0, input.target);

    return { selected, droppedCount: Math.max(0, byPhrase.size - selected.length) };
  }
}
