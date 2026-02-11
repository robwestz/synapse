export interface CommunityDetectionInput {
  adjacencyMatrix: number[][];
  nodeIds: string[];
}

export interface CommunityDetectionOutput {
  clusters: string[][];
  modularity: number;
}

export function runCommunityDetection(
  input: CommunityDetectionInput,
): CommunityDetectionOutput {
  // Placeholder: one cluster for all nodes.
  const ids = input.nodeIds ?? [];
  return { clusters: ids.length ? [ids] : [], modularity: 0 };
}
