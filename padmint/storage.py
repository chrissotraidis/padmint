"""What PadMint keeps on this computer, and removing what it no longer needs.

Everything lives in PadMint's own folder (~/.padmint). Game downloads are kept per
release (games/<game>-<tag>); the one for each game's latest release, or its newest
when the latest is unknown, is always kept. Tools that this PadMint's tools.lock.json
no longer names, downloaded apps and caches, unfinished downloads and older installed
PadMint versions can all be fetched again, so they may go. Installed copies, game files
and saves are never in this folder.
"""
import os
from pathlib import Path
import shutil
import threading
import time

from . import tools, update
from .manifest import catalog


def size(path):
    """Bytes the folder takes on disk, without following links."""
    total, stack = 0, [tools._long(path)]
    while stack:
        try:
            with os.scandir(stack.pop()) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        else:
                            info = entry.stat(follow_symlinks=False)
                            total += getattr(info, "st_blocks", 0) * 512 or info.st_size
                    except OSError:
                        pass
        except OSError:
            pass
    return total


def game_of(folder_name):
    """The catalog game a games/ folder belongs to, by its longest matching id."""
    matches = [game for game in catalog() if folder_name.startswith(game + "-")]
    return max(matches, key=len) if matches else None


def items(latest=None):
    """Everything in PadMint's folder worth listing, with whether it may be removed."""
    latest = latest or {}
    home = tools.home()
    found = []
    games = home / "games"
    folders = sorted((p for p in games.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime) \
        if games.is_dir() else []
    owner = {path.name: game_of(path.name) for path in folders}
    newest = {}
    for path in folders:
        game = owner[path.name]
        if game and not path.name.endswith(".partial"):
            newest[game] = path.name
    for path in folders:
        game = owner[path.name]
        version = path.name[len(game) + 1:] if game else path.name
        partial = path.name.endswith(".partial")
        keep = not partial and game is not None and (
            version == latest.get(game) if latest.get(game) in
            {p.name[len(game) + 1:] for p in folders if owner[p.name] == game}
            else newest.get(game) == path.name)
        found.append({"id": "games/" + path.name, "kind": "game", "game": game,
                      "version": version.removesuffix(".partial"),
                      "reason": "partial" if partial else "current" if keep else "old", "removable": not keep})
    lock = tools.lock()
    host = _host()
    wanted = {f"{name}-{tools.version(tool, host)}" for name, tool in lock.items()}
    root = home / "tools"
    for path in sorted(root.iterdir()) if root.is_dir() else []:
        if path.is_dir():
            used = path.name in wanted
            found.append({"id": "tools/" + path.name, "kind": "tool", "name": path.name,
                          "reason": "current" if used else "unused", "removable": not used})
    for sub in ("apps", "cache"):
        for path in sorted((home / sub).iterdir()) if (home / sub).is_dir() else []:
            if path.is_dir():
                found.append({"id": f"{sub}/{path.name}", "kind": sub, "game": path.name if path.name in catalog() else None,
                              "name": path.name, "reason": "cache", "removable": True})
    current = update.installed()
    for path in sorted(update.folder().iterdir()) if update.folder().is_dir() else []:
        if path.is_dir():
            kept = bool(current) and path.name == current[0]
            found.append({"id": "padmint/" + path.name, "kind": "padmint", "version": path.name,
                          "reason": "current" if kept else "old", "removable": not kept})
    return found


def _host():
    from . import cli
    return cli.host_id()


STATE = {"state": "idle"}


def measure(latest=None):
    """Measure in the background (a big folder takes a while); STATE holds the result."""
    if STATE.get("state") == "measuring":
        return
    STATE.clear()
    STATE.update(state="measuring")

    def work():
        try:
            listed = items(latest)
            for item in listed:
                item["size"] = size(tools.home() / item["id"])
            usage = shutil.disk_usage(tools.home() if tools.home().exists() else tools.home().parent)
            STATE.update(state="ready", items=listed, total=sum(i["size"] for i in listed),
                         free=usage.free, folder=str(tools.home()), when=int(time.time()))
        except Exception as error:
            STATE.update(state="failed", error=str(error))
    threading.Thread(target=work, daemon=True).start()


def remove(ids, latest=None):
    """Remove the listed folders that may be removed; returns the bytes freed."""
    from . import cli
    allowed = {item["id"] for item in items(latest) if item["removable"]}
    home = tools.home().resolve()
    freed = 0
    for item_id in ids:
        if item_id not in allowed:
            raise ValueError(f"PadMint keeps {item_id}")
        path = (home / item_id).resolve()
        if home not in path.parents:
            raise ValueError(f"{item_id} is outside PadMint's folder")
        freed += size(path)
        # A game's download holds Git's read-only files, and the Android NDK's paths are longer
        # than Windows allows: a plain rmtree stops at either, with the folder half removed.
        cli._remove_tree(Path(tools._long(path)))
    return freed

