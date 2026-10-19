"""The PadMint window: a page in the player's web browser, served by this computer.

It serves only on 127.0.0.1 with a random token, uses the Python standard library,
and makes copies by running "python -m padmint make", so the window can never do more
than the terminal. Nothing is uploaded.
"""
import concurrent.futures
import io
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import webbrowser

from . import __version__, cli, installed, storage, tools, update
from .manifest import catalog
from .say import LANGUAGES, MESSAGES, language, localized, phrase

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "art"


def strings(lang):
    return {key[2:]: value.get(lang, value["en"]) for key, value in MESSAGES.items() if key.startswith("w_")}


def input_formats(inputs):
    """An exhaustive format list only when every input alternative supplies one."""
    if any(not item.get("formats") for item in inputs):
        return []
    return sorted({name for item in inputs for name in item["formats"]})


def setup_level(entry, platforms):
    """How much a player sets up before this game, for its card: "easy" when a ready-to-play
    app exists, otherwise on a Mac "xcode" (Xcode only) or "brew" (Xcode and Homebrew
    packages, the catalog's before_build line). None elsewhere."""
    if entry.get("ready_to_play"):
        return "easy"
    if not cli.host_id().startswith("macos") or not set(platforms) & {"ios", "macos"}:
        return None
    return "brew" if entry.get("before_build") else "xcode"


def player_data(lang):
    """Everything the page shows before a build: games, devices and game files found."""
    folder = cli.player_folder()
    games = []
    for game, name, platforms in cli.player_games():
        entry = catalog()[game]
        needs_file = entry.get("player_game_file", "build") != "in-app"
        games.append({"id": game, "name": name, "needs_file": needs_file,
                      "about": entry.get("game") or (entry.get("manifest") or {}).get("game", ""),
                      "formats": [f.upper() for f in input_formats([item for item in (entry.get("manifest") or {}).get("inputs", [])
                                                                 if item.get("when", "build") == "build"])],
                      "ids": entry.get("game_ids") or [],
                      "platforms": [{"id": p, "label": cli.platform_label(p, lang),
                                     "short": phrase(f"w_short_{p}", lang) if f"w_short_{p}" in MESSAGES else p}
                                    for p in platforms],
                      "held": cli.unavailable_devices(entry, platforms, lang),
                      "files": [],  # read on demand (/api/files): opening the window never waits on Downloads
                      "setup": setup_level(entry, platforms),
                      "ready": ({"text": localized(entry["ready_to_play"], "text", lang),
                                 "url": entry["ready_to_play"]["url"],
                                 "platforms": entry["ready_to_play"].get("platforms", platforms)}
                                if entry.get("ready_to_play") else None),
                      "page": entry.get("player_help") or entry["repo_url"], "issues": entry["repo_url"] + "/issues"})
    apps = [] if cli.on_android() else [
        {"id": app, "name": name, "about": catalog()[app].get("game", ""), "plays_on": catalog()[app].get("plays_on", []),
         "intro": phrase("download_intro", lang, name=name).strip(),
         "steps": localized(catalog()[app]["download"], "steps", lang),
         "guide": catalog()[app].get("player_help") or catalog()[app]["repo_url"]}
        for app, name in cli.downloads()]
    waiting = [{"id": game, "name": name, "about": catalog()[game]["game"], "status": catalog()[game]["later"].get("status"),
                "text": localized(catalog()[game]["later"], "text", lang), "plays_on": catalog()[game].get("plays_on", []),
               "link": catalog()[game].get("player_help") or catalog()[game]["repo_url"]}
               for game, name in cli.later()]
    # Games PadMint builds, but not here: listed with the reason, never silently left out.
    waiting += [{"id": game, "name": name,
                 "about": catalog()[game].get("game") or (catalog()[game].get("manifest") or {}).get("game", ""),
                 "text": (localized(catalog()[game]["off_mac"], "text", lang) if catalog()[game].get("off_mac")
                          else phrase("w_needs_mac" if "ios" in targets else "w_needs_windows", lang, name=name)),
                 "tag": (None if catalog()[game].get("off_mac")
                         else phrase("w_needs_mac_tag", lang) if "ios" in targets else None),
                 "plays_on": ["iphone", "ipad"] if "ios" in targets else [],
                 "link": ((catalog()[game].get("off_mac") or {}).get("url")
                          or catalog()[game].get("player_help") or catalog()[game]["repo_url"])}
                for game, name, targets in cli.elsewhere()]
    return {"lang": lang, "version": __version__, "host": cli.host_id(), "folder": str(folder),
            "saved_in": phrase("saved_in", lang, folder=folder), "games": games, "downloads": apps, "later": waiting,
            "text": strings(lang), "picker": not cli.on_android(), "reveal": not cli.on_android(),
            "art": sorted(path.stem for path in ART.glob("*.png")), "library": library(),
            "self_update": bool(update.platform()), "installed": installed.snapshot()}


def library():
    """The copies this PadMint has finished, newest first: one entry per game and device,
    read from the build records PadMint keeps next to each downloaded release and remembered
    in library.json, so removing an old download in Storage doesn't forget the copy."""
    saved = tools.tools_root().parent / "library.json"
    try:
        found = {(item["id"], item["platform"]): item for item in json.loads(saved.read_text())}
    except (OSError, ValueError, KeyError, TypeError):
        found = {}
    before = dict(found)
    for path in (tools.tools_root().parent / "games").glob("*/build/padmint/*/runs/*/record.json"):
        try:
            record = json.loads(path.read_text())
            when = path.stat().st_mtime
        except (OSError, ValueError):
            continue
        game, target = record.get("game"), record.get("target")
        folder = path.parents[5].name  # games/<game>-<release tag>
        if (record.get("status") != "completed" or game not in catalog() or not target
                or not folder.startswith(game + "-") or folder.endswith(".partial")):
            continue
        key = (game, target)
        if key not in found or when > found[key]["when"] or (
                when == found[key]["when"] and found[key]["version"] != folder[len(game) + 1:]):
            found[key] = {"id": game, "platform": target, "version": folder[len(game) + 1:], "when": int(when)}
    found = {key: item for key, item in found.items() if item.get("id") in catalog()}
    if found != before:
        try:
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_text(json.dumps(list(found.values())))
        except OSError:
            pass
    return sorted(found.values(), key=lambda item: -item["when"])


VERSIONS = {"done": False, "padmint": None, "games": {}}


def release_tag(repo_url):
    """A repository's latest release tag, from where /releases/latest lands."""
    with tools.open_url(repo_url.removesuffix(".git").rstrip("/") + "/releases/latest") as response:
        landed = response.geturl()
    return urllib.parse.unquote(landed.rsplit("/releases/tag/", 1)[1].split("?")[0].strip("/")) \
        if "/releases/tag/" in landed else None


def check_versions():
    """Every game's latest release and PadMint's own, read once per window in the background.
    For games PadMint builds this also keeps the release recipe, so plans show at once."""
    offered = {game for game, _name, _targets in cli.player_games()}

    def one(game):
        entry = catalog()[game]
        try:
            if game in offered:
                release = cli.latest_release(entry["repo_url"])
                VERSIONS["games"][game] = release[0]
                if game not in RECIPES:
                    recipe, source = cli.published_recipe(game, release=release)
                    if not source.startswith("PadMint's built-in copy"):
                        RECIPES[game] = recipe
            else:
                VERSIONS["games"][game] = release_tag(entry["repo_url"])
        except Exception:  # offline: the page simply shows no update news
            pass

    def padmint():
        try:
            found = update.latest()
            VERSIONS["padmint"] = "v" + found if found else None
        except Exception:
            pass

    with concurrent.futures.ThreadPoolExecutor(6) as pool:
        pool.submit(padmint)
        list(pool.map(one, [game for game, entry in catalog().items() if entry.get("repo_url")]))
    VERSIONS["done"] = True


def plan(game, platform_name, lang, disc=None):
    """What a build will do on this computer, before it starts: what it downloads and from
    where, how big, what the player installs first, and where the copy goes. Read from the
    recipe the game's latest release publishes (as doctor does), so the tools and the programs
    to install first match what the build will use; sizes are close, not exact."""
    entry = catalog()[game]
    manifest = release_recipe(game) or entry.get("manifest") or {}
    target = (manifest.get("targets") or {}).get(platform_name) or {}
    host, table = cli.host_id(), tools.lock()
    any_host = bool(target.get("ios_module"))
    items = []
    for name in tools._with_companions([n for n in target.get("tools", []) if n in table], host, table, any_host):
        download = tools.host_entry(table[name], host, any_host)
        if download:
            items.append({"name": name, "version": tools.version(table[name], host), "size": download.get("size"),
                          "source": urlparse(download["url"]).hostname, "here": tools.installed(name, host)})
    needs = cli.requirement_checks(manifest, platform_name, disc, lang)
    before = cli.before_build(game)
    # One Homebrew line for everything still missing: the game's README packages that aren't
    # here, and every missing program whose note says "brew install ...".
    brew = [package["name"] for package in (before or {}).get("packages", []) if not package["ok"]]
    for need in needs:
        match = None if need["ok"] else re.match(r"brew install ((?:[\w@.+-]+ ?)+)", need["note"])
        if match:
            need["brew"] = True
            brew += match.group(1).split()
    brew = list(dict.fromkeys(brew))
    mac_setup = None
    if before or brew:
        mac_setup = {"homebrew": bool(shutil.which("brew")),
                     "brew_line": "brew install " + " ".join(brew) if brew else "",
                     "other": [line for line in (before or {}).get("commands", []) if not line.startswith("brew install ")],
                     "packages": (before or {}).get("packages", [])}
    name = manifest.get("name") or entry.get("name", game)
    key = f"w_output_{platform_name}"
    # The same steps the finished page shows, so nobody meets the phone part for the first time
    # after a build of an hour or more.
    preview = Path(cli.player_folder()) / phrase("w_the_ipa" if platform_name == "ios" else "w_your_copy", lang)
    steps, note, _guide = cli.next_step_text({"id": game, **entry}, platform_name, preview, lang)
    install = {"steps": steps, "note": note} if steps else None
    return {"repo": entry["repo_url"], "tools": items, "tools_folder": str(tools.tools_root()),
            "app": bool(target.get("published_app")), "space_gb": cli.player_free_space(entry, platform_name),
            "folder": str(cli.player_folder()), "needs": needs, "mac_setup": mac_setup, "install": install,
            "output": phrase(key, lang, name=name) if key in MESSAGES else "",
            "inputs": [item for item in manifest.get("inputs", []) if item.get("when", "build") == "build"]}


RECIPES = {}


def release_recipe(game):
    """The game's latest release recipe, fetched once per PadMint window; None when it can't
    be read (the plan then falls back to the catalog's copy). Only a recipe read from the
    release is kept: after a failed read, the next plan tries the release again."""
    if game not in RECIPES:
        try:
            recipe, source = cli.published_recipe(game)
        except Exception:  # an offline or too-old PadMint still shows the catalog's plan
            return None
        if source.startswith("PadMint's built-in copy"):
            return recipe
        RECIPES[game] = recipe
    return RECIPES[game]


PHASES = ("release", "source", "tools", "app", "build", "save")


def phases(events, code):
    """The build's phases from make's events file, as the page shows them."""
    found, tool_list, stage = {}, {}, None
    for line in events:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        kind = event.pop("phase", None)
        if kind in PHASES:
            found.setdefault(kind, {}).update(event)
        elif kind == "tool" and event.get("name"):
            tool_list.setdefault(event["name"], {}).update(event)
        elif kind == "stage":
            stage = event
    if code is not None and code != 0:
        for value in found.values():
            if value.get("state") == "running":
                value["state"] = "cancelled" if code == 130 else "failed"
    result = [dict(found[name], id=name) for name in PHASES if name in found]
    return result, list(tool_list.values()), stage


def pick_file(title, folder):
    """The system's own Open dialog: the chosen path, None if cancelled, False if there is none."""
    env = dict(os.environ, PADMINT_PICK_TITLE=title, PADMINT_PICK_FOLDER=str(folder))
    if sys.platform == "darwin":
        # "activate" first, so the dialog comes to the front instead of opening behind the browser.
        argv = ["osascript", "-e", "activate", "-e", 'POSIX path of (choose file with prompt (system attribute '
                '"PADMINT_PICK_TITLE") default location (POSIX file (system attribute "PADMINT_PICK_FOLDER")))']
    elif os.name == "nt":
        argv = ["powershell", "-NoProfile", "-STA", "-Command",
                "Add-Type -AssemblyName System.Windows.Forms;"
                "$f = New-Object System.Windows.Forms.Form -Property @{TopMost=$true};"
                "$d = New-Object System.Windows.Forms.OpenFileDialog;"
                "$d.Title = $env:PADMINT_PICK_TITLE; $d.InitialDirectory = $env:PADMINT_PICK_FOLDER;"
                "if ($d.ShowDialog($f) -eq 'OK') { [Console]::OutputEncoding = [Text.Encoding]::UTF8;"
                " [Console]::Write($d.FileName) }"]
    elif shutil.which("zenity"):
        argv = ["zenity", "--file-selection", "--title", title, "--filename", str(folder) + os.sep]
    elif shutil.which("kdialog"):
        argv = ["kdialog", "--getopenfilename", str(folder)]
    else:
        return False
    try:
        result = subprocess.run(argv, capture_output=True, env=env)
    except OSError:
        return False
    path = result.stdout.decode("utf-8", "replace").strip()
    return path if result.returncode == 0 and path else None


def check_file(game, path, lang):
    """None when the file can be used for game, else why not, in the player's words."""
    disc = cli.dropped_path(path)
    if not disc.is_file():
        return phrase("no_file", lang, path=disc)
    problem = cli.file_problem(disc)
    if problem:
        return problem
    # A player may pick the game's app (an APK or IPA) or a ZIP instead of the game file.
    manifest = release_recipe(game) or catalog()[game].get("manifest") or {}
    inputs = [item for item in manifest.get("inputs", []) if item.get("when", "build") == "build"]
    formats = input_formats(inputs)
    if formats and disc.suffix.lower().lstrip(".") not in formats:
        return phrase("w_not_game_file", lang, file=disc.name, name=manifest.get("name", game),
                      formats=", ".join(name.upper() for name in formats))
    try:
        cli.game_file.check_file_hash(manifest, disc)
    except (OSError, ValueError) as error:
        return str(error)
    # Installers and other non-disc inputs must not trigger a disc-tool download.
    if inputs and not any(item.get("type") in cli.game_file.DISC_TYPES or item.get("type") == "n64-rom"
                          for item in inputs):
        return None
    found = cli.game_from_file(disc, cli.player_games(), io.StringIO())
    if found and game not in found:
        return phrase("w_wrong_game", lang, name=manifest.get("name", game))
    return None


class Builds:
    """At most one copy made from the window at a time."""

    def __init__(self):
        self.lock = threading.Lock()
        self.process = self.log = self.job = self.events = None

    def start(self, game, platform_name, disc, lang):
        with self.lock:
            if self.process and self.process.poll() is None:
                raise ValueError("A build is already running")
            folder = Path(tempfile.mkdtemp(prefix="padmint-window-"))
            self.log = folder / "output.log"
            argv = [sys.executable, "-m", "padmint", "make", game, platform_name,
                    "--out", str(cli.player_folder()), "--result-file", str(folder / "result.json")]
            if disc:
                argv += ["--disc", str(disc)]
            self.events = folder / "events.jsonl"
            env = dict(os.environ, PADMINT_LANG=lang, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1",
                       PADMINT_EVENTS=str(self.events))
            # Its own process group, so Cancel (Ctrl-Break on Windows) reaches only the build.
            group = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt"
                     else {"start_new_session": True})
            with self.log.open("wb") as stream:
                self.process = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=stream,
                                                stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **group)
            self.job = {"game": game, "platform": platform_name, "lang": lang, "folder": folder,
                        "device": cli.platform_label(platform_name, lang),
                        "started": time.time(), "result": None}

    def status(self, lang=None):
        """The build as the page shows it, in lang (the page's language now; the build's
        own messages stay in the language it started in)."""
        if self.process is None:
            return {"state": "idle"}
        job, code = self.job, self.process.poll()
        lines = self.log.read_text("utf-8", "replace").splitlines() if self.log.exists() else []
        step = "tools"
        header = phrase("step_build", job["lang"], jobs=0).strip().split(":")[0]
        if any(line.startswith(header) for line in lines):
            step = "build"
        # The newest line that says something: skip the "still running" heartbeat.
        now = next((line.strip() for line in reversed(lines)
                    if line.strip() and "build_progress:" not in line), "")
        state = {None: "running", 0: "done", 130: "cancelled"}.get(code, "failed")
        if code is not None and "ended" not in job:
            job["ended"] = time.time()  # the clock stops when the build does
        events = (self.events.read_text("utf-8", "replace").splitlines()
                  if self.events and self.events.exists() else [])
        found, tool_list, stage = phases(events, code)
        reply = {"state": state, "step": "done" if code == 0 else step, "now": now[-200:], "game": job["game"],
                 "device": job.get("device", ""), "elapsed": int(job.get("ended", time.time()) - job["started"]),
                 "tail": lines[-60:],
                 "lines": len(lines), "exit_code": code, "phases": found, "tools": tool_list, "stage": stage}
        if code == 0:
            reply["result"] = self.result(lang)
        reply["device"] = cli.platform_label(job["platform"], lang) if lang else reply["device"]
        return reply

    def result(self, lang=None):
        job = self.job
        lang = lang or job["lang"]
        job.setdefault("results", {})
        if lang not in job["results"]:
            try:
                built = Path(json.loads((job["folder"] / "result.json").read_text())["file"])
            except (OSError, ValueError, KeyError):
                built = None
            steps, note, guide = cli.next_step_text(catalog()[job["game"]], job["platform"], built, lang)
            entry = catalog()[job["game"]]
            name = (entry.get("manifest") or {}).get("name") or entry.get("name", job["game"])
            key = f"w_output_{job['platform']}"
            job["results"][lang] = {"file": str(built) if built else None, "steps": steps, "note": note,
                                    "guide": guide,
                                    "private": phrase(cli.private_note(release_recipe(job["game"])
                                                                       or entry.get("manifest")), lang),
                                    "warning": (phrase("w_ios27", lang, name=name, issues=entry["repo_url"] + "/issues")
                                                if built and built.suffix.lower() == ".ipa"
                                                and cli.ios27_launch_risk(built) else ""),
                                    "about": phrase(key, lang, name=name) if key in MESSAGES else ""}
        return job["results"][lang]

    def running(self):
        return bool(self.process and self.process.poll() is None)

    def cancel(self):
        if self.process and self.process.poll() is None:
            # PadMint cancels and keeps finished work.
            self.process.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)

    def reveal(self):
        if self.process and self.process.poll() == 0 and self.result()["file"]:
            cli.reveal(Path(self.result()["file"]))


