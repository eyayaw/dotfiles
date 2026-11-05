# Snippets

One TOML file feeds both macOS Text Replacements (synced to the iPhone by iCloud, expanding in
every native text field) and Alfred snippet collections (multi-line, `{cursor}`, `{date}`,
`{clipboard}`). Edit `snippets.toml`, then:

```sh
uv run snippets/build.py
```

Each table is a collection. Its `macos` and `alfred` keys hold the prefix typed before a keyword
in that tool, so `site` expands as `qqsite` on the iPhone and `..site` through Alfred; a missing key
keeps the collection out of that tool. A collection bound to macOS cannot hold an Alfred
placeholder. Private entries live in the gitignored `private.toml` with the same schema and merge
into the same collections.

The build rewrites the Alfred collections the TOML names inside Alfred's live preferences folder,
and Alfred picks them up by itself. For macOS it writes `build/Text Replacements.plist`; drag that
file onto `System Settings › Keyboard › Text Replacements`, the only import path macOS supports.
