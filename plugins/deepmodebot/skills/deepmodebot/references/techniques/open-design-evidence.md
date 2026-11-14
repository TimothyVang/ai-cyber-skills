# Open design evidence

Use when a recorded journey needs an editable workflow diagram, or a proposed UI needs an open design tool.
Keep **recorded workflow** and **prospective design** separate. A diagram of recorder observations does not prove a design was implemented, imported into Penpot, or accepted by reviewers.

## Export a recorded workflow

1. Use the recorder's hash-validated evidence bundle. Preserve the original user intent, expectations, actual observations, failed steps, and capture limitations.
2. Choose a NEW output directory outside the bundle. From the repository root:

   ```bash
   python plugins/deepmodebot/skills/deepmodebot/assets/e2e/design.py \
     --bundle .scratch/evidence/journey --out .scratch/evidence/journey-design
   ```

3. Open `journey-design/index.html`. It indexes every recorded step, its full observations, screenshot and textual snapshot, recorded video, and sampled frames.
   `workflow.svg` has editable step groups, text, rectangles and paths, plus local evidence links. Each step PNG is embedded in the SVG as a thumbnail, not loaded from an external thumbnail file. `workflow.mmd` is editable Mermaid source.
   Embedded screenshots remain raster images: their depicted buttons, fields and other UI controls are not editable SVG controls.
   `design.json` pins the source bundle hash and exported artifact hashes. The exporter also copies media bytes unchanged into `assets/`; originals remain untouched. The complete folder preserves portable media and relative evidence links.
4. Render the SVG in a real browser. Capture the render and inspect all cards at readable zoom. Follow a step link and screenshot link. Move the complete export folder and confirm its relative links still work.
   The SVG previews abbreviate long fields; the HTML index retains their full text. Embedded thumbnails travel with the SVG, but its evidence links still need the exported folder. SVG hyperlinks and Mermaid click links may be discarded or disabled by importers.
5. If the input capture failed, report a failed recording with an editable diagnostic index. A successful export does not turn failed or incomplete evidence into acceptance.

The [2026-11-13 invoice pilot](../../../../../../docs/evidence/ecosystem-pilot-2026-11-13/README.md) rendered the generated SVG in a browser with six editable step groups and six embedded PNG images. Its text and rectangles are diagram primitives; the screenshot pixels remain raster.
A separate isolated Penpot 2.18 run imported that SVG, edited a native rectangle from width 984 to 1000, and exported both `.penpot` and SVG. The archive retains the edited geometry. Text remained raw SVG, not native rich text; screenshots remain raster.
The [native evidence and provenance](../../../../../../docs/evidence/ecosystem-pilot-2026-11-13/penpot/provenance.json) retain screenshots and a supplementary edit video. Raw exported SVG depends on local-server media; a clearly labeled derivative embeds the unchanged archive images and was rendered in a browser. No native-file re-import or interaction prototype is claimed.

## Use a real design tool

Choose Penpot for boards, components, and interaction prototypes. Choose Excalidraw for sketch-like workflows, or draw.io for editable diagram nodes and connectors.
The [dated research and isolated local launch recipe](../../../../../../docs/research/open-design-tools.md) covers exact license scope, import limits, and prerequisites.

- Penpot: insert the SVG into a new file's canvas using the image tool or drag-and-drop. This is different from importing a native `.penpot` file at the dashboard.
  Inspect the imported layer tree and edit one text or shape in a duplicate. Export that selection back to SVG and retain the result beside screenshots of the actual import and edit.
  Report which primitives remained editable. If text becomes raw SVG or a raster image, report that limitation rather than calling it an editable Penpot design.
- Excalidraw: convert Mermaid through its official Mermaid-to-Excalidraw integration, then retain the editable `.excalidraw` scene and exported preview. Conversion support varies by diagram type.
- draw.io: insert Mermaid using the **Diagram** option, not **Image**. Save the native diagram. SVG alone is not evidence that native diagram shapes survived.

Use only an explicitly authorized account or isolated local deployment. Local files uploaded to hosted editors leave the workstation; obtain approval before that transfer.
Use fresh local project data, loopback-only published ports, and project-local configuration. Leave unrelated containers and personal browser profiles alone.
Read-only inspection comes before MCP writes. Keep MCP keys out of URLs in evidence, screenshots, logs, and committed configuration.

## Prospective UI design

Create a separate proposal file or page labeled **Prospective design, not observed runtime**.
Record its user intent, states, navigation, accessibility requirements, and the recorded steps that motivated each change.
Use actual editable boards and prototype connections when claiming a Penpot prototype. An imported sequence diagram is not a runnable interaction prototype.
Implement the agreed proposal, record the real journey again, and apply the independent visual-review gate to the new recording. Design-tool output is not a substitute for that gate.
Keep source recordings immutable. Publish approved public-safe diagrams and evidence under a discoverable repository-local evidence folder, linked from the delivery report. Private raw review events and OAuth metadata stay local.

## Done when

Every recorded step has its intent context, expectation, actual observation, and available image link in the exported index; unavailable evidence remains explicit.
The original bundle still validates, the portable export renders and its links work, and any claimed design-tool import or prototype has retained runtime proof.
The report distinguishes generated SVG, successful native import, prospective design, runtime recording, and independent acceptance.

## Sources checked 2026-11-13

- [Penpot layer export formats](https://help.penpot.app/user-guide/export-import/exporting-layers/)
- [Penpot SVG data and import limitations](https://help.penpot.app/technical-guide/developer/data-guide/)
- [Penpot prototyping](https://help.penpot.app/user-guide/prototyping-testing/prototyping/)
- [Penpot MCP architecture and active-page scope](https://help.penpot.app/mcp/)
- [Excalidraw Mermaid conversion API](https://docs.excalidraw.com/docs/@excalidraw/mermaid-to-excalidraw/api)
- [draw.io editable Mermaid insertion](https://www.drawio.com/docs/manual/mermaid/)
