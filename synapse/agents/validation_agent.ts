import { AbstractAgent } from "./base_agent";
import type { AgentContext, AgentWarning } from "./types";

export interface ValidationInput {
  signatureConfidences: number[];
  minConfidence: number;
  minPassRatio: number;
}

export interface ValidationOutput {
  pass: boolean;
  passRatio: number;
  failedCount: number;
}

export class ValidationAgent extends AbstractAgent<ValidationInput, ValidationOutput> {
  readonly id = "validation_agent" as const;

  validate(input: ValidationInput): AgentWarning[] {
    const warnings: AgentWarning[] = [];
    if (input.minPassRatio < 0 || input.minPassRatio > 1) {
      warnings.push({ code: "ratio_invalid", message: "minPassRatio must be between 0 and 1." });
    }
    return warnings;
  }

  protected async execute(input: ValidationInput, _ctx: AgentContext): Promise<ValidationOutput> {
    const total = Math.max(1, input.signatureConfidences.length);
    const passed = input.signatureConfidences.filter((v) => v >= input.minConfidence).length;
    const passRatio = passed / total;
    return {
      pass: passRatio >= input.minPassRatio,
      passRatio,
      failedCount: total - passed,
    };
  }
}
