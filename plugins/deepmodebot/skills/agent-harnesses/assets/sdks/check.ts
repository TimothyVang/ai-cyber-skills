import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { createRequire } from "node:module";
import { join } from "node:path";
import { Codex } from "@openai/codex-sdk";
import { SessionManager } from "@oh-my-pi/pi-coding-agent";

const require = createRequire(import.meta.url);
const scratch = await mkdtemp(join(import.meta.dir, ".check-"));
try {
  const codex = new Codex();
  const thread = codex.startThread({
    workingDirectory: scratch,
    sandboxMode: "read-only",
    approvalPolicy: "never",
    networkAccessEnabled: false,
    webSearchMode: "disabled",
  });
  assert.equal(thread.id, null, "No Codex model turn should have started");
  const codexVersion = spawnSync("node", [require.resolve("@openai/codex/bin/codex.js"), "--version"], {
    encoding: "utf8", timeout: 15000,
    env: { ...process.env, CODEX_HOME: join(scratch, "codex") },
  });
  assert.equal(codexVersion.status, 0, codexVersion.error?.message || codexVersion.stderr);
  console.log(`Codex SDK: thread constructed; ${codexVersion.stdout.trim()}`);

  const manager = SessionManager.inMemory(scratch);
  try {
    const entryId = manager.appendMessage({ role: "user", content: "Local SDK check", timestamp: Date.now() });
    assert.equal(manager.getSessionFile(), undefined);
    const entry = manager.getBranch().find(item => item.id === entryId);
    assert.ok(entry && entry.type === "message");
    assert.equal(entry.message.content, "Local SDK check");
    console.log("omp SDK: in-memory message append/read PASS; no model session created");
  } finally {
    await manager.close();
  }

  const env = { ...process.env, CLAUDE_CONFIG_DIR: join(scratch, "claude"), CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1" };
  for (const key of Object.keys(env)) {
    if (/^(ANTHROPIC_|CLAUDE_CODE_(OAUTH|USE_)|OPENAI_API_KEY$|CODEX_API_KEY$)/.test(key)) delete env[key];
  }
  const claude = spawnSync("node", [join(import.meta.dir, "check_claude.mjs")], {
    cwd: scratch, env, encoding: "utf8", timeout: 30000,
  });
  assert.equal(claude.status, 0, claude.error?.message || claude.stderr);
  assert.match(claude.stdout, /native initialization handshake PASS/);
  console.log(claude.stdout.trim());
  console.log("No model turns requested. Authentication and inference remain unverified.");
} finally {
  await rm(scratch, { recursive: true, force: true });
}
