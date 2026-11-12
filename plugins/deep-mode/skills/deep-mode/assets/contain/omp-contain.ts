// omp tool_call hook: block write/edit/ast_edit calls whose target path is outside the project root.
// Enforces deep-mode's "Contain the work" rule. Install: copy to ~/.omp/agent/hooks/pre/ (all sessions) or
// <repo>/.omp/hooks/pre/ (one repo), or pass `--hook <this file>` for one run.
// Roots = the worktree holding the session cwd plus its main checkout (they differ in a linked worktree, e.g. one
// under <root>/.worktrees/ or an Orca workspace), or the cwd outside git. Also allowed: omp session resources
// (local://, artifact://, agent://, proc://, xd://, out://, conflict://, cfg://) and `extraWriteRoots` in a root's
// .deep-mode.json (only paths the user named). bash and eval are not covered.
import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

const WRITE_TOOLS: Record<string, true> = { write: true, edit: true, ast_edit: true };
const SESSION_URL = /^(local|artifact|agent|proc|xd|out|conflict|cfg):\/\//i;
const HEADER = /^\[(.+)#[0-9A-Za-z]+\]$/; // a copied [path#TAG] header: omp strips the wrapper before writing
const ANY_URL = /^[a-z][a-z0-9+.-]*:\/\//i;
const caseless = process.platform === "win32" || process.platform === "darwin";

interface ToolCallEvent {
	toolName: string;
	input?: Record<string, unknown>;
}

type ToolCallResult = { block: true; reason: string } | undefined;

interface HookApi {
	on(event: "tool_call", handler: (event: ToolCallEvent, ctx: { cwd?: string }) => Promise<ToolCallResult>): void;
}

function real(p: string): string {
	const expanded = p === "~" || p.startsWith("~/") || p.startsWith("~\\") ? path.join(os.homedir(), p.slice(1)) : p;
	let resolved = path.resolve(expanded);
	try {
		resolved = fs.realpathSync.native(resolved);
	} catch {
		// Target may not exist yet; resolve its nearest existing parent so symlinked parents still count.
		const parent = path.dirname(resolved);
		if (parent !== resolved) resolved = path.join(real(parent), path.basename(resolved));
	}
	return caseless ? resolved.toLowerCase() : resolved;
}

function inside(p: string, root: string): boolean {
	const rel = path.relative(root, p);
	return rel === "" || (!rel.startsWith("..") && !path.isAbsolute(rel));
}

// The worktree holding cwd first, then the main checkout.
function projectRoots(cwd: string): string[] {
	try {
		const [toplevel, common] = execFileSync(
			"git",
			["-C", cwd, "rev-parse", "--path-format=absolute", "--show-toplevel", "--git-common-dir"],
			{ encoding: "utf8", timeout: 10_000, stdio: ["ignore", "pipe", "ignore"] },
		)
			.split(/\r?\n/)
			.map(line => line.replace(/[\\/]+$/, ""));
		if (!toplevel || !common) return [cwd];
		return path.basename(common) === ".git" ? [toplevel, path.dirname(common)] : [toplevel];
	} catch {
		return [cwd];
	}
}

function allowedRoots(roots: string[]): string[] {
	const allowed = [...roots];
	for (const root of roots) {
		try {
			const config: unknown = JSON.parse(fs.readFileSync(path.join(root, ".deep-mode.json"), "utf8"));
			const extra = config && typeof config === "object" && "extraWriteRoots" in config ? config.extraWriteRoots : undefined;
			if (!Array.isArray(extra)) continue;
			for (const p of extra) {
				if (typeof p === "string") allowed.push(path.isAbsolute(p) || p.startsWith("~") ? p : path.join(root, p));
			}
		} catch {}
	}
	return allowed.map(real);
}

function targets(input: Record<string, unknown>): string[] {
	const out: string[] = [];
	if (typeof input.path === "string") out.push(input.path);
	if (Array.isArray(input.paths)) for (const p of input.paths) if (typeof p === "string") out.push(p);
	return out.map(p => HEADER.exec(p.trim())?.[1] ?? p.trim()).filter(p => p.length > 0 && !SESSION_URL.test(p));
}

export default function (pi: HookApi): void {
	pi.on("tool_call", async (event, ctx) => {
		if (!WRITE_TOOLS[event.toolName]) return;
		const cwd = ctx?.cwd ?? process.cwd();
		const roots = projectRoots(cwd);
		const root = roots[0];
		const allowed = allowedRoots(roots);
		for (const target of targets(event.input ?? {})) {
			// skill://, vault://, ssh:// and other non-session URLs resolve outside the root. A selector suffix
			// (archive.zip:member, db.sqlite:table) stays on the path: `..` in it must count against the target.
			if (!ANY_URL.test(target) && allowed.some(r => inside(real(path.resolve(cwd, target)), r))) continue;
			return {
				block: true,
				reason:
					`deep-mode keeps all writes inside the project root ${root}. ${target} is outside it. ` +
					`Put scratch and temp files in ${path.join(root, ".scratch")} and worktrees in ${path.join(root, ".worktrees")}. ` +
					`If the user explicitly named this path, add it to extraWriteRoots in ${path.join(root, ".deep-mode.json")}.`,
			};
		}
		return undefined;
	});
}
