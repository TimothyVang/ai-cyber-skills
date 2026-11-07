# laziness-protocol

Group: core. When: refactoring, sizing a diff, or tempted to add abstractions, layers, or signal threading.
- **Rule.** Bias to deletion and the smallest change that solves the problem.
- **Checks.** Is the same choice made in several places? Put it behind one source of truth and pass the result as a simple flag. Is this the smallest diff that solves it? Fewer lines beat "elegant" boilerplate.
- **Anti-patterns.** New layers or abstractions nobody asked for; threading a signal through many functions instead of deciding once; frameworks where a small script would do.
