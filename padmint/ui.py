"""The PadMint window: a page in the player's web browser, served by this computer.

It serves only on 127.0.0.1 with a random token, uses the Python standard library,
and makes copies by running "python -m padmint make", so the window can never do more
than the terminal. Nothing is uploaded.
"""
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import webbrowser

from . import __version__, cli, tools
from .manifest import catalog
from .say import LANGUAGES, MESSAGES, language, localized, phrase

ROOT = Path(__file__).resolve().parent.parent


def strings(lang):
    return {key[2:]: value.get(lang, value["en"]) for key, value in MESSAGES.items() if key.startswith("w_")}


def player_data(lang):
    """Everything the page shows before a build: games, devices and game files found."""
    folder = cli.player_folder()
    games = []
    for game, name, platforms in cli.player_games():
        entry = catalog()[game]
        needs_file = entry.get("player_game_file", "build") != "in-app"
        files = cli.game_files(folder, entry.get("manifest")) if needs_file else []
        games.append({"id": game, "name": name, "needs_file": needs_file,
                      "about": entry.get("game") or (entry.get("manifest") or {}).get("game", ""),
                      "formats": sorted({f.upper() for item in (entry.get("manifest") or {}).get("inputs", [])
                                         for f in item.get("formats", [])}),
                      "ids": entry.get("game_ids") or [],
                      "platforms": [{"id": p, "label": cli.platform_label(p, lang),
                                     "short": phrase(f"w_short_{p}", lang) if f"w_short_{p}" in MESSAGES else p}
                                    for p in platforms],
                      "files": [str(path) for path in files[:8]],
                      "ready": ({"text": localized(entry["ready_to_play"], "text", lang),
                                 "url": entry["ready_to_play"]["url"]} if entry.get("ready_to_play") else None),
                      "page": entry.get("player_help") or entry["repo_url"], "issues": entry["repo_url"] + "/issues"})
    apps = [] if cli.on_android() else [
        {"id": app, "name": name, "about": catalog()[app].get("game", ""), "plays_on": catalog()[app].get("plays_on", []),
         "intro": phrase("download_intro", lang, name=name).strip(),
         "steps": localized(catalog()[app]["download"], "steps", lang),
         "guide": catalog()[app].get("player_help") or catalog()[app]["repo_url"]}
        for app, name in cli.downloads()]
    waiting = [{"id": game, "name": name, "about": catalog()[game]["game"],
                "text": localized(catalog()[game]["later"], "text", lang), "plays_on": catalog()[game].get("plays_on", []),
               "link": catalog()[game].get("player_help") or catalog()[game]["repo_url"]}
               for game, name in cli.later()]
    # Games PadMint builds, but not here: listed with the reason, never silently left out.
    waiting += [{"id": game, "name": name,
                 "about": catalog()[game].get("game") or (catalog()[game].get("manifest") or {}).get("game", ""),
                 "text": phrase("w_needs_mac" if "ios" in targets else "w_needs_windows", lang, name=name),
                 "tag": phrase("w_needs_mac_tag", lang) if "ios" in targets else None,
                 "plays_on": ["iphone", "ipad"] if "ios" in targets else [],
                 "link": catalog()[game].get("player_help") or catalog()[game]["repo_url"]}
                for game, name, targets in cli.elsewhere()]
    return {"lang": lang, "version": __version__, "folder": str(folder),
            "saved_in": phrase("saved_in", lang, folder=folder), "games": games, "downloads": apps, "later": waiting,
            "text": strings(lang), "picker": not cli.on_android(), "reveal": not cli.on_android()}


