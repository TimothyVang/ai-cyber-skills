# migrate-callers-then-delete-legacy-apis

Group: architecture. When: introducing a new internal API while old callers exist.
- **Rule.** Migrate every caller and delete the old API in the same wave; no compatibility layers. Update tests to assert the new contract; delete tests that only protect pre-refactor implementation details.
- **Applies when.** No external users depend on backward compatibility; the project can absorb coordinated breaking changes; the new API is part of a simplification/refactor.
