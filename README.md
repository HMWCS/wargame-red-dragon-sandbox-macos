# wrd-macos-sandbox

macOS-native CLI patcher for six Sandbox Mod features in Steam Wargame: Red Dragon.

`uv run wrd-sandbox on` enables the baseline sandbox patches.
Use `uv run wrd-sandbox on --max-packs-99` to add the optional `99 Deck Cards per Unit` patch.
`uv run wrd-sandbox off` restores the original file and deletes the managed backup.

## Setup

```bash
uv sync
```

For development and tests:

```bash
uv sync --dev
```

## Usage

```bash
uv run wrd-sandbox status
uv run wrd-sandbox on
uv run wrd-sandbox on --max-packs-99
uv run wrd-sandbox off
```

`on`/`off` are idempotent. Repeating the same command should not change the result.

Optional:

```bash
uv run wrd-sandbox status --game-root "/absolute/path/to/Wargame Red Dragon"
```
