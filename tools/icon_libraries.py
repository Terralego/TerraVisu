import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import TypedDict

import cairosvg


class MetaItem(TypedDict):
    name: str
    aliases: list[str]
    tags: list[str]


class IndexItem(TypedDict):
    name: str
    id: str


ICON_LIBRARIES_ROOT = Path("public/media/icon-libraries")
REPO_CONFIG = {
    "mdi": {
        "path": "https://github.com/Templarian/MaterialDesign.git",
        "name": "Material Design Icons",
    }
}
PNG_SIZE = 64


def clone_repo(repo_url: str, target_path: Path) -> None:
    """Clone a git repository to the specified directory."""
    print(f"Cloning {repo_url}")
    if target_path.exists():
        shutil.rmtree(target_path)
    _ = subprocess.run(["git", "clone", repo_url, target_path], check=True)


class Mdi:
    def run(self, clone_path: Path, target_path: Path, json_path: Path):
        source_svg_path = clone_path / "svg"
        print(f"Generating icons to {target_path}")
        self.copy_svg_folder(source_svg_path, target_path)
        self.process_meta_json(clone_path, json_path)

    def copy_svg_folder(self, source_dir: Path, target_dir: Path) -> None:
        """Copy the svg folder from source to target."""
        print("Clearing previous icons")
        if target_dir.exists():
            shutil.rmtree(target_dir)
        print("Converting svg to png")
        if not target_dir.exists():
            os.makedirs(target_dir)
        svg_files = [f for f in source_dir.glob("*.svg")]
        num_svg = len(svg_files)
        current_index = 1
        for svg_file in source_dir.glob("*.svg"):
            png_file = target_dir / f"{svg_file.stem}.png"
            cairosvg.svg2png(
                url=str(svg_file),
                write_to=str(png_file),
                output_height=PNG_SIZE,
                output_width=PNG_SIZE,
            )
            print(f"{current_index}/{num_svg}", end="\r")
            current_index += 1
        print()

    def process_meta_json(self, clone_path: Path, json_path: Path) -> None:
        """Process meta.json, keeping only name, aliases, and tags."""
        print("Generating icons.json")
        meta_path = clone_path / "meta.json"
        with open(meta_path, encoding="utf-8") as f:
            data: list[MetaItem] = json.load(f)

        result: list[MetaItem] = []
        for item in data:
            result.append(
                {
                    "name": item.get("name"),
                    "aliases": item.get("aliases"),
                    "tags": item.get("tags"),
                }
            )

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f)


def generate_libraries_index():
    index_path = ICON_LIBRARIES_ROOT / "index.json"
    print(f"Creating libraries index at {index_path}")
    subdirectories = [item for item in ICON_LIBRARIES_ROOT.iterdir() if item.is_dir()]
    libraries_index: list[IndexItem] = []
    for subdir in subdirectories:
        if subdir.name in REPO_CONFIG:
            libraries_index.append(
                {"id": subdir.name, "name": REPO_CONFIG[subdir.name]["name"]}
            )
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(libraries_index, f)


def check_library(library: str):
    if library not in REPO_CONFIG:
        error_str = f"Unkown library '{library}'. Supported libraries are {[r for r in REPO_CONFIG]}."
        raise ValueError(error_str)


def check_cwd():
    script_path = Path("tools/icon_libraries.py")
    if not script_path.exists():
        error_str = "This script must be run from the project root."
        raise ValueError(error_str)


def main(library: str):
    check_library(library)
    check_cwd()

    target_path = ICON_LIBRARIES_ROOT / library
    clone_path = Path("/tmp") / library
    json_path = target_path / "icons.json"

    clone_repo(REPO_CONFIG[library]["path"], clone_path)
    Mdi().run(clone_path, target_path, json_path)
    print("Cleaning up cloned repo")
    shutil.rmtree(clone_path)
    generate_libraries_index()
    print("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    _ = parser.add_argument(
        "--library",
        type=str,
        default="mdi",
        help="Icon library to clone (only 'mdi' supported for now).",
    )
    args = parser.parse_args()
    library: str = args.library
    main(library)
