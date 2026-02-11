export interface PerspectiveDistanceInput {
  perspectiveA: string;
  perspectiveB: string;
}

export interface PerspectiveDistanceOutput {
  alignment: number;
  isInversion: boolean;
}

const order = ["seeker", "educator", "advisor", "neutral", "regulator", "provider"];
const inversionPairs = new Set(["seeker|provider", "provider|seeker", "advisor|regulator", "regulator|advisor"]);

export function runPerspectiveDistance(
  input: PerspectiveDistanceInput,
): PerspectiveDistanceOutput {
  const a = (input.perspectiveA ?? "").toLowerCase().trim();
  const b = (input.perspectiveB ?? "").toLowerCase().trim();
  if (!a || !b) return { alignment: 0, isInversion: false };
  if (a === b) return { alignment: 1, isInversion: false };

  const pair = `${a}|${b}`;
  const isInversion = inversionPairs.has(pair);
  if (isInversion) return { alignment: 0, isInversion: true };

  const ai = order.indexOf(a);
  const bi = order.indexOf(b);
  if (ai === -1 || bi === -1) return { alignment: 0.5, isInversion: false };

  const maxDistance = order.length - 1;
  const distance = Math.abs(ai - bi);
  return { alignment: 1 - distance / maxDistance, isInversion: false };
}
