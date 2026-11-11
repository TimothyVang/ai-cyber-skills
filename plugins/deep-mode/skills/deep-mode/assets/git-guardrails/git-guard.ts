// Git guard for omp: a pre-tool hook. Install to .omp/hooks/pre/ (project) or ~/.omp/agent/hooks/pre/ (user),
// together with git-guard-patterns.txt in the same folder. Blocks matching commands in the bash tool
// and in eval cells, which can also run shell commands.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const patternFile = join(dirname(fileURLToPath(import.meta.url)), "git-guard-patterns.txt");

function loadPatterns(): RegExp[] | undefined {
	try {
		return readFileSync(patternFile, "utf8")
			.split(/\r?\n/)
			.filter(line => line.trim() !== "" && !line.trimStart().startsWith("#"))
			.map(line => new RegExp(line, "m"));
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
		const patterns = loadPatterns();
		if (!patterns) return { block: true, reason: `git guard: cannot read ${patternFile}; blocking until it is restored.` };
		const text = String(event.input?.[field] ?? "");
		for (const pattern of patterns) {
			const hit = pattern.exec(text);
			if (hit) {
				return {
					block: true,
					reason:
						`Blocked by the git guard: "${hit[0]}" can destroy work or rewrite shared history. ` +
						"Use a safe form instead (git stash, a new branch, git push --force-with-lease to your own feature branch, " +
						"a PR for the default branch), or ask the user to run it themselves.",
				};
			}
		}
	});
}
