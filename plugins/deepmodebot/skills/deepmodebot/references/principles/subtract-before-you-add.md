# subtract-before-you-add

Group: core. When: sequencing an addition, refactor, or rewrite.
- **Rule.** Remove complexity first, then build. Default to subtraction; leave the design slightly simpler and more capable behind the same or smaller surface.
- **Checks.** Removal sequenced before construction. Cut before you polish. Design for observed usage, not speculative edge cases. No speculative validators, parsers, or guards beyond the spec. Remove redundant prompt instructions and templates. A reference with no novel content is deleted, not stubbed.
- **Anti-patterns.** Building on top of dead code; stub references left behind.
