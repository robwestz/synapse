export interface SerpOverlapInput {
  urlsA: string[];
  urlsB: string[];
}

export interface SerpOverlapOutput {
  overlap: number;
  sharedUrls: string[];
}

export function runSerpOverlap(input: SerpOverlapInput): SerpOverlapOutput {
  const a = new Set((input.urlsA ?? []).map((u) => u.trim()).filter(Boolean));
  const b = new Set((input.urlsB ?? []).map((u) => u.trim()).filter(Boolean));
  const shared = [...a].filter((u) => b.has(u));
  const unionSize = new Set([...a, ...b]).size;
  const overlap = unionSize === 0 ? 0 : shared.length / unionSize;
  return { overlap, sharedUrls: shared };
}
