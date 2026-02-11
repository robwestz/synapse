export interface WeightedConcept {
  token: string;
  weight: number;
}

export interface ConceptOverlapInput {
  conceptsA: WeightedConcept[];
  conceptsB: WeightedConcept[];
}

export interface ConceptOverlapOutput {
  overlap: number;
  shared: string[];
  onlyA: string[];
  onlyB: string[];
}

function toMap(items: WeightedConcept[]): Map<string, number> {
  const m = new Map<string, number>();
  for (const it of items ?? []) {
    const t = it.token.trim().toUpperCase();
    if (!t) continue;
    m.set(t, Math.max(0, it.weight ?? 0));
  }
  return m;
}

export function runConceptOverlap(input: ConceptOverlapInput): ConceptOverlapOutput {
  const a = toMap(input.conceptsA);
  const b = toMap(input.conceptsB);
  const tokens = new Set([...a.keys(), ...b.keys()]);
  let minSum = 0;
  let maxSum = 0;
  const shared: string[] = [];
  const onlyA: string[] = [];
  const onlyB: string[] = [];

  for (const t of tokens) {
    const av = a.get(t) ?? 0;
    const bv = b.get(t) ?? 0;
    minSum += Math.min(av, bv);
    maxSum += Math.max(av, bv);
    if (av > 0 && bv > 0) shared.push(t);
    else if (av > 0) onlyA.push(t);
    else if (bv > 0) onlyB.push(t);
  }

  return {
    overlap: maxSum === 0 ? 0 : minSum / maxSum,
    shared,
    onlyA,
    onlyB,
  };
}
