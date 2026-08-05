# Mirror CLI

Mirror CLI provides the commands for creating and inspecting projects.

## Commands

- `mirror startproject <name>` — create a project scaffold.
- `mirror startapp <name>` — add an application package inside `apps/`.
- `mirror doctor` — validate the current scaffold.
- `mirror list-capabilities` — inspect discovered capabilities.
- `mirror list-providers` — inspect discovered providers.
- `mirror status` — print a basic runtime status summary.
- `mirror worker` — start the local worker backend for alpha development.
- `mirror run` — experimental pipeline command in the alpha snapshot.

The CLI package also ships the scaffolding templates used by the project
initializer commands.