def make_handler(token, builds, restart=None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def reply(self, code, body, kind="application/json"):
            data = (body if isinstance(body, bytes) else body.encode() if isinstance(body, str)
                    else json.dumps(body).encode())
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(data)

        def allowed(self):
            query = parse_qs(urlparse(self.path).query)
            supplied = self.headers.get("X-PadMint-Token") or query.get("token", [""])[0]
            host = (self.headers.get("Host") or "").split(":")[0]
            return host in ("127.0.0.1", "localhost") and secrets.compare_digest(supplied, token)

        def lang(self, form=None):
            chosen = (form or {}).get("lang") or parse_qs(urlparse(self.path).query).get("lang", [""])[0]
            return chosen if chosen in LANGUAGES else language()

        def do_GET(self):
            if not self.allowed():
                return self.reply(403, {"error": "Open the address printed in the PadMint window"})
            route = urlparse(self.path).path
            if route == "/":
                data = json.dumps(player_data(self.lang())).replace("</", "<\\/")
                return self.reply(200, PAGE.replace("__TOKEN__", token).replace("__DATA__", data),
                                  "text/html; charset=utf-8")
            if route == "/api/player":
                return self.reply(200, player_data(self.lang()))
            if route == "/api/files":
                # Game files in the player's Downloads folder, for the chosen game only. On a Mac
                # this is what can make macOS ask about the Downloads folder, so it is never part
                # of opening the window.
                game = parse_qs(urlparse(self.path).query).get("game", [""])[0]
                if game not in {id_ for id_, _name, _platforms in cli.player_games()}:
                    return self.reply(400, {"error": "unknown game"})
                entry = catalog()[game]
                files = cli.game_files(cli.player_folder(), release_recipe(game) or entry.get("manifest"))
                return self.reply(200, {"files": [str(path) for path in files[:8]]})
            if route == "/api/versions":
                return self.reply(200, VERSIONS)
            if route == "/api/installed":
                return self.reply(200, installed.status("fresh" in parse_qs(urlparse(self.path).query)))
            if route == "/api/update":
                return self.reply(200, update.STATE)
            if route == "/api/storage":
                if storage.STATE.get("state") == "idle" or "fresh" in parse_qs(urlparse(self.path).query):
                    storage.measure(latest_tags())
                return self.reply(200, storage.STATE)
            match = re.fullmatch(r"/art/([a-z0-9]+)\.png", route)
            if match and (ART / f"{match.group(1)}.png").is_file():
                return self.reply(200, (ART / f"{match.group(1)}.png").read_bytes(), "image/png")
            if route == "/api/build":
                return self.reply(200, builds.status(self.lang()))
            if route == "/api/plan":
                query = parse_qs(urlparse(self.path).query)
                game, platform_name = query.get("game", [""])[0], query.get("platform", [""])[0]
                if not any(id_ == game and platform_name in platforms
                           for id_, _name, platforms in cli.player_games()):
                    return self.reply(400, {"error": "That game cannot be made for that device on this computer"})
                return self.reply(200, plan(game, platform_name, self.lang(), query.get("disc", [None])[0]))
            return self.reply(404, {"error": "not found"})

        def do_POST(self):
            if not self.allowed():
                return self.reply(403, {"error": "forbidden"})
            try:
                length = min(int(self.headers.get("Content-Length") or 0), 65536)
                form = json.loads(self.rfile.read(length) or b"{}")
                route, lang = urlparse(self.path).path, self.lang(form)
                if route == "/api/pick":
                    path = pick_file(phrase("w_file", lang), cli.player_folder())
                    return self.reply(200, {"path": path or None, "available": path is not False})
                if route == "/api/file":
                    return self.reply(200, {"problem": check_file(form["game"], form["path"], lang)})
                if route == "/api/make":
                    game, platform_name = form["game"], form["platform"]
                    if not any(id_ == game and platform_name in platforms
                               for id_, _name, platforms in cli.player_games()):
                        raise ValueError("That game cannot be made for that device on this computer")
                    disc = cli.dropped_path(form["path"]).resolve() if form.get("path") else None
                    builds.start(game, platform_name, disc, lang)
                    return self.reply(200, builds.status())
                if route == "/api/cancel":
                    builds.cancel()
                    return self.reply(200, builds.status())
                if route == "/api/update":
                    if not VERSIONS.get("padmint") or not update.newer(VERSIONS["padmint"]):
                        raise ValueError("This is the newest PadMint")
                    update.start(VERSIONS["padmint"].lstrip("v"))
                    return self.reply(200, update.STATE)
                if route == "/api/restart":
                    if builds.running():
                        raise ValueError(phrase("w_st_busy", lang))
                    if restart is None:
                        raise ValueError("PadMint can't restart itself here")
                    self.reply(200, {})
                    threading.Thread(target=restart, daemon=True).start()
                    return None
                if route == "/api/remove":
                    if builds.running():
                        raise ValueError(phrase("w_st_busy", lang))
                    freed = storage.remove(list(form.get("ids") or []), latest_tags())
                    storage.STATE.update(state="idle")
                    return self.reply(200, {"freed": freed})
                if route == "/api/reveal":
                    builds.reveal()
                    return self.reply(200, {})
                return self.reply(404, {"error": "not found"})
            except (KeyError, ValueError, OSError) as error:
                return self.reply(400, {"error": str(error)})

    return Handler


def latest_tags():
    """Each game's latest release tag, as far as the background check has read them."""
    return {game: tag for game, tag in VERSIONS["games"].items() if tag}


def serve(port=0, open_browser=True):
    # After an update PadMint restarts itself on the same address, so the open page and the
    # Mac app's window keep working: the restarted process gets the port and token back.
    token = os.environ.pop("PADMINT_UI_TOKEN", "") or secrets.token_urlsafe(24)
    reused = os.environ.pop("PADMINT_UI_PORT", "")
    if reused:
        port, open_browser = int(reused), False
    builds = Builds()
    holder = {}

    def restart():
        time.sleep(0.3)  # let the reply reach the page
        holder["restarting"] = True
        server = holder["server"]
        server.shutdown()
        server.server_close()
        os.environ.update(PADMINT_UI_PORT=str(server.server_address[1]), PADMINT_UI_TOKEN=token)
        os.environ.pop("PADMINT_FROM_UPDATE", None)
        os.execv(sys.executable, [sys.executable, "-m", "padmint", "ui", "--no-open"])

    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(token, builds, restart))
    holder["server"] = server
    url = f"http://127.0.0.1:{server.server_address[1]}/?token={token}"
    print(phrase("w_open", language(), version=__version__, url=url), flush=True)
    # Read every game's latest release (and its recipe) in the background, so the page can
    # say what is up to date and the plan shows at once.
    threading.Thread(target=check_versions, daemon=True).start()
    if open_browser:
        if cli.on_android():  # the phone's browser, through Termux
            subprocess.run([str(cli.TERMUX_OPEN_URL), url], check=False)
        else:
            webbrowser.open(url)
    try:
        server.serve_forever()
        while holder.get("restarting"):  # the restart thread replaces this process
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        builds.cancel()
        server.server_close()
    return 0


PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><title>PadMint</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Cdefs%3E%3ClinearGradient id='pmg' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%235ff0b0'/%3E%3Cstop offset='1' stop-color='%2314945f'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='64' height='64' rx='15' fill='url(%23pmg)'/%3E%3Cpath fill='%2306281a' d='M19 19h26c7.2 0 12.6 6.6 11.2 13.7l-2.1 10.2c-1 4.9-7.1 6.6-10.5 2.9L39 41H25l-4.6 4.8c-3.4 3.7-9.5 2-10.5-2.9L7.8 32.7C6.4 25.6 11.8 19 19 19z'/%3E%3Cpath stroke='%235ff0b0' stroke-width='4' stroke-linecap='round' d='M20 26v10M15 31h10'/%3E%3Cpath fill='%235ff0b0' d='M37 37c0-6.5 4.8-11 12-11 0 6.5-4.8 11-12 11z'/%3E%3Cpath stroke='%2306281a' stroke-width='1.8' stroke-linecap='round' d='M39.5 34.5l6.5-6'/%3E%3C/svg%3E">
<style>
:root{--bg:#0f1714;--panel:#16211d;--panel2:#1c2a25;--line:#2a3c35;--text:#e8f1ec;--muted:#9db3a9;--mint:#3ddc97;--mint2:#1fa572;--bad:#ff7a7a;--warn:#f5c56b;
 font-family:-apple-system,"Segoe UI",Roboto,system-ui,sans-serif;color-scheme:dark}
