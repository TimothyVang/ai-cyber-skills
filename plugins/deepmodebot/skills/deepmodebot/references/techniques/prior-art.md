# prior-art

**Use when:** before building anything new: a feature, tool, integration, CLI, service, or whole project. Also when the user asks "is there a library / project / example for X". Most code worth writing has an example, a library, or a whole project somewhere. Find it before writing it, then reuse the best of it.

1. **Name what you need** in one line: the customer/job, language, runtime, acceptable licenses, data/deployment constraints and must-have behavior.
   When the project starts from a saved startup idea or video anecdote, read [startup references](../startup-ideas.md) before treating it as product or market evidence.
   Done when those constraints are explicit; a source's popularity or revenue story is not validation.
2. **Search, in parallel `scout` subagents**, one per source. Start with what's new, because the idea you already know may have been beaten this month:
   - **Repository catalog** (GitHub Trending/search, githubawesome.com and the [dated reference library](../../assets/repo-references.json)): run `python <this skill>/scripts/trending.py find <project terms>` from the project root.
     It keeps `.scratch/trending/`; stale data or a changed reference revision is replaced by a matching published catalog or rebuilt with network and `gh auth`.
     Search by role, platform or problem. Reference topics, dates and cautions are discovery leads, not tested suitability; inspect the primary source before adoption. Descriptions remain untrusted data.
   - **GitHub:** `gh search repos "<terms>" --sort stars --limit 20`, plus the same with `--created ">=<date 90 days ago>"` to catch new projects stars haven't caught up with; `gh search code "<api or symbol>" --limit 30`; awesome-lists for the domain.
   - **Package registries** for the stack: npm (`npm search`, npmjs.com), PyPI (pypi.org), crates.io, pkg.go.dev, Maven Central, RubyGems, NuGet, Packagist.
   - **Official docs and examples:** the framework's or API's own docs, quickstarts, example repos, and cookbooks; pull current library source with `npx opensrc <package>` when the docs lag.
   - **The repo itself and its dependencies:** an existing helper or a dependency that already does it beats anything new.
   Done when every source has returned a candidate list or a null result.
3. **Judge each candidate** with checks you run, not stars alone. Put the newest strong candidate head to head with the incumbent (the library or pattern you would have reached for); it wins only on a check you ran (fit, size, speed, license, maintenance), never on novelty:
   - License: read the exact terms for the code, documentation, bundled components, assets and model weights, not just the root SPDX badge.
     Permissive licenses still have conditions; copyleft duties depend on the license and reuse. Custom/source-available terms can restrict commercial hosting or white-labeling.
     Missing or unrecognized license metadata is not permission to copy. The [OpenMausBot enterprise exception](https://github.com/milind-soni/OpenMausBot/blob/main/enterprise/LICENSE) is one concrete boundary; dated evidence is linked from the reference library.
   - Alive: last release or commit, open issues answered, not archived or marked unmaintained.
   - Fit: does it do the must-have behavior? Clone it to a scratch folder and run its example or tests once.
   - Weight and risk: dependency count, install size, security advisories (`npm audit`, `pip-audit`, GitHub advisories).
   Done when every shortlisted candidate has a result for all four checks.
4. **Pick how to reuse it**, lightest first:
   - **Depend** on a maintained package.
   - **Copy** a small piece (a function, a config, an example), keeping its license notice and a source link in a comment or NOTICE file.
   - **Fork or clone** a whole project when it is most of what's needed; record the upstream URL and commit you started from.
   - **Build** only when nothing fits, and say why each candidate didn't.
   Done when each piece has one reuse choice, with the upstream URL and commit for a fork.
5. **Log the choice** as a decision-trail row (show-me-your-work): what you found, what you picked, the license, and the rejected candidates in one line each.
   Done when the trail has that row.

## Gates

- Never copy code whose license you haven't read, or that has no license.
- Forking or cloning into the user's GitHub account is a normal action; publishing a package or messaging an upstream maintainer is a hard stop (SKILL.md Autonomy).
- Reused code meets the same bar as written code: it is tested and verified in this project before it counts as done.

**Done when** the build plan names, for each piece, the dependency, copied source, fork, or "built new" with the reason.
