#!/usr/bin/env python3
"""
De bag
Given a Zip Archive file containing a bag,
1. Unzip to a temporary destination
2. validate the bag in the temporary destination
3. If it validates, move the payload in "data" to the specified output.
Usage: unzip-debag bag_archive_location data_location Top_level_article_name
"""
import logging

import argparse
from typing import Any, AnyStr

from bag.bag_ops import *

def reallypath(what_path: AnyStr) ->  Any:
    """
    Resolves everything about the path
    :param what_path: Pathlike object
    :return: fully resolved path
    """
    from os import path

    # jimk #499: detect non-file paths and don't expand
    if what_path is None:
        return None
    # Regex more elegant, but need fast way to say UNCs must be at beginning
    if what_path.find('://') > 0 or what_path.startswith('//') or what_path.startswith('\\'):
        return what_path

    return path.realpath(path.expandvars(path.expanduser(what_path)))

logger = logging.getLogger(__name__)


def must_exist_directory(path_str: str):
    """
    Argparse type specifying a string which represents
    an existing file path
    :param path_str: String repr of a path
    :return:
    """
    real_path: Path = reallypath(path_str)
    if not os.path.exists(real_path):
        logger.error(f"{str(real_path)} not found")
        raise argparse.ArgumentError(message="{str(real_path)} not found")
    if not os.path.isdir(real_path):
        logger.error(f"{str(real_path)} not a directory")
        raise argparse.ArgumentError(message= f"{str(real_path)} not a directory")
    if not os.access(real_path, os.F_OK):
        logger.error(f"{str(real_path)} not accessible")
        raise argparse.ArgumentError(message= f"{str(real_path)} not accessible")
    if not os.access(real_path, os.R_OK or os.W_OK or os.X_OK):
        logging.error(f"{str(real_path)} not a writable directory")
        raise argparse.ArgumentError(message= f"{str(real_path)} not a writable directory")
    return real_path

def parse_args() -> argparse.Namespace:
    """
    Returns unzip_args
    :rtype: object
    """
    ap = argparse.ArgumentParser(usage="-[d|b] [-p] [-t] src dst",
                                 description="Unzips a LOC Bag, validates it, and extracts the payload")
    ops_args = ap.add_mutually_exclusive_group(required=True)
    ops_args.add_argument("-d", "--debag", action='store_true', help="unzip and debag")
    ops_args.add_argument("-b", "--bag", action='store_true', help="bag and zip")
    ap.add_argument("-v", "--verbose", action='store_true', help="Verbose")
    ap.add_argument("-p", "--preserve", action='store_true', help="Preserve Original Source", default=False)
    ap.add_argument("-t", "--tempdir", help="Override system temporary directory. Created if not exists")
    ap.add_argument("-i", "--in-daemon", help="We're in a daemon, so don't multiprocess - DONT USE ON COMMAND LINE!", action='store_true')

    ap.add_argument("src", help="Source directory, if bagging, source zip if debagging")
    ap.add_argument("dst", help="if bagging, container for zipped bag. If debagging, container for work")
    # Not required until we debag any bags, not just ours
    #    ap.add_argument("work_name", help="Work Name (RID) - required for bagging, optional if debagging", nargs="*")

    parsed_args:object = ap.parse_args()
    parsed_args.src = reallypath(parsed_args.src)
    parsed_args.dst = reallypath(parsed_args.dst)
    if parsed_args.tempdir is not None:
        parsed_args.tempdir = reallypath(parsed_args.tempdir)

    return parsed_args


def check_space(src: str, dst: str, tmp: str, preserve: bool) -> bool:
    """
    Validates that there is enough space on 'dest' and 'tmp' to hold the contents of 'src'
    :param src: source to test
    :param dst: destination path
    :param tmp: tmp directory (used to prepare zip)
    :param preserve: true if you're copying source, not making a bag in place
    :return: true if there is enough free space on both the dest and tmp
    false otherwise. Returns false if dst are empty, or do not exist
    """

    # Calc the space of src

    err_try: str = None
    if not src:
        logger.error("src must be non-empty ")
        return False

    if not dst:
        logger.error("dst must be non-empty ")
        return False

    src_contents_size: int = 0

    if os.path.isdir(src):
        for path, dirs, files in os.walk(src):
            for f in files:
                fp = os.path.join(path, f)
                src_contents_size += os.path.getsize(fp)
    else:
        src_contents_size = os.path.getsize(src)

    rc: bool = True

    try:
        err_try = dst
        dst_stat = os.statvfs(dst)

        dst_free: int = dst_stat.f_bavail * dst_stat.f_frsize
        if dst_free < src_contents_size:
            logging.error("Source %s requires %s free bytes on destination. %s contains only %s ",
                          src, format(src_contents_size, ','),
                          dst, format(dst_free, ','))
            rc = False

        err_try = tmp
        tmp_stat = os.statvfs(tmp)

        tmp_free: int = tmp_stat.f_bavail * tmp_stat.f_frsize

        # If you're preserving, you're using twice the space on tmp, so report twice as much needed
        required_contents_size: int = src_contents_size * (1 if not preserve else 2)

        if tmp_free < src_contents_size:
            logging.error("Source %s requires %s free bytes on temp file system, %s contains only %s",
                          src, format(required_contents_size, ','),
                          tmp, format(tmp_free, ','))
            rc = False

    except FileNotFoundError:
        rc = False
        logger.error("Directory %s not found,", err_try, exc_info=1)

    return rc


def main():
    _args = parse_args()

    # Better logger, to not log sub-modules
    # Thx https://stackoverflow.com/questions/38668496/python3-logging-exclude-certain-modules
    # log_format = '[%(asctime)s] [%(levelname)s] - %(message)s'
    global logger
    log_level = logging.INFO if not _args.verbose else logging.DEBUG
    h = logging.StreamHandler()
    h.setLevel(log_level)
    logger.addHandler(h)

    os.makedirs(_args.dst, exist_ok=True)

    if _args.tempdir is not None:
        # Create all upper directories if necessary.
        os.makedirs(_args.tempdir, exist_ok=True)
        tempfile.tempdir = _args.tempdir

    # args.preserve only applies to bagging operations
    check_space(_args.src, _args.dst, tempfile.gettempdir(), _args.preserve & _args.bag)

    if _args.debag:
        debag(_args.src, _args.dst, _args.in_daemon)
    if _args.bag:
        bag(_args.src, _args.dst, _args.preserve, _args.in_daemon)


if __name__ == "__main__":
    main()
