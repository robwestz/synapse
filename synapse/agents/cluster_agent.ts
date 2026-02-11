import { AbstractAgent } from "./base_agent";
import type { AgentContext, AgentWarning, ClusterLite } from "./types";

export interface ClusterInput {
  nodeIds: string[];
  minClusters?: number;
  maxClusters?: number;
}

export interface ClusterOutput {
  clusters: ClusterLite[];
}

export class ClusterAgent extends AbstractAgent<ClusterInput, ClusterOutput> {
  readonly id = "cluster_agent" as const;

  validate(input: ClusterInput): AgentWarning[] {
    const warnings: AgentWarning[] = [];
    if (!input.nodeIds.length) {
      warnings.push({ code: "nodes_empty", message: "No nodes provided for clustering." });
    }
    return warnings;
  }

  protected async execute(input: ClusterInput, _ctx: AgentContext): Promise<ClusterOutput> {
    // Placeholder clustering: one simple cluster from all nodes.
    const clusters: ClusterLite[] = [
      {
        id: "cluster_1",
        label: "Initial Cluster",
        nodeIds: input.nodeIds,
        cohesion: 0.5,
      },
    ];
    return { clusters };
  }
}
