# Patterns from shipped apps (Mobbin)

Real, shipped products, so prefer these over concept shots as layout references. Free-tier previews only (2 per pattern). Screens: `TimothyVang/frontend:reference/screens/mobbin/`.

## What each pattern search showed

| Pattern (facet) | Total on Mobbin | Captured | What it shows |
| --- | --- | --- | --- |
| Chat Bot (`screenPatterns.Chat+Bot`) | 524 screens | `chat-bot/strut`, `chat-bot/linear` | **Strut:** a three-pane writing app with the AI chat docked right. The "You" / assistant turns sit in a narrow column, with an orange inline "Create a doc" action on the reply and the composer pinned at the bottom. **Linear:** an empty-state agent home ("Welcome to Linear / Ask anything") with a centered composer and three suggestion cards below it, which are capability chips (PLAYBOOK §4a) |
| Settings & Preferences (`screenPatterns.Settings+%26+Preferences`) | 3,202 screens | `attio`, `patreon` | Both use a left settings nav with grouped sections and a single narrow form column. Patreon has a large page title and a solid primary button at the form's end; Attio is denser, with its profile section in a card |
| Notifications (`screenPatterns.Notifications`) | 612 screens | `bonsai`, `deel` | **Bonsai:** an activity feed as a right-hand column on the dashboard. **Deel:** a popover notification panel with tabs and per-item actions, anchored to the bell |
| My Account & Profile (`screenPatterns.My+Account+%26+Profile`) | 369 screens | `peerlist`, `duolingo` | Profile header card, then stat tiles and lists. Duolingo puts gamified stats in a 2×2 grid |
| Charts (`screenPatterns.Charts`) | 1,404 screens | `beehiiv`, `cake-equity` | **beehiiv:** KPI row → line chart → right rail. **Cake Equity:** a donut ownership chart in a card grid with an activity rail |
| Side Navigation (`screenElements.Side+Navigation`) | 1,566 UI | `pandadoc`, `opensea` | **PandaDoc:** a light, grouped sidebar with a workspace switcher on top and a "Get started" checklist panel on the right. **OpenSea:** a collapsed icon rail beside a dense data table |
| Progress Indicator (`screenElements.Progress+Indicator`) | 1,783 UI | `pandadoc`, `cake-equity` | Setup-progress checklists in a dashboard rail or banner ("n of m complete") |
| Stepper (`screenElements.Stepper`) | 347 UI | `uniswap`, `zoom` | **Zoom:** a numbered vertical checkout stepper ("1. How many licenses… 2. Choose your plan…"). **Uniswap:** a stepped liquidity form |
| File Upload (`screenElements.File+Upload`) | 1,157 UI | `shopify`, `veed` | **Shopify:** an inline dropzone inside a long product form. **VEED:** a modal "New Project" with a dropzone and source options (record, stock) |
| Onboarding (`flowActions.Onboarding`) | 683 flows | `remote-onboarding` | A split screen: a solid brand-color left panel with the sign-up form, and a product preview on the right |
| Setting Up (`flowActions.Setting+Up`) | 767 flows | `shopify-setting-up-an-account` | "Let's get started. Which of these best describes you?" A single question in a centered card over a blurred app shell |
| Filtering & Sorting (`flowActions.Filtering+%26+Sorting`) | 2,016 flows | `deel-filtering-people` | A filter popover with checkbox options anchored to a "Filter" button above a people table |

## Patterns worth taking for an agent product

- **Empty-state agent home** (Linear): a centered composer with 3 capability cards, matching PLAYBOOK §4a "idle composer".
- **Docked assistant pane** (Strut): chat as a right pane beside the work, with actions inline on the reply. Fits an agent that edits a document or workspace.
- **Setup checklist in a rail** (PandaDoc, Cake Equity): progress for first-run configuration, such as connecting tools or setting permissions.
- **Notification popover with per-item actions** (Deel): a model for an approvals inbox when the agent waits on the user while they're elsewhere.
- **One question per onboarding step** (Shopify): matches "one decision per approval" (PLAYBOOK §4a).
