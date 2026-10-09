"""Build and verify the single-skill ZIP offered to readers."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import hashlib

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "user-growth-six-steps"
TARGET = ROOT / "dist" / "user-growth-six-steps.zip"


def main():
    files = sorted(p for p in SKILL.rglob("*") if p.is_file()
                   and not any(part.startswith(".") or part == "__pycache__"
                               for part in p.relative_to(SKILL).parts)
                   and p.suffix not in (".pyc", ".pyo"))
    if not (SKILL / "SKILL.md") in files:
        raise ValueError("Missing SKILL.md")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(TARGET, "w", compression=ZIP_DEFLATED) as archive:
        for path in files:
            info = ZipInfo((Path(SKILL.name) / path.relative_to(SKILL)).as_posix())
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    with ZipFile(TARGET) as archive:
        assert len(archive.infolist()) == len(files)
        assert archive.testzip() is None
        for path in files:
            member = (Path(SKILL.name) / path.relative_to(SKILL)).as_posix()
            assert archive.read(member) == path.read_bytes(), member
    print(f"{TARGET}\nVerified {len(files)} files; SHA256 {hashlib.sha256(TARGET.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
