import { AhrefsAdapter, type AhrefsClient, type AhrefsRequest } from "../adapters/ahrefs";
import { FirecrawlAdapter, type FirecrawlClient, type FirecrawlBatchScrapeOptions, type FirecrawlScrapeOptions, type FirecrawlSearchOptions } from "../adapters/firecrawl";
import { LlmAdapter, type LlmClient, type LlmMessageInput } from "../adapters/llm";
import { SerpMetadataAdapter } from "../adapters/serp_metadata";
import type { PipelineDependencies } from "../kernel/pipeline";
import { spawn } from "node:child_process";

interface FetchClientConfig {
  timeoutMs?: number;
}

interface CliProfile {
  name: string;
  command: string;
  args: string[];
  usePromptFlag: boolean;
  promptFlag: string;
}

async function postJson(
  url: string,
  body: unknown,
  headers: Record<string, string>,
  timeoutMs = 45_000,
): Promise<unknown> {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...headers,
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    const text = await res.text();
    if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}: ${text.slice(0, 500)}`);
    }
    return text ? JSON.parse(text) : {};
  } finally {
    clearTimeout(t);
  }
}

async function getJson(
  url: string,
  headers: Record<string, string>,
  timeoutMs = 45_000,
): Promise<unknown> {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method: "GET",
      headers,
      signal: controller.signal,
    });
    const text = await res.text();
    if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}: ${text.slice(0, 500)}`);
    }
    return text ? JSON.parse(text) : {};
  } finally {
    clearTimeout(t);
  }
}

class AhrefsHttpClient implements AhrefsClient {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly timeoutMs: number;
  private readonly httpMethod: "POST" | "GET";
  private readonly authMode: "bearer" | "query_api_key" | "query_token";

  constructor(config: FetchClientConfig = {}) {
    this.baseUrl = process.env.AHREFS_BASE_URL ?? "https://api.ahrefs.com/v3";
    this.apiKey = process.env.AHREFS_API_KEY;
    this.timeoutMs = config.timeoutMs ?? 45_000;
    this.httpMethod = (process.env.AHREFS_HTTP_METHOD?.toUpperCase() === "GET" ? "GET" : "POST");
    this.authMode = (process.env.AHREFS_AUTH_MODE as AhrefsHttpClient["authMode"]) ?? "bearer";
  }

  private endpointPath(endpoint: AhrefsRequest["endpoint"]): string {
    const explicit =
      process.env[`AHREFS_PATH_${endpoint.toUpperCase().replace(/-/g, "_")}`];
    if (explicit) return explicit.replace(/^\/+/, "");
    const endpointMap: Record<AhrefsRequest["endpoint"], string> = {
      "serp-overview": "serp-overview",
      "keywords-explorer-overview": "keywords-explorer/overview",
      "organic-keywords": "site-explorer/organic-keywords",
      "related-terms": "keywords-explorer/related-terms",
      "matching-terms": "keywords-explorer/matching-terms",
      "search-suggestions": "keywords-explorer/search-suggestions",
    };
    return endpointMap[endpoint];
  }

  async call(request: AhrefsRequest): Promise<unknown> {
    if (!this.apiKey) throw new Error("AHREFS_API_KEY is missing.");
    const path = this.endpointPath(request.endpoint);
    const urlBase = `${this.baseUrl.replace(/\/$/, "")}/${path}`;
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(request.params)) {
      if (v == null) continue;
      params.set(k, String(v));
    }
    const headers: Record<string, string> = {};
    if (this.authMode === "bearer") headers.Authorization = `Bearer ${this.apiKey}`;
    if (this.authMode === "query_api_key") params.set("api_key", this.apiKey);
    if (this.authMode === "query_token") params.set("token", this.apiKey);
    if (this.httpMethod === "GET") {
      return getJson(`${urlBase}?${params.toString()}`, headers, this.timeoutMs);
    }
    return postJson(
      urlBase,
      Object.fromEntries(params.entries()),
      headers,
      this.timeoutMs,
    );
  }
}

class FirecrawlHttpClient implements FirecrawlClient {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly timeoutMs: number;

  constructor(config: FetchClientConfig = {}) {
    this.baseUrl = process.env.FIRECRAWL_BASE_URL ?? "https://api.firecrawl.dev/v1";
    this.apiKey = process.env.FIRECRAWL_API_KEY;
    this.timeoutMs = config.timeoutMs ?? 45_000;
  }

  private headers(): Record<string, string> {
    if (!this.apiKey) throw new Error("FIRECRAWL_API_KEY is missing.");
    return { Authorization: `Bearer ${this.apiKey}` };
  }

  async search(options: FirecrawlSearchOptions): Promise<unknown> {
    return postJson(
      `${this.baseUrl.replace(/\/$/, "")}/search`,
      options,
      this.headers(),
      this.timeoutMs,
    );
  }

  async scrape(options: FirecrawlScrapeOptions): Promise<unknown> {
    return postJson(
      `${this.baseUrl.replace(/\/$/, "")}/scrape`,
      options,
      this.headers(),
      this.timeoutMs,
    );
  }