def plan(game, platform_name, lang):
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
    needs = [{"label": cli.label(tool), "ok": cli.check_program(tool)[0], "note": tool.get("note", "")}
             for tool in cli.player_requirements(manifest)]
    name = manifest.get("name") or entry.get("name", game)
    key = f"w_output_{platform_name}"
    return {"repo": entry["repo_url"], "tools": items, "tools_folder": str(tools.tools_root()),
            "app": bool(target.get("published_app")), "space_gb": entry.get("free_space_gb"),
            "folder": str(cli.player_folder()), "needs": needs, "before": cli.before_build(game),
            "output": phrase(key, lang, name=name) if key in MESSAGES else ""}


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
        argv = ["osascript", "-e", 'POSIX path of (choose file with prompt (system attribute '
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
    manifest = catalog()[game].get("manifest") or {}
    formats = sorted({name for item in manifest.get("inputs", []) for name in item.get("formats", [])})
    if formats and disc.suffix.lower().lstrip(".") not in formats:
        return phrase("w_not_game_file", lang, file=disc.name, name=manifest.get("name", game),
                      formats=", ".join(name.upper() for name in formats))
    found = cli.game_from_file(disc, cli.player_games(), io.StringIO())
    if found and game not in found:
        name = (catalog()[game].get("manifest") or {}).get("name", game)
        return phrase("w_wrong_game", lang, name=name)
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

    def cancel(self):
        if self.process and self.process.poll() is None:
            # PadMint cancels and keeps finished work.
            self.process.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)

    def reveal(self):
        if self.process and self.process.poll() == 0 and self.result()["file"]:
            cli.reveal(Path(self.result()["file"]))


def make_handler(token, builds):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def reply(self, code, body, kind="application/json"):
            data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
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
            if route == "/api/build":
                return self.reply(200, builds.status(self.lang()))
            if route == "/api/plan":
                query = parse_qs(urlparse(self.path).query)
                game, platform_name = query.get("game", [""])[0], query.get("platform", [""])[0]
                if not any(id_ == game and platform_name in platforms
                           for id_, _name, platforms in cli.player_games()):
                    return self.reply(400, {"error": "That game cannot be made for that device on this computer"})
                return self.reply(200, plan(game, platform_name, self.lang()))
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
                if route == "/api/reveal":
                    builds.reveal()
                    return self.reply(200, {})
                return self.reply(404, {"error": "not found"})
            except (KeyError, ValueError, OSError) as error:
                return self.reply(400, {"error": str(error)})

    return Handler


def serve(port=0, open_browser=True):
    token = secrets.token_urlsafe(24)
    builds = Builds()
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(token, builds))
    url = f"http://127.0.0.1:{server.server_address[1]}/?token={token}"
    print(phrase("w_open", language(), version=__version__, url=url), flush=True)
    # Read every game's latest recipe in the background, so the plan shows at once.
    threading.Thread(target=lambda: [release_recipe(game) for game, _name, _targets in cli.player_games()],
                     daemon=True).start()
    if open_browser:
        if cli.on_android():  # the phone's browser, through Termux
            subprocess.run([str(cli.TERMUX_OPEN_URL), url], check=False)
        else:
            webbrowser.open(url)
    try:
        server.serve_forever()
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
</style></head><body><div class="wrap">
<header><a class="brand" id="home" href="#"><div class="mark"><svg viewBox="0 0 64 64" aria-hidden="true"><defs><linearGradient id="pmg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5ff0b0"/><stop offset="1" stop-color="#14945f"/></linearGradient></defs><rect width="64" height="64" rx="15" fill="url(#pmg)"/><path fill="#06281a" d="M19 19h26c7.2 0 12.6 6.6 11.2 13.7l-2.1 10.2c-1 4.9-7.1 6.6-10.5 2.9L39 41H25l-4.6 4.8c-3.4 3.7-9.5 2-10.5-2.9L7.8 32.7C6.4 25.6 11.8 19 19 19z"/><path stroke="#5ff0b0" stroke-width="4" stroke-linecap="round" d="M20 26v10M15 31h10"/><path fill="#5ff0b0" d="M37 37c0-6.5 4.8-11 12-11 0 6.5-4.8 11-12 11z"/><path stroke="#06281a" stroke-width="1.8" stroke-linecap="round" d="M39.5 34.5l6.5-6"/></svg></div>
<div><h1>PadMint</h1><div class="v" id="ver"></div></div></a>
<div class="top"><a class="gh" id="gh" href="https://github.com/chrissotraidis" target="_blank" rel="noopener" title="GitHub" aria-label="GitHub"><svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg></a>
<select id="lang" aria-label="Language"><option value="en">English</option><option value="es">Español</option><option value="pt">Português</option></select></div></header>

