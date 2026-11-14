import { startup } from "@anthropic-ai/claude-agent-sdk";

const warm = await startup({
  initializeTimeoutMs: 20000,
  options: {
    cwd: process.cwd(), tools: [], mcpServers: {}, settingSources: [],
    permissionMode: "dontAsk", persistSession: false,
  },
});
await warm[Symbol.asyncDispose]();
console.log("Claude Agent SDK: native initialization handshake PASS; no prompt sent");
