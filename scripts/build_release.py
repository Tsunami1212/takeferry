"""Build the portable Python application from this checkout. No build dependencies."""
import argparse
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(archive, name, body):
    entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
    entry.create_system = 3
    entry.external_attr = (stat.S_IFREG | 0o644) << 16
    entry.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(entry, body)


def build(output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    modules = sorted((ROOT / "takeferry").glob("*.py"))
    samples = sorted((ROOT / "takeferry" / "data" / "rainy-door").glob("*"))
    skill = ROOT / "skills" / "takeferry"
    guides = sorted(path for path in skill.rglob("*")
                    if path.is_file() and (path.name == "LICENSE" or path.suffix in (".md", ".json")))
    with zipfile.ZipFile(output, "x") as archive:
        write(archive, "__main__.py", b"from takeferry.__main__ import main\nraise SystemExit(main())\n")
        # Directory entries let importlib.resources traverse samples in a zipapp.
        for name in ("takeferry/", "takeferry/data/", "takeferry/data/rainy-door/"):
            write(archive, name, b"")
        names = [("takeferry/_skill/" + p.relative_to(skill).as_posix(), p) for p in guides]
        directories = {parent.as_posix() + "/" for name, _ in names for parent in Path(name).parents
                       if parent.as_posix() not in (".", "takeferry")}
        for directory in sorted(directories):
            write(archive, directory, b"")
        for name, source in names:
            write(archive, name, source.read_bytes())
        for file in modules + samples + [ROOT / "LICENSE", ROOT / "THIRD_PARTY_NOTICES.md"]:
            write(archive, file.relative_to(ROOT).as_posix(), file.read_bytes())
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    print(build(parser.parse_args().output))
