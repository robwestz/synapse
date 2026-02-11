import { AbstractAgent } from "./base_agent";
import type { AgentContext, AgentWarning, SynapseEdgeLite } from "./types";

export interface SynapseInput {
  nodeIds: string[];
  minStrength?: number;
}

export interface SynapseOutput {
  edges: SynapseEdgeLite[];
}

export class SynapseAgent extends AbstractAgent<SynapseInput, SynapseOutput> {
  readonly id = "synapse_agent" as const;

  validate(input: SynapseInput): AgentWarning[] {
    const warnings: AgentWarning[] = [];
    if (input.nodeIds.length < 2) {
      warnings.push({
        code: "nodes_too_few",
        message: "At least two nodes are required to generate edges.",
      });
    }
    return warnings;
  }

  protected async execute(input: SynapseInput, _ctx: AgentContext): Promise<SynapseOutput> {
    const minStrength = input.minStrength ?? 0.3;
    const edges: SynapseEdgeLite[] = [];
    for (let i = 0; i < input.nodeIds.length - 1; i++) {
      const from = input.nodeIds[i];
      const to = input.nodeIds[i + 1];
      const strength = 0.35;
      if (strength < minStrength) continue;
      edges.push({
        from,
        to,
        strength,
        family: "TRANSITION",
        contradiction: false,
      });
    }
    return { edges };
  }
}