<section class="hero"><p data-t="intro"></p><div class="chips"><span class="chip" data-t="trust_local"></span><span class="chip" data-t="trust_upload"></span><span class="chip" data-t="trust_open"></span></div>
</section>
<section class="about" id="about"><h2 data-t="about_title"></h2><div class="flow"><div><i>1</i><b data-t="flow_1"></b><span data-t="flow_1s"></span></div><div><i>2</i><b data-t="flow_2"></b><span data-t="flow_2s"></span></div><div><i>3</i><b data-t="flow_3"></b><span data-t="flow_3s"></span></div></div>
<div class="explain"><details id="howBox"><summary data-t="how_title"></summary><ol><li data-t="how_1"></li><li data-t="how_2"></li><li data-t="how_3"></li><li data-t="how_4"></li><li data-t="how_5"></li></ol></details>
<details id="whyBox"><summary data-t="why_title"></summary><p data-t="why_1"></p><p data-t="why_2"></p></details></div></section>

<main id="form">
<section class="card" id="pickCard"><button class="btn back hidden" id="changeGame" data-t="change"></button><h2 data-t="step1"></h2>
<div id="finder"><div class="search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><input id="search" type="search" autocomplete="off"></div></div>
<div class="pills" id="pills"><div class="tabs" id="tabs" role="tablist"><button class="tab" data-g="all" role="tab"><span data-t="tab_all"></span><span class="n"></span></button><button class="tab" data-g="build" role="tab"><span data-t="tab_build"></span><span class="n"></span></button><button class="tab" data-g="download" role="tab"><span data-t="tab_download"></span><span class="n"></span></button><button class="tab" data-g="later" role="tab"><span data-t="later_head"></span><span class="n"></span></button></div><div class="filters" id="filters"></div></div>
<p class="note" id="groupNote"></p><div class="list" id="list"></div><p class="small hidden" id="gamePage"><a target="_blank" rel="noopener" id="gamePageLink"></a></p><p class="muted hidden" id="noMatch" data-t="no_match"></p></section>

<section class="card hidden" id="dlBox"><h2 id="dlName"></h2><p id="dlIntro"></p><ol class="next" id="dlSteps"></ol><p class="small" id="dlGuide"></p><button class="btn back backBtn" data-t="change"></button></section>

<section class="card hidden" id="laterBox"><h2 id="laterName"></h2><p class="muted" id="laterAbout"></p><p id="laterText"></p><div class="row"><a class="btn" id="laterLink" target="_blank"></a><button class="btn back backBtn" data-t="change"></button></div></section>

<section class="card banner hidden" id="readyBox"><h2 data-t="ready_title"></h2><p id="readyText"></p><div class="row"><a class="btn main" id="readyLink" target="_blank" data-t="ready_link"></a></div><p class="muted small" data-t="ready_or"></p></section>

<section class="card hidden" id="fileBox"><h2 data-t="step2"></h2><p id="fileHint" class="small"></p>
<div class="row"><button class="btn" id="choose" data-t="choose"></button></div>
<div id="foundBox"><p class="muted small" id="found"></p><div id="files"></div></div>
<details id="typeBox"><summary data-t="type_toggle"></summary><p class="muted small" data-t="type"></p>
<div class="row"><input id="path" style="flex:1;min-width:240px"><button class="btn" id="use" data-t="use"></button></div></details>
<p class="state" id="fileState"></p></section>
<section class="card hidden" id="inApp"><h2 data-t="step2"></h2><p id="inAppText" class="muted"></p></section>

<section class="card hidden" id="deviceBox"><h2 data-t="step3"></h2><div class="grid" id="devices"></div></section>

<section class="card plan hidden" id="planBox"><h2 data-t="plan_title"></h2><div id="plan"></div>
<div class="row" style="margin-top:.8rem"><button class="btn main" id="make" data-t="make" disabled></button></div>
<p class="bad" id="makeError"></p></section>
</main>

