#!/usr/bin/env python3
"""Verify a Roadmap Studio release directory or deterministic ZIP archive."""

import argparse
import hashlib
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"\bconst\s+APP_VERSION\s*=\s*(['\"])([^'\"]+)\1\s*;")
PAYLOAD_FILES = (
    "index.html",
    "vendor/PPTXGENJS_LICENSE",
    "vendor/pptxgen.bundle.js",
)
METADATA_FILES = ("release.json", "SHA256SUMS")
ALLOWED_FILES = frozenset(PAYLOAD_FILES + METADATA_FILES)
ALLOWED_DIRECTORIES = frozenset({"vendor"})


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def version_from_text(text, origin):
    matches = VERSION_RE.findall(text)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one APP_VERSION constant in {origin}, found {len(matches)}")
    version = matches[0][1]
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version):
        raise ValueError(f"invalid APP_VERSION: {version!r}")
    return version


def source_version(source=ROOT / "src" / "app.html"):
    return version_from_text(source.read_text(encoding="utf-8"), source)


class ReleaseFiles:
    def __init__(self, path):
        self.path = Path(path)
        self._zip = None
        if self.path.is_dir():
            directories = {
                item.relative_to(self.path).as_posix()
                for item in self.path.rglob("*")
                if item.is_dir() and not item.is_symlink()
            }
            unexpected_directories = directories - ALLOWED_DIRECTORIES
            if unexpected_directories:
                raise ValueError(
                    f"release contains unexpected directories: {', '.join(sorted(unexpected_directories))}"
                )
            self.names = {
                item.relative_to(self.path).as_posix()
                for item in self.path.rglob("*")
                if item.is_file() or item.is_symlink()
            }
            symlinks = [name for name in self.names if (self.path / name).is_symlink()]
            if symlinks:
                raise ValueError(f"release contains symlinks: {', '.join(sorted(symlinks))}")
        elif self.path.is_file() and self.path.suffix.lower() == ".zip":
            self._zip = zipfile.ZipFile(self.path)
            infos = self._zip.infolist()
            raw_names = [info.filename for info in infos if not info.is_dir()]
            directories = {info.filename.rstrip("/") for info in infos if info.is_dir()}
            unexpected_directories = directories - ALLOWED_DIRECTORIES
            if unexpected_directories:
                raise ValueError(
                    f"release archive contains unexpected directories: "
                    f"{', '.join(sorted(unexpected_directories))}"
                )
            if len(raw_names) != len(set(raw_names)):
                raise ValueError("release archive contains duplicate entries")
            for name in raw_names:
                pure = PurePosixPath(name)
                if pure.is_absolute() or ".." in pure.parts:
                    raise ValueError(f"unsafe archive entry: {name}")
            self.names = set(raw_names)
        else:
            raise ValueError(f"release path is not a directory or ZIP archive: {self.path}")

    def read(self, name):
        if self._zip:
            return self._zip.read(name)
        return (self.path / name).read_bytes()

    def close(self):
        if self._zip:
            self._zip.close()


class AssetParser(HTMLParser):
    ASSET_ATTRIBUTES = {"src", "href", "poster"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.assets = []
        self.csp = []
        self.style_fragments = []
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for attribute in self.ASSET_ATTRIBUTES:
            if values.get(attribute):
                self.assets.append(values[attribute].strip())
        if tag.lower() == "meta" and values.get("http-equiv", "").lower() == "content-security-policy":
            self.csp.append(values.get("content", ""))
        if values.get("style"):
            self.style_fragments.append(values["style"])
        if tag.lower() == "style":
            self._in_style = True

    def handle_endtag(self, tag):
        if tag.lower() == "style":
            self._in_style = False

    def handle_data(self, data):
        if self._in_style:
            self.style_fragments.append(data)


def parse_csp(value):
    directives = {}
    for part in value.split(";"):
        tokens = part.strip().split()
        if tokens:
            directives[tokens[0].lower()] = tokens[1:]
    return directives


def validate_public_url(value):
    if not isinstance(value, str):
        raise ValueError("publicURL must be a string")
    if value == "./":
        return
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or not parsed.path.endswith("/")
    ):
        raise ValueError("publicURL must be './' or an HTTPS URL ending in a slash")


