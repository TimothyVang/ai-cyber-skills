# model-the-domain

Group: architecture. When: writing stateful logic, or code that branches a lot or repeats a shape assumption across files.
- **Rule.** Encode the real domain in a data structure instead of scattered conditionals; make invalid states unrepresentable and delete branches. Cheap at write time; later it reads as a refactor and gets deferred.
- **Reach for.** State machine over scattered booleans/phases; typed model over loose params; map/registry/lookup table/discriminated union over branching across files; reducer or command/event model over ad hoc mutation; modules owning one body of domain knowledge (execution order is not ownership); small module boundary gathering repeated behavior/invariants; queue/cache/index/graph/tree/normalized collection where access calls for it. None fits → work out what the code must never allow and how data is read, then find the structure encoding exactly that.
- Don't force it: prefer boring code if the shape is clear, local, unlikely to grow. Distrust abstractions that add indirection without removing branches, duplicated rules, invalid states, or lifecycle risk.
- **Tells you skipped it.** A feature grows an if/else chain by one branch; a second boolean must stay in sync with the first; phase-named modules (load/validate/transform/save) repeat domain rules.
