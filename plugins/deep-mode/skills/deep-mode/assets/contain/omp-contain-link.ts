// omp tool_call hook that loads deep-mode's write guard (omp-contain.ts) from the installed plugin. Copy this
// file once to ~/.omp/agent/hooks/pre/; it never needs updating, because it reads the guard through the link omp
// keeps on the current plugin version (~/.omp/plugins/node_modules/deep-mode). A copy of omp-contain.ts itself
// would go stale with every plugin upgrade. If the plugin is not installed, omp reports this hook failing to load.
import * as os from "node:os";
import * as path from "node:path";
import { pathToFileURL } from "node:url";

const guard = path.join(os.homedir(), ".omp/plugins/node_modules/deep-mode", "skills/deep-mode/assets/contain/omp-contain.ts");
const mod = await import(pathToFileURL(guard).href); // dynamic: the path depends on the user's home folder

export default mod.default;
