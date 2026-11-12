# Third-party notices

deep-mode is MIT licensed: Copyright (c) 2026 Timothy Vang and deep-mode contributors. See `LICENSE`.

Some components derive from other MIT-licensed work. Each keeps its upstream copyright line and the full MIT permission text in the `LICENSE` file named below. Those files must ship with every copy of the component.

| Component | Upstream | License | Copyright line | License file |
|---|---|---|---|---|
| `plugins/deep-mode/skills/deep-mode/` | pstack `poteto-mode` skill, https://github.com/cursor/plugins/tree/main/pstack | MIT | Copyright (c) 2026 Lauren Tan | `plugins/deep-mode/skills/deep-mode/LICENSE` |
| `plugins/deep-mode/skills/deep-mode/references/techniques/grill.md` | `grilling` and `grill-me` skills, https://github.com/mattpocock/skills | MIT | Copyright (c) 2026 Matt Pocock | `plugins/deep-mode/skills/deep-mode/LICENSE` |
| `plugins/deep-mode/skills/deep-mode/references/playbooks/wayfinder.md` | `wayfinder` skill, https://github.com/mattpocock/skills | MIT | Copyright (c) 2026 Matt Pocock | `plugins/deep-mode/skills/deep-mode/LICENSE` |
| `plugins/deep-mode/skills/create-verification-skill/` | pstack `create-verification-skill` | MIT | Copyright (c) 2026 Lauren Tan | `plugins/deep-mode/skills/create-verification-skill/LICENSE` |
| `plugins/deep-mode/skills/maintain-verification-skill/` | pstack `maintain-verification-skill` | MIT | Copyright (c) 2026 Lauren Tan | `plugins/deep-mode/skills/maintain-verification-skill/LICENSE` |
| `plugins/deep-mode/skills/deep-stack/references/unslop/` | pstack `unslop` skill | MIT | Copyright (c) 2026 Lauren Tan | `plugins/deep-mode/skills/deep-stack/references/unslop/LICENSE` |

Public-domain components:

| Component | Upstream | License |
|---|---|---|
| `plugins/deep-mode/skills/deep-mode/assets/pr-conversation/font8x8_basic.hex` (the 8x8 bitmap font `arena.py` draws its text with) | `font8x8_basic.h` by Daniel Hepper, https://github.com/dhepper/font8x8, based on Marcel Sondaar's and IBM's public-domain VGA fonts | Public domain |

Review-evaluation source patches in `evals/review/cases.json` retain their upstream licenses. They are exact forward or reverse diffs of pinned repairs, not new implementations of those projects:

| Upstream | License | Copyright / attribution | License file |
|---|---|---|---|
| [pytest](https://github.com/pytest-dev/pytest), repair `3a85b5ead0753e50b7689c489235237acfa7b94e` | MIT | Copyright (c) 2004 Holger Krekel and others | `evals/review/licenses/LICENSE-pytest.txt` |
| [Requests](https://github.com/psf/requests), repairs `818d92764bd7035a0450d7b4e52ec9fc6d07abb6` and `0406663e1b802bb839aca40e9f6ea89d0c9255ef` | Apache-2.0 | Requests contributors; source paths and commits are recorded per case | `evals/review/licenses/LICENSE-requests.txt` |
| [Django](https://github.com/django/django), repair `41b43c74bda19753c757036673ea9db74acf494a` | BSD-3-Clause | Copyright (c) Django Software Foundation and individual contributors | `evals/review/licenses/LICENSE-django.txt` |

All other files in this repository are covered by the root `LICENSE`.