<main id="progress" class="hidden">
<section class="card banner" id="headCard"><p class="big" id="making"></p><p class="muted small"><span id="elapsedLabel" data-t="elapsed"></span>: <b id="elapsed"></b></p></section>
<section class="card"><ul class="steps" id="phases"></ul>
<div class="row" style="margin-top:.8rem"><button class="btn" id="cancel" data-t="cancel"></button><span class="muted small" id="cancelNote" data-t="cancel_note"></span>
<button class="btn hidden" id="again" data-t="again"></button></div></section>
<section class="card hidden" id="finished"></section>
<section class="card"><details id="logBox"><summary><span data-t="log"></span> <span class="muted" id="lineCount"></span></summary>
<pre id="tail"></pre><button class="btn" id="copy" data-t="copy_log"></button></details></section>
</main>
<footer><span data-t="local_note"></span><span><a href="https://github.com/chrissotraidis/padmint" target="_blank" data-t="source"></a> · <a id="reportLink" href="https://github.com/chrissotraidis/padmint/issues" target="_blank" data-t="report"></a></span></footer>
</div>
<script>
const T="__TOKEN__";let D=__DATA__,S=D.text;const H={"Content-Type":"application/json","X-PadMint-Token":T};
const $=id=>document.getElementById(id);let file=null,reading=false,sel=null,dev=null,shown=false;
const fill=(k,v)=>Object.entries(v||{}).reduce((s,[a,b])=>s.split("{"+a+"}").join(b),S[k]||"");
for(const e of document.querySelectorAll("[data-t]"))e.textContent=S[e.dataset.t]||"";
document.documentElement.lang=D.lang;$("lang").value=D.lang;$("ver").textContent="v"+D.version;$("search").placeholder=S.search;
$("choose").classList.toggle("hidden",!D.picker);
let last=null;
function texts(){for(const e of document.querySelectorAll("[data-t]"))e.textContent=S[e.dataset.t]||"";document.documentElement.lang=D.lang;$("search").placeholder=S.search;$("home").setAttribute("aria-label",S.home||"PadMint")}
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
const COLORS={"GameCube":"#6c5ce7","Wii":"#2d9cdb","N64":"#e2463a","PlayStation":"#4b5a6b","Steam":"#2a6fb0","PC":"#d9822b"};
const BADGES={"GameCube":"GC","Wii":"Wii","N64":"64","PlayStation":"PS","Steam":"PC","PC":"PC"};
const colorOf=x=>COLORS[systemOf(x)]||"#1fa572";
let group="all";const all=()=>[...D.games,...D.downloads,...D.later];
const groupOf=id=>D.games.some(x=>x.id==id)?"build":D.downloads.some(x=>x.id==id)?"download":"later";
const DEVICES={ipad:"iPad",iphone:"iPhone",mac:"Mac"};
for(const b of document.querySelectorAll(".tab"))b.onclick=()=>{group=b.dataset.g;cards()};
function filters(){const systems=[...new Set(all().map(systemOf).filter(Boolean))].sort();
 $("filters").replaceChildren(...["",...systems].map(s=>{const b=el("button",s||S.all,"filter"+(s==system?" on":""));b.onclick=()=>{system=s;filters();cards()};return b}))}
function row(x){const kind=groupOf(x.id),b=el("button",null,"item "+kind+(x.id==sel?" on":""));b.style.setProperty("--c",colorOf(x));
 const badge=el("span",BADGES[systemOf(x)]||(x.name||"?").charAt(0),"av");badge.title=systemOf(x)?fill("original",{system:systemOf(x)}):"";
 b.append(badge,el("span",x.about?title(x):x.name,"t"));const t=el("div",null,"tags");
 if(kind=="later")t.append(el("span",x.tag||S.later_head,"tag soon"));if(kind=="download")t.append(el("span",S.dl_tag,"tag dl"));
 if(kind=="build"&&x.ready)t.append(el("span",S.ready_tag,"tag ready"));
 if(kind=="build")for(const p of x.platforms)t.append(el("span",p.short||p.label,"tag"));else{const o=x.plays_on||[];const ios=o.includes("iphone")&&o.includes("ipad")?["iPhone/iPad"]:o.filter(d=>d!="mac").map(d=>DEVICES[d]);for(const d of [...ios,...(o.includes("mac")?["Mac"]:[])])t.append(el("span",d,"tag"))}b.append(t);
 b.append(el("span",x.name+(systemOf(x)?" · "+fill("original",{system:systemOf(x)}):""),"s"));b.onclick=()=>choose(x.id);return b}
