"""Minimal IPA structure/provenance checks, not signing or gameplay acceptance."""
import copy
import hashlib
import json
import os
from pathlib import PurePosixPath
import plistlib
import shutil
import stat
import zipfile
from xml.parsers.expat import ExpatError
from .apple import linked_sdks, validate_scene_startup


def validate_ipa(path, game, revision, disc_sha256):
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError("IPA has duplicate entries")
            for name in names:
                if name.startswith("/") or ".." in PurePosixPath(name).parts or "\\" in name:
                    raise ValueError("IPA contains an unsafe entry path")
            if archive.testzip() is not None:
                raise ValueError("IPA failed ZIP integrity validation")
            plists = [name for name in names if name.startswith("Payload/")
                      and len(name.split("/")) == 3 and name.endswith(".app/Info.plist")]
            if len(plists) != 1:
                raise ValueError("IPA must contain exactly one top-level app Info.plist")
            app = plists[0].rsplit("/", 1)[0]

            def member(name):
                info = archive.getinfo(name)
                if info.is_dir() or stat.S_ISLNK(info.external_attr >> 16) or info.file_size == 0:
                    raise ValueError("Required IPA member must be a nonempty regular file")
                return info

            def metadata(name):
                if member(name).file_size > 1024 * 1024:
                    raise ValueError("IPA metadata exceeds 1 MiB")
                return archive.read(name)

            def executable_hash(name):
                member(name)
                with archive.open(name) as stream:
                    magic = stream.read(4)
                    if magic not in (b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf",
                                     b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca",
                                     b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca"):
                        raise ValueError("IPA executable/module has no supported Mach-O header")
                    digest = hashlib.sha256(magic)
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                    return digest.hexdigest()

            info = plistlib.loads(metadata(plists[0]))
            if not isinstance(info, dict):
                raise ValueError("IPA Info.plist must be a dictionary")
            executable = info.get("CFBundleExecutable")
            if (not isinstance(executable, str) or not executable
                    or executable in (".", "..") or "/" in executable or "\\" in executable):
                raise ValueError("IPA has no valid declared executable")
            if not isinstance(info.get("CFBundleIdentifier"), str) or not info["CFBundleIdentifier"]:
                raise ValueError("IPA has no bundle identifier")
            binary_hash = executable_hash(app + "/" + executable)
            with archive.open(app + "/" + executable) as stream:
                slices = linked_sdks(stream, archive.getinfo(app + "/" + executable).file_size)
            apple = validate_scene_startup(info, slices)
            if game is None:
                return {"check": "minimal-ipa-structure", "executable_sha256": binary_hash,
                        "apple_compatibility": apple}
            provenance_name = (app + "/BuilderProvenance.json" if game == "bluewake"
                               else "KartPadBuilderProvenance.json")
            provenance = json.loads(metadata(provenance_name))
            if not isinstance(provenance, dict):
                raise ValueError("IPA provenance must be an object")
            if game == "bluewake":
                if (provenance.get("profile") != "bluewake"
                        or provenance.get("source_commit") != revision
                        or provenance.get("source_modified") is not False
                        or provenance.get("local_training") is not True
                        or provenance.get("containsTranslatedGameCode") is not True
                        or provenance.get("packaging_commit", revision) != revision):
                    raise ValueError("BlueWake provenance does not match the requested build")
                # Fixed adapter contract, not an arbitrary path from the archive.
                module_hash = executable_hash(app + "/Frameworks/gGZLE01_recomp.dylib")
                if module_hash != provenance.get("module_sha256"):
                    raise ValueError("BlueWake module hash does not match provenance")
            elif (provenance.get("schemaVersion") != 1
                  or provenance.get("profileId") != "mkwii-rmcp01-rev0"
                  or provenance.get("imageSHA256") != disc_sha256
                  or provenance.get("containsUserSuppliedTranslatedCode") is not True):
                raise ValueError("KartPad provenance does not match the requested disc/profile")
            return {"check": "minimal-ipa-structure-and-provenance", "executable_sha256": binary_hash,
                    "apple_compatibility": apple,
                    "provenance_sha256": hashlib.sha256(archive.read(provenance_name)).hexdigest()}
    except (zipfile.BadZipFile, KeyError, plistlib.InvalidFileException,
            json.JSONDecodeError, UnicodeError, RuntimeError, ExpatError) as error:
        raise ValueError("IPA is malformed or missing required package metadata") from error


def launch_link(game_id):
    """The link (URL scheme) a PadMint-built game answers to, so the PadMint Library app
    can tell it is installed and open it. Scheme names allow letters, digits, + - and ."""
    return "padmint-" + game_id.lower()


def add_launch_link(path, game_id):
    """Register padmint-<game>:// in an unsigned IPA's app Info.plist; returns the scheme.
    Every other entry is copied unchanged. The player's signing tool signs the result."""
    scheme = launch_link(game_id)
    path = str(path)
    with zipfile.ZipFile(path) as archive:
        plists = [name for name in archive.namelist() if name.startswith("Payload/")
                  and name.count("/") == 2 and name.endswith(".app/Info.plist")]
        if len(plists) != 1:
            raise ValueError("IPA must contain exactly one top-level app Info.plist")
        raw = archive.read(plists[0])
        info = plistlib.loads(raw)
        types = info.get("CFBundleURLTypes")
        types = [item for item in types if isinstance(item, dict)] if isinstance(types, list) else []
        if any(scheme in (item.get("CFBundleURLSchemes") or []) for item in types):
            return scheme
        info["CFBundleURLTypes"] = types + [{"CFBundleURLName": scheme, "CFBundleURLSchemes": [scheme]}]
        updated = plistlib.dumps(info, fmt=plistlib.FMT_BINARY if raw.startswith(b"bplist")
                                 else plistlib.FMT_XML, sort_keys=False)
        temporary = path + ".linking"
        try:
            with zipfile.ZipFile(temporary, "w") as out:
                for item in archive.infolist():
                    entry = copy.copy(item)  # writing updates offsets and sizes; keep the reader's
                    if item.filename == plists[0]:
                        out.writestr(entry, updated)
                    elif item.is_dir():
                        out.writestr(entry, b"")
                    else:
                        # Streamed: a game module can be hundreds of MB.
                        with archive.open(item) as source, \
                                out.open(entry, "w", force_zip64=item.file_size >= 1 << 31) as target:
                            shutil.copyfileobj(source, target, 1 << 20)
        except BaseException:
            if os.path.exists(temporary):
                os.unlink(temporary)
            raise
    os.replace(temporary, path)
    return scheme