  async batchScrape(options: FirecrawlBatchScrapeOptions): Promise<unknown> {
    return postJson(
      `${this.baseUrl.replace(/\/$/, "")}/batch/scrape`,
      options,
      this.headers(),
      this.timeoutMs,
    );
  }
}

class AnthropicHttpClient implements LlmClient {
  private readonly apiKey?: string;
  private readonly baseUrl: string;
  private readonly timeoutMs: number;
  constructor(config: FetchClientConfig = {}) {
    this.apiKey = process.env.ANTHROPIC_API_KEY;
    this.baseUrl = process.env.ANTHROPIC_BASE_URL ?? "https://api.anthropic.com/v1/messages";
    this.timeoutMs = config.timeoutMs ?? 60_000;
  }

  async generate(input: LlmMessageInput): Promise<string> {
    if (!this.apiKey) throw new Error("ANTHROPIC_API_KEY is missing.");
    const payload = {
      model: input.model ?? process.env.LLM_MODEL ?? "claude-sonnet-4-20250514",
      max_tokens: input.maxTokens ?? Number(process.env.LLM_MAX_TOKENS ?? 4000),
      system: input.system,
      messages: [{ role: "user", content: input.user }],
      temperature: 0.1,
    };
    const raw = await postJson(
      this.baseUrl,
      payload,
      {
        "x-api-key": this.apiKey,
        "anthropic-version": "2023-06-01",
      },
      this.timeoutMs,
    ) as {
      content?: Array<{ type?: string; text?: string }>;
    };
    const text = raw.content?.find((c) => c.type === "text")?.text ?? "";
    if (!text) throw new Error("Empty response text from Anthropic.");
    return text;
  }
}

class CliCommandLlmClient implements LlmClient {
  private readonly timeoutMs: number;
  private readonly profile: CliProfile;

  constructor(profile: CliProfile, config: FetchClientConfig = {}) {
    this.profile = profile;
    this.timeoutMs = config.timeoutMs ?? 180_000;
  }