function cards(){const q=$("search").value.trim().toLowerCase();
 const match=x=>(!q||(x.name+" "+(x.about||"")).toLowerCase().includes(q))&&(!system||systemOf(x)==system);
 const order=a=>a.sort((x,y)=>sortKey(x).localeCompare(sortKey(y)));
 const G={build:order(D.games.filter(match)),download:order(D.downloads.filter(match)),later:order(D.later.filter(match))};
 G.all=order([...G.build,...G.download,...G.later]);
 if(sel){group="all";G.all=all().filter(x=>x.id==sel)}
 else if(!G[group].length){const k=["all","build","download","later"].find(k=>G[k].length);if(k)group=k}
 $("finder").classList.toggle("hidden",!!sel);$("changeGame").classList.toggle("hidden",!sel);$("tabs").classList.toggle("hidden",!!sel);$("pills").classList.toggle("hidden",!!sel);const one=sel&&all().find(x=>x.id==sel);$("gamePage").classList.toggle("hidden",!(one&&one.page));if(one&&one.page){$("gamePageLink").href=one.page;$("gamePageLink").textContent=fill("game_page",{name:one.name})+" ↗"}
 for(const b of document.querySelectorAll(".tab")){b.classList.toggle("on",b.dataset.g==group);b.setAttribute("aria-selected",b.dataset.g==group);b.querySelector(".n").textContent=G[b.dataset.g].length}
 $("groupNote").textContent=sel?"":S[{all:"all_note",build:"builds",download:"no_build",later:"later_note"}[group]];
 $("list").replaceChildren(...G[group].map(x=>row(x)));$("list").classList.toggle("hidden",!G[group].length);
 $("noMatch").classList.toggle("hidden",!!G[group].length);layout()}
function back(top){sel=null;file=null;dev=null;for(const id of ["fileBox","deviceBox","planBox","dlBox","readyBox","laterBox","inApp"])$(id).classList.add("hidden");cards();if(top)scrollTo({top:0,behavior:"smooth"});else $("pickCard").scrollIntoView({behavior:"smooth"})}
function layout(){$("about").classList.toggle("hidden",!!sel||!$("progress").classList.contains("hidden"))}
function home(){if(last&&last.state=="running"){scrollTo({top:0,behavior:"smooth"});return}
 last=null;shown=false;$("progress").classList.add("hidden");$("form").classList.remove("hidden");$("finished").replaceChildren();$("finished").classList.add("hidden");
 $("cancel").disabled=false;$("logBox").open=false;$("makeError").textContent="";$("reportLink").href="https://github.com/chrissotraidis/padmint/issues";
 $("search").value="";system="";group="all";filters();back(true)}
