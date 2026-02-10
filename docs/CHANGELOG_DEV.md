# CHANGELOG_DEV (WIP)

Kurzliste von Änderungen im Branch `dev`, die noch nicht als Add-on Release getaggt sind.

- Stable Releases: `CHANGELOG.md` (Tags `copilot_core-vX.Y.Z`).

## Unreleased (dev)

### In Arbeit
- Core Add-on: Neues `/api/v1/tag-system` Blueprint liefert die kanonische Tag-Registry (mehrsprachig) und stellt ein abgesichertes Assignments-Endpoint bereit, damit die HA-Integration das Label-Mapping testen kann.
- Core Add-on: Persistenter Tag-Assignment-Store (JSON unter `/data/tag_assignments.json`) inklusive Filter-GET/POST-Upsert und Validierung der erlaubten Subject-Kinds.
