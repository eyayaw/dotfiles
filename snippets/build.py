"""Build macOS text replacements and Alfred snippet collections from snippets.toml.

Reads snippets.toml and, when present, private.toml next to this file. Both share one schema and
merge, and a keyword defined in both is an error. Writes build/Text Replacements.plist for dragging
onto System Settings > Keyboard > Text Replacements, the only import path macOS supports, and
replaces every Alfred collection the TOML names inside Alfred's live preferences folder, which
Alfred reloads on its own. Collections the TOML does not name stay untouched.

Schema: every top-level table is a collection. A `macos` or `alfred` key sends it to that tool,
and the value is the prefix typed before each keyword there. The macOS shortcut is the prefix and
keyword joined, and a macOS-bound snippet cannot hold an Alfred placeholder such as {cursor}.

    [personal]
    alfred = ".."
    macos = "qq"
    [personal.snippets]
    keyword = "text"
"""

import json
import plistlib
import shutil
import sys
import tomllib
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = ("snippets.toml", "private.toml")
TARGETS = ("macos", "alfred")
ALFRED_PREFS = Path.home() / "Library/Application Support/Alfred/prefs.json"
# Fixed namespace, so a keyword keeps its uid across runs and Alfred updates the snippet in place.
UID_NAMESPACE = uuid.UUID("6f1c2a2e-5f1d-4b7a-9d3e-2c8e7a0b4f11")


def merge(collection: dict, body: dict, where: str) -> None:
    for target in TARGETS:
        if target not in body:
            continue
        prefix = body[target]
        if not isinstance(prefix, str):
            sys.exit(f"{where}: {target} must be a prefix string")
        if collection.get(target, prefix) != prefix:
            sys.exit(f"{where}: {target} prefix differs from the other file")
        collection[target] = prefix
    new = body.get("snippets", {})
    duplicates = collection["snippets"].keys() & new.keys()
    if duplicates:
        sys.exit(f"{where}: keyword defined twice: {', '.join(sorted(duplicates))}")
    for keyword, text in new.items():
        if not isinstance(text, str) or not text:
            sys.exit(f"{where}: {keyword!r} must be a non-empty string")
        if "/" in keyword:
            sys.exit(f"{where}: {keyword!r} must not contain '/' (it names a file)")
        # Alfred fires on the keyword's last character, so `..x` would expand while typing
        # data.table's `..xcols`, and single letters are what follows `..` in R.
        if len(keyword) < 2:
            sys.exit(f"{where}: {keyword!r} is a single character and would fire early")
    collection["snippets"].update(new)


def load() -> dict[str, dict]:
    collections: dict[str, dict] = {}
    for name in SOURCES:
        path = HERE / name
        if not path.exists():
            continue
        for title, body in tomllib.loads(path.read_text()).items():
            collection = collections.setdefault(title, {"snippets": {}})
            merge(collection, body, f"{name} [{title}]")
    for title, collection in collections.items():
        if not any(target in collection for target in TARGETS):
            sys.exit(f"[{title}] names no target: add a macos or alfred prefix")
        if "macos" in collection:
            for keyword, text in collection["snippets"].items():
                if "{" in text:
                    sys.exit(f"[{title}] {keyword!r} holds a placeholder, which macOS pastes as is")
    return collections


def alfred_snippets_dir() -> Path:
    if not ALFRED_PREFS.exists():
        sys.exit(f"{ALFRED_PREFS} not found: install Alfred and launch it once")
    # prefs.json "current" is the preferences bundle Alfred uses, inside its sync folder if set.
    return Path(json.loads(ALFRED_PREFS.read_text())["current"]) / "snippets"


def entries(collections: dict[str, dict], target: str) -> dict[str, str]:
    """Map each full trigger (prefix + keyword) for target to its text; a repeat is an error."""
    triggers: dict[str, str] = {}
    for title, collection in collections.items():
        if target not in collection:
            continue
        for keyword, text in collection["snippets"].items():
            trigger = collection[target] + keyword
            if trigger in triggers:
                sys.exit(f"[{title}] {keyword!r}: {target} trigger {trigger!r} is defined twice")
            triggers[trigger] = text
    return triggers


def write_macos(entries: dict[str, str], out: Path) -> None:
    # Format of the file System Settings exports by drag, checked 2026-11-04:
    # https://support.apple.com/guide/mac-help/mchl2a7bd795/mac
    out.parent.mkdir(exist_ok=True)
    with out.open("wb") as f:
        items = [{"phrase": phrase, "shortcut": shortcut} for shortcut, phrase in entries.items()]
        plistlib.dump(items, f)


def write_alfred(collections: dict[str, dict], snippets_dir: Path) -> None:
    # The layout Alfred writes itself: <collection>/info.plist and one "<name> [<UID>].json" each.
    for title, collection in collections.items():
        if "alfred" not in collection:
            continue
        folder = snippets_dir / title
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)
        with (folder / "info.plist").open("wb") as f:
            affix = {"snippetkeywordprefix": collection["alfred"], "snippetkeywordsuffix": ""}
            plistlib.dump(affix, f)
        for keyword, text in collection["snippets"].items():
            uid = str(uuid.uuid5(UID_NAMESPACE, f"{title}/{keyword}")).upper()
            snippet = {"snippet": text, "uid": uid, "name": keyword, "keyword": keyword}
            (folder / f"{keyword} [{uid}].json").write_text(
                json.dumps({"alfredsnippet": snippet}, ensure_ascii=False, indent=2) + "\n"
            )


def main() -> None:
    collections = load()
    entries(collections, "alfred")
    macos = entries(collections, "macos")
    plist = HERE / "build" / "Text Replacements.plist"
    write_macos(macos, plist)
    print(f"{len(macos)} text replacements -> {plist.relative_to(HERE)}")
    print("  drag it into System Settings > Keyboard > Text Replacements")
    write_alfred(collections, alfred_snippets_dir())
    for title, collection in collections.items():
        if "alfred" in collection:
            print(f"{len(collection['snippets'])} snippets -> Alfred collection {title!r}")


if __name__ == "__main__":
    main()
