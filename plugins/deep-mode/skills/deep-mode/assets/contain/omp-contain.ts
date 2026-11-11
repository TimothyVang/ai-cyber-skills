// omp tool_call hook for deep-mode. Blocks write/edit/ast_edit calls whose target path is outside the project root
// ("Contain the work"), and read/grep/edit calls that name a secret file (.env.keys, private keys, .kdbx,
// ~/.aws/credentials, .scratch/auth/; .env itself is readable). Install: copy to ~/.omp/agent/hooks/pre/ (all sessions) or
// <repo>/.omp/hooks/pre/ (one repo), or pass `--hook <this file>` for one run.
// Roots = the worktree holding the session cwd plus its main checkout (they differ in a linked worktree, e.g. one
// under <root>/.worktrees/ or an Orca workspace), or the cwd outside git. Also allowed: omp session stores (local://,
// artifact://, agent://, proc://, xd://) and `extraWriteRoots` in a root's .deep-mode.json (only paths the user
// named). bash and eval are not covered.
import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

const WRITE_TOOLS: Record<string, true> = { write: true, edit: true, ast_edit: true };
const SECRET_READ_TOOLS: Record<string, true> = { read: true, grep: true, edit: true };
const SECRET_FILE = /^(\.env\.keys|id_(rsa|dsa|ecdsa|ed25519)|\.netrc|\.pgpass|\.git-credentials)$|\.(pem|key|p12|pfx|kdbx|jks|keystore)$/i;
const SECRET_DIR = /[\\/](\.aws[\\/]credentials|\.scratch[\\/]auth[\\/].*)$/i;
const SESSION_URL = /^(local|artifact|agent|proc|xd):\/\//i;
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

// grep takes `;`-separated paths with `!` excludes; read paths may end in a `:range` or `:raw` selector.
function targets(input: Record<string, unknown>): string[] {
	const out: string[] = [];
	if (typeof input.path === "string") out.push(...input.path.split(";"));
	if (Array.isArray(input.paths)) for (const p of input.paths) if (typeof p === "string") out.push(p);
	return out.map(p => p.trim()).filter(p => p.length > 0 && !p.startsWith("!") && !SESSION_URL.test(p));
}

function isSecret(file: string): boolean {
	const p = file.replace(/:[^\\/]*$/, "");
	return SECRET_FILE.test(path.basename(p)) || SECRET_DIR.test(p);
}

export default function (pi: HookApi): void {
	pi.on("tool_call", async (event, ctx) => {
		const tool = event.toolName;
		if (!WRITE_TOOLS[tool] && !SECRET_READ_TOOLS[tool]) return;
		const cwd = ctx?.cwd ?? process.cwd();
		const list = targets(event.input ?? {});
		if (SECRET_READ_TOOLS[tool]) {
			const secret = list.find(t => !ANY_URL.test(t) && isSecret(path.resolve(cwd, t)));
			if (secret) {
				return {
					block: true,
					reason:
						`deep-mode never reads key, password-database, credential, or saved-session files, and ${secret} is one. ` +
						"Let the tool that needs it load it (`dotenvx run -- <cmd>`, `ssh`, `bw`), and ask the user for anything only " +
						"they should see. Rules: deep-mode references/credentials/README.md.",
				};
			}
		}
		if (!WRITE_TOOLS[tool]) return;
		const roots = projectRoots(cwd);
		const root = roots[0];
		const allowed = allowedRoots(roots);
		for (const target of list) {
			const file = target.replace(/^([^:]{2,}):[^\\/].*$/, "$1"); // archive.zip:member, db.sqlite:table
			// skill://, omp://, ssh:// and other non-session URLs resolve outside the root.
			if (!ANY_URL.test(target) && allowed.some(r => inside(real(path.resolve(cwd, file)), r))) continue;
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
