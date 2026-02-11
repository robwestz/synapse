export interface MmrCandidate {
  id: string;
  relevance: number;
}

export interface MmrSelectionInput {
  candidates: MmrCandidate[];
  k: number;
  mmrLambda: number;
}

export interface MmrSelectionOutput {
  selectedIds: string[];
  droppedIds: string[];
}

export function runMmrSelection(input: MmrSelectionInput): MmrSelectionOutput {
  // Placeholder: relevance-only selection. Replace with full pairwise MMR in ticket.
  const sorted = [...(input.candidates ?? [])].sort((a, b) => b.relevance - a.relevance);
  const selected = sorted.slice(0, Math.max(0, input.k)).map((c) => c.id);
  const dropped = sorted.slice(Math.max(0, input.k)).map((c) => c.id);
  return { selectedIds: selected, droppedIds: dropped };
}
