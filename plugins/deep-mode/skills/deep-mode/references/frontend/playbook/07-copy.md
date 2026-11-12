## 7. Copy
[anthropic frontend-design skill; vercel]
- Write from the user's side, in the user's terms ("notifications", not "webhook config").
- Sentence case (chosen for this repo over Vercel's Title Case), active voice, plain verbs, no filler.
- A CTA names its result ("Save changes", not "Submit"). The name stays consistent through the flow ("Publish" produces the toast "Published").
- Destructive actions use Verb + Noun and never "OK" or "Confirm". A dialog's title and its primary button share the verb ("Delete project?" → "Delete project"). Explain what deletion does *before* the confirm. Offer undo when it can honestly be supported. [articles/component-gallery/modal; articles/checklist-design]
- Errors say what happened and how to fix it; they don't apologize and aren't vague. Upload errors are specific ("The file must be smaller than 2 MB").
- Empty states invite the next action. There are three kinds: nothing yet (educate), no results (adjust the query), failed to load (plain, no jokes). [articles/checklist-design; articles/component-gallery/empty-state]
- **Accessible names:** distinguishing word first (usually a verb), 1–3 words, never the role word, no trailing period. A switch's label never changes with its state. [articles/wai-aria-apg]
- **Hedging tracks real reliability** ("is" vs "may"). No human persona framing for the agent: no "think", "understand" or "feel" in system copy, and no "Great question!". AI labels are verb-first and user-initiated ("Summarize with agent"); disclosure labels name the action ("Rewritten by agent"); attributions say "Because you…". [articles/microsoft-hax G2; articles/google-pair; articles/ai-ux/microsoft-agents-copilot-mcp-apps; articles/ai-ux/atlassian-rovo-ai-guidelines]
- In-progress labels end with `…` ("Saving…").
