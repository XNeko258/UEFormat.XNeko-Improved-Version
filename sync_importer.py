"""Verify that importer/ is byte-identical between the two distributions.

Usage:
    python sync_importer.py --check
    python sync_importer.py --fix --source standalone
    python sync_importer.py --fix --source toolbox
"""

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

STANDALONE = Path("io_scene_ueformat/importer")
TOOLBOX = Path("tools/importers/ueformat/_importer")


def compare_dirs(a: Path, b: Path) -> list[str]:
    diffs = []
    a_files = {p.relative_to(a) for p in a.rglob("*") if p.is_file()}
    b_files = {p.relative_to(b) for p in b.rglob("*") if p.is_file()}
    for rel in sorted(a_files | b_files):
        pa, pb = a / rel, b / rel
        if not pa.exists():
            diffs.append(f"missing in standalone: {rel}")
        elif not pb.exists():
            diffs.append(f"missing in toolbox: {rel}")
        elif not filecmp.cmp(pa, pb, shallow=False):
            diffs.append(f"differs: {rel}")
    return diffs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--source", choices=["standalone", "toolbox"])
    args = parser.parse_args()

    if not STANDALONE.is_dir() or not TOOLBOX.is_dir():
        print("ERROR: run from repository root.")
        return 1

    diffs = compare_dirs(STANDALONE, TOOLBOX)
    if not diffs:
        print("OK: importer/ copies are identical.")
        return 0

    print("DIFFERENCES FOUND:")
    for d in diffs:
        print(f"  {d}")

    if not args.fix:
        return 2
    if not args.source:
        print("\n--fix requires --source")
        return 1

    src = STANDALONE if args.source == "standalone" else TOOLBOX
    dst = TOOLBOX if args.source == "standalone" else STANDALONE
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"\nCopied {src} -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())