# Open design tools and recorded workflow evidence

Checked 2026-11-13 against the primary sources linked below. Product documentation and default image tags change; record the actual version and image digest used in each runtime proof.

## Decision and boundaries

Use an original, static SVG plus Mermaid source as the portable recorded-workflow interchange. Use Penpot when the task needs editable UI boards and prototypes, not merely a diagram image.
Excalidraw and draw.io are credible open-source alternatives for sketching and diagramming, respectively. They are not asserted to have full Figma feature parity or superior benchmark results.
The exporter does not depend on or copy these projects' code, icons, templates, fonts, or marketing assets.
It copies the operator's validated recording artifacts byte-for-byte into a separate export directory, preserving source recordings and their hashes.

A **recorded workflow index** reflects actual recorder results, including failures. Arrows show recording order, not a causal claim.
A **prospective design** proposes future screens or behavior. Keep it in a separate page or file with that label.
A **Penpot import** is a runtime event requiring observed UI evidence. Generated SVG alone is not Penpot-authored output, an imported native design, or an interaction prototype.

## Primary-source findings

### Penpot

- [Layers documentation](https://help.penpot.app/user-guide/designing/layers/) describes image insertion with the toolbar, `K`, or drag-and-drop, and boards, text, shapes, and paths.
- [Data guide](https://help.penpot.app/technical-guide/developer/data-guide/) describes SVG nodes converted into Penpot shapes and metadata used for properties without direct SVG equivalents. Attributes absent from export/import functions are lost on round-trip. This is not a blanket guarantee of editable text, hyperlink retention, or perfect import for arbitrary SVG.
- [Layer export](https://help.penpot.app/user-guide/export-import/exporting-layers/) supports PNG, JPEG, WEBP, SVG, and PDF presets. PDF conversion explicitly does not guarantee all SVG features match.
- [Native file export/import](https://help.penpot.app/user-guide/export-import/export-import-files/) is a separate dashboard/workspace workflow. Current `.penpot` exports contain JSON and assets in a ZIP structure; the docs describe older formats separately. Do not rename this exporter's SVG to `.penpot`.
- [Prototyping](https://help.penpot.app/user-guide/prototyping-testing/prototyping/) connects boards with click, mouse-enter, mouse-leave, or delayed triggers. Actions include navigation, overlays, previous screen, and URL opening. Prototype flows are exercised in View mode. Diagram arrows do not create these interactions.
- [MCP](https://help.penpot.app/mcp/) connects an AI client, server, and plugin in an open Penpot file. Its context follows the currently focused page, and only one browser tab owns the active connection. A suspended tab can stop operations.
- Remote MCP uses a personal key in the configured URL's `userToken`; treat that URL as a secret. Local MCP exposes filesystem-related capabilities that remote mode does not, including local-path image import. Both can modify designs. Start with read-only inspection, verify the focused page, and restrict writes to the authorized file.
- [Docker setup](https://help.penpot.app/technical-guide/getting-started/docker/) requires Docker and Compose, documents a project-scoped launch, and recommends controlling image versions. It also documents interactive `manage.py create-profile` with `enable-prepl-server`.

### Excalidraw

The [official repository](https://github.com/excalidraw/excalidraw) describes an open-source canvas editor, PNG/SVG export, and editable `.excalidraw` JSON.
Its hosted application adds collaboration, offline PWA support, and local-first persistence. Those app features are not all promised as drop-in features of the npm editor package.
The [official Mermaid conversion API](https://docs.excalidraw.com/docs/@excalidraw/mermaid-to-excalidraw/api) returns editable element skeletons for supported diagram types; unsupported types can instead return an image and binary files.
Retain the native scene and verify individual shape editing rather than assuming an SVG import is fully editable.

### draw.io

The [official repository](https://github.com/jgraph/drawio) describes a diagramming and whiteboarding application, not an SVG editor. Its SVG export is intended for embedding, not general round-trip editing.
The [Mermaid guide](https://www.drawio.com/docs/manual/mermaid/) distinguishes **Diagram**, which produces native shapes/connectors, from **Image**, which produces a single non-editable SVG image.
The current guide says source regeneration retains label/style overrides but resets geometry and connector paths. Save the native diagram and record the mode used.
The current repository README labels that repository distribution a test version and points separately to paid production deployments. Do not generalize the code license into a promise that every hosted or commercial distribution is free.

## License scope, not brand shorthand

| Project | Inspected primary source | Scope and obligations |
| --- | --- | --- |
| Penpot | [Actual LICENSE](https://raw.githubusercontent.com/penpot/penpot/develop/LICENSE) | MPL-2.0. Covered source and modifications remain subject to MPL when distributed; preserve notices and source availability duties. Separate larger-work files may have other terms. No trademark rights are granted. |
| Excalidraw editor | [Actual LICENSE](https://raw.githubusercontent.com/excalidraw/excalidraw/master/LICENSE) | MIT, copyright 2020 Excalidraw. Copies or substantial portions require the copyright and permission notice. This does not license every separately supplied third-party library asset or a paid service. |
| Mermaid-to-Excalidraw | [Actual LICENSE](https://raw.githubusercontent.com/excalidraw/mermaid-to-excalidraw/master/LICENSE) | MIT, copyright 2023 Excalidraw. Preserve its notice if copying substantial code. It is a separate repository/package from the editor. |
| draw.io source | [Actual LICENSE](https://raw.githubusercontent.com/jgraph/drawio/dev/LICENSE) and [README scope](https://github.com/jgraph/drawio) | Apache-2.0 source code. Retain license, applicable attribution/NOTICE, and modification notices when redistributing covered code. Icons, stencils, and templates have separately stated restrictions. |

The inspected draw.io README specifically restricts using its icon/stencil assets and derivatives in Atlassian products or marketplace/plugin products without written permission, while excluding end-user diagram output from that restriction.
It also notes third-party icon copyrights and makes no copyright claim on user-created diagrams. Therefore “the whole asset library is Apache-2.0” would be false.
No third-party implementation or artwork was copied for this exporter. Recheck the selected distribution's LICENSE, NOTICE, and asset-specific terms before future reuse.

## Read-only workstation observations

Observed during this assignment, without starting services or changing contexts:

```text
docker context show
  desktop-linux
docker context ls
  default -> npipe:////./pipe/docker_engine
  desktop-linux (active) -> npipe:////./pipe/dockerDesktopLinuxEngine
docker info --format '{{json .ServerVersion}}'
  "29.9.2"
docker compose version
  Docker Compose version v5.6.1
docker image ls --format '{{.Repository}}:{{.Tag}}' --filter reference='penpotapp/*'
  no rows
```

`docker ps` showed running unrelated workloads and no Penpot containers. An existing unrelated Mailpit publishes `127.0.0.1:8025`; do not stop it or reuse its storage.
The Docker engine is reachable. This does not prove spare memory/disk capacity or that Penpot will start successfully.
No personal browser profile, account, credential, or Penpot login was inspected. Authorized browser-account availability remains unknown.
No Penpot service was installed, pulled, started, or imported into by the research/export worker. Rendering and import proof belong to the integration run.

## Minimal isolated official-compose recipe

This recipe is not by itself deployment evidence. The [integration pilot](../evidence/ecosystem-pilot-2026-11-13/README.md) records actual observations and failures. Use this only for disposable local proof, not production.
Use a unique project directory under `.scratch/penpot-proof/`, an unused loopback port, and the existing local `desktop-linux` context. Avoid changing the global Docker context.
Image pulls require network and disk. Creating a local test identity and starting services require the operator's applicable authorization. External hosted uploads require separate approval.

1. Download [the official compose file](https://raw.githubusercontent.com/penpot/penpot/main/docker/images/docker-compose.yaml) into that project directory and retain its SHA-256 with the proof.
   At inspection its Penpot image fallback was `2.18`; its services included frontend, backend, exporter, admin-console, MCP, PostgreSQL 15, Valkey 8.1, and Mailpit.
   The help page also describes later-version migration rules. Do not combine an arbitrary future image tag with an older compose file. Pin a matching release and record resolved image digests.
2. The official defaults publish frontend `9001:8080` and Mailpit `8025:8025`, enable telemetry, and contain example secrets. Do not launch those defaults unmodified.
   Set session-only environment variables `PENPOT_VERSION`, `PENPOT_SECRET_KEY`, and `PENPOT_DB_PASSWORD` through a secret injector or non-echoing local generator.
   Use independent random values, at least 64 random bytes for the master secret as recommended in the compose comments. Do not print values or place them in command arguments.
3. Create `local-only.yaml` beside the downloaded file. The following is an original override using Compose `!override`; the observed Compose v5 supports this merge syntax.
   Keep frontend/backend/exporter flags consistent. This recipe disables registration and MCP; use the documented interactive administrator command for a local test identity.

   ```yaml
   x-local-flags: &local-flags
     PENPOT_FLAGS: disable-registration disable-email-verification enable-login-with-password enable-prepl-server disable-secure-session-cookies disable-telemetry disable-mcp
     PENPOT_PUBLIC_URI: http://localhost:19001
   networks:
     penpot:
       internal: true
     ingress: {}
   services:
     penpot-frontend:
       ports: !override ["127.0.0.1:19001:8080"]
       networks: [penpot, ingress]
       volumes:
         - ./offline-external.conf:/etc/nginx/overrides/location.d/external-locations.conf:ro
       environment:
         <<: *local-flags
     penpot-backend:
       environment:
         <<: *local-flags
         PENPOT_SECRET_KEY: ${PENPOT_SECRET_KEY:?required}
         PENPOT_DATABASE_PASSWORD: ${PENPOT_DB_PASSWORD:?required}
         PENPOT_TELEMETRY_ENABLED: "false"
     penpot-exporter:
       environment:
         <<: *local-flags
         PENPOT_SECRET_KEY: ${PENPOT_SECRET_KEY:?required}
     penpot-admin-console:
       environment:
         PENPOT_PUBLIC_URI: http://localhost:19001
         PENPOT_SECRET_KEY: ${PENPOT_SECRET_KEY:?required}
         PENPOT_DATABASE_PASSWORD: ${PENPOT_DB_PASSWORD:?required}
     penpot-postgres:
       environment:
         POSTGRES_PASSWORD: ${PENPOT_DB_PASSWORD:?required}
     penpot-mailpit:
       ports: !override []
   ```

   Keep backend dependencies on the internal network. The frontend also needs the ingress bridge: Docker Desktop did not expose an effective host port when it had only the internal network.
   This does not establish an OS-wide egress sandbox. The browser separately allows only loopback hosts; only the frontend is published, on loopback.
   Create `offline-external.conf` beside the override to explicitly disable external template and Google-font proxies:

   ```nginx
   location ^~ /github/penpot-files/ { return 503; }
   location ^~ /internal/gfonts/ { return 503; }
   ```

   Without this override, the isolated frontend failed startup resolving `raw.githubusercontent.com`. External templates and fonts remain unavailable; do not replace them with fake successful responses.
   Image pulls still use the Docker daemon's network.
   Local HTTP uses disabled secure cookies only for this isolated test. Do not copy these flags to a remotely accessible deployment.
4. From the proof directory, validate without printing expanded secrets, then start only this unique project if authorized:

   ```bash
   docker --context desktop-linux compose -p deepmode-design-proof \
     -f docker-compose.yaml -f local-only.yaml config --quiet
   docker --context desktop-linux compose -p deepmode-design-proof \
     -f docker-compose.yaml -f local-only.yaml up -d
   docker --context desktop-linux compose -p deepmode-design-proof \
     -f docker-compose.yaml -f local-only.yaml ps
   ```

   Inspect effective published ports and container health. Retain redacted startup errors rather than calling the service ready from `up` alone.
   Do not capture full `compose config` or container environment output; both can contain expanded secrets.
5. If authorized, create a dedicated local test identity through the documented interactive command; credentials belong in the protected local session, not transcripts:

   ```bash
   docker --context desktop-linux compose -p deepmode-design-proof \
     -f docker-compose.yaml -f local-only.yaml exec penpot-backend \
     python3 manage.py create-profile --skip-tutorial --skip-walkthrough
   ```

   For automation, send credentials only through protected stdin, never argv or logs. Use binary UTF-8 input with LF delimiters when invoking Linux container prompts from Windows.
   The pilot's initial CLI-created account rejected login. An `update-profile` call using binary stdin restored access; the exact initial failure cause was not isolated.

   Open `http://localhost:19001` in an isolated browser, sign in to that test identity, create a new file, and insert `workflow.svg` on its canvas.
   The dashboard's native-file Import dialog is not the same operation. Keep MCP disabled for this simple UI import proof.
6. When finished, stop only this project's containers with the same project/file arguments and `down`. Retain the project's volumes for review; do not run `down -v`, prune, or affect unrelated services.

Sources for the recipe: [official compose](https://raw.githubusercontent.com/penpot/penpot/main/docker/images/docker-compose.yaml), [Docker setup](https://help.penpot.app/technical-guide/getting-started/docker/), [Penpot configuration](https://help.penpot.app/technical-guide/configuration/), and [Compose merge rules](https://docs.docker.com/reference/compose-file/merge/).
The upstream compose is downloaded for execution, not vendored into this repository. Preserve its applicable notices if redistributing a modified copy.

## Exact runtime proof required

1. Run `design.py --bundle <verified-bundle> --out <new-directory>` from the E2E asset path. Retain stdout and `design.json`; failure exits nonzero. Run the bundle validator again to establish unchanged original hashes.
2. In an isolated real browser, open `index.html`, inspect all step images and full observations, play the finalized video, and open `workflow.svg`. Capture readable step images and an overview of the actual SVG rendering.
3. Follow a step's full-observation link and screenshot link. Copy/move the complete exported folder and repeat offline; assets are relative and content-addressed. Do not upload it to a public design service without approval.
4. In a working, authorized Penpot instance, insert the SVG on the canvas. Retain an import screenshot and the layer tree, edit a text or rectangle in a duplicate, then export SVG and the native `.penpot` file if supported. Record which primitive types and hyperlinks survived.
5. If claiming a prototype, create at least two boards and an actual interaction connection in a separately labeled prospective-design page, then record View mode exercising that connection. Importing a workflow diagram does not satisfy this criterion.
6. Retain import or startup failures, absent permissions, and unsupported SVG primitives. Report the strongest demonstrated claim only: generated, rendered, imported, editable, round-tripped, or prototyped.
7. Run `python -m unittest discover -s plugins/deepmodebot/skills/deepmodebot/assets/e2e -p test_design.py` for text-injection and failed-capture rendering boundaries. These helper tests do not establish browser rendering or Penpot compatibility.

Retain approved public-safe observations in the [repository evidence inventory](../evidence/ecosystem-pilot-2026-11-13/README.md). A successful SVG render or service startup is not proof of native import, editable layers, or export round-trip.

## Observed local Penpot pilot

The [retained native evidence](../evidence/ecosystem-pilot-2026-11-13/penpot/provenance.json) comes from Penpot 2.18 on an isolated Docker Desktop project, not a hosted design account.
The generated six-step SVG imported into a new canvas. A native rectangle's width changed from 984 to 1000; the downloaded `.penpot` archive contains width `1000.0000000000001` for that shape.
The archive contains native groups/rectangles and raw SVG nodes. Its text remained raw SVG, not native rich text. Screenshot content remains raster. No interaction prototype or native-file re-import was exercised.

The native agent-browser download reported cancellation. A separate owned Chrome session downloaded the actual archive and SVG; no production profile or external upload was used.
Raw SVG export retained twelve local-server image references. A separately named portable derivative embeds the corresponding unchanged PNG bytes from the native archive.
That derivative rendered with all twelve embedded images in a real browser. The raw output is retained unchanged so portability is not falsely attributed to Penpot.
Before/after screenshots and a finalized 101.233-second supplementary edit video accompany the archive. This video is separate from the invoice recording/replay's three-person visual panel.
