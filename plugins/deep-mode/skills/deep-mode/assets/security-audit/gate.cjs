#!/usr/bin/env node
// Turns a security-audit run into a PR verdict.
// Usage: node gate.cjs <output-dir> <skill-dir> [fail-at] [block-on-unvalidated] [accepted-file]
// Prints the PR comment (Markdown) to stdout. Exit 1 blocks the PR: a confirmed finding at or
// above fail-at, an invalid or missing findings.json, or (when enabled) any needs_validation lead.
// accepted-file lists fingerprints a reviewer accepted, one per line as `<fingerprint> # <reason>`;
// those never block and are shown as accepted.
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const RANK = { informational: 0, low: 1, medium: 2, high: 3, critical: 4 };
const MARKER = "<!-- deep-mode-security-audit -->";

function cell(text) {
  return String(text ?? "").replace(/\r?\n/g, " ").replace(/\|/g, "\\|").slice(0, 300);
}

function where(record) {
  const steps = Array.isArray(record.trace) ? record.trace : [];
  const sink = steps.find((s) => s.kind === "sink") || steps[steps.length - 1];
  return sink ? `\`${sink.file}:${sink.line}\`` : "";
}

function main() {
  const [outDir, skillDir, failAtArg = "high", blockArg = "true", acceptedFile] = process.argv.slice(2);
  if (!outDir || !skillDir) {
    console.error("Usage: node gate.cjs <output-dir> <skill-dir> [fail-at] [block-on-unvalidated] [accepted-file]");
    return 2;
  }
  const failAt = failAtArg.toLowerCase();
  if (!(failAt in RANK)) {
    console.error(`fail-at must be one of ${Object.keys(RANK).join(", ")}`);
    return 2;
  }
  const blockOnUnvalidated = blockArg === "true";
  const lines = [MARKER, "## Security audit"];
  const findingsPath = path.join(outDir, "findings.json");

  // Fail closed: a missing or invalid result blocks, so a broken audit can't pass a PR.
  if (!fs.existsSync(findingsPath)) {
    lines.push("", "**Blocked:** the audit produced no `findings.json`. See the job log.");
    console.log(lines.join("\n"));
    return 1;
  }
  const check = spawnSync(process.execPath, [path.join(skillDir, "validate-findings.cjs"), findingsPath], {
    encoding: "utf8",
  });
  if (check.status !== 0) {
    lines.push("", "**Blocked:** `findings.json` failed validation.", "", "```", (check.stdout + check.stderr).trim().slice(0, 3000), "```");
    console.log(lines.join("\n"));
    return 1;
  }

  const records = JSON.parse(fs.readFileSync(findingsPath, "utf8"));
  const confirmed = records
    .filter((r) => r.verdict === "confirmed")
    .sort((a, b) => RANK[b.severity.overall_severity] - RANK[a.severity.overall_severity]);
  const accepted = new Map();
  if (acceptedFile && fs.existsSync(acceptedFile)) {
    for (const raw of fs.readFileSync(acceptedFile, "utf8").split(/\r?\n/)) {
      const [fingerprint, ...reason] = raw.split("#");
      if (fingerprint.trim()) accepted.set(fingerprint.trim(), reason.join("#").trim() || "no reason given");
    }
  }
  const open = (r) => !accepted.has(r.fingerprint);
  const leads = records.filter((r) => r.verdict === "needs_validation");
  const rejected = records.filter((r) => r.verdict === "rejected");
  const blocking = confirmed.filter((r) => open(r) && RANK[r.severity.overall_severity] >= RANK[failAt]);
  const blockingLeads = blockOnUnvalidated ? leads.filter(open) : [];

  let status = {};
  const metaPath = path.join(outDir, "run-metadata.json");
  if (fs.existsSync(metaPath)) {
    try {
      status = JSON.parse(fs.readFileSync(metaPath, "utf8"));
    } catch {
      status = {};
    }
  }

  const blocked = blocking.length > 0 || blockingLeads.length > 0;
  lines.push(
    "",
    blocked ? "**Blocked.**" : "**Passed.**",
    `${confirmed.length} confirmed (${blocking.length} at or above ${failAt}), ${leads.length} need validation, ${rejected.length} rejected.`,
  );
  if (status.run_status && status.run_status !== "complete") {
    lines.push(`Run status: \`${status.run_status}\`${status.incomplete_reason ? ` (${status.incomplete_reason})` : ""}. Coverage is partial.`);
  }
  if (confirmed.length) {
    lines.push("", "| Severity | Finding | Where | Fix |", "|---|---|---|---|");
    for (const r of confirmed) {
      lines.push(`| ${r.severity.overall_severity} | ${cell(r.title)} | ${where(r)} | ${cell(r.remediation && r.remediation.strategy)} |`);
    }
  }
  if (leads.length) {
    lines.push("", `Needs validation (no severity until someone confirms or rejects it)${blockOnUnvalidated ? "; each one blocks until it is fixed or accepted" : ""}:`, "");
    for (const r of leads) {
      const blocker = Array.isArray(r.blockers) && r.blockers.length ? ` Blocked on: ${cell(typeof r.blockers[0] === "string" ? r.blockers[0] : JSON.stringify(r.blockers[0]))}` : "";
      lines.push(`- ${cell(r.title)} ${where(r)} (\`${r.fingerprint}\`).${blocker}`);
    }
  }
  const acceptedHere = records.filter((r) => accepted.has(r.fingerprint));
  if (acceptedHere.length) {
    lines.push("", "Accepted by a reviewer (not blocking):", "");
    for (const r of acceptedHere) lines.push(`- ${cell(r.title)} (\`${r.fingerprint}\`): ${cell(accepted.get(r.fingerprint))}`);
  }
  console.log(lines.join("\n"));
  return blocked ? 1 : 0;
}

process.exit(main());
