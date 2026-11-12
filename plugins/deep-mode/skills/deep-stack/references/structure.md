# Structure shared code

Use this when two or more workflows repeat the same operation, or when a new feature needs mechanics that already exist. The project's existing architecture wins. This split is the default only when the project has no convention.

## The split

- **Entry points** (route handlers, server actions, CLI commands, jobs) decide *whether* and *when*. They hold product rules: permissions, plan limits, which steps run in which order.
- **Services** decide *how*. A service does one reusable operation, such as charging a card or sending an email. It takes explicit inputs and returns a structured result: a success value or a typed error.
- Services do not read request state, session globals, or UI state. Everything they need arrives as an argument.
- Services do not call entry points. Entry points may call several services.

## Steps

1. List the places that repeat the operation. Note what differs between them.
2. Move the shared part into one service. Make every difference an input.
3. Keep the decisions that differ in the entry points.
4. Return a result object instead of throwing for expected failures, so callers handle them explicitly.
5. Replace every copy with a call to the service. Delete the copies.

## Done when

No operation is duplicated across callers, and the repo's typecheck and lint pass.
