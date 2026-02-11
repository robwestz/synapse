import type { SkillId } from "./skills";
import { runClusterSignatureAggregation } from "../skills/cluster_signature_aggregation";
import { runCommunityDetection } from "../skills/community_detection";
import { runConceptOverlap } from "../skills/concept_overlap";
import { runIntentDistance } from "../skills/intent_distance";
import { runMmrSelection } from "../skills/mmr_selection";
import { runPerspectiveDistance } from "../skills/perspective_distance";
import { runSerpOverlap } from "../skills/serp_overlap";
import { runSynapseStrength } from "../skills/synapse_strength";

type SkillRunner = (input: unknown) => unknown;

const runners: Record<SkillId, SkillRunner> = {
  serp_overlap: runSerpOverlap,
  concept_overlap: runConceptOverlap,
  intent_distance: runIntentDistance,
  perspective_distance: runPerspectiveDistance,
  synapse_strength: runSynapseStrength,
  mmr_selection: runMmrSelection,
  community_detection: runCommunityDetection,
  cluster_signature_aggregation: runClusterSignatureAggregation,
};

export function runSkill<TInput = unknown, TOutput = unknown>(
  skillId: SkillId,
  input: TInput,
): TOutput {
  const runner = runners[skillId];
  if (!runner) {
    throw new Error(`Unknown skill: ${skillId}`);
  }
  return runner(input) as TOutput;
}
