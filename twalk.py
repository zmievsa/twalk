from argparse import ArgumentParser
from io import TextIOWrapper
import logging
from pathlib import Path as ImportedPath

class Path(type(ImportedPath())):
    def with_stem(self, stem) -> "Path":
        return self.with_name(stem + self.suffix)

from typing import Iterator, Optional, Sequence
from typing_extensions import Literal

PROG = "twalk"
__version__ = "1.0.0"

# labels for unarchivation
LABEL_PREFIX = "182hbgovrj1l,lvlpmr3u9p420"
BEGIN_DIR_SUFFIX, END_DIR_SUFFIX, FILE_NAME_SUFFIX, BEGIN_FILE_SUFFIX, END_FILE_SUFFIX = (str(i) for i in range(1, 6))
BEGIN_DIR, END_DIR, FILE_NAME, BEGIN_FILE, END_FILE = (LABEL_PREFIX + str(i) for i in range(1, 6))


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
    iterator = iter(file_to_unarchive.read_text().split(LABEL_PREFIX))
    next(iterator) # The first element will be empty string
    _unpack_dir(next(iterator), iterator, file_to_unarchive.parent)


def _unpack_dir(current_token: str, tokens: Iterator[str], root: Path):
    dir_name = current_token[1:]
    root = root / dir_name
    root.mkdir()
    current_token = next(tokens)
    while not current_token.startswith(END_DIR_SUFFIX):
        if current_token.startswith(BEGIN_DIR_SUFFIX):
            _unpack_dir(current_token, tokens, root)

        elif current_token.startswith(FILE_NAME_SUFFIX):
            fname = current_token[1:]
            fpath = root / fname
            data = next(tokens)[1:] # BEGIN_FILE
            fpath.write_text(data)
            next(tokens) # END FILE
        current_token = next(tokens) # Token after END_FILE/END_DIR


def _get_output_file_path(path: Path) -> Path:
    output_file_path: Path = path.with_suffix(".txt")
    i: int = 1
    while output_file_path.exists():
        output_file_path = path.with_stem(f"{path.stem} ({i})").with_suffix(".txt")
        i += 1
    return output_file_path


if __name__ == "__main__":
    main()
