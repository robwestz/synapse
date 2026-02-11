import type {
  AgentContext,
  AgentResult,
  AgentWarning,
  BaseAgent,
} from "./types";

export abstract class AbstractAgent<TInput, TOutput>
  implements BaseAgent<TInput, TOutput>
{
  abstract readonly id: BaseAgent<TInput, TOutput>["id"];

  abstract validate(input: TInput): AgentWarning[];

  protected abstract execute(input: TInput, ctx: AgentContext): Promise<TOutput>;

  async run(input: TInput, ctx: AgentContext): Promise<AgentResult<TOutput>> {
    const started = Date.now();
    const warnings = this.validate(input);
    const output = await this.execute(input, ctx);

    return {
      agentId: this.id,
      ok: true,
      output,
      warnings,
      durationMs: Date.now() - started,
    };
  }
}
