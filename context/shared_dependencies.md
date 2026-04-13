# Shared Dependencies

Cross-file contract manifest. Populated by the Architect Agent during pipeline setup and updated after each Coder task completes. Every Coder invocation receives this file as context.

---

## Shared Types & Models

<!-- Pydantic models, TypedDicts, dataclasses, and Protocol classes used across more than one file. -->
<!-- Format: class name, source module, field names and types. -->

_Populated by Architect Agent (AGT-02)._

---

## Exported Function Signatures

<!-- Public functions exported from one module and imported by another. -->
<!-- Format: function name, source module, parameter types, return type. -->

_Populated by Architect Agent (AGT-02) and updated after each Coder task._

---

## API Contracts

<!-- REST endpoint definitions: method, path, request body schema, response schema, status codes. -->

_Populated by Architect Agent (AGT-02)._

---

## Data Schemas

<!-- Database models, JSON schemas, and any persistent data structures. -->
<!-- Include field names, types, constraints, and relationships. -->

_Populated by Architect Agent (AGT-02)._

---

## Environment Variables

<!-- All env vars the application reads. Name, type, required/optional, description. -->
<!-- These are loaded via config.py — never accessed directly with os.environ outside that module. -->

| Variable | Type | Required | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | string | yes | Anthropic API key for all Claude calls |
| `E2B_API_KEY` | string | yes | e2b.dev sandbox execution |
| `GITHUB_PAT` | string | yes | GitHub personal access token (repo scope only) |

_Additional variables added by Architect Agent (AGT-02) based on project brief._

---

## File Registry

<!-- Tracks every generated file: path, owning module, and its exported public interface. -->
<!-- Updated after each Coder task completes (Ralph Loop step 5). -->
<!-- Coder reads this to get dependency signatures without receiving full source code. -->

| File Path | Module | Exported Interface |
|---|---|---|

_Populated progressively as Coder tasks complete._
