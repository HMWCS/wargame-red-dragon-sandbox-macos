# Wargame: Red Dragon Sandbox Patcher for macOS

An unofficial macOS Apple Silicon patcher for selected community Sandbox Mod features in the Steam version of Wargame: Red Dragon.

This is a separate macOS implementation inspired by the community Sandbox Mod Installer. It is not an official macOS version of that project, and it does not install the full Windows Sandbox Mod package.

## What it changes

The normal `on` command enables five changes:

- 10v10 maps in normal lobbies.
- 900 activation points for every deck.
- 9 slots in each deck category by default.
- Prototype units are treated as regular units.
- FOBs have near-unlimited supplies.

Optional:

- `--max-packs-99` also unlocks all available unit veterancy options.

The changes are local to your installed game files.

## Install and use

Requirements: an Apple Silicon Mac (M1/M2/M3/M4), the Steam version of Wargame: Red Dragon, and an internet connection for the first setup.

1. Open **Terminal** (`Applications` → `Utilities` → `Terminal`) and install [`uv`](https://docs.astral.sh/uv/getting-started/installation/).

   If you already have Homebrew, use:

   ```bash
   brew install uv
   ```

   Otherwise, use the official installer:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   `uv` manages the required Python version and project dependencies, so you normally do not need to install Python separately. Close and reopen Terminal after installation.

2. On this GitHub page, click **Code** → **Download ZIP**, then unzip the downloaded file.

3. In Terminal, type `cd ` (including the trailing space), drag the unzipped project folder into the Terminal window, and press **Return**.

4. Close Wargame: Red Dragon, then run:

   ```bash
   uv run wrd-sandbox on
   ```

   The first run may take a moment while `uv` prepares the environment.

Optional: enable the all-veterancy change too:

```bash
uv run wrd-sandbox on --max-packs-99
```

Check the current state:

```bash
uv run wrd-sandbox status
```

Restore the original game file:

```bash
uv run wrd-sandbox off
```

`off` restores the original file saved before patching and removes this tool's managed backup.

## If the game is not found

The default Steam location is:

```text
~/Library/Application Support/Steam/steamapps/common/Wargame Red Dragon
```

If your game is elsewhere, add `--game-root "/path/to/Wargame Red Dragon"` to `on`, `status`, and `off`.

If Terminal says `uv: command not found`, close and reopen Terminal and try again.

## Notes

- This project has been tested on Apple Silicon macOS only.
- Close the game before changing files.
- This project does not include or distribute any game files.
- It is unofficial and is not affiliated with Eugen Systems, Focus Entertainment, or Valve.

## Acknowledgments

This project was inspired by the community [Sandbox Mod Installer](https://github.com/TheWRDNoob/Sandbox-Mod-Installer). The original installer is a separate project and is not an official component of this repository; see its [license](https://github.com/Noob-Development/Sandbox-Mod-Installer/blob/main/license) for its own terms.

This project declares the following AGPL-licensed upstream packages, both maintained by [ev1313](https://github.com/ev1313):

- [`wgrd-cons-parsers`](https://github.com/ev1313/wgrd-cons-parsers) — used to read and write Wargame data.
- [`wgrd-cons-tools`](https://github.com/ev1313/wgrd-cons-tools) — declared as a project dependency.

These are separate upstream projects; this repository is an independent macOS implementation.

## License

This project is licensed under the GNU Affero General Public License v3.0 or later. See [`LICENSE`](LICENSE).