$("home").onclick=e=>{e.preventDefault();home()};$("home").setAttribute("aria-label",S.home||"PadMint");
$("search").oninput=cards;$("changeGame").onclick=back;for(const b of document.querySelectorAll(".backBtn"))b.onclick=back;
function choose(id){sel=id;file=null;dev=null;$("fileState").textContent="";$("path").value="";cards();const g=game(),a=app(),w=waiting();
 $("laterBox").classList.toggle("hidden",!w);
 if(w){$("laterName").textContent=w.name;$("laterAbout").textContent=[systemOf(w)?fill("original",{system:systemOf(w)}):"",(w.plays_on||[]).length?fill("plays_on",{devices:(w.plays_on.includes("iphone")&&w.plays_on.includes("ipad")?["iPhone/iPad"]:w.plays_on.filter(d=>d!="mac").map(d=>DEVICES[d])).concat(w.plays_on.includes("mac")?["Mac"]:[]).join(", ")}):""].filter(Boolean).join(" · ");$("laterText").textContent=w.text;$("laterLink").href=w.link;$("laterLink").textContent=fill("later_link",{name:w.name});$("laterBox").scrollIntoView({behavior:"smooth"})}
 $("dlBox").classList.toggle("hidden",!a);
 $("readyBox").classList.toggle("hidden",!(g&&g.ready));if(g&&g.ready){$("readyText").textContent=g.ready.text;$("readyLink").href=g.ready.url}
 if(a){$("dlName").textContent=a.name;$("dlIntro").textContent=a.intro;$("dlSteps").replaceChildren(...a.steps.map(s=>linked(s)));
  const l=el("a",a.guide);l.href=a.guide;l.target="_blank";$("dlGuide").replaceChildren(S.guide+": ",l);$("dlBox").scrollIntoView({behavior:"smooth"})}
 for(const id of ["fileBox","deviceBox","planBox"])$(id).classList.add("hidden");$("inApp").classList.add("hidden");if(!g)return;
 if(g.needs_file){$("fileBox").classList.remove("hidden");
  const h=$("fileHint");h.replaceChildren(el("b",fill("file_hint",{game:g.about||g.name})));
  if(g.formats.length)h.append(" ",el("span",fill("file_formats",{formats:g.formats.join(", ")}),"muted"));
  if(g.ids.length)h.append(" · ",el("span",fill(g.ids[0].length==4?"file_code":"file_ids",{ids:g.ids.join(", ")}),"muted"));$("foundBox").classList.toggle("hidden",!g.files.length);$("found").textContent=fill("found",{folder:D.folder});
  $("files").replaceChildren(...g.files.map(f=>{const b=el("button",null,"btn file");b.append(el("b",base(f)),el("span","→","muted"));b.title=f;b.onclick=()=>useFile(f);return b}))}
 else{$("inAppText").textContent=fill("file_in_app",{name:g.name});$("inApp").classList.remove("hidden")}
 $("deviceBox").classList.remove("hidden");$("devices").replaceChildren(...g.platforms.map(p=>{const b=el("button",null,"pick");b.append(el("b",p.label));b.onclick=()=>pickDevice(p.id);b.dataset.id=p.id;return b}));
 if(g.platforms.length==1)pickDevice(g.platforms[0].id);($("fileBox").classList.contains("hidden")?$("deviceBox"):$("fileBox")).scrollIntoView({behavior:"smooth"});ready()}
async function pickDevice(id){dev=id;for(const b of $("devices").children)b.classList.toggle("on",b.dataset.id==id);$("planBox").classList.remove("hidden");$("plan").replaceChildren(el("p",fill("plan_loading",{name:(game()||{}).name||""}),"muted loading"));
 const r=await (await fetch("/api/plan?game="+sel+"&platform="+id+"&lang="+D.lang,{headers:H})).json();if(dev!=id)return;showPlan(r);ready()}
let blocked=false;
function showPlan(p){const g=game(),box=$("plan");box.replaceChildren();if(p.error){box.append(el("p",p.error,"bad"));return}
 if(p.output)box.append(el("div",p.output,"out"));
 blocked=p.needs.some(n=>!n.ok);
 if(p.needs.length){box.append(el("p",S.plan_needs,"state"));const u=el("ul",null,"tools");for(const n of p.needs){const li=el("li");li.append(el("span",n.label),el("span",n.ok?S.needs_ok:S.needs_missing,n.ok?"ok":"bad"));u.append(li);if(!n.ok)u.append(el("li",n.note,"detail"))}box.append(u)}
 if(p.before){const b=p.before;box.append(el("p",S.before_title,"state"),linked(b.homebrew?S.before_hint:S.before_brew,"p"));
  if(b.homebrew&&b.packages.length){const k=el("div",null,"pks");for(const x of b.packages)k.append(el("span",(x.ok?"✓ ":"✗ ")+x.name,"pk"+(x.ok?"":" no")));box.append(k)}
  for(const line of b.commands){const c=el("div",null,"cmd"),btn=el("button",S.copy);c.append(el("code",line),btn);
   btn.onclick=async()=>{try{await navigator.clipboard.writeText(line);btn.textContent=S.copied;setTimeout(()=>btn.textContent=S.copy,1500)}catch(e){getSelection().selectAllChildren(c.firstChild)}};box.append(c)}}
 const o=el("ol");const repo=p.repo.replace("https://","");o.append(el("li",fill("plan_source",{name:g.name,repo})));
  if(p.tools.length){const li=el("li",fill("plan_tools",{folder:p.tools_folder}));const u=el("ul",null,"tools");
  for(const t of p.tools){const r=el("li");r.append(el("span",t.name+" "+t.version+" · "+fill("from",{host:t.source})),el("span",t.here?S.tool_here:gb(t.size),t.here?"ok":"muted"));u.append(r)}
  li.append(u);o.append(li)}if(p.app)o.append(el("li",fill("plan_app",{name:g.name})));
 o.append(el("li",g.needs_file?S.plan_build:S.plan_build_app),el("li",fill("plan_save",{folder:p.folder})));box.append(o);
 if(p.space_gb)box.append(el("p",fill("plan_space",{gb:p.space_gb}),"muted small"))}