  private quoteCmdArg(arg: string): string {
    if (!arg) return "\"\"";
    if (!/[ \t"]/g.test(arg)) return arg;
    return `"${arg.replace(/"/g, '\\"')}"`;
  }

  private static cleanEnv(): NodeJS.ProcessEnv {
    const env = { ...process.env };
    // Strip empty ANTHROPIC_API_KEY so CLI tools (claude -p) use session auth
    // instead of attempting API-key auth with an empty key.
    if (!env.ANTHROPIC_API_KEY) delete env.ANTHROPIC_API_KEY;
    return env;
  }

  private runSpawn(
    command: string,
    args: string[],
    stdinText?: string,
  ): Promise<{ code: number | null; stdout: string; stderr: string; error?: Error }> {
    return new Promise((resolve) => {
      const child = spawn(command, args, {
        stdio: ["pipe", "pipe", "pipe"],
        shell: false,
        env: CliCommandLlmClient.cleanEnv(),
      });
      let stdout = "";
      let stderr = "";
      const t = setTimeout(() => {
        child.kill();
        resolve({ code: null, stdout, stderr: `${stderr}\nTimed out` });
      }, this.timeoutMs);

      child.stdout.on("data", (d) => {
        stdout += String(d);
      });
      child.stderr.on("data", (d) => {
        stderr += String(d);
      });
      child.on("error", (err) => {
        clearTimeout(t);
        resolve({ code: null, stdout, stderr, error: err as Error });
      });
      child.on("close", (code) => {
        clearTimeout(t);
        resolve({ code, stdout, stderr });
      });

      if (stdinText != null) child.stdin.write(stdinText);
      child.stdin.end();
    });
  }

  async generate(input: LlmMessageInput): Promise<string> {
    const prompt = [
      `System: ${input.system}`,
      "",
      "User:",
      input.user,
      "",
      "Svarskrav: returnera endast textsvaret utan extra wrappers.",
    ].join("\n");

    // Attempt 1: direct spawn with explicit prompt argument (best for non-interactive CLIs)
    const argsWithPrompt = this.profile.usePromptFlag
      ? [...this.profile.args, this.profile.promptFlag, prompt]
      : [...this.profile.args];
    let result = await this.runSpawn(this.profile.command, argsWithPrompt);

    // Attempt 2 (Windows): resolve command through cmd.exe when ENOENT/EINVAL.
    if (
      process.platform === "win32" &&
      result.error &&
      /ENOENT|EINVAL/i.test(result.error.message)
    ) {
      const cmdLine = [
        this.quoteCmdArg(this.profile.command),
        ...argsWithPrompt.map((a) => this.quoteCmdArg(a)),
      ].join(" ");
      result = await this.runSpawn("cmd.exe", ["/d", "/s", "/c", cmdLine]);
    }

    // Attempt 3: fallback to stdin mode when CLI rejects prompt-flag usage.
    if (
      result.code !== 0 &&
      /Not enough arguments following|Usage:/i.test(result.stderr)
    ) {
      const stdinArgs = [...this.profile.args];
      result = await this.runSpawn(this.profile.command, stdinArgs, prompt);
      if (
        process.platform === "win32" &&
        result.error &&
        /ENOENT|EINVAL/i.test(result.error.message)
      ) {
        const cmdLine = [
          this.quoteCmdArg(this.profile.command),
          ...stdinArgs.map((a) => this.quoteCmdArg(a)),
        ].join(" ");
        result = await this.runSpawn("cmd.exe", ["/d", "/s", "/c", cmdLine], prompt);
      }
    }

    if (result.error) throw result.error;
    if (result.code !== 0) {
      throw new Error(
        `[${this.profile.name}] LLM CLI failed (${result.code}): ${result.stderr.slice(0, 800)}`,
      );
    }
    const out = result.stdout.trim();
    if (!out) {
      throw new Error(`[${this.profile.name}] LLM CLI returned empty stdout.`);
    }
    return out;
  }
}

class MultiCliLlmClient implements LlmClient {
  private readonly clients: CliCommandLlmClient[];

  constructor(clients: CliCommandLlmClient[]) {
    this.clients = clients;
  }

  async generate(input: LlmMessageInput): Promise<string> {
    if (!this.clients.length) {
      throw new Error("LLM cli_multi has no configured clients.");
    }
    const errors: string[] = [];
    for (const client of this.clients) {
      try {
        return await client.generate(input);
      } catch (err) {
        errors.push(String(err));
      }
    }
    throw new Error(`All CLI providers failed: ${errors.join(" | ")}`);
  }
}

function parseArgString(value: string | undefined): string[] {
  return (value ?? "")
    .split(" ")
    .map((x) => x.trim())
    .filter(Boolean);
}

function cliProfileFromEnv(name: string, defaults?: Partial<CliProfile>): CliProfile {
  const upper = name.toUpperCase();
  const command =
    process.env[`LLM_CLI_${upper}_COMMAND`] ??
    defaults?.command ??
    process.env.LLM_CLI_COMMAND ??
    name;
  const namedArgs = parseArgString(process.env[`LLM_CLI_${upper}_ARGS`]);
  const globalArgs = parseArgString(process.env.LLM_CLI_ARGS);
  const args = namedArgs.length ? namedArgs : defaults?.args ?? globalArgs;
  const usePromptFlagRaw =
    process.env[`LLM_CLI_${upper}_USE_PROMPT_FLAG`] ??
    (defaults?.usePromptFlag == null ? undefined : String(defaults.usePromptFlag)) ??
    process.env.LLM_CLI_USE_PROMPT_FLAG ??
    "true";
  const promptFlag =
    process.env[`LLM_CLI_${upper}_PROMPT_FLAG`] ??
    defaults?.promptFlag ??
    process.env.LLM_CLI_PROMPT_FLAG ??
    "-p";

  return {
    name,
    command,
    args: Array.isArray(args) ? args : [],
    usePromptFlag: usePromptFlagRaw !== "false",
    promptFlag,
  };
}

export function createLiveDependenciesFromEnv(config: FetchClientConfig = {}): PipelineDependencies {
  const ahrefs = new AhrefsAdapter(new AhrefsHttpClient(config));
  const firecrawl = new FirecrawlAdapter(new FirecrawlHttpClient(config));
  const llmProvider = (process.env.LLM_PROVIDER ?? "cli").toLowerCase();
  let llmClient: LlmClient;
  if (llmProvider === "cli") {
    llmClient = new CliCommandLlmClient(
      cliProfileFromEnv("primary", { command: process.env.LLM_CLI_COMMAND ?? "claude" }),
      config,
    );
  } else if (llmProvider === "cli_multi") {
    const chain = (process.env.LLM_CLI_CHAIN ?? "claude,chatgpt,gemini")
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);
    const clients = chain.map((name) =>
      new CliCommandLlmClient(cliProfileFromEnv(name), config),
    );
    llmClient = new MultiCliLlmClient(clients);
  } else {
    llmClient = new AnthropicHttpClient(config);
  }
  const llm = new LlmAdapter(llmClient);
  const serpMetadata = new SerpMetadataAdapter();
  return { ahrefs, firecrawl, llm, serpMetadata };
}

export function assertLiveEnvReady(): { ok: boolean; missing: string[] } {
  const llmProvider = (process.env.LLM_PROVIDER ?? "cli").toLowerCase();
  const required = ["AHREFS_API_KEY"];
  if (llmProvider === "cli") {
    required.push("LLM_CLI_COMMAND");
  } else if (llmProvider === "cli_multi") {
    required.push("LLM_CLI_CHAIN");
  } else if (llmProvider === "anthropic") {
    required.push("ANTHROPIC_API_KEY");
  } else {
    required.push("LLM_PROVIDER");
  }
  const missing = required.filter((k) => !process.env[k]);
  return { ok: missing.length === 0, missing };
}
