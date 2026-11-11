# prior-art

**Use when:** before building anything new: a feature, tool, integration, CLI, service, or whole project. Also when the user asks "is there a library / project / example for X". Most code worth writing has an example, a library, or a whole project somewhere. Find it before writing it, then reuse the best of it.

1. **Name what you need** in one line, with its hard constraints: language, runtime, license the project can accept, and must-have behavior.
2. **Search, in parallel `scout` subagents**, one per source:
   - **GitHub:** `gh search repos "<terms>" --sort stars --limit 20` and `gh search code "<api or symbol>" --limit 30`; awesome-lists for the domain.
   - **Package registries** for the stack: npm (`npm search`, npmjs.com), PyPI (pypi.org), crates.io, pkg.go.dev, Maven Central, RubyGems, NuGet, Packagist.
   - **Official docs and examples:** the framework's or API's own docs, quickstarts, example repos, and cookbooks; pull current library source with `npx opensrc <package>` when the docs lag.
   - **The repo itself and its dependencies:** an existing helper or a dependency that already does it beats anything new.
3. **Judge each candidate** with checks you run, not stars alone:
   - License: compatible with this project? (MIT, Apache-2.0, and BSD reuse freely; GPL and AGPL bind the whole project; no license means no rights to copy.)
   - Alive: last release or commit, open issues answered, not archived or marked unmaintained.
   - Fit: does it do the must-have behavior? Clone it to a scratch folder and run its example or tests once.
   - Weight and risk: dependency count, install size, security advisories (`npm audit`, `pip-audit`, GitHub advisories).
4. **Pick how to reuse it**, lightest first:
   - **Depend** on a maintained package.
   - **Copy** a small piece (a function, a config, an example), keeping its license notice and a source link in a comment or NOTICE file.
   - **Fork or clone** a whole project when it is most of what's needed; record the upstream URL and commit you started from.
   - **Build** only when nothing fits, and say why each candidate didn't.
5. **Log the choice** as a decision-trail row (show-me-your-work): what you found, what you picked, the license, and the rejected candidates in one line each.

## Gates

- Never copy code whose license you haven't read, or that has no license.
- Forking or cloning into the user's GitHub account is a normal action; publishing a package or messaging an upstream maintainer is a hard stop (SKILL.md Autonomy).
- Reused code meets the same bar as written code: it is tested and verified in this project before it counts as done.

**Done when** the build plan names, for each piece, the dependency, copied source, fork, or "built new" with the reason.
