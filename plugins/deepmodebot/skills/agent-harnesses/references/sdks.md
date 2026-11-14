# Agent SDKs: install, use, and verify

Checked 2026-11-13. Use this reference when embedding Antigravity, Claude Code, Codex, or omp in an application. These are agent harness SDKs, not the lower-level Gemini, Anthropic, or OpenAI model clients. Installing an SDK neither signs in nor authorizes model calls, tool execution, or background automation.

## Choose the surface

| Harness | Official package | Runtime | Entry point |
|---|---|---|---|
| Google Antigravity | `google-antigravity` | Python 3.10+ and its platform wheel | `google.antigravity.Agent`, `LocalAgentConfig` |
| Claude Agent SDK (formerly Claude Code SDK) | `@anthropic-ai/claude-agent-sdk`; Python alternative `claude-agent-sdk` | Node 18.14+ or Python 3.10+ | `query()`; Python also has `ClaudeSDKClient` |
| OpenAI Codex | `@openai/codex-sdk` | Node 18+ and a Codex binary | `Codex`, `startThread()`, `run()` |
| omp | `@oh-my-pi/pi-coding-agent` | Bun 1.4.4+ | `createAgentSession()`, `SessionManager` |

Sources: [Antigravity setup](https://antigravity.google/docs/getting-started?tab=sdk), [Claude quickstart](https://code.claude.com/docs/en/agent-sdk/quickstart.md), [Codex SDK](https://github.com/openai/codex/tree/main/sdk/typescript), [omp SDK](https://github.com/can1357/oh-my-pi/blob/main/docs/sdk.md).

## Install the optional SDK workspace

The [SDK workspace](../assets/sdks/package.json) pins the three JavaScript packages; [requirements.txt](../assets/sdks/requirements.txt) pins Antigravity. This workspace is optional. The deepmodebot plugin and GitHub bot do not acquire these dependencies or switch execution backends merely because these files exist.

Start from the checkout root and copy the source-only kit into a fresh ignored workspace. The repository checker scans plugin assets, so keep installed dependencies under `.scratch/`, not inside the distributed plugin.

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force .scratch | Out-Null
Copy-Item -Recurse plugins/deepmodebot/skills/agent-harnesses/assets/sdks .scratch/sdk-runtime
cd .scratch/sdk-runtime
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
bun install --frozen-lockfile
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe check_antigravity.py
bun check.ts
```

On macOS/Linux, first run `mkdir -p .scratch` and `cp -R plugins/deepmodebot/skills/agent-harnesses/assets/sdks .scratch/sdk-runtime`, then `cd .scratch/sdk-runtime`. Use `python3 -m venv .venv` and `.venv/bin/python` in place of the Windows Python commands. Bun commands are unchanged. Use a fresh target; do not overwrite an existing environment. Activation is not required.

Keep `.venv/` and `node_modules/` local. Do not install into the shared Python user environment. On the checked Windows host, a user-wide Antigravity install upgraded protobuf to 7.x, conflicting with existing `opentelemetry-proto` and `pywidevine` requirements for protobuf below 7. The isolated workspace avoids that conflict; it does not repair the shared environment.

`check_antigravity.py` and `check.ts` exercise installed SDK APIs without sending a model prompt. A passing check proves local package usability only, not provider authentication, inference, or agent tool permissions during a model turn.

For another app, install dependencies in that app's own environment. JavaScript modules are resolved from the importing file's project, not from a global installation. Copy the reviewed manifest/lock and examples as needed; do not import from a machine-specific worktree path.

## Google Antigravity CLI versus SDK

The [overview](https://antigravity.google/docs/overview?tab=cli) distinguishes the App, `agy` CLI, IDE extensions, and Python SDK. `pip install google-antigravity` installs the Python SDK and its runtime, not the interactive `agy` command.

The [CLI setup guide](https://antigravity.google/docs/getting-started?tab=cli) places Windows `agy.exe` in `%LOCALAPPDATA%\agy\bin`. If the installer completed but the terminal cannot find `agy`, use the existing executable directly or refresh only that terminal's PATH:

```powershell
& "$env:LOCALAPPDATA\agy\bin\agy.exe" --version
$env:Path = "$env:LOCALAPPDATA\agy\bin;$env:Path"
agy --help
```

Add that directory to the user PATH for future terminals. Do not replace the entire PATH or reinstall the SDK to fix CLI command resolution. Interactive `agy` performs its own sign-in and workspace-trust flow. Headless usage is `agy -p "<approved task>" --output-format json`; see the [CLI reference](https://antigravity.google/docs/cli/reference/) and [headless guide](https://antigravity.google/docs/cli/headless/).

### Python SDK usage

The [SDK overview](https://antigravity.google/docs/sdk/overview/) documents `GEMINI_API_KEY`, or Gemini Enterprise/Vertex configuration and Application Default Credentials. Do not assume an `agy` Google AI subscription login authenticates the Python SDK. [Local model configurations](https://antigravity.google/docs/sdk/local-models/) are a separate keyless option when an actual local model/server is available; installing this workspace does not download or start one.

After the operator has approved the provider, input data, and spend, inject credentials into the process without putting values in source or command history. This example permits file reading but no shell, write, web, or subagent tools:

```python
import asyncio
from pathlib import Path
from google.antigravity import Agent, CapabilitiesConfig, LocalAgentConfig
from google.antigravity.types import BuiltinTools

def config():
    return LocalAgentConfig(
        workspaces=[str(Path.cwd())],
        capabilities=CapabilitiesConfig(enabled_tools=[BuiltinTools.VIEW_FILE]),
    )

async def main():
    async with Agent(config()) as agent:
        response = await agent.chat("Read README.md and summarize its purpose.")
        print(await response.text())

if __name__ == "__main__":
    asyncio.run(main())
```

[Tools and skills](https://antigravity.google/docs/sdk/tools/) documents:

- `tools=[python_function]` registers a custom tool using its signature and docstring. It executes in your Python process; inspect its side effects before exposing it.
- `CapabilitiesConfig(enabled_tools=[...])` selects built-in tools. `BuiltinTools.read_only()` is a broader group, not a claim of no network access.
- `skills_paths=["/absolute/path/to/skill"]` accepts a skill directory or a parent containing several skills. For this plugin, select the intended directories under `plugins/deepmodebot/skills/`.
- MCP configuration is separate from skills. Only connect reviewed servers; see [SDK MCP](https://antigravity.google/docs/sdk/mcp/).
- [Policies](https://antigravity.google/docs/sdk/policies/) add `allow`, `deny`, and `ask_user` hooks. Tool selection and approval policies are not an OS sandbox.

Example custom tool, with a deterministic local result rather than invented external data:

```python
from google.antigravity import LocalAgentConfig

def character_count(text: str) -> int:
    """Count Unicode code points in the supplied text."""
    return len(text)

config = LocalAgentConfig(tools=[character_count])
```

## Claude Agent SDK

Install the current name, not the retired Claude Code SDK package. [TypeScript upstream](https://github.com/anthropics/claude-agent-sdk-typescript) confirms `@anthropic-ai/claude-agent-sdk`; [Python upstream](https://github.com/anthropics/claude-agent-sdk-python) confirms `claude-agent-sdk`. This workspace installs the TypeScript edition. Python consumers can install the alternative inside their own venv.

The [quickstart](https://code.claude.com/docs/en/agent-sdk/quickstart.md) documents `ANTHROPIC_API_KEY` and supported cloud-provider authentication. Both editions normally bundle Claude Code; keep optional dependencies enabled. An existing interactive CLI login is not evidence that a redistributed SDK product may use subscription credentials. The [SDK terms notice](https://code.claude.com/docs/en/agent-sdk/overview.md) prohibits offering claude.ai login or rate limits in third-party products without prior approval.

After separately approving authentication and spend:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Read README.md and summarize its purpose. Do not change files.",
  options: {
    cwd: process.cwd(),
    tools: ["Read"],
    allowedTools: ["Read"],
    permissionMode: "dontAsk",
    settingSources: [],
    mcpServers: {},
    maxTurns: 3,
    maxBudgetUsd: 0.25,
  },
})) {
  if (message.type === "result") {
    if (message.subtype !== "success" || message.is_error) {
      throw new Error(`Claude run failed: ${message.subtype}`);
    }
    console.log(message.result);
  }
}
```

`tools` limits the built-in set; `allowedTools` only pre-approves tools and is not an allowlist. `dontAsk` denies unapproved actions rather than bypassing permissions. `settingSources: []` avoids ambient settings; deliberately load project settings/plugins only after review. Source: [TypeScript reference](https://code.claude.com/docs/en/agent-sdk/typescript.md).

Consume result failures as failures, including budget/turn limits. Keep session IDs if resumability is intended; use SDK hooks and `createSdkMcpServer`/`tool` for custom tools rather than inventing a second agent loop. See [MCP](https://code.claude.com/docs/en/agent-sdk/mcp.md) and [sessions](https://code.claude.com/docs/en/agent-sdk/sessions.md).

## Codex SDK

The [official TypeScript SDK](https://github.com/openai/codex/tree/main/sdk/typescript) wraps a Codex subprocess and exchanges JSONL events. Its native platform dependency must be present; do not install with optional dependencies omitted. The SDK is not the `openai` model-client package.

After reviewing the selected Codex login/configuration and approving a run:

```typescript
import { Codex } from "@openai/codex-sdk";

const codex = new Codex();
const thread = codex.startThread({
  workingDirectory: process.cwd(),
  sandboxMode: "read-only",
  approvalPolicy: "never",
  networkAccessEnabled: false,
  webSearchMode: "disabled",
});
const turn = await thread.run("Read README.md and summarize its purpose.");
console.log(turn.finalResponse);
console.log(turn.usage);
```

Run inside the intended Git repository. `skipGitRepoCheck: true` deliberately permits a non-repository folder; do not enable it to hide a wrong cwd. Call `run()` again on the same thread for follow-up work, `runStreamed()` for structured events, and `resumeThread(id, options)` to resume with explicit restrictions. A resumed thread's security options must be supplied deliberately.

By default the subprocess inherits the environment. An SDK `apiKey` or `CODEX_API_KEY` can select API billing instead of a stored ChatGPT login. For subscription-only execution remove `OPENAI_API_KEY` and `CODEX_API_KEY` from a child environment and do not pass `apiKey`. Preserve the user's existing stores; never copy tokens into examples. Sources: [SDK environment controls](https://github.com/openai/codex/tree/main/sdk/typescript), [Codex authentication](https://learn.chatgpt.com/docs/auth).

## omp SDK

Use Bun, not Node, for the in-process SDK. The package root exports `createAgentSession`, `SessionManager`, `AuthStorage`, `ModelRegistry`, and `Settings`. The narrower `/sdk` entry does not export all of them. Source: [omp SDK](https://github.com/can1357/oh-my-pi/blob/main/docs/sdk.md).

The default `createAgentSession()` discovers user credentials, settings, skills, extensions, MCP, tools, and persistent sessions. It is useful for an intentional full harness, not a neutral import check. For an approved embedded run, select the exact model and narrow tools:

```typescript
import { createAgentSession, SessionManager } from "@oh-my-pi/pi-coding-agent";

const modelPattern = process.env.OMP_SDK_MODEL;
if (!modelPattern) throw new Error("Set OMP_SDK_MODEL to an approved provider/model ID");
const { session, modelFallbackMessage } = await createAgentSession({
  cwd: process.cwd(),
  modelPattern,
  sessionManager: SessionManager.inMemory(),
  toolNames: ["read"],
  restrictToolNames: true,
  enableMCP: false,
  enableLsp: false,
  disableExtensionDiscovery: true,
});
try {
  if (modelFallbackMessage) throw new Error(modelFallbackMessage);
  const unsubscribe = session.subscribe(event => {
    if (event.type === "message_update" && event.assistantMessageEvent.type === "text_delta") {
      process.stdout.write(event.assistantMessageEvent.delta);
    }
  });
  try {
    await session.prompt("Read README.md and summarize its purpose.");
  } finally {
    unsubscribe();
  }
} finally {
  await session.dispose();
}
```

`toolNames` alone is not an allowlist; `restrictToolNames: true` enforces the restriction. In-memory sessions avoid transcript persistence, but do not prevent credential/config discovery or all harness state. Dispose sessions in `finally`. For multiple top-level sessions in one process, give each its own `AgentRegistry`. Use omp RPC instead when process/language isolation is required. Source: [SDK lifecycle and restricted tools](https://github.com/can1357/oh-my-pi/blob/main/docs/sdk.md).

## Acceptance and limits

- Install all four packages in the optional workspace and run both local checks plus `pip check`.
- Record actual versions, platform, command outputs, and which native runtimes launched.
- Model-backed examples require a separate approved run with credentials, a model, data boundaries, and a spend/time cap. Import success is not inference success.
- Keep the existing GitHub bot's ACP/subscription path unchanged. These SDKs are opt-in application dependencies, not four automatically configured bot backends.

### Local installation evidence, 2026-11-13

Exercised on Windows x64 with Python 3.13.3, Node 24.22.2, and Bun 1.4.4.

| Package | Installed version | Observed result |
|---|---|---|
| `google-antigravity` | 0.1.23 | Config construction and actual custom-tool dispatch returned 9 for `SDK check`; platform runtime file present |
| `@anthropic-ai/claude-agent-sdk` | 0.3.325 | Native Claude initialization handshake succeeded without a prompt; child process exited |
| `@openai/codex-sdk` | 0.169.0 | SDK thread constructed; bundled CLI returned `codex-cli 0.169.0` |
| `@oh-my-pi/pi-coding-agent` | 18.20.0 | In-memory message append/read succeeded without a model session |

The isolated venv's `python -m pip check` printed `No broken requirements found.` The Bun frozen-lock install reported no changes. `agy --version` separately returned `1.5.8`; this does not establish Python SDK authentication.

An initial combined Bun smoke completed its SDK checks but failed to remove its scratch directory with Windows `EBUSY` after Claude teardown. The final check runs Claude's SDK handshake in a separate Node process and waits for process exit before removing the directory; that run exited 0, including cleanup. Other operating systems and model-backed runs remain unverified.