@media (prefers-color-scheme:light){:root{--bg:#f3f7f5;--panel:#fff;--panel2:#eef5f1;--line:#d6e3dc;--text:#14211c;--muted:#5a6f66;--mint:#14945f;--mint2:#0f7a4e;--bad:#c62828;--warn:#9a6700;color-scheme:light}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);line-height:1.5}
a{color:var(--mint)}.wrap{max-width:860px;margin:0 auto;padding:1.4rem 1.2rem 3rem}
header{display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap}
.top{display:flex;align-items:center;gap:.6rem}.gh{display:inline-grid;place-items:center;width:2.4rem;height:2.4rem;color:var(--text);border:1px solid var(--line);border-radius:10px;background:var(--panel)}
.gh:hover{border-color:var(--mint);color:var(--mint)}.gh svg{width:20px;height:20px}
.btn.back{border:0;background:none;color:var(--mint);font-weight:650;padding:.2rem 0;margin:0 0 .4rem}.btn.back:hover{text-decoration:underline}
.backBtn{margin-top:.6rem}
.item.later{opacity:.72}.item.later .av{filter:grayscale(.85)}.item.later .t{font-weight:600}
.tag.soon{background:color-mix(in srgb,var(--muted) 18%,transparent);color:var(--muted)}.tag.dl{background:color-mix(in srgb,#2d9cdb 18%,transparent);color:#2d9cdb}
.brand{display:flex;align-items:center;gap:.7rem;color:inherit;text-decoration:none;border-radius:12px}.brand:hover h1{color:var(--mint)}.brand:focus-visible{outline:2px solid var(--mint);outline-offset:4px}.brand h1{margin:0;font-size:1.6rem;letter-spacing:-.02em}
.brand .v{color:var(--muted);font-size:.85rem}.mark{width:42px;height:42px;filter:drop-shadow(0 4px 10px color-mix(in srgb,var(--mint) 30%,transparent))}
.mark svg{width:100%;height:100%;display:block}
select,input{font:inherit;color:var(--text);background:var(--panel2);border:1px solid var(--line);border-radius:9px;padding:.55rem .7rem}
.hero{margin:1.4rem 0 1rem}.hero p{margin:.2rem 0 .8rem;font-size:1.08rem}
.chips{display:flex;gap:.5rem;flex-wrap:wrap}.chip{font-size:.85rem;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:.2rem .7rem}
.explain{display:grid;gap:.5rem;margin-top:.9rem}.explain details{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:.55rem .9rem}
.explain summary{color:var(--text);font-weight:600}.explain ol{margin:.5rem 0 .2rem;padding-left:1.3rem}.explain li{margin:.3rem 0}.explain p{font-size:.95rem;margin:.5rem 0 .2rem}
.chip:before{content:"✓ ";color:var(--mint)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1.1rem 1.2rem;margin:1rem 0}
.card h2{margin:0 0 .7rem;font-size:1.1rem}.muted{color:var(--muted)}.small{font-size:.88rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:.6rem}
.pick{text-align:left;background:var(--panel2);border:1px solid var(--line);border-radius:11px;padding:.7rem .8rem;color:var(--text);cursor:pointer;font:inherit}
.pick:hover{border-color:var(--mint)}.pick.on{border-color:var(--mint);box-shadow:0 0 0 2px color-mix(in srgb,var(--mint) 35%,transparent)}
.pick b{display:block}.pick span{display:block;color:var(--muted);font-size:.82rem;margin-top:.15rem}
.tags{margin-top:.4rem;display:flex;gap:.3rem;flex-wrap:wrap}.tag{font-size:.72rem;border-radius:6px;padding:.05rem .4rem;background:color-mix(in srgb,var(--mint) 16%,transparent);color:var(--mint)}
.sub{margin:1rem 0 .5rem;font-size:.9rem;color:var(--muted);font-weight:600}
.list{display:flex;flex-direction:column;border:1px solid var(--line);border-radius:11px;overflow:hidden}
.item{display:grid;grid-template-columns:auto 1fr auto;gap:.1rem .85rem;align-items:center;text-align:left;background:var(--panel2);border:0;border-bottom:1px solid var(--line);padding:.6rem .85rem;color:var(--text);cursor:pointer;font:inherit;transition:background .15s,padding .15s}
.item:last-child{border-bottom:0}.item:hover{background:color-mix(in srgb,var(--c,var(--mint)) 12%,var(--panel2));padding-left:1.05rem}
.item.on{background:color-mix(in srgb,var(--mint) 18%,var(--panel2));box-shadow:inset 3px 0 0 var(--mint)}
.item .av{grid-row:1/span 2;width:2.4rem;height:2.4rem;border-radius:11px;display:grid;place-items:center;font-weight:800;font-size:.8rem;letter-spacing:.02em;color:#fff;background:linear-gradient(135deg,var(--c),color-mix(in srgb,var(--c) 60%,#000));box-shadow:0 2px 6px color-mix(in srgb,var(--c) 35%,transparent)}
.item .t{font-weight:650;grid-column:2}.item .s{color:var(--muted);font-size:.83rem;grid-column:2}.item .tags{grid-row:1/span 2;grid-column:3;margin:0;justify-content:flex-end}
.tabs{display:flex;gap:.2rem;border-bottom:1px solid var(--line);margin:.5rem 0 .6rem;overflow-x:auto}
.tab{background:none;border:0;border-bottom:3px solid transparent;padding:.55rem .8rem;font:inherit;font-weight:600;color:var(--muted);cursor:pointer;white-space:nowrap;transition:color .15s,border-color .15s}
.tab:hover{color:var(--text)}.tab.on{color:var(--text);border-bottom-color:var(--mint)}
.tab .n{display:inline-block;margin-left:.35rem;min-width:1.5rem;padding:0 .4rem;border-radius:999px;background:var(--panel2);font-size:.78rem;color:var(--muted)}.tab.on .n{background:var(--mint);color:#06281a}
.note{margin:.1rem 0 .6rem;font-size:.88rem;color:var(--muted)}
.flow{display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem;margin:1rem 0 .4rem}
.flow div{position:relative;background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:.75rem .85rem .75rem 3rem}
.flow i{position:absolute;left:.8rem;top:.8rem;width:1.6rem;height:1.6rem;border-radius:50%;background:var(--mint);color:#06281a;font-style:normal;font-weight:800;display:grid;place-items:center;font-size:.85rem}
.flow b{display:block}.flow span{color:var(--muted);font-size:.86rem}
@media (max-width:620px){.flow{grid-template-columns:1fr}}
.filters{display:flex;gap:.35rem;flex-wrap:wrap;margin:.2rem 0 .6rem}.filter{font:inherit;font-size:.82rem;border-radius:999px;padding:.2rem .7rem;border:1px solid var(--line);background:transparent;color:var(--muted);cursor:pointer}
.filter.on{background:var(--mint);border-color:var(--mint);color:#06281a;font-weight:600}
#search{width:100%;max-width:none;font-size:1rem;padding:.65rem .8rem}
button.btn{font:inherit;border-radius:10px;padding:.6rem 1.1rem;border:1px solid var(--line);background:var(--panel2);color:var(--text);cursor:pointer}
button.btn:hover{border-color:var(--mint)}button.main{background:var(--mint);border-color:var(--mint);color:#06281a;font-weight:700;font-size:1.05rem;padding:.75rem 1.4rem}
a.btn{display:inline-block;text-decoration:none;border-radius:10px;padding:.6rem 1.1rem;border:1px solid var(--line);background:var(--panel2);color:var(--text)}a.btn:hover{border-color:var(--mint)}
a.main{background:var(--mint);border-color:var(--mint);color:#06281a;font-weight:700}
.tag.ready{background:var(--mint);color:#06281a;font-weight:600}
button:disabled{opacity:.45;cursor:default}.row{display:flex;gap:.6rem;flex-wrap:wrap;align-items:center}
.tag.setup{background:color-mix(in srgb,var(--warn) 18%,transparent);color:var(--warn)}.tag.setup.xcode{background:color-mix(in srgb,var(--mint) 16%,transparent);color:var(--mint)}.tag.setup.easy{background:var(--mint);color:#06281a;font-weight:600}
.why{margin:.5rem 0 0;color:var(--muted);font-size:.9rem}.setup-box{background:var(--panel2);border-radius:10px;padding:.6rem .8rem;margin:.6rem 0}.setup-box .tools li.detail{display:block;border-bottom:0;padding-top:0}
.file{display:flex;justify-content:space-between;gap:.6rem;width:100%;margin:.3rem 0}.file b{overflow-wrap:anywhere}
.state{margin:.6rem 0 0;font-weight:600}.ok{color:var(--mint)}.bad{color:var(--bad)}.warn{color:var(--warn)}
details summary{cursor:pointer;color:var(--muted)}
.plan ol{margin:.2rem 0 .4rem;padding-left:1.3rem}.plan li{margin:.35rem 0;overflow-wrap:anywhere}
.tools{list-style:none;padding:0;margin:.3rem 0}.tools li{display:flex;justify-content:space-between;gap:.8rem;border-bottom:1px dashed var(--line);padding:.25rem 0;font-size:.9rem}
.out{background:var(--panel2);border-radius:10px;padding:.6rem .8rem;margin:.6rem 0}
.hidden{display:none!important}
.steps{list-style:none;margin:0;padding:0}.steps li{display:grid;grid-template-columns:1.8rem 1fr;gap:.5rem;padding:.55rem 0;border-bottom:1px solid var(--line)}
.ico{width:1.4rem;height:1.4rem;border-radius:50%;display:grid;place-items:center;font-size:.8rem;border:2px solid var(--line);margin-top:.1rem}
.done .ico{background:var(--mint);border-color:var(--mint);color:#06281a}.running .ico{border-color:var(--mint);border-top-color:transparent;animation:spin 1s linear infinite}
.failed .ico{border-color:var(--bad);color:var(--bad)}.cancelled .ico{color:var(--muted)}@keyframes spin{to{transform:rotate(360deg)}}
.pending{color:var(--muted)}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.78rem}.detail{font-size:.86rem;color:var(--muted);overflow-wrap:anywhere}
.bar{height:6px;background:var(--panel2);border-radius:99px;overflow:hidden;margin:.35rem 0 .1rem}.bar i{display:block;height:100%;background:var(--mint);width:0}
pre{background:#0a0f0d;color:#cfe3d8;border-radius:10px;padding:.8rem;white-space:pre-wrap;max-height:22rem;overflow:auto;font-size:.8rem;margin:.6rem 0}
.big{font-size:1.25rem;margin:0}.next li{margin:.5rem 0;overflow-wrap:anywhere}.banner{border-left:4px solid var(--mint)}.banner.badb{border-left-color:var(--bad)}
footer{margin-top:2rem;color:var(--muted);font-size:.82rem;display:flex;gap:1rem;flex-wrap:wrap;justify-content:space-between}

.wrap{max-width:1000px}
body{background:radial-gradient(1100px 480px at 0% -8%,color-mix(in srgb,var(--mint) 13%,transparent),transparent 70%),var(--bg)}
html{scrollbar-color:color-mix(in srgb,var(--muted) 45%,transparent) transparent;scrollbar-width:thin}
::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-thumb{background:color-mix(in srgb,var(--muted) 40%,transparent);border-radius:99px;border:2px solid var(--bg)}::-webkit-scrollbar-track{background:transparent}
.hero{margin:1.6rem 0 1.1rem}.hero p{font-size:1.3rem;font-weight:650;letter-spacing:-.01em;margin:.2rem 0 .7rem}
.search{position:relative}.search svg{position:absolute;left:.85rem;top:50%;transform:translateY(-50%);width:18px;height:18px;color:var(--muted)}
#search{padding-left:2.6rem;border-radius:12px}
.pills{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem .9rem;margin:.75rem 0 .35rem}
.tabs{display:flex;flex-wrap:wrap;gap:.35rem;margin:0;border:0;overflow:visible}
.tab{border:1px solid var(--line);border-radius:999px;padding:.38rem .85rem;background:var(--panel2);color:var(--muted);font-size:.9rem}
.tab:hover{color:var(--text);border-color:var(--mint)}.tab.on{background:var(--mint);border-color:var(--mint);color:#06281a}
.tab.on .n{background:rgba(0,0,0,.14);color:#06281a}
.filters{margin:0;gap:.3rem}.filter{font-size:.78rem;padding:.18rem .6rem}
.note{margin:.35rem 0 .7rem}
.list{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:.55rem;border:0;border-radius:0;overflow:visible}
.item{border:1px solid var(--line);border-radius:13px;padding:.75rem .85rem;align-items:start;grid-template-rows:auto auto 1fr;transition:border-color .15s,transform .15s,background .15s}
.item:last-child{border-bottom:1px solid var(--line)}
.item:hover{padding-left:.85rem;transform:translateY(-1px);border-color:color-mix(in srgb,var(--c) 70%,var(--line));background:color-mix(in srgb,var(--c) 7%,var(--panel2))}
.item.on{grid-column:1/-1;box-shadow:inset 3px 0 0 var(--mint)}
.item .av{grid-row:1/span 3}.item .tags{grid-row:3;grid-column:2;justify-content:flex-start;margin-top:.4rem}
.about{margin:0 0 .4rem}.about h2{font-size:.95rem;margin:0;color:var(--muted);font-weight:650;text-transform:uppercase;letter-spacing:.06em}
.about .flow{margin:.55rem 0 .5rem}.about .explain{grid-template-columns:1fr 1fr;align-items:start;margin-top:0}
@media (max-width:620px){.about .explain{grid-template-columns:1fr}.about .flow{gap:.4rem}.about .flow div{padding:.45rem .7rem .45rem 2.6rem}.about .flow i{top:.5rem;left:.65rem}.about .flow span{font-size:.82rem}}

.item.on{padding:.95rem 1rem}.item.on .av{width:3.1rem;height:3.1rem;font-size:.95rem;border-radius:14px}.item.on .t{font-size:1.2rem}
#pickCard h2{margin-bottom:.5rem}#gamePage{margin:.6rem 0 0}#gamePage a{font-weight:600;text-decoration:none}#gamePage a:hover{text-decoration:underline}
#fileBox h2,#deviceBox h2,#planBox h2{display:flex;align-items:center;gap:.5rem}
.card{box-shadow:0 1px 0 color-mix(in srgb,var(--text) 4%,transparent),0 8px 24px -18px rgba(0,0,0,.5)}

.loading{display:flex;align-items:center;gap:.6rem}.loading:before{content:"";width:1rem;height:1rem;border-radius:50%;border:2px solid var(--line);border-top-color:var(--mint);animation:spin 1s linear infinite}
.cmd{display:flex;gap:.5rem;align-items:center;background:#0a0f0d;color:#cfe3d8;border-radius:9px;padding:.4rem .45rem .4rem .7rem;margin:.35rem 0}
.cmd code{flex:1;overflow-wrap:anywhere;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.8rem}
.cmd button{font:inherit;font-size:.78rem;border-radius:7px;padding:.2rem .6rem;border:1px solid #2a3c35;background:#16211d;color:#cfe3d8;cursor:pointer}.cmd button:hover{border-color:var(--mint)}
.pks{display:flex;flex-wrap:wrap;gap:.3rem;margin:.3rem 0 .2rem}.pk{font-size:.76rem;border-radius:6px;padding:.05rem .45rem;background:color-mix(in srgb,var(--mint) 15%,transparent);color:var(--mint)}
.pk.no{background:color-mix(in srgb,var(--bad) 13%,transparent);color:var(--bad)}

#headCard .big{font-size:1.45rem;font-weight:750;letter-spacing:-.01em}
#headCard.okb{background:linear-gradient(135deg,color-mix(in srgb,var(--mint) 16%,var(--panel)),var(--panel))}
#headCard.okb .big:before{content:"✓";display:inline-grid;place-items:center;width:1.8rem;height:1.8rem;margin-right:.6rem;border-radius:50%;background:var(--mint);color:#06281a;font-size:1rem;vertical-align:.12em}

/* Launcher: one column, the player's own games first, real art, clear status. */
.wrap{max-width:880px;padding-top:0}
header{position:sticky;top:0;z-index:5;margin:0 -1.2rem;padding:.75rem 1.2rem;background:color-mix(in srgb,var(--bg) 80%,transparent);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid color-mix(in srgb,var(--line) 60%,transparent)}
.vstat{font-size:.8rem;font-weight:650;border-radius:999px;padding:.32rem .8rem;border:1px solid var(--line);color:var(--muted);text-decoration:none;background:var(--panel);white-space:nowrap}
.vstat.ok{color:var(--mint)}.vstat.upd{background:var(--warn);border-color:var(--warn);color:#2a1d00;animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{50%{box-shadow:0 0 0 6px color-mix(in srgb,var(--warn) 22%,transparent)}}
.sechead{display:flex;align-items:baseline;justify-content:space-between;gap:1rem;margin:1.7rem 0 .7rem}
.sechead h2,#pickTitle{margin:0;font-size:1.35rem;letter-spacing:-.02em}
#pickTitle{margin:1.9rem 0 .8rem}
.art{flex:none;width:52px;height:52px;border-radius:13px;overflow:hidden;display:grid;place-items:center;background:linear-gradient(135deg,var(--c),color-mix(in srgb,var(--c) 55%,#000));box-shadow:0 6px 16px -8px color-mix(in srgb,var(--c) 85%,#000),inset 0 0 0 1px rgba(255,255,255,.08);transition:transform .2s}
.art img{width:100%;height:100%;object-fit:cover;display:block}
.art.gen{color:#fff;font-weight:800;font-size:1rem;letter-spacing:.02em}
.art.big{width:104px;height:104px;border-radius:24px;font-size:1.7rem}
.shelf{display:flex;flex-direction:column;gap:.55rem}
.lib{display:flex;align-items:center;gap:1rem;padding:.85rem 1rem;border-radius:16px;cursor:pointer;background:linear-gradient(100deg,color-mix(in srgb,var(--c) 20%,var(--panel)) 0%,var(--panel) 60%);border:1px solid color-mix(in srgb,var(--c) 28%,var(--line));transition:transform .18s,border-color .18s,box-shadow .18s;animation:rise .35s both;animation-delay:calc(var(--i,0)*35ms)}
.lib:hover{transform:translateY(-2px);border-color:color-mix(in srgb,var(--c) 70%,var(--line));box-shadow:0 14px 30px -18px color-mix(in srgb,var(--c) 90%,#000)}
.lib:hover .art,.item:hover .art{transform:scale(1.06) rotate(-2deg)}
.lib .art{width:64px;height:64px;border-radius:16px}
.body{flex:1;min-width:0;display:flex;flex-direction:column;text-align:left}
.body .t{font-weight:700;font-size:1.05rem;line-height:1.25;color:var(--text)}
.body .s{color:var(--muted);font-size:.86rem}
.body .m{color:var(--muted);font-size:.8rem;opacity:.9}
.side{display:flex;align-items:center;gap:.55rem;flex:none;flex-wrap:wrap;justify-content:flex-end}
.badge{font-size:.78rem;font-weight:650;border-radius:999px;padding:.22rem .7rem;white-space:nowrap}
.badge.ok{color:var(--mint);background:color-mix(in srgb,var(--mint) 14%,transparent)}
.badge.upd{color:#2a1d00;background:var(--warn)}
button.btn.ghost{background:transparent}button.btn.main.small{font-size:.9rem;padding:.5rem 1rem}
.welcome{display:flex;flex-direction:column;gap:.3rem;margin:1.6rem 0 .2rem;padding:1.1rem 1.2rem;border-radius:16px;border:1px dashed color-mix(in srgb,var(--mint) 45%,var(--line));background:color-mix(in srgb,var(--mint) 7%,var(--panel))}
.more{margin-top:.6rem;width:100%;border-style:dashed}#shelfNote{font-weight:600}
.welcome b{font-size:1.15rem}.welcome span{color:var(--muted)}
#pickCard{background:none;border:0;box-shadow:none;padding:0;margin-top:0}
.list{display:flex;flex-direction:column;gap:0;border:1px solid var(--line);border-radius:16px;overflow:hidden;background:var(--panel)}
.item{display:flex;align-items:center;gap:.95rem;width:100%;border:0;border-radius:0;border-bottom:1px solid var(--line);background:transparent;padding:.7rem 1rem;transform:none;animation:rise .3s both;animation-delay:calc(var(--i,0)*16ms)}
.item:last-child{border-bottom:0}
.item:hover{transform:none;padding-left:1rem;border-color:var(--line);background:color-mix(in srgb,var(--c) 10%,var(--panel))}
.item .body .t{font-size:1rem}
.ver{font-size:.78rem;color:var(--muted);font-variant-numeric:tabular-nums}
.own{font-size:.76rem;font-weight:650;color:var(--mint)}.own.upd{color:var(--warn)}
.act{font-size:.8rem;font-weight:700;border-radius:999px;padding:.32rem .85rem;white-space:nowrap}
.act.build{background:var(--mint);color:#06281a}.act.download{background:color-mix(in srgb,#2d9cdb 22%,transparent);color:#5bb8f0}.act.later{background:color-mix(in srgb,var(--muted) 14%,transparent);color:var(--muted)}
.act.build:after,.act.download:after{content:" ›"}
.item.later .art{filter:grayscale(.85);opacity:.65}.item.later .t{color:var(--muted)}
.settled .item,.settled .lib{animation:none}
@keyframes rise{from{opacity:0;transform:translateY(6px)}}
#hero{position:relative;display:flex;align-items:center;gap:1.3rem;padding:1.4rem;border-radius:22px;overflow:hidden;margin:.2rem 0 .3rem;background:radial-gradient(640px 240px at 0% 0%,color-mix(in srgb,var(--c) 45%,transparent),transparent 70%),linear-gradient(120deg,color-mix(in srgb,var(--c) 22%,var(--panel)),var(--panel));border:1px solid color-mix(in srgb,var(--c) 40%,var(--line));animation:rise .3s both}
#hero h2{margin:0;font-size:1.75rem;letter-spacing:-.02em;line-height:1.15}#hero p{margin:.15rem 0 .55rem}
.facts{display:flex;flex-wrap:wrap;gap:.35rem}.fact{font-size:.78rem;border-radius:999px;padding:.16rem .62rem;background:color-mix(in srgb,var(--text) 9%,transparent);color:var(--text)}
.fact.new{background:var(--warn);color:#2a1d00;font-weight:650}.fact.mine{color:var(--mint)}
#devices{display:flex;flex-direction:column;gap:.45rem}
.pick{display:flex;align-items:center;justify-content:space-between;gap:.8rem;padding:.85rem 1rem;border-radius:12px;transition:border-color .15s,background .15s}
.pick:hover:not(:disabled){background:color-mix(in srgb,var(--mint) 7%,var(--panel2))}
.pick:after{content:"›";color:var(--muted);font-size:1.25rem;line-height:1}.pick.on:after{content:"✓";color:var(--mint)}
.pick span{margin:0}
button.main{background:linear-gradient(180deg,color-mix(in srgb,var(--mint) 82%,#fff),var(--mint));box-shadow:0 8px 22px -12px var(--mint);transition:transform .12s,box-shadow .2s}
button.main:hover:not(:disabled){transform:translateY(-1px);box-shadow:0 12px 28px -12px var(--mint)}
button.main:active:not(:disabled){transform:translateY(1px)}
.aboutbox{margin:2.2rem 0 0;border:1px solid var(--line);border-radius:14px;padding:.75rem 1rem;background:var(--panel)}
.aboutbox>summary{font-weight:650;color:var(--text)}.aboutbox .hero{margin:.9rem 0 .6rem}.aboutbox .hero p{font-size:1.05rem}
@media (max-width:620px){.lib,.item{flex-wrap:wrap}.side{width:100%;justify-content:flex-start;padding-left:calc(52px + .95rem)}#hero{flex-direction:column;align-items:flex-start}}

.card.done{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.8rem 1.2rem;animation:rise .25s both}
.card.done>:not(h2):not(.sum){display:none!important}.card.done h2{margin:0;font-size:.95rem;color:var(--muted);font-weight:600}
.sum{display:none}.card.done .sum{display:flex;align-items:center;gap:.9rem;min-width:0}
.sum b{color:var(--mint);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
button.btn.link{background:none;border:0;color:var(--mint);font-weight:650;padding:.2rem .3rem}button.btn.link:hover{text-decoration:underline}
#nowBox{display:flex;align-items:center;gap:1rem;margin:1.4rem 0 0;padding:1rem 1.1rem;border-radius:16px;cursor:pointer;border:1px solid color-mix(in srgb,var(--mint) 50%,var(--line));background:linear-gradient(100deg,color-mix(in srgb,var(--mint) 16%,var(--panel)),var(--panel));animation:rise .3s both}
#nowBox.hidden{display:none}#nowBox.failed{border-color:var(--bad)}#nowBox .bar{margin:.45rem 0 0}
.headrow{display:flex;align-items:center;gap:1rem}#headArt .art{width:72px;height:72px;border-radius:18px}#headBar .bar{height:8px;margin-top:1rem}
.bar i{transition:width .6s ease;background:linear-gradient(90deg,var(--mint2),var(--mint))}
.bar.live i{background-image:linear-gradient(90deg,var(--mint2),var(--mint),color-mix(in srgb,var(--mint) 60%,#fff),var(--mint),var(--mint2));background-size:200% 100%;animation:shimmer 1.8s linear infinite}
@keyframes shimmer{to{background-position:-200% 0}}

/* Polish pass: one button system, quiet focus rings, a real header, intro, sheet and Storage. */
*:focus{outline:none}*:focus-visible{outline:2px solid var(--mint);outline-offset:2px;border-radius:10px}
button.btn,a.btn{display:inline-flex;align-items:center;justify-content:center;gap:.45rem;min-height:2.5rem;padding:0 1.05rem;border-radius:11px;font-weight:650;font-size:.93rem;line-height:1;border:1px solid color-mix(in srgb,var(--text) 12%,transparent);background:color-mix(in srgb,var(--text) 6%,transparent);color:var(--text);text-decoration:none;transition:background .15s,border-color .15s,transform .1s,box-shadow .2s}
button.btn:hover:not(:disabled),a.btn:hover{background:color-mix(in srgb,var(--text) 11%,transparent);border-color:color-mix(in srgb,var(--text) 20%,transparent)}
button.btn:active:not(:disabled),a.btn:active{transform:translateY(1px)}
button.btn.main,a.btn.main,a.main{background:linear-gradient(180deg,#6af0b5,var(--mint));border-color:transparent;color:#05261a;box-shadow:0 1px 0 rgba(255,255,255,.35) inset,0 8px 20px -12px var(--mint)}
button.btn.main:hover:not(:disabled),a.btn.main:hover{background:linear-gradient(180deg,#7ff5c2,#4be3a2);box-shadow:0 1px 0 rgba(255,255,255,.4) inset,0 12px 26px -12px var(--mint)}
button.btn.main{font-size:1rem;min-height:2.85rem;padding:0 1.5rem}button.btn.small,button.btn.main.small{min-height:2.2rem;font-size:.86rem;padding:0 .95rem}
button.btn.ghost{background:transparent}button.btn.danger{color:var(--bad);border-color:color-mix(in srgb,var(--bad) 35%,transparent);background:transparent}
button.btn.danger:hover:not(:disabled){background:color-mix(in srgb,var(--bad) 12%,transparent)}
button.btn.back{min-height:auto;padding:.2rem 0;border:0;background:none;color:var(--mint)}button.btn.back:hover{background:none;text-decoration:underline}
button.btn.link{min-height:auto;padding:.15rem .2rem;border:0;background:none;color:var(--mint)}button.btn.link:hover:not(:disabled){background:none;text-decoration:underline}
header{display:flex;align-items:center;gap:1rem;flex-wrap:nowrap}.brand{flex:none}.brand h1{font-size:1.3rem}.brand .v{display:none}.mark{width:36px;height:36px}
.nav{display:flex;gap:.2rem;padding:.22rem;border-radius:12px;background:color-mix(in srgb,var(--text) 6%,transparent);margin-right:auto}
.navb{font:inherit;font-size:.9rem;font-weight:650;color:var(--muted);background:none;border:0;border-radius:9px;padding:.42rem .9rem;cursor:pointer;transition:background .15s,color .15s}
.navb:hover{color:var(--text)}.navb.on{background:var(--panel2);color:var(--text);box-shadow:0 1px 2px rgba(0,0,0,.35)}
.top{gap:.45rem}.gh{width:2.4rem;height:2.4rem;border-radius:11px;background:color-mix(in srgb,var(--text) 6%,transparent);border-color:transparent}
.langw{position:relative;display:inline-flex;align-items:center;height:2.4rem;border-radius:11px;background:color-mix(in srgb,var(--text) 6%,transparent);color:var(--muted)}
.langw:hover{background:color-mix(in srgb,var(--text) 11%,transparent)}.langw svg{position:absolute;left:.65rem;width:16px;height:16px;pointer-events:none}
.langw select{appearance:none;-webkit-appearance:none;background:transparent;border:0;height:100%;padding:0 .8rem 0 2.05rem;color:var(--text);font-weight:600;font-size:.88rem;cursor:pointer;border-radius:11px}
.langw select:focus-visible{outline:2px solid var(--mint);outline-offset:2px}
button.vstat{font:inherit;font-size:.82rem;font-weight:650;cursor:default;height:2.4rem;border-radius:11px;padding:0 .85rem;background:color-mix(in srgb,var(--mint) 12%,transparent);border:0;color:var(--mint)}
button.vstat.upd{cursor:pointer;background:var(--warn);color:#2a1d00}button.vstat.upd:hover{filter:brightness(1.06)}button.vstat.wait{background:color-mix(in srgb,var(--text) 6%,transparent);color:var(--muted)}
.intro{position:relative;margin:1.5rem 0 .4rem;padding:1.5rem 1.6rem;border-radius:22px;overflow:hidden;border:1px solid color-mix(in srgb,var(--mint) 22%,var(--line));background:radial-gradient(700px 260px at 100% 0%,color-mix(in srgb,#2d9cdb 22%,transparent),transparent 70%),radial-gradient(600px 260px at 0% 100%,color-mix(in srgb,var(--mint) 22%,transparent),transparent 70%),var(--panel)}
.intro h1{margin:0 0 .45rem;font-size:1.65rem;line-height:1.2;letter-spacing:-.025em;max-width:30ch}
.intro p{margin:0;color:var(--muted);max-width:62ch;font-size:1rem}
.intro ol{display:flex;flex-wrap:wrap;gap:.4rem 1.4rem;list-style:none;padding:0;margin:1rem 0 .2rem;counter-reset:s}
.intro li{counter-increment:s;display:flex;align-items:center;gap:.5rem;font-weight:600;font-size:.92rem}
.intro li:before{content:counter(s);display:grid;place-items:center;width:1.5rem;height:1.5rem;border-radius:50%;background:var(--mint);color:#05261a;font-size:.78rem;font-weight:800}
.intro .row{margin-top:.9rem}
.intro.compact{padding:1rem 1.2rem}.intro.compact h1{font-size:1.15rem;margin-bottom:.2rem}.intro.compact ol{display:none}.intro.compact p{font-size:.9rem}
.sheet{position:fixed;inset:0;z-index:20;display:grid;place-items:center;padding:1.2rem;background:rgba(3,8,6,.6);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);animation:fade .2s both}
.sheet.hidden{display:none}@keyframes fade{from{opacity:0}}
.sheetbox{position:relative;width:min(640px,100%);max-height:calc(100vh - 2.4rem);overflow:auto;padding:1.6rem 1.7rem;border-radius:22px;background:var(--panel);border:1px solid var(--line);box-shadow:0 30px 80px -20px rgba(0,0,0,.7);animation:rise .25s both}
.sheetbox h2{margin:0 0 .5rem;font-size:1.35rem;letter-spacing:-.02em}.sheetbox p{color:var(--muted)}
.sheet .x{position:absolute;top:.8rem;right:.8rem;width:2.2rem;height:2.2rem;border-radius:50%;border:0;background:color-mix(in srgb,var(--text) 7%,transparent);color:var(--muted);font-size:1.2rem;cursor:pointer}.sheet .x:hover{color:var(--text)}
.sheet .flow{grid-template-columns:1fr;gap:.4rem}.sheet .flow div{padding:.6rem .8rem .6rem 2.9rem}.sheet .flow i{top:.65rem}
.sheet .explain{grid-template-columns:1fr}.sheet .about h2{margin:1.1rem 0 .4rem}.sheet .chips{margin:.8rem 0 .2rem}.sheet .hero{margin:0}
.who{display:flex;gap:.9rem;align-items:flex-start;padding:.9rem 1rem;border-radius:14px;background:color-mix(in srgb,var(--mint) 9%,var(--panel2));margin:.6rem 0 .2rem}.who b{display:block}
.upd-head{display:flex;align-items:center;gap:1rem;margin-bottom:.4rem}.upd-head .mark{width:56px;height:56px}
#storage .sechead{margin-top:1.6rem}
.st-sum{display:flex;align-items:center;gap:1.2rem;flex-wrap:wrap;padding:1.3rem 1.4rem;border-radius:20px;background:var(--panel);border:1px solid var(--line);margin-top:1.4rem}
.st-sum .big{font-size:2rem;font-weight:800;letter-spacing:-.03em;line-height:1}.st-sum .body{min-width:200px}
.st-meter{height:10px;border-radius:99px;overflow:hidden;display:flex;background:color-mix(in srgb,var(--text) 8%,transparent);margin:.7rem 0 .35rem}
.st-meter i{display:block;height:100%}.st-meter .cch{background:#5bb8f0}.item.later .m{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.st-meter .keep{background:var(--mint)}.st-meter .old{background:var(--warn)}
.legend{display:flex;gap:1rem;flex-wrap:wrap;font-size:.8rem;color:var(--muted)}.legend span:before{content:"";display:inline-block;width:.6rem;height:.6rem;border-radius:3px;margin-right:.35rem;background:var(--c)}
.st-row{display:flex;align-items:center;gap:.9rem;padding:.65rem 1rem;border-bottom:1px solid var(--line)}.st-row:last-child{border-bottom:0}
.st-row .art{width:40px;height:40px;border-radius:11px;font-size:.85rem}.st-row .sz{font-variant-numeric:tabular-nums;font-weight:650;min-width:4.5rem;text-align:right}
.glyph{background:linear-gradient(135deg,#3a4a44,#1f2a26)!important;color:var(--muted)!important;font-size:1.1rem!important}
details.kept{margin-top:.8rem}details.kept>summary{padding:.4rem 0;font-weight:600}
.toast{position:fixed;left:50%;bottom:1.4rem;transform:translateX(-50%);z-index:30;padding:.7rem 1.1rem;border-radius:12px;background:var(--mint);color:#05261a;font-weight:700;box-shadow:0 14px 34px -14px rgba(0,0,0,.7);animation:rise .25s both}
.native footer .localnote{display:none}
.who .mark{width:44px;height:44px;flex:none}.who span{display:block;margin-top:.15rem}.who b span{display:inline;margin:0}.who b a{color:var(--mint);text-decoration:none}.who b a:hover{text-decoration:underline}
.sheet .hero>p,.sheet .about>h2,.sheet .about .flow{display:none}.sheet .chips{margin:.9rem 0 .4rem}
.sheet .explain details{background:none;border:0;padding:0;margin-top:.9rem}.sheet .explain summary{pointer-events:none;list-style:none;color:var(--text);font-weight:700;font-size:1.02rem}
.sheet .explain summary::-webkit-details-marker{display:none}.sheet .explain li,.sheet .explain p{color:var(--muted)}
html{min-height:100%;background:var(--bg)}body{min-height:100vh;background-attachment:fixed}
@media (max-width:640px){header{flex-wrap:wrap}.nav{order:3;width:100%;margin-right:0}.nav .navb{flex:1}.intro h1{font-size:1.3rem}}

@media (prefers-color-scheme:light){.act.download{color:#1d6fa5}.vstat.upd,.badge.upd,.fact.new{color:#2a1d00}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}


/* Launcher with a sidebar: where each game is, readable rows, one clear action. */
.app{display:grid;grid-template-columns:240px minmax(0,1fr);min-height:100vh}
#side{position:sticky;top:0;height:100vh;overflow:auto;display:flex;flex-direction:column;padding:1.1rem .7rem .9rem;border-right:1px solid color-mix(in srgb,var(--line) 75%,transparent);background:color-mix(in srgb,var(--panel) 60%,transparent)}
#side .brand{padding:.2rem .55rem 1rem}#side .brand h1{font-size:1.2rem}#side .mark{width:34px;height:34px}
.sidenav{display:flex;flex-direction:column;gap:.1rem;flex:1}
.sh{font-size:.7rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);padding:1rem .6rem .3rem;opacity:.85}.sh:empty{padding:.5rem 0;border-top:1px solid color-mix(in srgb,var(--line) 70%,transparent);margin-top:.7rem}
.sn{display:flex;align-items:center;gap:.6rem;width:100%;font:inherit;font-size:.9rem;font-weight:600;color:var(--text);background:none;border:0;border-radius:9px;padding:.45rem .6rem;cursor:pointer;text-align:left;transition:background .12s}
.sn:hover{background:color-mix(in srgb,var(--text) 6%,transparent)}.sn.on{background:color-mix(in srgb,var(--mint) 17%,transparent)}
.ic{width:18px;height:18px;flex:none;display:grid;place-items:center;color:var(--muted)}.ic svg{width:100%;height:100%;display:block}.sn.on .ic{color:var(--mint)}
.sn .l{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sn .c{font-size:.74rem;font-weight:650;color:var(--muted);font-variant-numeric:tabular-nums}
.sn.hot .c{background:var(--warn);color:#2a1d00;border-radius:99px;padding:.02rem .48rem}
.sn.away .l{color:var(--muted)}.sn.live{background:color-mix(in srgb,var(--mint) 10%,transparent);margin-bottom:.3rem}.sn.live .c{color:var(--mint)}
.ic.spin{width:14px;height:14px;margin:0 2px;border-radius:50%;border:2px solid var(--line);border-top-color:var(--mint);animation:spin 1s linear infinite}
.sidefoot{display:flex;flex-direction:column;align-items:stretch;gap:.5rem;padding:.9rem .25rem 0}
.sidefoot .vstat{width:100%;justify-content:center}.footrow{display:flex;gap:.45rem}.footrow .langw{flex:1}.footrow .langw select{width:100%}
.sidefoot .btn.link{justify-content:flex-start;padding:.2rem .35rem;color:var(--muted);font-weight:600}.sidefoot .btn.link:hover{color:var(--mint)}
.wrap{max-width:960px;width:100%;margin:0;padding:.4rem 2.2rem 3rem}
#shelf>.sechead{align-items:flex-start;margin:1.6rem 0 .9rem}#shelfTitle{margin:0;font-size:1.6rem;letter-spacing:-.025em}#shelfSub{margin:.2rem 0 0;max-width:62ch}
#shelfNote{white-space:nowrap}#shelfNote.loading:before{width:.8rem;height:.8rem}
.group{font-size:.74rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin:1.3rem .2rem .45rem}.group:first-child{margin-top:.2rem}
.shelf{display:flex;flex-direction:column;gap:0;border:1px solid var(--line);border-radius:16px;overflow:hidden;background:var(--panel)}
.mg{display:flex;align-items:flex-start;gap:1rem;padding:.9rem 1.1rem;border-bottom:1px solid var(--line);cursor:pointer;transition:background .15s;animation:rise .3s both;animation-delay:calc(var(--i,0)*18ms)}
.mg:last-child{border-bottom:0}.mg:hover{background:color-mix(in srgb,var(--c) 9%,var(--panel))}.mg:hover .art{transform:scale(1.05)}
.mg .art{width:56px;height:56px;border-radius:14px}.mg .side{align-self:center;flex-wrap:nowrap}.mg .body .t{font-size:1.02rem}
.where{display:flex;flex-direction:column;gap:.22rem;margin-top:.5rem}
.cp{display:flex;align-items:center;gap:.5rem;font-size:.86rem;flex-wrap:wrap;line-height:1.35}.cp .ic{width:16px;height:16px}
.cp b{font-weight:650}.cp .d{color:var(--muted)}.cp.built b,.cp.away b{color:var(--muted);font-weight:600}.cp .badge{padding:.05rem .5rem;font-size:.72rem}
.okt{color:var(--mint);font-size:.84rem;font-weight:650;white-space:nowrap}.chev{color:var(--muted);font-size:1.4rem;line-height:1;padding-left:.2rem}
.empty{padding:1.4rem 1.2rem;border:1px dashed var(--line);border-radius:16px;color:var(--muted);text-align:center}
#copies{margin:.7rem 0 .2rem;padding:.9rem 1.15rem;border-radius:16px;border:1px solid var(--line);background:var(--panel);display:flex;flex-direction:column;gap:.35rem}
#copies h3{margin:0 0 .15rem;font-size:.72rem;letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}#copies .cp{font-size:.93rem}
.item .side{gap:.8rem}.own{font-size:.8rem}.act{padding:0;border-radius:0;background:none!important;font-size:.84rem;min-width:5.5rem;text-align:right}
.act.build{color:var(--mint)}.act.build.upd{color:var(--warn)}.act.download{color:#5bb8f0}.act.later{color:var(--muted)}.act.build:after,.act.download:after{content:" ›";font-size:1.05rem}
@media (max-width:820px){.app{display:block}#side{position:sticky;z-index:6;height:auto;flex-direction:row;flex-wrap:wrap;align-items:center;gap:.4rem .6rem;padding:.6rem .8rem;border-right:0;border-bottom:1px solid var(--line);background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}
 #side .brand{padding:0}.sidenav{order:3;flex:1 1 100%;flex-direction:row;overflow-x:auto;gap:.2rem;scrollbar-width:none}.sidenav::-webkit-scrollbar{display:none}.sh{display:none}.sn{width:auto;white-space:nowrap;flex:none}.sn .l{overflow:visible}
 .sidefoot{flex-direction:row;align-items:center;padding:0;margin-left:auto}.sidefoot .vstat{width:auto}.sidefoot .btn.link{display:none}.wrap{padding:.2rem 1rem 2rem}#shelf>.sechead{flex-direction:column;gap:.4rem}}
@media (max-width:560px){.mg{flex-wrap:wrap}.mg .side{width:100%;justify-content:flex-start;padding-left:calc(56px + 1rem)}.mg .chev{display:none}.footrow .langw{display:none}}
.mg{align-items:center;gap:.85rem;padding:.6rem 1rem}
.mg .art{width:44px;height:44px;border-radius:11px}.mg:hover .art{transform:scale(1.04)}
.tl{display:flex;align-items:baseline;gap:.55rem;min-width:0}
.tl .t{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}.mg .body .t{font-size:.98rem}
.tl .s{white-space:nowrap;flex:none;font-size:.78rem}
.mg .where{flex-direction:row;flex-wrap:wrap;gap:.1rem 1.1rem;margin-top:.18rem}
.mg .cp{font-size:.8rem;gap:.32rem;flex-wrap:nowrap;white-space:nowrap}.mg .cp .ic{width:13px;height:13px;opacity:.75}.mg .cp .badge{display:none}
.cp .vv{color:var(--muted);font-variant-numeric:tabular-nums}.cp .vv.old{color:var(--warn);font-weight:650}
.mg .side{gap:.4rem}.mg button.btn.main.small{min-height:1.95rem;font-size:.8rem;padding:0 .85rem;box-shadow:none;background:color-mix(in srgb,var(--mint) 16%,transparent);color:var(--mint);border:1px solid color-mix(in srgb,var(--mint) 35%,transparent)}.mg button.btn.main.small:hover:not(:disabled){background:var(--mint);color:#05261a;box-shadow:none}@media (prefers-color-scheme:light){.mg button.btn.main.small{color:#0b6b45}}.mg .chev{font-size:1.2rem}
.item{padding:.5rem 1rem;gap:.85rem}.item .art{width:40px;height:40px;border-radius:10px}
.item .body .t{font-size:.97rem}.item .body .s{font-size:.8rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#shelf>.sechead{margin:1.3rem 0 .7rem}#shelfTitle{font-size:1.45rem}
@media (max-width:560px){.tl{flex-direction:column;gap:0}.mg .where{gap:.1rem .8rem}}
.here{margin:-.35rem 0 .9rem;padding:.65rem .9rem;border-radius:12px;background:color-mix(in srgb,var(--mint) 8%,var(--panel));border:1px solid color-mix(in srgb,var(--mint) 22%,var(--line));color:var(--text);font-size:.88rem;line-height:1.45}
.own.none{color:var(--muted);font-weight:500}.item .side .own{white-space:nowrap}
.group.fold{display:flex;align-items:center;gap:.4rem;background:none;border:0;font-family:inherit;cursor:pointer;padding:0;text-align:left}.group.fold:hover{color:var(--text)}
.group.fold .tw{display:inline-block;transition:transform .15s;font-size:1rem;line-height:1}.group.fold.open .tw{transform:rotate(90deg)}
#lookAgain{gap:.4rem}#lookAgain:before{content:"↻";font-size:1rem}
.setbtn{flex:1;display:flex;align-items:center;gap:.5rem;font:inherit;font-size:.88rem;font-weight:600;color:var(--text);background:var(--panel2);border:1px solid var(--line);border-radius:11px;padding:.5rem .75rem;cursor:pointer}.setbtn:hover{border-color:var(--mint)}
#settingsPanel h2{margin:0 0 .6rem}.setrow{display:flex;align-items:center;gap:1rem;padding:.85rem 0;border-top:1px solid var(--line)}#settingsPanel>.setrow{border-top:0}
.settxt{flex:1;min-width:0;display:flex;flex-direction:column;gap:.15rem}.settxt b{font-size:.95rem}.settxt span{font-size:.84rem;overflow-wrap:anywhere}
.setctl{display:flex;gap:.45rem;align-items:center;flex:none}.setctl .langw{min-width:11rem}.setctl a.btn{text-decoration:none}
.okt.soft{color:var(--muted)}
#shelf>.sechead .row{flex-wrap:nowrap;align-items:center;gap:.55rem}#shelfNote{white-space:nowrap;font-size:.82rem}
#lookAgain{width:2.25rem;min-height:2.25rem;padding:0;border-radius:50%;font-size:0}#lookAgain:before{font-size:1.05rem}
@media (max-width:560px){.setrow{flex-wrap:wrap}.setctl{width:100%}}
html.locked,html.locked body{overflow:hidden}.sheet{overscroll-behavior:contain}.sheetbox{overscroll-behavior:contain}
</style></head><body><div class="app">
<aside id="side"><a class="brand" id="home" href="#"><div class="mark"><svg viewBox="0 0 64 64" aria-hidden="true"><defs><linearGradient id="pmg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5ff0b0"/><stop offset="1" stop-color="#14945f"/></linearGradient></defs><rect width="64" height="64" rx="15" fill="url(#pmg)"/><path fill="#06281a" d="M19 19h26c7.2 0 12.6 6.6 11.2 13.7l-2.1 10.2c-1 4.9-7.1 6.6-10.5 2.9L39 41H25l-4.6 4.8c-3.4 3.7-9.5 2-10.5-2.9L7.8 32.7C6.4 25.6 11.8 19 19 19z"/><path stroke="#5ff0b0" stroke-width="4" stroke-linecap="round" d="M20 26v10M15 31h10"/><path fill="#5ff0b0" d="M37 37c0-6.5 4.8-11 12-11 0 6.5-4.8 11-12 11z"/><path stroke="#06281a" stroke-width="1.8" stroke-linecap="round" d="M39.5 34.5l6.5-6"/></svg></div><div><h1>PadMint</h1><div class="v" id="ver"></div></div></a>
<nav class="sidenav" id="sidenav"></nav>
<div class="sidefoot"><button class="vstat hidden" id="vstat"></button><div class="footrow"><button class="setbtn" id="settingsSide"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg><span data-t="settings"></span></button><a class="gh" id="gh" href="https://github.com/chrissotraidis" target="_blank" rel="noopener" title="GitHub" aria-label="GitHub"><svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg></a></div><button class="btn link hidden" id="aboutSide" data-t="about_padmint"></button></div></aside>
<div class="wrap">

<main id="form">
<section class="intro" id="intro"><h1 data-t="hero_title"></h1><p data-t="hero_text"></p><ol><li data-t="intro_1"></li><li data-t="intro_2"></li><li data-t="intro_3"></li></ol><div class="row"><button class="btn link" id="aboutOpen" data-t="learn_more"></button></div></section>
<section class="hidden" id="nowBox"></section>
<section class="hidden" id="shelf"><div class="sechead"><div><h2 id="shelfTitle"></h2><p class="note" id="shelfSub"></p></div><div class="row"><span class="muted small" id="shelfNote"></span><button class="btn small ghost" id="lookAgain"></button></div></div><div id="shelfList"></div></section>
<section class="card" id="pickCard"><h2 id="pickTitle"></h2><p class="here hidden" id="here"></p><button class="btn back hidden" id="changeGame" data-t="change"></button><div id="hero" class="hidden"></div><div id="copies" class="hidden"></div>
<div id="finder"><div class="search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><input id="search" type="search" autocomplete="off"></div></div>
<div class="pills" id="pills"><div class="tabs" id="tabs" role="tablist"><button class="tab" data-g="all" role="tab"><span data-t="tab_all"></span><span class="n"></span></button><button class="tab" data-g="build" role="tab"><span data-t="tab_build"></span><span class="n"></span></button><button class="tab" data-g="download" role="tab"><span data-t="tab_download"></span><span class="n"></span></button><button class="tab" data-g="later" role="tab"><span id="laterHead" data-t="later_head"></span><span class="n"></span></button><button class="tab" data-g="missing" role="tab"><span data-t="tab_missing"></span><span class="n"></span></button></div><div class="filters" id="filters"></div></div>
<p class="note" id="groupNote"></p><div class="list" id="list"></div><p class="small hidden" id="gamePage"><a target="_blank" rel="noopener" id="gamePageLink"></a></p><p class="muted hidden" id="noMatch" data-t="no_match"></p></section>

<section class="card hidden" id="dlBox"><h2 id="dlName"></h2><p id="dlIntro"></p><ol class="next" id="dlSteps"></ol><p class="small" id="dlGuide"></p><button class="btn back backBtn" data-t="change"></button></section>

<section class="card hidden" id="laterBox"><h2 id="laterName"></h2><p class="muted" id="laterAbout"></p><p id="laterText"></p><div class="row"><a class="btn" id="laterLink" target="_blank"></a><button class="btn back backBtn" data-t="change"></button></div></section>

<section class="card hidden" id="fileBox"><h2 data-t="step2"></h2><div id="fileHint" class="small"></div>
<div class="row"><button class="btn" id="choose" data-t="choose"></button></div>
<div id="foundBox"><p class="muted small" id="found"></p><div id="files"></div></div>
<details id="typeBox"><summary data-t="type_toggle"></summary><p class="muted small" data-t="type"></p>
<div class="row"><input id="path" style="flex:1;min-width:240px"><button class="btn" id="use" data-t="use"></button></div></details>
<p class="state" id="fileState"></p><div class="sum" id="fileSum"><b id="fileSumText"></b><button class="btn link" id="fileChange" data-t="change_short"></button></div></section>
<section class="card hidden" id="inApp"><h2 data-t="step2"></h2><p id="inAppText" class="muted"></p></section>

<section class="card hidden" id="deviceBox"><h2 data-t="step3"></h2><div class="grid" id="devices"></div><p class="muted small hidden" id="heldNote"></p><div class="sum" id="devSum"><b id="devSumText"></b><button class="btn link" id="devChange" data-t="change_short"></button></div>
<details class="small"><summary data-t="device_help"></summary><p data-t="update_help"></p><a href="https://github.com/chrissotraidis/padmint/releases/latest" target="_blank" rel="noopener" data-t="update"></a></details></section>

<section class="card banner hidden" id="readyBox"><h2 data-t="ready_title"></h2><p id="readyText"></p><div class="row"><a class="btn main" id="readyLink" target="_blank"></a></div><p class="muted small" data-t="ready_or"></p></section>

<section class="card plan hidden" id="planBox"><h2 data-t="plan_title"></h2><div id="plan"></div>
<div class="row" style="margin-top:.8rem"><button class="btn main" id="make" data-t="make" disabled></button></div><p class="why" id="makeWhy"></p>
<p class="bad" id="makeError"></p></section>
</main>

<main id="progress" class="hidden">
<section class="card banner" id="headCard"><div class="headrow"><span id="headArt"></span><div><p class="big" id="making"></p><p class="muted small"><span id="elapsedLabel" data-t="elapsed"></span>: <b id="elapsed"></b> <span id="headPct"></span></p></div></div><div id="headBar"></div></section>
<section class="card"><ul class="steps" id="phases"></ul>
<div class="row" style="margin-top:.8rem"><button class="btn" id="cancel" data-t="cancel"></button><span class="muted small" id="cancelNote" data-t="cancel_note"></span>
<button class="btn hidden" id="again" data-t="again"></button></div></section>
<section class="card hidden" id="finished"></section>
<section class="card"><details id="logBox"><summary><span data-t="log"></span> <span class="muted" id="lineCount"></span></summary>
<pre id="tail"></pre><button class="btn" id="copy" data-t="copy_log"></button></details></section>
</main>
<main id="storage" class="hidden"><div class="sechead"><h2 data-t="nav_storage"></h2></div><p class="note" data-t="st_intro"></p><div id="stBody"></div></main>
<div id="aboutHome"><div class="hidden" id="settingsPanel"><h2 data-t="settings"></h2><div class="setrow"><div class="settxt"><b data-t="set_lang_t"></b><span class="muted" data-t="set_lang_d"></span></div><div class="setctl"><label class="langw"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3 12h18M12 3c2.6 2.6 3.9 5.6 3.9 9s-1.3 6.4-3.9 9c-2.6-2.6-3.9-5.6-3.9-9S9.4 5.6 12 3z" fill="none" stroke="currentColor" stroke-width="1.8"/></svg><select id="lang" aria-label="Language"><option value="en">English</option><option value="es">Español</option><option value="pt">Português</option></select></label></div></div><div id="setBody"></div></div><div class="hidden" id="aboutPanel"><h2 data-t="about_padmint"></h2><div class="who"><div class="mark"><svg viewBox="0 0 64 64" aria-hidden="true"><defs><linearGradient id="pmg2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5ff0b0"/><stop offset="1" stop-color="#14945f"/></linearGradient></defs><rect width="64" height="64" rx="15" fill="url(#pmg2)"/><path fill="#06281a" d="M19 19h26c7.2 0 12.6 6.6 11.2 13.7l-2.1 10.2c-1 4.9-7.1 6.6-10.5 2.9L39 41H25l-4.6 4.8c-3.4 3.7-9.5 2-10.5-2.9L7.8 32.7C6.4 25.6 11.8 19 19 19z"/><path stroke="#5ff0b0" stroke-width="4" stroke-linecap="round" d="M20 26v10M15 31h10"/><path fill="#5ff0b0" d="M37 37c0-6.5 4.8-11 12-11 0 6.5-4.8 11-12 11z"/><path stroke="#06281a" stroke-width="1.8" stroke-linecap="round" d="M39.5 34.5l6.5-6"/></svg></div><div><b><span data-t="who_title"></span> <a href="https://github.com/chrissotraidis" target="_blank" rel="noopener">Kahris</a></b><span class="muted" data-t="who_text"></span></div></div><section class="hero"><p data-t="intro"></p><div class="chips"><span class="chip" data-t="trust_local"></span><span class="chip" data-t="trust_upload"></span><span class="chip" data-t="trust_open"></span></div>
</section>
<section class="about" id="about"><h2 data-t="about_title"></h2><div class="flow"><div><i>1</i><b data-t="flow_1"></b><span data-t="flow_1s"></span></div><div><i>2</i><b data-t="flow_2"></b><span data-t="flow_2s"></span></div><div><i>3</i><b data-t="flow_3"></b><span data-t="flow_3s"></span></div></div>
<div class="explain"><details id="howBox"><summary data-t="how_title"></summary><ol><li data-t="how_1"></li><li data-t="how_2"></li><li data-t="how_3"></li><li data-t="how_4"></li><li data-t="how_5"></li></ol></details>
<details id="whyBox"><summary data-t="why_title"></summary><p data-t="why_1"></p><p data-t="why_2"></p></details></div></section></div></div>
<div class="sheet hidden" id="sheet"><div class="sheetbox" role="dialog" aria-modal="true"><button class="x" id="sheetClose" aria-label="Close">×</button><div id="sheetBody"></div></div></div>
<footer><span class="localnote" data-t="local_note"></span><span><a href="https://github.com/chrissotraidis/padmint/releases/latest" target="_blank" rel="noopener" data-t="update"></a> · <a href="https://github.com/chrissotraidis/padmint" target="_blank" data-t="source"></a> · <a id="reportLink" href="https://github.com/chrissotraidis/padmint/issues" target="_blank" data-t="report"></a></span></footer>
</div></div>
<script>
const T="__TOKEN__";let D=__DATA__,S=D.text;const H={"Content-Type":"application/json","X-PadMint-Token":T};
const $=id=>document.getElementById(id);let file=null,reading=false,sel=null,dev=null,shown=false,fileRequest=0;
const fill=(k,v)=>Object.entries(v||{}).reduce((s,[a,b])=>s.split("{"+a+"}").join(b),S[k]||"");
for(const e of document.querySelectorAll("[data-t]"))e.textContent=S[e.dataset.t]||"";
document.documentElement.lang=D.lang;$("lang").value=D.lang;$("ver").textContent="v"+D.version;$("search").placeholder=S.search_hint||S.search;
$("choose").classList.toggle("hidden",!D.picker);
let last=null;
function texts(){for(const e of document.querySelectorAll("[data-t]"))e.textContent=S[e.dataset.t]||"";document.documentElement.lang=D.lang;$("search").placeholder=S.search_hint||S.search;$("home").setAttribute("aria-label",S.home||"PadMint");vstat()}
$("lang").onchange=async()=>{const lang=$("lang").value,r=await (await fetch("/api/player?lang="+lang,{headers:H})).json();
 if(r.error)return;D=r;S=D.text;texts();history.replaceState(null,"","?token="+T+"&lang="+lang);filters();cards();
 if(sel){const keep={file,dev};const g=game();if(g||app()||waiting())redraw(keep)}
 if(last){shown=false;$("finished").replaceChildren();const r2=await (await fetch("/api/build?lang="+lang,{headers:H})).json();show(r2)}};
function redraw(keep){const was=keep.file,state=$("fileState").textContent;choose(sel);if(was){file=was;$("path").value=was;$("fileState").className="state ok";$("fileState").textContent="✓ "+fill("file_ok",{file:base(was)})}
 if(keep.dev&&game())pickDevice(keep.dev);ready()}
async function post(p,b){const r=await fetch(p,{method:"POST",headers:H,body:JSON.stringify(Object.assign({lang:D.lang},b||{}))});return r.json()}
const base=p=>p.split(/[\\/]/).pop();
function el(tag,text,cls){const e=document.createElement(tag);if(text!=null&&text!=="")e.textContent=text;if(cls)e.className=cls;return e}
const gb=b=>b?(b>=1e9?(b/1e9).toFixed(1)+" GB":Math.max(1,Math.round(b/1e6))+" MB"):"";
const game=()=>D.games.find(g=>g.id==sel),app=()=>D.downloads.find(a=>a.id==sel),waiting=()=>D.later.find(l=>l.id==sel);
let system="";
const title=g=>(g.about||g.name).replace(/\s*\([^)]*\)\s*$/,"");
const systemOf=g=>{const m=(g.about||"").match(/\(([^),]+)/);return m?m[1].replace(/ prototype$/,""):""};
const sortKey=g=>title(g).replace(/^(The|A) /i,"").toLowerCase();
const COLORS={"GameCube":"#6c5ce7","Wii":"#2d9cdb","N64":"#e2463a","PlayStation":"#4b5a6b","Steam":"#2a6fb0","PC":"#d9822b","Xbox":"#2f8f2f"};
const BADGES={"GameCube":"GC","Wii":"Wii","N64":"64","PlayStation":"PS","Steam":"PC","PC":"PC","Xbox":"X"};
// The disc ID's fourth letter is its region: E North America, P Europe, J Japan.
const REGIONS={E:"us",P:"eu",J:"jp"};
function fileHint(g,inputs){const h=$("fileHint");h.replaceChildren(el("b",fill("file_hint",{game:g.about||g.name})));
 const id=g.ids[0]||"",region=id.length>=4&&REGIONS[id[3]];
 if(region)h.append(" ",fill("file_region",{region:S["region_"+region]}));
 const formats=inputs?(inputs.every(i=>(i.formats||[]).length)?[...new Set(inputs.flatMap(i=>i.formats))].map(f=>f.toUpperCase()):[]):g.formats;
 const facts=[formats.length?fill("file_formats",{formats:formats.join(", ")}):"",g.ids.length?fill(id.length==4?"file_code":"file_ids",{ids:g.ids.join(", ")}):""].filter(Boolean);
 if(facts.length)h.append(el("div",facts.join(" · "),"muted"));
 const notes=(inputs||[]).filter(i=>i.description);
 if(notes.length>1){h.append(el("p",S.which_file,"state"));const u=el("ul");for(const i of notes)u.append(el("li",i.description));h.append(u)}
 else if(notes.length){const d=el("details");d.append(el("summary",S.more_file),el("p",notes[0].description,"muted"));h.append(d)}}
const colorOf=x=>COLORS[systemOf(x)]||"#1fa572";
let group="all";const all=()=>[...D.games,...D.downloads,...D.later];
const groupOf=id=>D.games.some(x=>x.id==id)?"build":D.downloads.some(x=>x.id==id)?"download":"later";
const DEVICES={ipad:"iPad",iphone:"iPhone",mac:"Mac"};
let V={done:false,games:{},padmint:null};
const ART=new Set(D.art||[]);
// A release tag's version, wherever it sits in the tag: v0.8.3, touch-v0.1.0, v0.1.0-preview.2.
const tagVersion=t=>{const m=String(t||"").match(/\d+(?:\.\d+)*/);return m?"v"+m[0]:t};
const latest=id=>{const t=(V.games||{})[id];return t?tagVersion(t):t};
const owned=id=>(D.library||[]).some(l=>l.id==id);
const initials=x=>(x.name||"?").replace(/(Pad|Touch)$/,"").slice(0,2).toUpperCase();
function art(x,big){const s=el("span",null,"art"+(big?" big":""));s.style.setProperty("--c",colorOf(x));
 const plain=()=>{s.classList.add("gen");s.textContent=initials(x)};
 if(ART.has(x.id)){const i=el("img");i.alt="";i.src="/art/"+x.id+".png?token="+T;i.onerror=()=>{i.remove();plain()};s.append(i)}else plain();return s}
function devicesOf(x,kind){if(kind=="build")return x.platforms.map(p=>p.short||p.label);const o=x.plays_on||[];
 return [...(o.includes("iphone")&&o.includes("ipad")?["iPhone/iPad"]:o.filter(d=>d!="mac").map(d=>DEVICES[d])),...(o.includes("mac")?["Mac"]:[])]}
function ago(t){const f=new Intl.RelativeTimeFormat(D.lang,{numeric:"auto"}),s=Date.now()/1000-t;if(s<60&&S.just_now)return S.just_now;
 for(const [n,k] of [["year",31536000],["month",2592000],["week",604800],["day",86400],["hour",3600],["minute",60]])if(s>=k)return f.format(-Math.floor(s/k),n);return f.format(0,"minute")}
function vstat(){const a=$("vstat"),newer=!!V.padmint&&cmpv(V.padmint,D.version)>0;
 a.className="vstat"+(newer?" upd":V.padmint?"":" wait")+(V.done&&!V.padmint?" hidden":"");
 a.textContent=newer?fill("pm_update",{version:V.padmint})+" · "+S.up_short+" ›":V.padmint?"✓ v"+D.version:S.checking;a.title=V.padmint&&!newer?S.up_to_date:"";
 a.onclick=newer?openUpdate:null}
const cmpv=(a,b)=>{const x=a.replace(/^v/,"").split(".").map(Number),y=b.replace(/^v/,"").split(".").map(Number);for(let i=0;i<Math.max(x.length,y.length);i++){const d=(x[i]||0)-(y[i]||0);if(d)return d}return 0};
// Where each game is: the iPhones and iPads paired with this Mac, its Applications folder, and copies PadMint built.
let moved=false,I=D.installed||{state:"idle",mac:[],devices:[]},view="mine",shelfSig="",sideSig="";
const ICONS={mine:'<rect x="3.5" y="3.5" width="7" height="7" rx="2"/><rect x="13.5" y="3.5" width="7" height="7" rx="2"/><rect x="3.5" y="13.5" width="7" height="7" rx="2"/><rect x="13.5" y="13.5" width="7" height="7" rx="2"/>',
 updates:'<circle cx="12" cy="12" r="8.5"/><path d="M12 16V8M8.5 11.5L12 8l3.5 3.5"/>',library:'<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>',
 ipad:'<rect x="4.5" y="2.5" width="15" height="19" rx="2.5"/><path d="M11 18.5h2"/>',iphone:'<rect x="6.5" y="2.5" width="11" height="19" rx="2.5"/><path d="M11 18.5h2"/>',
 mac:'<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',android:'<rect x="5" y="8" width="14" height="10" rx="3"/><path d="M8 5l1.5 2.5M16 5l-1.5 2.5"/>',
 storage:'<ellipse cx="12" cy="6" rx="7.5" ry="2.8"/><path d="M4.5 6v12c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8V6M4.5 12c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8"/>',
 built:'<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>',windows:'<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>'};
function ico(k){const s=el("span",null,"ic");s.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+(ICONS[k]||ICONS.built)+'</svg>';return s}
const norm=v=>String(tagVersion(v)||"").replace(/^v/,"");
const onMac=()=>String(D.host||"").startsWith("macos");
const known=id=>all().some(x=>x.id==id);
function copies(id){const out=[],lib=(D.library||[]).filter(l=>l.id==id);
 for(const d of I.devices||[]){const mine=(d.apps||[]).filter(a=>a.game==id);if(!mine.length)continue;const top=mine.map(a=>norm(a.version)).sort((x,y)=>cmpv(y||"0",x||"0"))[0];
  out.push({where:"dev:"+d.id,kind:d.kind,label:d.name,version:top,platform:"ios",away:!d.reachable,seen:d.checked,extra:mine.length-1})}
 for(const a of I.mac||[])if(a.game==id){const b=lib.find(l=>l.platform=="macos"),bv=b?norm(b.version):"";out.push({where:"mac",kind:"mac",label:S.this_mac,version:bv&&a.version&&bv.startsWith(a.version)?bv:norm(a.version),platform:"macos"})}
 for(const l of lib)if(!out.some(c=>c.platform==l.platform))out.push({where:l.platform=="android"?"android":"built",kind:l.platform=="android"?"android":"built",label:fill("built_copy",{device:S["short_"+l.platform]||l.platform}),version:norm(l.version),platform:l.platform,built:true,when:l.when});
 return out}
function stateOf(id){const c=copies(id),v=latest(id),old=v?c.filter(x=>x.version&&cmpv(x.version,v)<0):[];return {copies:c,latest:v,old,stale:old.length>0}}
function mineIds(){const ids=new Set((D.library||[]).map(l=>l.id));for(const d of I.devices||[])for(const a of d.apps||[])ids.add(a.game);for(const a of I.mac||[])ids.add(a.game);return [...ids].filter(known)}
function places(){const out=(I.devices||[]).map(d=>({view:"dev:"+d.id,name:d.name,kind:d.kind,count:new Set((d.apps||[]).map(a=>a.game).filter(known)).size,away:!d.reachable,d}));
 if(onMac())out.push({view:"mac",name:S.this_mac,kind:"mac",count:mineIds().filter(id=>copies(id).some(c=>c.platform=="macos")).length});
 if((D.library||[]).some(l=>l.platform=="android"))out.push({view:"android",name:"Android",kind:"android",count:mineIds().filter(id=>copies(id).some(c=>c.platform=="android")).length});return out}
const fits=(c,v)=>v=="mine"||v=="updates"||(v=="mac"?c.platform=="macos":v=="android"?c.platform=="android":c.where==v);
function inView(id,v){return v=="updates"?stateOf(id).stale:copies(id).some(c=>fits(c,v))}
function viewName(){const p=places().find(d=>d.view==view);return view=="updates"?S.sn_updates:view=="library"?S.library:p?p.name:S.sn_mine}
function whereLine(c,v){const li=el("div",null,"cp"+(c.built?" built":"")+(c.away?" away":"")),stale=!!v&&!!c.version&&cmpv(c.version,v)<0,bits=[c.version?"v"+c.version:c.platform=="macos"?S.in_apps:S.version_unknown];
 if(c.built&&c.when)bits.push(fill("built_when",{when:ago(c.when)}));
 if(c.away&&c.seen&&I.state=="ready")bits.push(fill("seen",{when:ago(c.seen)}));
 if(c.built&&c.platform=="ios"&&I.state=="ready"&&(I.devices||[]).some(d=>d.reachable))bits.push(S.not_on_devices);
 if(c.platform=="android")bits.push(S.android_unseen);if(c.extra)bits.push(fill("n_copies",{n:c.extra+1}));
 const ver=bits.shift(),rest=bits.join(" · ");li.append(ico(c.kind),el("b",c.label),el("span",ver,"vv"+(stale?" old":"")));if(rest)li.append(el("span",rest,"d"));if(stale)li.append(el("span",fill("new_version",{version:v}),"badge upd"));return li}
function copiesBox(x){const b=$("copies"),st=x&&stateOf(x.id);if(!st||!st.copies.length){b.classList.add("hidden");b.replaceChildren();return}
 b.replaceChildren(el("h3",S.your_copies),...st.copies.map(c=>whereLine(c,st.latest)));b.classList.remove("hidden")}
function mgRow(id,i){const x=all().find(y=>y.id==id),st=stateOf(id),shown=st.copies.filter(c=>fits(c,view)),old=st.latest?shown.filter(c=>c.version&&cmpv(c.version,st.latest)<0):[],r=el("div",null,"mg"+(old.length?" stale":""));r.style.setProperty("--c",colorOf(x));r.style.setProperty("--i",Math.min(i,20));
 const body=el("div",null,"body"),where=el("div",null,"where"),tl=el("div",null,"tl");tl.append(el("span",x.about?title(x):x.name,"t"),el("span",x.name+(systemOf(x)?" · "+systemOf(x):""),"s"));body.append(tl);
 where.append(...shown.map(c=>whereLine(c,st.latest)));body.append(where);
 const side=el("div",null,"side");
 if(old.length){const g=D.games.find(y=>y.id==id),p=g&&g.platforms.find(q=>q.id==old[0].platform),b=el("button",fill("update_to",{version:st.latest}),"btn main small");b.onclick=e=>{e.stopPropagation();choose(id);if(p)pickDevice(p.id)};side.append(b)}
 else if(st.latest&&shown.some(c=>c.version))side.append(el("span","✓ "+S.latest_short,"okt"));else if(shown.length)side.append(el("span","✓ "+S.installed,"okt soft"));
 side.append(el("span","›","chev"));r.append(art(x),body,side);r.onclick=()=>choose(id);return r}
function shelf(){const busy=!!sel||view=="library"||view=="storage"||!$("progress").classList.contains("hidden");$("shelf").classList.toggle("hidden",busy);if(busy)return;
 const ids=mineIds().filter(id=>inView(id,view)).sort((a,b)=>sortKey(all().find(x=>x.id==a)).localeCompare(sortKey(all().find(x=>x.id==b))));
 const sig=JSON.stringify([ids,view,I,V.done&&V.games,D.lang,D.library]);if(sig==shelfSig)return;const first=!shelfSig;shelfSig=sig;
 const p=places().find(d=>d.view==view),checking=I.state!="ready";$("shelfTitle").textContent=viewName();
 $("shelfSub").textContent=view=="mine"?(ids.length&&V.done?fill(ids.some(id=>stateOf(id).stale)?"mine_stats":"mine_stats_ok",{games:ids.length,updates:ids.filter(id=>stateOf(id).stale).length}):S.mine_note):view=="updates"?(V.done?(ids.length?S.updates_note:""):S.checking):view=="mac"?S.mac_note:view=="android"?S.android_note:p?[p.d.model,p.away?(p.d.checked?fill("seen",{when:ago(p.d.checked)}):S.device_away):S.device_live].filter(Boolean).join(" · "):"";
 $("shelfNote").textContent=checking?S.checking_devices:I.checked?fill("checked",{when:ago(I.checked)}):"";$("lookAgain").title=S.check_again_tip;$("lookAgain").setAttribute("aria-label",S.check_again_tip);$("shelfNote").classList.toggle("loading",checking);
 $("lookAgain").classList.toggle("hidden",checking||view=="updates"||view=="android"||(!I.xcode&&!onMac()));
 const parts=[];if(view=="mine"&&onMac()&&I.state=="ready"&&!I.xcode)parts.push(el("p",S.no_xcode_note,"note"));
 const list=rows=>{const l=el("div",null,"shelf"+(first?"":" settled"));l.append(...rows.map(mgRow));return l};
 if(!ids.length)parts.push(el("p",view=="updates"?(V.done?"✓ "+S.no_updates:S.checking):view=="mine"?S.empty_mine:S.empty_device,"empty"));
 else if(view=="mine"&&V.done){const up=ids.filter(id=>stateOf(id).stale),rest=ids.filter(id=>!stateOf(id).stale);
  if(up.length)parts.push(...fold("up",S.sec_updates+" · "+up.length,list(up)));if(rest.length)parts.push(...fold("rest",(up.length?S.sec_current:S.sec_all)+" · "+rest.length,list(rest)))}
 else parts.push(list(ids));
 $("shelfList").replaceChildren(...parts)}
function side(){const mine=mineIds(),ups=mine.filter(id=>stateOf(id).stale).length,running=last&&last.state=="running",cur=sel||!$("progress").classList.contains("hidden")?null:view,pl=places();
 const sig=JSON.stringify([mine.length,ups,V.done,cur,pl.map(d=>[d.view,d.name,d.count,d.away]),running&&[last.game,overall(last)],D.lang]);if(sig==sideSig)return;sideSig=sig;
 const item=(v,k,label,count,extra)=>{const b=el("button",null,"sn"+(cur==v?" on":"")+(extra?" "+extra:""));b.append(ico(k),el("span",label,"l"));if(count!==""&&count!=null)b.append(el("span",String(count),"c"));b.onclick=()=>go(v);return b};
 const parts=[];
 if(running){const g=D.games.find(x=>x.id==last.game)||{name:last.game},b=el("button",null,"sn live");b.append(el("span",null,"ic spin"),el("span",fill("making",{name:g.name,device:last.device||""}),"l"),el("span",overall(last)+"%","c"));b.onclick=()=>{watch=true;show(last);scrollTo({top:0})};parts.push(b)}
 parts.push(el("div",S.sn_library,"sh"),item("mine","mine",S.sn_mine,mine.length||""),item("updates","updates",S.sn_updates,V.done?(ups||""):"",ups?"hot":""),item("library","library",S.sn_browse,all().length));
 if(pl.length){parts.push(el("div",S.sn_devices,"sh"));for(const d of pl)parts.push(item(d.view,d.kind,d.name,d.count||"",d.away?"away":""))}
 parts.push(el("div","","sh"),item("storage","storage",S.nav_storage,""));$("sidenav").replaceChildren(...parts)}
async function seen(fresh){try{const r=await (await fetch("/api/installed"+(fresh?"?fresh=1":""),{headers:H})).json();if(r.error)return;I=r;if(!moved&&!sel&&(view=="mine"||view=="library")){const n=mineIds().length;if(n)view="mine";else if(r.state=="ready")view="library"}layout();if(view=="library"&&!sel&&r.state=="ready")cards();if(sel)hero(all().find(x=>x.id==sel));if(r.state!="ready")setTimeout(()=>seen(false),900)}catch(e){}}
function hero(x){const h=$("hero");if(!x){h.classList.add("hidden");h.replaceChildren();copiesBox(null);return}
 const kind=groupOf(x.id),body=el("div",null,"hbody"),facts=el("div",null,"facts"),v=latest(x.id),st=stateOf(x.id);h.style.setProperty("--c",colorOf(x));
 body.append(el("h2",x.about?title(x):x.name),el("p",x.name+(systemOf(x)?" · "+fill("original",{system:systemOf(x)}):""),"muted"));
 if(v)facts.append(el("span",fill("latest",{version:v}),"fact"+(st.stale?" new":"")));
 
 for(const d of devicesOf(x,kind))facts.append(el("span",d,"fact"));
 if(kind=="build"&&x.setup)facts.append(el("span",S["setup_"+x.setup],"fact"));
 body.append(facts);h.replaceChildren(art(x,true),body);h.classList.remove("hidden");copiesBox(x)}
async function versions(){try{const r=await (await fetch("/api/versions",{headers:H})).json();V=r;vstat();
 if(r.done){cards();if(sel)hero(all().find(x=>x.id==sel))}else{layout();setTimeout(versions,1200)}}catch(e){}}


for(const b of document.querySelectorAll(".tab"))b.onclick=()=>{group=b.dataset.g;cards()};
function filters(){const systems=[...new Set(all().map(systemOf).filter(Boolean))].sort();
 $("filters").replaceChildren(...["",...systems].map(s=>{const b=el("button",s||S.all,"filter"+(s==system?" on":""));b.onclick=()=>{system=s;filters();cards()};return b}))}

const size=b=>b>=1e9?(b/1e9).toFixed(b>=1e11?0:1)+" GB":b>=1e6?Math.round(b/1e6)+" MB":b>0?Math.max(1,Math.round(b/1e3))+" KB":"0 KB";
function toast(text){const t=el("div",text,"toast");document.body.append(t);setTimeout(()=>t.remove(),2800)}
function lockPage(on){const h=document.documentElement;if(h&&h.classList)h.classList.toggle("locked",on)}
function sheet(...nodes){$("sheetBody").replaceChildren(...nodes);$("sheet").classList.remove("hidden");lockPage(true)}
function closeSheet(){for(const id of ["aboutPanel","settingsPanel"])if($(id).parentNode==$("sheetBody"))$("aboutHome").append($(id));$("sheet").classList.add("hidden");lockPage(false)}
$("sheetClose").onclick=closeSheet;$("sheet").onclick=e=>{if(e.target==$("sheet"))closeSheet()};
$("aboutOpen").onclick=$("aboutSide").onclick=()=>{$("howBox").open=$("whyBox").open=true;$("aboutPanel").classList.remove("hidden");sheet($("aboutPanel"))};
function nav(){side()}

function intro(){const busy=!!sel||view!="library"||!$("progress").classList.contains("hidden")||!$("storage").classList.contains("hidden");
 $("intro").classList.toggle("hidden",busy||mineIds().length>0)}
// PadMint updates itself where it can, else the button opens the download page.
function openSettings(){const row=(t,d,...ctl)=>{const r=el("div",null,"setrow"),tx=el("div",null,"settxt"),c=el("div",null,"setctl");tx.append(el("b",t),el("span",d,"muted"));c.append(...ctl);r.append(tx,c);return r},rows=[];
 const newer=!!V.padmint&&cmpv(V.padmint,D.version)>0;let vb;if(newer){vb=el("button",fill("pm_update",{version:V.padmint}),"btn main small");vb.onclick=()=>{closeSheet();openUpdate()}}else vb=el("span",V.padmint?"✓ "+S.up_to_date:S.checking,"okt");
 rows.push(row(S.set_version_t,"v"+D.version,vb));
 const ds=I.devices||[],look=el("button",S.look_again,"btn small");look.onclick=()=>{closeSheet();seen(true)};
 rows.push(row(S.set_devices_t,ds.length?fill("here_devices",{devices:ds.map(d=>d.name).join(", ")}):onMac()?(I.xcode?S.here_no_devices:S.here_no_xcode):S.set_devices_off,...(onMac()?[look]:[])));
 rows.push(row(S.set_saved_t,D.folder));
 const st=el("button",S.nav_storage,"btn small");st.onclick=()=>{closeSheet();go("storage")};rows.push(row(S.set_storage_t,S.set_storage_d,st));
 const ab=el("button",S.about_padmint,"btn small"),rep=el("a",S.report,"btn small");ab.onclick=()=>{closeSheet();$("aboutOpen").onclick()};rep.href="https://github.com/chrissotraidis/padmint/issues";rep.target="_blank";rep.rel="noopener";
 rows.push(row(S.set_help_t,S.set_help_d,ab,rep));$("setBody").replaceChildren(...rows);$("settingsPanel").classList.remove("hidden");sheet($("settingsPanel"))}
function openUpdate(){const v=V.padmint;if(!D.self_update){window.open("https://github.com/chrissotraidis/padmint/releases/latest","_blank");return}
 const head=el("div",null,"upd-head");head.append(markIcon(),el("h2",fill("up_title",{version:v})));
 const state=el("div"),go=el("button",S.up_now,"btn main");go.onclick=async()=>{go.disabled=true;const r=await post("/api/update");if(r.error){state.replaceChildren(el("p",r.error,"bad"));go.disabled=false;return}watchUpdate(state,go)};
 const row=el("div",null,"row");row.append(go);sheet(head,el("p",S.up_text),state,row)}
function markIcon(){const i=el("div",null,"mark");i.innerHTML=$("home").querySelector(".mark").innerHTML;return i}
async function watchUpdate(state,go){const r=await (await fetch("/api/update",{headers:H})).json();
 if(r.state=="downloading"||r.state=="installing"){state.replaceChildren(el("p",r.state=="installing"?S.up_installing:fill("up_downloading",{percent:r.percent||0}),"state"),bar(r.state=="installing"?100:r.percent||0));setTimeout(()=>watchUpdate(state,go),400);return}
 if(r.state=="failed"){const a=el("a",S.up_manual,"btn");a.href="https://github.com/chrissotraidis/padmint/releases/latest";a.target="_blank";state.replaceChildren(el("p",fill("up_failed",{error:r.error||""}),"bad"),a);go.disabled=false;return}
 if(r.state=="ready"){state.replaceChildren(el("p","✓ "+fill("up_installed",{version:r.version}),"state ok"));go.textContent=S.up_restart;go.disabled=false;
  go.onclick=async()=>{go.disabled=true;const x=await post("/api/restart");if(x.error){state.append(el("p",x.error,"bad"));go.disabled=false;return}
   state.replaceChildren(el("p",S.up_restarting,"muted loading"));const wait=async()=>{try{const ok=await fetch("/api/versions",{headers:H});if(ok.ok){location.reload();return}}catch(e){}setTimeout(wait,700)};setTimeout(wait,1200)}}}
// Storage: what PadMint keeps in its folder, and removing what it no longer needs.
let ST=null;
function storageView(){watch=false;sel=null;view="storage";$("form").classList.add("hidden");$("progress").classList.add("hidden");$("storage").classList.remove("hidden");nav("storage");intro();scrollTo({top:0});loadStorage(true)}
async function loadStorage(fresh){const r=await (await fetch("/api/storage"+(fresh?"?fresh=1":""),{headers:H})).json();if($("storage").classList.contains("hidden"))return;ST=r;renderStorage();if(r.state=="measuring"||r.state=="idle")setTimeout(()=>loadStorage(false),900)}
function nameOf(i){const g=i.game&&all().find(x=>x.id==i.game);return g?(g.about?title(g):g.name):i.kind=="padmint"?"PadMint":i.name||i.id}
function stRow(i){const r=el("div",null,"st-row"),g=i.game&&all().find(x=>x.id==i.game),port=g?g.name:i.name||i.id,game=g&&g.about?title(g):"";let t,sub;
 if(i.kind=="game"){const v=latest(i.game);t=port+" "+(i.version?tagVersion(i.version):"");sub=[game,i.reason=="current"&&v&&v!=tagVersion(i.version)?fill("st_r_behind",{version:v}):S["st_r_"+(i.reason=="current"?"newest":i.reason)]]}
 else if(i.kind=="apps"){t=fill("st_kind_app",{name:port});sub=[game,S.st_app_note]}
 else if(i.kind=="cache"){t=fill("st_kind_extra",{name:port});sub=[game,S.st_extra_note]}
 else if(i.kind=="tool"){t=i.name;sub=[i.reason=="unused"?S.st_r_unused:S.st_r_tool]}
 else{t="PadMint "+(i.version||"");sub=[i.reason=="current"?S.st_r_newest:S.st_r_old]}
 const a=g?art(g):el("span",i.kind=="tool"?"⚙":i.kind=="padmint"?"P":"⇣","art gen glyph"),body=el("div",null,"body");body.append(el("span",t,"t"),el("span",sub.filter(Boolean).join(" · "),"s"));
 r.append(a,body,el("span",size(i.size),"sz"));if(i.removable){const b=el("button",S.st_remove,"btn small danger");b.onclick=()=>confirmRemove([i]);r.append(b)}return r}
function renderStorage(){const box=$("stBody");if(!ST||ST.state!="ready"){box.replaceChildren(el("p",ST&&ST.state=="failed"?ST.error:S.st_calc,ST&&ST.state=="failed"?"bad":"muted loading"));return}
 const items=ST.items,bulk=items.filter(i=>i.removable&&i.reason!="cache"),gone=bulk.reduce((a,i)=>a+i.size,0),cache=items.filter(i=>i.reason=="cache");
 const sum=el("div",null,"st-sum"),body=el("div",null,"body");body.append(el("div",size(ST.total),"big"),el("span",fill("st_folder_line",{folder:ST.folder,free:size(ST.free)}),"s"));const cacheSize=cache.reduce((a,i)=>a+i.size,0);
 const meter=el("div",null,"st-meter"),keep=el("i",null,"keep"),old=el("i",null,"old"),cch=el("i",null,"cch"),span=Math.max(1,ST.total);keep.style.width=(100*(ST.total-gone-cacheSize)/span)+"%";old.style.width=(100*gone/span)+"%";cch.style.width=(100*cacheSize/span)+"%";meter.append(keep,old,cch);
 const lg=el("div",null,"legend"),l1=el("span",S.st_in_use+" · "+size(ST.total-gone-cacheSize)),l2=el("span",S.st_safe+" · "+size(gone)),l3=el("span",S.st_cache+" · "+size(cacheSize));l1.style.setProperty("--c","var(--mint)");l2.style.setProperty("--c","var(--warn)");l3.style.setProperty("--c","#5bb8f0");lg.append(l1,l2);if(cacheSize)lg.append(l3);body.append(meter,lg);
 const side=el("div",null,"side");if(gone){const b=el("button",fill("st_free_up",{size:size(gone)}),"btn main");b.onclick=()=>confirmRemove(bulk);side.append(b)}else side.append(el("span","✓ "+S.st_nothing,"badge ok"));
 sum.append(body,side);const parts=[sum];
 const group=(key,list,note)=>{if(!list.length)return;const h=el("div",null,"sechead");h.append(el("h2",S[key]),el("span",size(list.reduce((a,i)=>a+i.size,0)),"muted small"));parts.push(h);if(note)parts.push(el("p",S[note],"note"));const l=el("div",null,"list");l.append(...list.sort((a,b)=>b.size-a.size).map(stRow));parts.push(l)};
 group("st_old",items.filter(i=>i.removable&&i.reason!="cache"&&i.reason!="unused"),"st_old_note");group("st_tools",items.filter(i=>i.reason=="unused"));group("st_cache",cache,"st_cache_note");
 const kept=items.filter(i=>!i.removable);if(kept.length){const d=el("details",null,"kept"),s=el("summary",fill("st_kept_sum",{games:kept.filter(i=>i.kind=="game").length,tools:kept.filter(i=>i.kind=="tool").length,size:size(kept.reduce((a,i)=>a+i.size,0))}));const l=el("div",null,"list");l.append(...kept.sort((a,b)=>b.size-a.size).map(stRow));d.append(s,el("p",S.st_kept_note,"note"),l);parts.push(d)}
 const un=el("details",null,"kept");un.append(el("summary",S.st_uninstall),el("p",fill("st_uninstall_text",{folder:ST.folder}),"note"));parts.push(un);
 box.replaceChildren(...parts)}
function confirmRemove(list){const total=list.reduce((a,i)=>a+i.size,0),go=el("button",fill("st_remove_size",{size:size(total)}),"btn main"),no=el("button",S.st_cancel,"btn ghost"),row=el("div",null,"row");
 const ul=el("ul",null,"tools");for(const i of list.slice(0,6)){const li=el("li");li.append(el("span",nameOf(i)+(i.version?" "+i.version:"")),el("span",size(i.size),"muted"));ul.append(li)}if(list.length>6)ul.append(el("li","+"+(list.length-6),"muted"));
 no.onclick=closeSheet;go.onclick=async()=>{go.disabled=true;no.disabled=true;go.textContent=S.st_removing;const r=await post("/api/remove",{ids:list.map(i=>i.id)});closeSheet();
  if(r.error){toast(r.error);return}toast(fill("st_freed",{size:size(r.freed)}));ST=null;renderStorage();loadStorage(true)};
 row.append(go,no);sheet(el("h2",fill("st_confirm_title",{size:size(total)})),el("p",fill("st_confirm_text",{folder:ST.folder})),ul,row)}


function kindName(c){return {ipad:"iPad",iphone:"iPhone",mac:"Mac",android:"Android"}[c.kind]||S.built_short}
function here(){const h=$("here"),show=!sel&&view=="library";h.classList.toggle("hidden",!show);if(!show)return;const parts=[];
 if(onMac()){parts.push(fill("here_mac",{build:D.games.length,apps:D.downloads.length}));const ds=(I.devices||[]);
  if(ds.length)parts.push(fill("here_devices",{devices:ds.map(d=>d.name).join(", ")}));else if(I.state=="ready")parts.push(I.xcode?S.here_no_devices:S.here_no_xcode)}
 else if(!D.picker)parts.push(S.here_phone);
 else{const names=D.games.map(g=>g.about?title(g):g.name).join(", ");parts.push(fill(names?"here_other":"here_other_none",{names,apps:D.downloads.length,mac:D.later.length}))}
 h.textContent=parts.join(" ")}
function fold_text(v){return String(v||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}
function fold(key,label,body){const open=localStorage.getItem("pm.fold."+key)!="1",h=el("button",null,"group fold"+(open?" open":""));h.append(el("span","›","tw"),el("span",label));h.setAttribute("aria-expanded",open);body.classList.toggle("hidden",!open);
 h.onclick=()=>{const now=body.classList.toggle("hidden");h.classList.toggle("open",!now);h.setAttribute("aria-expanded",!now);localStorage.setItem("pm.fold."+key,now?"1":"0")};return [h,body]}
function row(x,i){const kind=groupOf(x.id),b=el("button",null,"item "+kind);b.style.setProperty("--c",colorOf(x));b.style.setProperty("--i",Math.min(i||0,24));
 b.title=systemOf(x)?fill("original",{system:systemOf(x)}):"";const body=el("span",null,"body"),meta=[devicesOf(x,kind).join(", ")];
 if(kind=="build"&&x.ready){const on=x.platforms.filter(p=>x.ready.platforms.includes(p.id)).map(p=>p.short||p.label);if(on.length)meta.push(fill("ready_tag",{devices:on.join(", ")}))}
 if(kind=="build"&&x.setup&&x.setup!="easy")meta.push(S["setup_"+x.setup]);if(kind=="later"&&x.text)b.title=x.text;
 const line=[x.name+(systemOf(x)?" · "+systemOf(x):""),...meta].filter(Boolean).join(" · ");body.append(el("span",x.about?title(x):x.name,"t"),el("span",line,"s"));body.title=line;
 const side=el("span",null,"side"),st=stateOf(x.id),v=st.latest,where=[...new Set(st.copies.map(kindName))].join(" · ");
 if(kind=="later"){}else if(st.stale){const o=st.old.map(c=>c.version).sort(cmpv)[0];side.append(el("span",(o?"v"+o+" → ":"")+v,"own upd"))}
 else if(st.copies.length)side.append(el("span","✓ "+fill("lib_on",{where}),"own"));else if(mineIds().length)side.append(el("span",S.lib_not_installed,"own none"));
 side.append(el("span",kind=="later"&&x.status?S["status_"+x.status]:kind=="later"&&x.tag?x.tag:S[kind=="build"&&st.stale?"act_update":{build:"act_build",download:"act_download",later:"act_later"}[kind]],"act "+kind+(kind=="build"&&st.stale?" upd":"")));
 b.append(art(x),body,side);b.onclick=()=>choose(x.id);return b}
function cards(){const q=$("search").value.trim().toLowerCase();
 const words=fold_text(q).split(" ").filter(Boolean),match=x=>{const hay=fold_text([x.name,x.about,title(x),systemOf(x),...(x.platforms||[]).map(p=>p.label)].filter(Boolean).join(" "));return words.every(w=>hay.includes(w))&&(!system||systemOf(x)==system)};
 const order=a=>a.sort((x,y)=>sortKey(x).localeCompare(sortKey(y)));
 const G={build:order(D.games.filter(match)),download:order(D.downloads.filter(match)),later:order(D.later.filter(match))};
 G.all=order([...G.build,...G.download,...G.later]);G.missing=mineIds().length?G.all.filter(x=>groupOf(x.id)!="later"&&!copies(x.id).length):[];
 if(sel){group="all";G.all=all().filter(x=>x.id==sel)}
 else if(!G[group].length){const k=["all","build","download","later","missing"].find(k=>G[k].length);if(k)group=k}
 $("finder").classList.toggle("hidden",!!sel);$("changeGame").classList.toggle("hidden",!sel);$("tabs").classList.toggle("hidden",!!sel);$("pills").classList.toggle("hidden",!!sel);const one=sel&&all().find(x=>x.id==sel);$("gamePage").classList.toggle("hidden",!(one&&one.page));if(one&&one.page){$("gamePageLink").href=one.page;$("gamePageLink").textContent=fill("game_page",{name:one.name})+" ↗"}
 for(const b of document.querySelectorAll(".tab")){b.classList.toggle("on",b.dataset.g==group);b.setAttribute("aria-selected",b.dataset.g==group);b.querySelector(".n").textContent=G[b.dataset.g].length;b.classList.toggle("hidden",b.dataset.g=="missing"?!G.missing.length&&group!="missing":b.dataset.g!="all"&&!all().some(x=>groupOf(x.id)==b.dataset.g))}$("laterHead").textContent=onMac()?S.later_head:S.needs_mac_head;here();
 $("groupNote").textContent=sel?"":S[{all:D.later.length?(onMac()?"all_note":"all_note_off_mac"):"all_note_plain",build:"builds",download:"no_build",later:onMac()?"later_note":"needs_mac_note",missing:"missing_note"}[group]]+(onMac()&&(group=="all"||group=="build")&&D.games.some(g=>g.setup)?" "+S.start_note:"");
 $("pickTitle").textContent=S.library;$("pickTitle").classList.toggle("hidden",!!sel);$("pickCard").classList.toggle("hidden",!sel&&view!="library");$("changeGame").textContent="← "+viewName();hero(sel?all().find(x=>x.id==sel):null);
 $("list").replaceChildren(...(sel?[]:G[group].map((x,i)=>row(x,i))));$("list").classList.toggle("hidden",!!sel||!G[group].length);$("list").classList.toggle("settled",listShown);listShown=true;
 $("noMatch").classList.toggle("hidden",!!G[group].length);layout()}
function back(top){++fileRequest;reading=false;sel=null;file=null;dev=null;for(const id of ["fileBox","deviceBox","planBox","dlBox","readyBox","laterBox","inApp"])$(id).classList.add("hidden");cards();if(top||view!="library")scrollTo({top:0});else $("pickCard").scrollIntoView({behavior:"smooth"})}
let listShown=false;
function layout(){intro();shelf();side()}
function go(v){moved=true;view=v;if(v=="storage"){closeSheet();storageView();return}home(true)}
function home(keep){if(!keep)view=(mineIds().length?"mine":"library");$("storage").classList.add("hidden");closeSheet();if(last&&last.state=="running"){watch=false;$("progress").classList.add("hidden");$("form").classList.remove("hidden");back(true);now(last);return}
 last=null;shown=false;$("progress").classList.add("hidden");$("form").classList.remove("hidden");$("finished").replaceChildren();$("finished").classList.add("hidden");
 $("cancel").disabled=false;$("logBox").open=false;$("makeError").textContent="";$("reportLink").href="https://github.com/chrissotraidis/padmint/issues";
 $("search").value="";system="";group="all";watch=true;now(null);filters();back(true)}
$("home").onclick=e=>{e.preventDefault();home()};$("lookAgain").onclick=()=>seen(true);$("home").setAttribute("aria-label",S.home||"PadMint");
$("settingsSide").onclick=openSettings;{const lc=$("lang").onchange;$("lang").onchange=async()=>{await lc();if($("settingsPanel").parentNode==$("sheetBody"))openSettings()}}$("search").oninput=cards;document.onkeydown=e=>{if(e.key=="Escape"&&!$("sheet").classList.contains("hidden")){closeSheet();return}const t=e.target;if(t&&t.closest&&t.closest("input,textarea,select,[contenteditable]"))return;const find=(e.key=="f"&&(e.metaKey||e.ctrlKey))||e.key=="/",typed=e.key.length==1&&!e.metaKey&&!e.ctrlKey&&!e.altKey&&/\S/.test(e.key);if(!find&&!typed)return;if(!$("sheet").classList.contains("hidden")||!$("progress").classList.contains("hidden"))return;if(sel)back(true);if(view!="library")go("library");const box=$("search");box.focus();if(find){e.preventDefault();box.select()}};$("changeGame").onclick=back;for(const b of document.querySelectorAll(".backBtn"))b.onclick=back;
function choose(id){++fileRequest;reading=false;sel=id;file=null;dev=null;editFile=editDev=false;$("fileState").textContent="";$("path").value="";cards();const g=game(),a=app(),w=waiting();
 $("laterBox").classList.toggle("hidden",!w);
 if(w){$("laterName").textContent=w.name;$("laterAbout").textContent=[systemOf(w)?fill("original",{system:systemOf(w)}):"",(w.plays_on||[]).length?fill("plays_on",{devices:(w.plays_on.includes("iphone")&&w.plays_on.includes("ipad")?["iPhone/iPad"]:w.plays_on.filter(d=>d!="mac").map(d=>DEVICES[d])).concat(w.plays_on.includes("mac")?["Mac"]:[]).join(", ")}):""].filter(Boolean).join(" · ");$("laterText").textContent=w.text;$("laterLink").href=w.link;$("laterLink").textContent=fill("later_link",{name:w.name});scrollTo({top:0})}
 $("dlBox").classList.toggle("hidden",!a);
 $("readyBox").classList.add("hidden");if(g&&g.ready){$("readyText").textContent=g.ready.text;$("readyLink").href=g.ready.url;$("readyLink").textContent=fill("ready_link",{devices:g.platforms.filter(p=>g.ready.platforms.includes(p.id)).map(p=>p.short||p.label).join(", ")})}
 if(a){$("dlName").textContent=a.name;$("dlIntro").textContent=a.intro;$("dlSteps").replaceChildren(...a.steps.map(s=>linked(s)));
  const l=el("a",a.guide);l.href=a.guide;l.target="_blank";$("dlGuide").replaceChildren(S.guide+": ",l);scrollTo({top:0})}
 for(const id of ["fileBox","deviceBox","planBox"])$(id).classList.add("hidden");$("inApp").classList.add("hidden");if(!g)return;
 if(g.needs_file){$("fileBox").classList.remove("hidden");
  fileHint(g,null);showFiles([]);loadFiles(g.id)}
 else{$("inAppText").textContent=fill("file_in_app",{name:g.name});$("inApp").classList.remove("hidden")}
 $("deviceBox").classList.remove("hidden");$("devices").replaceChildren(...g.platforms.map(p=>{const b=el("button",null,"pick");b.append(el("b",p.label));b.onclick=()=>pickDevice(p.id);b.dataset.id=p.id;return b}),
  ...(g.held||[]).map(h=>{const b=el("button",null,"pick");b.append(el("b",h.label),el("span",h.tag));b.disabled=true;b.setAttribute("aria-describedby","heldNote");return b}));
 const held=g.held||[];$("heldNote").classList.toggle("hidden",!held.length);if(held.length){const l=el("a",fill("later_link",{name:g.name}));l.href=g.page;l.target="_blank";$("heldNote").replaceChildren(held.map(h=>h.text).join(" ")+" ",l)}
 if(g.platforms.length==1)pickDevice(g.platforms[0].id);scrollTo({top:0});ready()}
let filesRequest=0;
function showFiles(files){$("foundBox").classList.toggle("hidden",!files.length);$("found").textContent=fill("found",{folder:D.folder});
 $("files").replaceChildren(...files.map(f=>{const b=el("button",null,"btn file");b.append(el("b",base(f)),el("span","→","muted"));b.title=f;b.onclick=()=>useFile(f);return b}))}
async function loadFiles(id){const request=++filesRequest;try{const r=await (await fetch("/api/files?game="+encodeURIComponent(id),{headers:H})).json();
 if(request==filesRequest&&sel==id)showFiles(r.files||[])}catch(e){}}
let planRequest=0;
async function pickDevice(id){const request=++planRequest;editDev=false;blocked=true;planning=true;dev=id;ready();for(const b of $("devices").children)b.classList.toggle("on",b.dataset.id==id);const rg=game();$("readyBox").classList.toggle("hidden",!(rg&&rg.ready&&rg.ready.platforms.includes(id)));$("planBox").classList.remove("hidden");$("plan").replaceChildren(el("p",fill("plan_loading",{name:(game()||{}).name||""}),"muted loading"));
 const selected=sel;try{const r=await (await fetch("/api/plan?game="+selected+"&platform="+id+"&lang="+D.lang+(file?"&disc="+encodeURIComponent(file):""),{headers:H})).json();if(request!=planRequest||dev!=id||sel!=selected)return;planning=false;showPlan(r);ready()}catch(e){if(request!=planRequest||dev!=id||sel!=selected)return;planning=false;$("plan").replaceChildren(el("p",String(e),"bad"));ready()}}
let blocked=false,planning=false;
function copyLine(line){const c=el("div",null,"cmd"),btn=el("button",S.copy);c.append(el("code",line),btn);
 btn.onclick=async()=>{try{await navigator.clipboard.writeText(line);btn.textContent=S.copied;setTimeout(()=>btn.textContent=S.copy,1500)}catch(e){getSelection().selectAllChildren(c.firstChild)}};return c}
function showPlan(p){const g=game(),box=$("plan");box.replaceChildren();if(p.error){box.append(el("p",p.error,"bad"));return}
 if(g.needs_file&&p.inputs)fileHint(g,p.inputs);
 if(p.output)box.append(el("div",p.output,"out"));
 blocked=p.needs.some(n=>!n.ok);
 const m=p.mac_setup,lines=m?[m.brew_line,...m.other].filter(Boolean):[];
 if(p.needs.length||lines.length){const s=el("div",null,"setup-box");s.append(el("p",S.plan_needs,"state"));
  if(p.needs.length){const u=el("ul",null,"tools");for(const n of p.needs){const li=el("li"),name=el("span",n.label);
    if(n.only&&n.only.length)name.append(el("span"," "+fill("only_for",{formats:n.only.map(f=>f.toUpperCase()).join(", ")}),"muted"));
    li.append(name,el("span",n.ok?S.needs_ok:S.needs_missing,n.ok?"ok":"bad"));u.append(li);
    if(!n.ok&&!(n.brew&&lines.length)){const d=linked(n.note,"li");d.className="detail";if(n.command)d.append(copyLine(n.command));u.append(d)}}s.append(u)}
  if(lines.length){s.append(el("p",S.before_title,"state"),linked(m.homebrew?S.before_hint:S.before_brew,"p"));
   if(m.homebrew&&m.packages.length){const k=el("div",null,"pks");for(const x of m.packages)k.append(el("span",(x.ok?"✓ ":"✗ ")+x.name,"pk"+(x.ok?"":" no")));s.append(k)}
   for(const line of lines)s.append(copyLine(line))}
  if(blocked||(m&&m.brew_line)){const again=el("button",S.check_again,"btn");again.onclick=()=>pickDevice(dev);const r=el("div",null,"row");r.append(again);s.append(r)}box.append(s)}
 const o=el("ol");const repo=p.repo.replace("https://","");o.append(el("li",fill("plan_source",{name:g.name,repo})));
  if(p.tools.length){const get=p.tools.filter(t=>!t.here),total=get.every(t=>t.size)?get.reduce((a,t)=>a+t.size,0):0,li=el("li",S.plan_tools+(total?" ("+gb(total)+")":""));
  const d=el("details"),u=el("ul",null,"tools");d.append(el("summary",S.details));
  for(const t of p.tools){const r=el("li");r.append(el("span",t.name+" "+t.version+" · "+fill("from",{host:t.source})),el("span",t.here?S.tool_here:gb(t.size),t.here?"ok":"muted"));u.append(r)}
  d.append(u,el("p",fill("tools_folder",{folder:p.tools_folder}),"muted small"));li.append(d);o.append(li)}if(p.app)o.append(el("li",fill("plan_app",{name:g.name})));
 o.append(el("li",g.needs_file?S.plan_build:S.plan_build_app),el("li",fill("plan_save",{folder:p.folder})));box.append(o);
 if(p.space_gb)box.append(el("p",fill("plan_space",{gb:p.space_gb}),"muted small"));
 if(p.install){const d=el("details"),ol=el("ol",null,"next");d.append(el("summary",S.install_preview));for(const s of p.install.steps)ol.append(linked(s));d.append(ol,el("p",p.install.note,"muted small"));box.append(d)}}
// The button is disabled by the state itself; the line under it only says which state it is.
let editFile=false,editDev=false,watch=true;
function ready(){const g=game(),why=!g?"none":!dev?"why_device":reading?"why_reading":(g.needs_file&&!file)?"why_file":planning?"why_loading":blocked?"why_blocked":"";
 $("make").disabled=!!why;{const st=sel&&stateOf(sel);$("make").textContent=st&&st.stale?fill("update_to",{version:st.latest}):S.make}$("makeWhy").textContent=why&&why!="none"?S[why]||"":"";
 const pf=g&&dev&&g.platforms.find(x=>x.id==dev);$("fileBox").classList.toggle("done",!!(g&&file&&!editFile));$("fileSumText").textContent=file?"✓ "+base(file):"";
 $("deviceBox").classList.toggle("done",!!(pf&&!editDev));$("devSumText").textContent=pf?"✓ "+pf.label:""}
$("fileChange").onclick=()=>{editFile=true;ready()};$("devChange").onclick=()=>{editDev=true;ready()};
async function useFile(path){if(!path)return;const request=++fileRequest,selected=sel;$("path").value=path;reading=true;file=null;ready();$("fileState").className="state";
 $("fileState").textContent="…";const r=await post("/api/file",{game:selected,path});if(request!=fileRequest||sel!=selected)return;reading=false;
 if(r.problem||r.error){$("fileState").className="state bad";$("fileState").textContent=r.problem||r.error}
 else{file=path;editFile=false;$("fileState").className="state ok";$("fileState").textContent="✓ "+fill("file_ok",{file:base(path)});if(dev)await pickDevice(dev)}ready()}
$("choose").onclick=async()=>{const request=fileRequest,selected=sel;$("fileState").className="state muted";$("fileState").textContent=S.picker_open;
 const r=await post("/api/pick");if(request!=fileRequest||sel!=selected)return;if($("fileState").textContent==S.picker_open)$("fileState").textContent="";
 if(r.path)useFile(r.path);else if(!r.available){$("typeBox").open=true;$("path").focus()}};
$("use").onclick=()=>useFile($("path").value.trim().replace(/^["']|["']$/g,""));
$("make").onclick=async()=>{$("make").disabled=true;watch=true;const r=await post("/api/make",{game:sel,platform:dev,path:file});
 if(r.error){$("makeError").textContent=r.error;ready();return}show(r);poll()};
$("cancel").onclick=async()=>{$("cancel").disabled=true;await post("/api/cancel")};
$("again").onclick=()=>home();
$("copy").onclick=async()=>{const text="PadMint "+D.version+" ("+D.host+")\n"+$("tail").textContent;
 try{await navigator.clipboard.writeText(text);$("copy").textContent=S.copied}catch(e){getSelection().selectAllChildren($("tail"))}};
const clock=s=>[Math.floor(s/3600),Math.floor(s/60)%60,s%60].map((n,i)=>i?String(n).padStart(2,"0"):n).join(":");
function linked(text,tag){tag=typeof tag=="string"?tag:null;const li=el(tag||"li",null,tag?"muted small":null);for(const part of text.split(/(https:\/\/[^\s)]*[^\s).,;:])/)){if(/^https:\/\//.test(part)){const a=el("a",part);a.href=part;a.target="_blank";li.append(a)}else li.append(part)}return li}
function bar(pct){const b=el("div",null,"bar"),i=el("i");i.style.width=Math.max(0,Math.min(100,pct))+"%";b.append(i);return b}
function phaseRow(p,r,g){const li=el("li",null,p.state||"pending"),ico=el("div",p.state=="done"?"✓":p.state=="failed"?"✕":p.state=="cancelled"?"–":"","ico"),body=el("div");
 const name=g?g.name:r.game;body.append(el("div",fill("ph_"+p.id,{name})));
 const repo=(p.repo||"").replace("https://","");
 if(p.id=="release"&&p.version)body.append(el("div",fill("version_from",{version:p.version,repo}),"detail"));
 if(p.id=="source"&&p.folder)body.append(el("div",p.folder,"detail"));
 if(p.id=="tools"){for(const t of r.tools){const d=el("div",null,"detail");d.append(t.name+" "+(t.version||"")+" · "+fill("from",{host:t.source||""})+" · "+(t.state=="ready"?"✓":t.state=="unpacking"?S.unpacking:(t.percent||0)+"% "+gb(t.size)));
   body.append(d);if(t.state=="downloading")body.append(bar(t.percent||0))}}
 if(p.id=="app"&&p.name)body.append(el("div",p.name,"detail"));
 if(p.id=="build"&&r.stage&&p.state=="running"){const s=r.stage;body.append(el("div",fill("stage",{stage:s.stage})+(s.total?" · "+s.completed+" / "+s.total+(s.unit?" "+s.unit:""):""),"detail"));if(s.total)body.append(bar(100*s.completed/s.total))}
 if(p.id=="build"&&p.state=="running"&&r.now)body.append(el("div",r.now.slice(-160),"detail mono"));
 if(p.id=="save"&&p.file)body.append(el("div",p.file,"detail ok"));
 li.append(ico,body);return li}
const WEIGHT={release:2,source:6,tools:10,app:4,build:76,save:2};
function overall(r){if(r.state=="done")return 100;const ids=Object.keys(WEIGHT),have={};for(const p of r.phases||[])have[p.id]=p;
 const list=ids.filter(id=>have[id]||(id!="app"&&r.state=="running")),total=list.reduce((a,id)=>a+WEIGHT[id],0);let got=0;
 for(const id of list){const p=have[id]||{};if(p.state=="done")got+=WEIGHT[id];else if(p.state=="running"&&id=="build"&&r.stage&&r.stage.total)got+=WEIGHT[id]*r.stage.completed/r.stage.total}
 return Math.max(1,Math.min(99,Math.round(100*got/Math.max(1,total))))}
function now(r){const b=$("nowBox");if(!r||watch||r.state=="idle"){b.classList.add("hidden");return}
 const g=D.games.find(x=>x.id==r.game)||{id:r.game,name:r.game},body=el("div",null,"body"),pct=overall(r);
 body.append(el("span",r.state=="done"?S.done_title:r.state=="failed"?S.failed_title:r.state=="cancelled"?S.cancelled:fill("making",{name:g.name,device:r.device||""}),"t"),
  el("span",(r.state=="running"?pct+"% · ":"")+clock(r.elapsed)+" · "+S.see_progress+" ›","s"));
 if(r.state=="running"){const x=bar(pct);x.classList.add("live");body.append(x)}
 b.replaceChildren(art(g),body);b.className=r.state;b.onclick=()=>{watch=true;show(last);scrollTo({top:0})}}
function show(r){if(r.state=="idle")return;last=r;now(r);if(!watch)return;$("storage").classList.add("hidden");nav("games");$("form").classList.add("hidden");$("progress").classList.remove("hidden");layout();
 const g=D.games.find(x=>x.id==r.game);$("making").textContent=r.state=="done"?S.done_title:r.state=="failed"?S.failed_title:r.state=="cancelled"?S.cancelled:fill("making",{name:g?g.name:r.game,device:r.device||""});
 if(g)$("headArt").replaceChildren(art(g));{const pct=overall(r),x=bar(pct);if(r.state=="running")x.classList.add("live");$("headBar").replaceChildren(r.state=="running"||r.state=="done"?x:"");$("headPct").textContent=r.state=="running"?" · "+pct+"%":""}
 $("headCard").classList.toggle("badb",r.state=="failed");$("headCard").classList.toggle("okb",r.state=="done");$("elapsedLabel").textContent=r.state=="done"?S.took:S.elapsed;$("elapsed").textContent=clock(r.elapsed);
 const ids=["release","source","tools","app","build","save"],have={};for(const p of r.phases||[])have[p.id]=p;
 const list=ids.filter(id=>have[id]||(id!="app"&&r.state=="running")).map(id=>have[id]||{id,state:"pending"});
 $("phases").replaceChildren(...list.map(p=>phaseRow(p,r,g)));
 const pre=$("tail"),stick=pre.scrollTop+pre.clientHeight>=pre.scrollHeight-20;pre.textContent=r.tail.length?r.tail.join("\n"):S.log_empty;if(stick)pre.scrollTop=pre.scrollHeight;$("lineCount").textContent=r.lines?"("+r.lines+")":"";$("copy").disabled=!r.tail.length;
 const over=r.state!="running";$("cancel").classList.toggle("hidden",over);$("cancelNote").classList.toggle("hidden",over);$("again").classList.toggle("hidden",!over);
 if(!over||shown)return;shown=true;if(r.state=="done")fetch("/api/player?lang="+D.lang,{headers:H}).then(x=>x.json()).then(x=>{if(x.library){D.library=x.library;layout()}}).catch(()=>{});const f=$("finished");f.classList.remove("hidden");if(g)$("reportLink").href=g.issues;
 if(r.state=="failed"){const p=el("p",S.failed+" ","bad"),a=el("a",g?g.issues:"");a.href=g?g.issues:"";a.target="_blank";p.append(a);f.append(p);$("logBox").open=true}
 if(r.state=="cancelled")f.classList.add("hidden");
 if(r.state=="done"&&r.result){const x=r.result;$("headCard").after(f);
  f.append(el("h2",S.what_you_got));if(x.about)f.append(el("p",x.about));
  if(x.file){const row=el("div",null,"row out");row.append(el("span",x.file,"mono ok"));if(D.reveal){const b=el("button",S.show,"btn");b.onclick=()=>post("/api/reveal");row.append(b)}f.append(row)}
  if(x.steps.length){const o=el("ol",null,"next");for(const s of x.steps)o.append(linked(s));f.append(el("h2",S.next),o)}
  if(x.note)f.append(el("p",x.note,"muted"));
  if(x.warning){const w=linked(x.warning,"p");w.className="warn small";f.append(w)}
  const p=el("p",S.guide+": ","small"),a=el("a",x.guide);a.href=x.guide;a.target="_blank";p.append(a);f.append(p,el("p",x.private,"warn small"))}}
async function poll(){const r=await (await fetch("/api/build?lang="+D.lang,{headers:H})).json();show(r);if(r.state=="running")setTimeout(poll,1500)}
if(!D.games.length&&!D.downloads.length){$("form").replaceChildren(el("p",S.none,"bad"))}else{view=mineIds().length?"mine":"library";filters();cards();poll();vstat();versions();seen(false)}
</script></body></html>
"""