function ready(){const g=game();$("make").disabled=!g||!dev||reading||blocked||(g.needs_file&&!file)}
async function useFile(path){if(!path)return;$("path").value=path;reading=true;file=null;ready();$("fileState").className="state";
 $("fileState").textContent="…";const r=await post("/api/file",{game:sel,path});reading=false;
 if(r.problem||r.error){$("fileState").className="state bad";$("fileState").textContent=r.problem||r.error}
 else{file=path;$("fileState").className="state ok";$("fileState").textContent="✓ "+fill("file_ok",{file:base(path)})}ready()}
$("choose").onclick=async()=>{const r=await post("/api/pick");if(r.path)useFile(r.path);else if(!r.available){$("typeBox").open=true;$("path").focus()}};
$("use").onclick=()=>useFile($("path").value.trim().replace(/^["']|["']$/g,""));
$("make").onclick=async()=>{$("make").disabled=true;const r=await post("/api/make",{game:sel,platform:dev,path:file});
 if(r.error){$("makeError").textContent=r.error;ready();return}show(r);poll()};
$("cancel").onclick=async()=>{$("cancel").disabled=true;await post("/api/cancel")};
$("again").onclick=home;
$("copy").onclick=async()=>{const text="PadMint "+D.version+" ("+navigator.platform+")\n"+$("tail").textContent;
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
function show(r){if(r.state=="idle")return;last=r;$("form").classList.add("hidden");$("progress").classList.remove("hidden");layout();
 const g=D.games.find(x=>x.id==r.game);$("making").textContent=r.state=="done"?S.done_title:r.state=="failed"?S.failed_title:r.state=="cancelled"?S.cancelled:fill("making",{name:g?g.name:r.game,device:r.device||""});
 $("headCard").classList.toggle("badb",r.state=="failed");$("headCard").classList.toggle("okb",r.state=="done");$("elapsedLabel").textContent=r.state=="done"?S.took:S.elapsed;$("elapsed").textContent=clock(r.elapsed);
 const ids=["release","source","tools","app","build","save"],have={};for(const p of r.phases||[])have[p.id]=p;
 const list=ids.filter(id=>have[id]||(id!="app"&&r.state=="running")).map(id=>have[id]||{id,state:"pending"});
 $("phases").replaceChildren(...list.map(p=>phaseRow(p,r,g)));
 const pre=$("tail"),stick=pre.scrollTop+pre.clientHeight>=pre.scrollHeight-20;pre.textContent=r.tail.length?r.tail.join("\n"):S.log_empty;if(stick)pre.scrollTop=pre.scrollHeight;$("lineCount").textContent=r.lines?"("+r.lines+")":"";$("copy").disabled=!r.tail.length;
 const over=r.state!="running";$("cancel").classList.toggle("hidden",over);$("cancelNote").classList.toggle("hidden",over);$("again").classList.toggle("hidden",!over);
 if(!over||shown)return;shown=true;const f=$("finished");f.classList.remove("hidden");if(g)$("reportLink").href=g.issues;
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
if(!D.games.length&&!D.downloads.length){$("form").replaceChildren(el("p",S.none,"bad"))}else{filters();cards();poll()}
</script></body></html>
"""
