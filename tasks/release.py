#!/usr/bin/env python3
"""Build deterministic, offline Roadmap Studio release packages."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from verify_release import PAYLOAD_FILES, ROOT, sha256, source_version, verify_release


DEFAULT_OUTPUT = ROOT / "release"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def build_check():
    subprocess.run(["python3", str(ROOT / "tasks" / "build.py"), "--check"], cwd=ROOT, check=True)


def metadata(source_files, version, public_url):
    files = {
        name: {"sha256": sha256(data), "bytes": len(data)}
        for name, data in source_files.items()
    }
    manifest = {
        "schemaVersion": 1,
        "name": "Roadmap Studio",
        "version": version,
        "publicURL": public_url,
        "files": files,
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    checksummed = dict(source_files)
    checksummed["release.json"] = manifest_bytes
    sums = "".join(f"{sha256(data)}  {name}\n" for name, data in sorted(checksummed.items()))
    return manifest_bytes, sums.encode("ascii")


def write_package(destination, version, public_url):
    source_files = {name: (ROOT / name).read_bytes() for name in PAYLOAD_FILES}
    manifest, sums = metadata(source_files, version, public_url)
    package_files = {**source_files, "release.json": manifest, "SHA256SUMS": sums}
    for name, data in package_files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o644)
    return package_files


def write_archive(path, package_files):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(package_files.items()):
            info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_STORED)


def same_tree(left, right):
    left_files = sorted(path.relative_to(left) for path in left.rglob("*") if path.is_file())
    right_files = sorted(path.relative_to(right) for path in right.rglob("*") if path.is_file())
    return left_files == right_files and all(
        (left / name).read_bytes() == (right / name).read_bytes() for name in left_files
    )


def replace_directory(source, destination):
    backup = destination.with_name(destination.name + ".previous")
    if backup.exists():
        shutil.rmtree(backup)
    if destination.exists():
        os.replace(destination, backup)
    try:
        os.replace(source, destination)
    except Exception:
        if backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def create_release(output, public_url="./"):
    output = Path(output).resolve()
    version = source_version()
    versions = output / "versions"
    archives = output / "archives"
    current = output / "current"
    version_dir = versions / version
    archive_path = archives / f"roadmap-studio-{version}.zip"

    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="roadmap-release-", dir=output) as temp_name:
        staged = Path(temp_name) / version
        package_files = write_package(staged, version, public_url)
        verify_release(staged, expected_version=version, expected_public_url=public_url)

        staged_archive = Path(temp_name) / archive_path.name
        write_archive(staged_archive, package_files)
        verify_release(staged_archive, expected_version=version, expected_public_url=public_url)

        versions.mkdir(parents=True, exist_ok=True)
        if version_dir.exists():
            if not same_tree(staged, version_dir):
                raise ValueError(f"immutable release already exists with different content: {version_dir}")
        else:
            shutil.copytree(staged, version_dir)

        archives.mkdir(parents=True, exist_ok=True)
        if archive_path.exists() and archive_path.read_bytes() != staged_archive.read_bytes():
            raise ValueError(f"immutable archive already exists with different content: {archive_path}")
        if not archive_path.exists():
            shutil.copy2(staged_archive, archive_path)

        staged_current = Path(temp_name) / "current"
        shutil.copytree(staged, staged_current)
        replace_directory(staged_current, current)

    verify_release(version_dir, expected_version=version, expected_public_url=public_url)
    verify_release(current, expected_version=version, expected_public_url=public_url)
    return version, version_dir, archive_path, current


def rollback(output, version):
    output = Path(output).resolve()
    selected = output / "versions" / version
    current = output / "current"
    verify_release(selected, source=None, expected_version=version)
    with tempfile.TemporaryDirectory(prefix="roadmap-rollback-", dir=output) as temp_name:
        staged = Path(temp_name) / "current"
        shutil.copytree(selected, staged)
        replace_directory(staged, current)
    verify_release(current, source=None, expected_version=version)
    if not same_tree(selected, current):
        raise ValueError("rollback did not reproduce the selected version")
    return current


def dry_run(public_url):
    build_check()
    with tempfile.TemporaryDirectory(prefix="roadmap-release-dry-run-") as temp_name:
        temp = Path(temp_name)
        first = create_release(temp / "first", public_url)
        second = create_release(temp / "second", public_url)
        first_hash = hashlib.sha256(first[2].read_bytes()).hexdigest()
        second_hash = hashlib.sha256(second[2].read_bytes()).hexdigest()
        if first_hash != second_hash:
            raise ValueError("repeated release builds produced different archives")

        current_index = first[3] / "index.html"
        current_index.write_bytes(b"rollback validation sentinel\n")
        rollback(temp / "first", first[0])
        verify_release(first[3], expected_version=first[0], expected_public_url=public_url)
        print(f"Dry run passed for {first[0]}: reproducible archive {first_hash}")
        print("Rollback validation passed: current restored from the immutable version folder")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build", help="build and verify a local release")
    build_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    build_parser.add_argument("--public-url", default="./")
    build_parser.add_argument("--dry-run", action="store_true")
    rollback_parser = subparsers.add_parser("rollback", help="restore current from an immutable version")
    rollback_parser.add_argument("version")
    rollback_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    try:
        if args.command == "build" and args.dry_run:
            dry_run(args.public_url)
        elif args.command == "build":
            build_check()
            version, version_dir, archive, current = create_release(args.output, args.public_url)
            print(f"Built Roadmap Studio {version}")
            print(f"Version: {version_dir}")
            print(f"Archive: {archive}")
            print(f"Current: {current}")
        else:
            current = rollback(args.output, args.version)
            print(f"Rolled current release back to {args.version}: {current}")
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        raise SystemExit(f"Release command failed: {error}") from error


if __name__ == "__main__":
    main()
