export interface SynapseStrengthInput {
  serpOverlap: number;
  conceptOverlap: number;
  perspectiveAlignment: number;
  entityOverlap: number;
  intentProximity: number;
}

export interface SynapseStrengthOutput {
  strength: number;
  contradiction: boolean;
  signalsPresent: number;
}

export function runSynapseStrength(input: SynapseStrengthInput): SynapseStrengthOutput {
  const weights = {
    serp: 0.5,
    concept: 0.2,
    perspective: 0.15,
    entity: 0.1,
    intent: 0.05,
  };

  const signals = [
    input.serpOverlap,
    input.conceptOverlap,
    input.perspectiveAlignment,
    input.entityOverlap,
    input.intentProximity,
  ].filter((v) => v > 0).length;

  let strength =
    weights.serp * input.serpOverlap +
    weights.concept * input.conceptOverlap +
    weights.perspective * input.perspectiveAlignment +
    weights.entity * input.entityOverlap +
    weights.intent * input.intentProximity;

  if (signals > 1) {
    strength *= Math.pow(1.3, signals - 1);
  }

  const contradiction = input.conceptOverlap > 0.6 && input.serpOverlap < 0.1;
  if (contradiction) {
    strength = Math.min(strength, 0.3);
  }

  return { strength: Math.min(1, strength), contradiction, signalsPresent: signals };
}