def verify_html(html_bytes, names):
    html = html_bytes.decode("utf-8")
    parser = AssetParser()
    parser.feed(html)
    if len(parser.csp) != 1:
        raise ValueError(f"expected one Content-Security-Policy meta tag, found {len(parser.csp)}")

    directives = parse_csp(parser.csp[0])
    required_csp = {
        "default-src": ["'none'"],
        "connect-src": ["'none'"],
        "object-src": ["'none'"],
        "base-uri": ["'none'"],
        "form-action": ["'none'"],
    }
    for directive, expected in required_csp.items():
        if directives.get(directive) != expected:
            raise ValueError(f"CSP must contain {directive} {' '.join(expected)}")

    css = "\n".join(parser.style_fragments)
    css_assets = re.findall(r"url\(\s*(['\"]?)([^)'\"]+)\1\s*\)", css, flags=re.IGNORECASE)
    css_imports = re.findall(r"@import\s+(?:url\()?\s*(['\"])([^'\"]+)\1", css, flags=re.IGNORECASE)
    assets = parser.assets + [match[1].strip() for match in css_assets + css_imports]
    for reference in assets:
        if not reference or reference.startswith(("#", "data:", "blob:")):
            continue
        parsed = urlsplit(reference)
        if parsed.scheme or parsed.netloc or reference.startswith("//"):
            raise ValueError(f"external resource reference is not allowed: {reference}")
        decoded_path = unquote(parsed.path)
        raw_path = PurePosixPath(decoded_path)
        if raw_path.is_absolute() or ".." in raw_path.parts or "\\" in decoded_path:
            raise ValueError(f"unsafe local resource reference: {reference}")
        normalized_path = decoded_path[2:] if decoded_path.startswith("./") else decoded_path
        path = PurePosixPath(normalized_path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe local resource reference: {reference}")
        if path.as_posix() not in names:
            raise ValueError(f"referenced package asset is missing: {reference}")

    if re.search(r"(?:https?|ftp|wss?)://", html, flags=re.IGNORECASE):
        raise ValueError("index.html contains an external resource URL")
    if "vendor/pptxgen.bundle.js" not in assets:
        raise ValueError("index.html does not reference the vendored PowerPoint runtime")


def parse_sums(data):
    sums = {}
    for line in data.decode("ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match or match.group(2) in sums:
            raise ValueError(f"invalid SHA256SUMS line: {line!r}")
        sums[match.group(2)] = match.group(1)
    return sums


def verify_release(path, source=ROOT / "src" / "app.html", expected_version=None, expected_public_url=None):
    release = ReleaseFiles(path)
    try:
        unexpected = release.names - ALLOWED_FILES
        missing = ALLOWED_FILES - release.names
        if unexpected or missing:
            raise ValueError(
                f"release file allowlist mismatch; missing={sorted(missing)}, unexpected={sorted(unexpected)}"
            )

        manifest = json.loads(release.read("release.json"))
        expected_manifest_keys = {"schemaVersion", "name", "version", "publicURL", "files"}
        if set(manifest) != expected_manifest_keys:
            raise ValueError("release.json has unexpected or missing fields")
        if manifest["schemaVersion"] != 1 or manifest["name"] != "Roadmap Studio":
            raise ValueError("release.json identity is invalid")
        validate_public_url(manifest["publicURL"])
        version = source_version(Path(source)) if source is not None else expected_version
        if version is None:
            raise ValueError("an expected version is required when source verification is disabled")
        if expected_version and version != expected_version:
            raise ValueError(f"source version {version!r} does not match expected {expected_version!r}")
        if manifest["version"] != version:
            origin = "source" if source is not None else "requested version"
            raise ValueError(f"manifest version {manifest['version']!r} does not match {origin} {version!r}")
        if expected_public_url is not None and manifest["publicURL"] != expected_public_url:
            raise ValueError("manifest publicURL does not match the requested deployment URL")

        payload = {name: release.read(name) for name in PAYLOAD_FILES}
        packaged_version = version_from_text(payload["index.html"].decode("utf-8"), "packaged index.html")
        if packaged_version != version:
            raise ValueError(
                f"packaged index version {packaged_version!r} does not match release version {version!r}"
            )
        expected_files = {
            name: {"sha256": sha256(data), "bytes": len(data)} for name, data in payload.items()
        }
        if manifest["files"] != expected_files:
            raise ValueError("release.json file metadata does not match packaged assets")

        sums = parse_sums(release.read("SHA256SUMS"))
        checksummed = PAYLOAD_FILES + ("release.json",)
        expected_sums = {name: sha256(release.read(name)) for name in checksummed}
        if sums != expected_sums:
            raise ValueError("SHA256SUMS does not match packaged files")

        verify_html(payload["index.html"], release.names)
        return {"version": version, "publicURL": manifest["publicURL"], "files": len(release.names)}
    finally:
        release.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--source", type=Path, default=ROOT / "src" / "app.html")
    parser.add_argument("--version")
    parser.add_argument("--public-url")
    args = parser.parse_args()
    try:
        result = verify_release(args.package, args.source, args.version, args.public_url)
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        raise SystemExit(f"Release verification failed: {error}") from error
    print(
        f"Verified Roadmap Studio {result['version']} package: "
        f"{result['files']} files, publicURL={result['publicURL']}"
    )


if __name__ == "__main__":
    main()
