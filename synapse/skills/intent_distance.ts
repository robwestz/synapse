export interface IntentDistanceInput {
  intentA: number;
  intentB: number;
}

export interface IntentDistanceOutput {
  distance: number;
  proximity: number;
}

export function runIntentDistance(input: IntentDistanceInput): IntentDistanceOutput {
  const a = Math.min(1, Math.max(0, input.intentA ?? 0));
  const b = Math.min(1, Math.max(0, input.intentB ?? 0));
  const distance = Math.abs(a - b);
  return { distance, proximity: 1 - distance };
}
