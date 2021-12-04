#!/usr/bin/env python3

from argparse import ArgumentParser, Namespace
from io import TextIOWrapper
import logging
from pathlib import Path
from typing import Iterator, Optional, Sequence

PROG = "twalk"
PACK_MODE = "pack"
UNPACK_MODE = "unpack"
__version__ = "1.0.13"

# labels for unarchivation

# We hope that this character never appears in source code
LABEL_PREFIX = "\u2042"
__suffixes = [str(i) for i in range(1, 6)]
BEGIN_DIR_SUFFIX, END_DIR_SUFFIX, FILE_NAME_SUFFIX, BEGIN_FILE_SUFFIX, END_FILE_SUFFIX = __suffixes
BEGIN_DIR, END_DIR, FILE_NAME, BEGIN_FILE, END_FILE = (LABEL_PREFIX + s for s in __suffixes)


logger = logging.getLogger(PROG)
logging.basicConfig(level=logging.WARNING, handlers=[logging.StreamHandler()])


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = _parse_args(argv)
    if args.silent:
        logger.disabled = True
    elif args.verbose:
        logger.setLevel(logging.DEBUG)

    mode: str = args.mode
    path: Path = args.path.resolve()
    ignore_binary: bool = args.ignore_binary
    if mode == UNPACK_MODE:
        if not path.is_file():
            raise ValueError(f"{path} is not a file.")
        _new_unpack(path)
    elif mode == PACK_MODE:
        logger.debug(f"ROOT PATH: {path}")
        if not path.is_dir():
            raise ValueError(f"{path} is not a directory.")
        try:
            _new_pack(path, ignore_binary)
        except ValueError as e:
            raise ValueError(
                """
                I do not and will not support binary or any other strange files.
                You see, this script might be used to circumvent some security measures
                and I'm fine with that as long as security measures do not make sense
                in your case. However, if you try to pack binary files, then I completely
                agree with security measures and believe that you should not be able to 
                hide them in a txt file.
                """
            ) from e


def _parse_args(argv: Optional[Sequence[str]]) -> Namespace:
    parser = ArgumentParser(
        PROG,
        description="Condense a directory tree into a single txt file or extract it from one",
    )

    parser.add_argument("mode", choices=(PACK_MODE, UNPACK_MODE), help="What to do with the specified path")
    parser.add_argument("path", type=Path, help="path to directory you wish to (un)pack")
    parser.add_argument(
        "-i",
        "--ignore_binary",
        action="store_true",
        default=False,
        help="Instead of raising an exception when encountering\n binary files during packing, skip them altogether",
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)

    logging_group = parser.add_mutually_exclusive_group()
    logging_group.add_argument("-V", "--verbose", action="store_true", default=False)
    logging_group.add_argument("-s", "--silent", action="store_true", default=False)

    return parser.parse_args(argv)


def _new_pack(dir_to_archive: Path, ignore_binary: bool) -> None:
    # Pathlib counts any dot as a suffix
    output_file_path = _get_non_existing_path(dir_to_archive.with_name(f"{dir_to_archive.name}.txt"))
    try:
        with output_file_path.open("w", encoding="utf-8") as output:
            _pack_dir(dir_to_archive, output, ignore_binary)
    except Exception as e:
        if output_file_path.exists():
            output_file_path.unlink()
        raise e


def _pack_dir(dir_to_archive: Path, output: TextIOWrapper, ignore_binary: bool) -> None:
    logger.debug(f"PACKING DIR: {dir_to_archive}'")
    output.write(f"{BEGIN_DIR}{Path(dir_to_archive).name}")
    for path in dir_to_archive.iterdir():
        if path.is_dir():
            _pack_dir(path, output, ignore_binary)
        elif path.is_file():
            _write_file_to_output(output, path, ignore_binary)
        else:
            logger.warning(f"Path type of '{path}' is not supported. Skipping.")
    output.write(END_DIR)


def _write_file_to_output(output: TextIOWrapper, path: Path, ignore_binary: bool) -> None:
    if ignore_binary:
        try:
            output.write(f"{FILE_NAME}{path.name}{BEGIN_FILE}{path.read_text()}{END_FILE}")
        except UnicodeDecodeError:
            logger.warning(f"Skipping binary file '{path}'")
    else:
        output.write(f"{FILE_NAME}{path.name}{BEGIN_FILE}{path.read_text()}{END_FILE}")


def _new_unpack(file_to_unarchive: Path) -> None:
    tokens = iter(file_to_unarchive.read_text(encoding="utf-8").split(LABEL_PREFIX))
    next(tokens)  # The first element will be empty string because file starts with DIR_OPEN
    _unpack_dir(next(tokens), tokens, file_to_unarchive.parent)


def _unpack_dir(current_token: str, tokens: Iterator[str], root: Path) -> None:
    root = _get_non_existing_path(root / current_token[1:])
    root.mkdir()
    current_token = next(tokens)
    while not current_token.startswith(END_DIR_SUFFIX):
        if current_token.startswith(BEGIN_DIR_SUFFIX):
            _unpack_dir(current_token, tokens, root)

        elif current_token.startswith(FILE_NAME_SUFFIX):
            fpath = root / current_token[1:]  # FILE_NAME (name)
            fpath.write_text(next(tokens)[1:])  # BEGIN_FILE (contents)
            next(tokens)  # END FILE
        current_token = next(tokens)  # Token after END_FILE/END_DIR


def _get_non_existing_path(path: Path) -> Path:
    logger.debug(f"GETTING NON-EXISTING PATH FOR '{path}'")
    output_path: Path = path
    i: int = 1
    while output_path.exists():
        # with_stem cannot be used in 3.6
        output_path = path.with_name(f"{path.stem} ({i}){path.suffix}")
        i += 1
    return output_path


if __name__ == "__main__":
    main()
