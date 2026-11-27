"""Read the same English directing skill from a checkout, zipapp or wheel."""
import os
import tempfile
import zipfile
from importlib.resources import files
from pathlib import Path

from .brief import TakeError


def skill_root():
    packaged = files("takeferry").joinpath("_skill")
    if packaged.joinpath("SKILL.md").is_file():
        return packaged
    source = Path(__file__).resolve().parents[1] / "skills" / "takeferry"
    if (source / "SKILL.md").is_file():
        return source
    raise TakeError("The directing skill is missing from this distribution.")


def skill_files(directory, prefix=""):
    for item in sorted(directory.iterdir(), key=lambda child: child.name):
        name = prefix + item.name
        if item.is_dir() and not item.name.startswith((".", "__")):
            yield from skill_files(item, name + "/")
        elif item.is_file() and (item.name == "LICENSE" or item.name.endswith((".md", ".json"))):
            yield name, item


def export_skill(destination):
    destination = Path(destination)
    if destination.exists():
        raise TakeError("Choose a new ZIP filename for the skill.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            for name, item in skill_files(skill_root()):
                info = zipfile.ZipInfo("takeferry/" + name)
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, item.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
        os.link(temporary, destination)
    finally:
        temporary.unlink()
    return destination
