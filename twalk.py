from argparse import ArgumentParser
from io import TextIOWrapper
import logging
from pathlib import Path as ImportedPath

class Path(type(ImportedPath())):
    def with_stem(self, stem) -> "Path":
        return self.with_name(stem + self.suffix)

from typing import Optional, Sequence, Tuple
from typing_extensions import Literal

PROG = "twalk"
__version__ = "0.1.0"

# labels for unarchivation
LABEL_PREFIX = "182hbgovrj1l,lvlpmr3u9p420"
BEGIN_DIR = LABEL_PREFIX + "OPEN_DIR"
END_DIR = LABEL_PREFIX + "END_DIR"
FILE_NAME = LABEL_PREFIX + "FILE_NAME"
BEGIN_FILE = LABEL_PREFIX + "FILE_BEGIN"
END_FILE = LABEL_PREFIX + "FILE_END"


logger = logging.getLogger(PROG)
logger.setLevel(logging.WARNING)


def main(argv: Optional[Sequence[str]] = None):
    parser = ArgumentParser(
        PROG,
        description="Condense a directory tree into a single txt file or extract it from one",
    )

    parser.add_argument("mode", choices=("pack", "unpack"), help="What to do with the specified path")
    parser.add_argument("path", type=Path, help="path to directory you wish to (un)pack")
    parser.add_argument("-V", "--verbose", action="store_true", default=False)
    parser.add_argument("-v", "--version", action="store_true", default=False)

    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        exit(0)
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    mode: Literal["pack", "unpack"] = args.mode
    path: Path = args.path

    if mode == "unpack":
        if not path.is_file():
            raise ValueError(f"{path} is not a file.")
        _new_unpack(path)
    elif mode == "pack":
        if not path.is_dir():
            raise ValueError(f"{path} is not a directory.")
        try:
            _new_pack(path)
        except ValueError as e:
            # This might be caught in a different case entirely...
            raise ValueError("I do not and will not support binary or any other strange files. Sowwy.") from e


def _new_pack(dir_to_archive: Path):
    output_file_path = _get_output_file_path(dir_to_archive)
    with output_file_path.open("w") as output:
        _pack(dir_to_archive, output)


def _pack(dir_to_archive: Path, output: TextIOWrapper):
    output.write(f"{BEGIN_DIR}{Path(dir_to_archive).name}")
    for path in dir_to_archive.iterdir():
        if path.is_dir():
            _pack(path, output)
        elif path.is_file():
            output.write(f"{FILE_NAME}{path.name}{BEGIN_FILE}{path.read_text()}{END_FILE}")
        else:
            logger.warn(f"Path type of '{path}' is not supported.")
    output.write(END_DIR)


def _new_unpack(file_to_unarchive: Path):
    _unpack(file_to_unarchive.read_text(), file_to_unarchive.parent)


def _unpack(text: str, root: Path) -> str:
    text = remove_prefix(text, BEGIN_DIR)
    dir_name, text = pop_data(text)
    root = root / dir_name
    root.mkdir()
    while not text.startswith(END_DIR):
        if text.startswith(BEGIN_DIR):
            text = _unpack(text, root)

        elif text.startswith(FILE_NAME):
            text = remove_prefix(text, FILE_NAME)
            fname, text = pop_data(text)
            text = remove_prefix(text, BEGIN_FILE)
            fpath = root / fname
            data, text = pop_data(text)
            fpath.write_text(data)
            text = remove_prefix(text, END_FILE)
    text = remove_prefix(text, END_DIR)
    return text


def remove_prefix(s: str, prefix: str) -> str:
    return s[len(prefix) :]


def pop_data(s: str) -> Tuple[str, str]:
    data = s[: s.find(LABEL_PREFIX)]
    return data, s[len(data) :]


def _get_output_file_path(path: Path) -> Path:
    output_file_path: Path = path.with_suffix(".txt")
    i: int = 1
    while output_file_path.exists():
        output_file_path = path.with_stem(f"{path.stem} ({i})").with_suffix(".txt")
        i += 1
    return output_file_path


if __name__ == "__main__":
    main()
