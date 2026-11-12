# type-system-discipline

Group: architecture. When: designing types, reviewing a signature, writing any statically-typed code.
- **Rule.** Make the compiler reject impossible states, mismatched primitives, and unhandled variants. Define errors and special cases out of existence rather than multiplying handlers.
- **Checks.** Brand semantic primitives (`UserId` vs `OrderId`; branded intersection or newtype); validate once at creation, trust downstream; two args sharing a primitive but meaning different things → brand them. External data is untyped until parsed (RPC, JSON, IPC, CLI, config, env, DB rows): a parse function at every boundary (see boundary-discipline). Derive types from the authoritative schema (protobuf, OpenAPI, GraphQL, migrations, design tokens) instead of hand-rolling a parallel type (see encode-lessons-in-structure). Exhaust variants.
- **Anti-patterns.** Hand-maintained parallel types; casts and `any` instead of parsing.
