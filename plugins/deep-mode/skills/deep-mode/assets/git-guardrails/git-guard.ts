// Git guard for omp: a pre-tool hook. Install to .omp/hooks/pre/ (project) or ~/.omp/agent/hooks/pre/ (user),
// together with git-guard-patterns.txt in the same folder. Blocks matching commands in the bash tool
// and in eval cells, which can also run shell commands.
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const patternFile = join(dirname(fileURLToPath(import.meta.url)), "git-guard-patterns.txt");

// A rule blocks a command; a rule with a branch blocks it only while that branch is checked out.
interface Rule {
	command: RegExp;
	branch?: RegExp;
}

function loadRules(): Rule[] | undefined {
	let text: string;
	try {
		text = readFileSync(patternFile, "utf8");
	} catch {
		return undefined;
	}
	const rules: Rule[] = [];
	for (const line of text.split(/\r?\n/)) {
		const trimmed = line.trimStart();
		if (trimmed === "" || trimmed.startsWith("#")) continue;
		const branchRule = /^@branch +([^ ]+) +(.+)$/.exec(trimmed);
		if (branchRule) rules.push({ branch: new RegExp(`^(${branchRule[1]})$`), command: new RegExp(branchRule[2], "m") });
		else rules.push({ command: new RegExp(line, "m") });
	}
	return rules;
}

function checkedOutBranch(cwd: string): string | undefined {
	try {
		const out = execFileSync("git", ["symbolic-ref", "--short", "-q", "HEAD"], {
			cwd,
			encoding: "utf8",
			stdio: ["ignore", "pipe", "ignore"],
		});
		return out.trim() || undefined;
	} catch {
		return undefined;
	}
}

const watched: Record<string, string> = { bash: "command", eval: "code" };

export default function gitGuard(pi: {
	on(event: "tool_call", handler: (event: { toolName: string; input: Record<string, unknown> }) => unknown): void;
}): void {
	pi.on("tool_call", event => {
		const field = watched[event.toolName];
		if (!field) return;
		const rules = loadRules();
		if (!rules) return { block: true, reason: `git guard: cannot read ${patternFile}; blocking until it is restored.` };
		// One line at a time, as grep does in git-guard.sh: arguments must not run on into the next command.
		// A backslash-newline continues the command on the next line.
		const lines = String(event.input?.[field] ?? "")
			.replace(/\\\r?\n/g, " ")
			.split(/\r?\n/);
		let branch: string | null | undefined = null;
		for (const rule of rules) {
			const hit = lines.map(line => rule.command.exec(line)).find(match => match !== null);
			if (!hit) continue;
			if (rule.branch) {
				if (branch === null) branch = checkedOutBranch(resolve(String(event.input?.cwd ?? "")));
				if (!branch || !rule.branch.test(branch)) continue;
			}
			return {
				block: true,
				reason:
					`Blocked by the git guard: "${hit[0]}" can destroy work or rewrite shared history. ` +
					"Use a safe form instead (git stash, a new branch, git push --force-with-lease to your own feature branch, " +
					"a PR for the default branch), or ask the user to run it themselves.",
			};
		}
	});
}
