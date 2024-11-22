import tempfile

import shutil
import time
import zipfile

import logging
import sys
import os
from pathlib import Path
from zipfile import ZipFile, BadZipFile, ZipInfo

import bagit

# The suffix of a path that contains a test_bag
BAG_SRC_SUFFIX: str = ".bag"

# Defined by LOC Bagit spec. root of data
BAG_DATA_NODE: str = "data"
# The suffix of a test_bag's folder which contains the work
# This is from the LOC BAG definition
BAG_WORK_NODE: str = str(Path(BAG_SRC_SUFFIX, BAG_DATA_NODE))
BAG_DEST_FOLDER_SUFFIX: str = "bags"


class BagErrorBead:
    """
    Detailed info about a test_bag error
    """

    def __init__(self, err_type: str, error_body: bagit.BagValidationError):
        self.err_type = err_type
        self.err_obj = error_body

    def __str__(self):
        details: str = "No detail available"
        if self.err_obj is not None:
            details = str(self.err_obj)
        return f"{self.err_type} {details}"


def archive_safe_test(zip_infos: []):
    """
    Returns if archive contains no paths outside itself, raises Error otherwise
    :type zip_infos: [ZipInfo]
    :param zip_infos: from zip infolist members for an archive. To be meaningful,
    it should be the complete archive
    :return:
    """
    if len([x.filename for x in zip_infos if x.filename.startswith('/') or x.filename.startswith('..')]) > 0:
        raise ValueError("Dangerous paths found in archive. Will not continue")


def validate_bag(test_bag: bagit.Bag, bag_errors_p: [()], n_processes: int) -> bool:
    """
    Validates a bag
    :param n_processes: Some contexts (e.g. docker) can't multiprocess
    :param test_bag: Bagit Bag object
    :param bag_errors_p: List of tuples(errorMnemonic:str, error
    :return: success flag in return code, and  bag_errors_p with populated data
    """

    bag_errors_p.clear()

    try:
        test_bag.validate(processes=n_processes)
    except bagit.BagValidationError as e:
        for d in e.details:
            if isinstance(d, bagit.ChecksumMismatch):
                bag_errors_p.append(("ChecksumFail", str(d)))
            if isinstance(d, bagit.FileMissing):
                bag_errors_p.append(("FileMissing", str(d)))
            if isinstance(d, bagit.UnexpectedFile):
                bag_errors_p.append(("UnexpectedFile", str(d)))
            else:
                bag_errors_p.append(("UnknownError", str(d)))

    return len(bag_errors_p) == 0


def log_bag_errors(bag_errors: [()]):
    """
    logs the objects in the list of tuples
    :param bag_errors:
    :return:
    """
    for bag_error in bag_errors:
        logging.error("{} {}", bag_error[0], bag_error[1])


def stupid_python_fix_times(stupid_zip_infos: [ZipInfo], dest_path: Path) -> None:
    """
    Handles the stupidity of the macOS python zip file not retaining mod times.
    On call, all the files in the ZipInfo list must exist.
    Sets access and mod times to the original time listed in the zip file
    :param stupid_zip_infos: ZipInfos from stupid zip file
    :param dest_path: destination path of zip parent (because zipInfos are relative)
    to the output root
    :return:
    """
    for f in stupid_zip_infos:
        name, date_time = f.filename, f.date_time
        target_path: Path = dest_path / name
        #
        # This line removes time zone
        date_time = time.mktime(date_time + (0, 0, -1))
        os.utime(target_path, (date_time, date_time))


def debag(bag_arcname: str, output_path_p: str, in_daemon: bool = True) -> [Path]:
    """
    Extracts bags from an archive and validates them
    :param bag_arcname: Zipped test_bag (source) Must contain one or more directory entries
    ending in .test_bag. Each of these is considered to be a test_bag created by BDRC.
    :param output_path_p: Parent of all the destinations
    zip members which are [A-Z0-9]+.test_bag
    ??? What if test_bag contains multiple Zips? So, scratch the work_name param
    Output tree:
    output_path_p
    +
    +--------WXXXX     Path(output_path_p / bag_work_name )
    |
    +------- bags/   dest_bag_path: == dest_path_parent / BAGS_FOLDER_SUFFIX
             +
             |
             +------  WXXXXX.test_bag/   when extracted, bag_path. bag_work_name is the WXXX part of the test_bag
                        +
                        |
                        +--- test_bag-specific files - don't care
                                    +
                                    |
                                    +-------- data/   The actual work
    :return:
    """

    n_processes = 1 if in_daemon else 6
    dest_path_parent: Path = Path(output_path_p)
    ei: object = None
    bag_errors: [] = []
    extracted_bag_paths: [Path] = []

    try:
        with ZipFile(bag_arcname, 'r') as bz:
            arc_members_infolist: [] = bz.infolist()

            # Reject unsafe archives (which contain references to members outside themselves)
            archive_safe_test(arc_members_infolist)

            # Test if there are any of our bags in the archive
            bag_zip_infos: [ZipInfo] = [arc_bag for arc_bag in arc_members_infolist if
                                        arc_bag.is_dir() and arc_bag.filename.endswith(BAG_SRC_SUFFIX + '/')]
            if len(bag_zip_infos) == 0:
                raise ValueError(
                    f"Zip {bag_arcname} not created by BDRC Bag. Must contain Directories ending in {BAG_SRC_SUFFIX} ")

            # Make the destination path

            dest_bag_path: Path = Path(dest_path_parent, BAG_DEST_FOLDER_SUFFIX)
            if not os.path.exists(dest_bag_path):
                os.mkdir(dest_bag_path)  # Just use system defaults

            logging.info(f"Extracting {dest_bag_path}")
            # Extractall doesnt preserve dates and times.
            bz.extractall(dest_bag_path)
            stupid_python_fix_times(arc_members_infolist, dest_bag_path)
            logging.info(f"Done extracting {dest_bag_path}")

            for bag_zip_info in bag_zip_infos:
                bag_path: Path = Path(dest_bag_path, bag_zip_info.filename)
                bag_zip_info = bagit.Bag(str(bag_path))
                if not validate_bag(bag_zip_info, bag_errors, n_processes):
                    log_bag_errors(bag_errors)
                else:
                    # Make a link to the bagged file in the destination directory
                    # TODO Put the work_rid in the test_bag metadata

                    # Assumption: the test_bag's work name is the STEM name of the unzipped folder.
                    # e.g. /parent/parent/.../somewhere/W12345.test_bag
                    # Path('/parent/parent/.../somewhere/W12345.test_bag').stem
                    # Out[6]: 'W12345'
                    bag_work_name = bag_path.stem
                    #
                    # We thought about using a work name, except that there could be more than one work in a test_bag.
                    # bag_work_name = work_name if work_name else bag_path.name.split(BAG_SRC_SUFFIX)[0]

                    # NB DANGER_WILL_ROBINSON you have to rsync with the -L option if you rsync a link
                    # ?? Is this putting files in data/ ? Because they're not in there when you manually unzip
                    # os.symlink(bag_path / BAG_DATA_NODE, Path(dest_path, bag_work_name))

                    # So, for background compatibility and space-saving, move the data/ in each test_bag into the
                    # dest_file_path, using the test_bag directory name with the '.test_bag' removed.
                    work_bag_dest_path: Path = Path(output_path_p, bag_work_name)
                    if os.path.exists(work_bag_dest_path):
                        if os.path.isdir(work_bag_dest_path):
                            logging.debug(f"Removing directory {work_bag_dest_path} (shutil.rmtree)")
                            shutil.rmtree(work_bag_dest_path)
                        else:
                            logging.debug(f"Removing file  {work_bag_dest_path}")
                            os.remove(work_bag_dest_path)
                    os.rename(bag_path / BAG_DATA_NODE, work_bag_dest_path)
                    extracted_bag_paths.append(work_bag_dest_path)
    except BadZipFile:
        ei = sys.exc_info()
        logging.error(ei[1])
        # raise ValueError(f"Bad Zip File: {bag_arcname}", ei)
    except FileNotFoundError:
        ei = sys.exc_info()
        logging.error(ei[1])
    except ValueError:
        ei = sys.exc_info()
        logging.error(ei[1])
    except IOError as ioe:
        ei = sys.exc_info()
        logging.error(ei[1])
        raise IOError from ioe

    if ei is None:
        logging.info(f"all well. Removing {bag_arcname}")
        os.remove(bag_arcname)
        return extracted_bag_paths


# reserved tags
# Per https://datatracker.ietf.org/doc/rfc8493/?include_text=1
# --source-organization SOURCE_ORGANIZATION
# --organization-address ORGANIZATION_ADDRESS
# --contact-name CONTACT_NAME
# --contact-phone CONTACT_PHONE
# --contact-email CONTACT_EMAIL
# --external-description EXTERNAL_DESCRIPTION
# --external-identifier EXTERNAL_IDENTIFIER
# --test_bag-size BAG_SIZE
# --test_bag-group-identifier BAG_GROUP_IDENTIFIER
# --test_bag-count BAG_COUNT
# --internal-sender-identifier INTERNAL_SENDER_IDENTIFIER
# --internal-sender-description INTERNAL_SENDER_DESCRIPTION
# --bagit-profile-identifier BAGIT_PROFILE_IDENTIFIER

def bag(bag_src: str, bag_dest: str, preserve_source: bool, in_daemon: bool, do_append: bool = False,
        append_dest: str = None):
    """
    Creates a test_bag from the source
    :param bag_src: Path to work to test_bag. Can be a pre-existing test_bag
    :param bag_dest: directory to contain resulting zip archive of test_bag
    :param preserve_source: True if you want to preserve the source, false if you
    want to override it.
    :return:
    """

    n_processes: int = 1 if in_daemon else 6
    # name of destination, under bag_dest
    dest_base_name = Path(bag_src).name

    # Easiest way to always remove the tmp dir
    with tempfile.TemporaryDirectory() as bag_temp_dir:
        # Test if we're zipping an already existing test_bag
        try:
            dest_bag = bagit.Bag(bag_src)
        except bagit.BagError:
            # Existing source is not a bag. Make new one.
            if preserve_source:
                # should result in bag_temp_dir/dest_base_name
                save_dir: Path = Path(bag_temp_dir, dest_base_name)
                bag_src: str = shutil.copytree(bag_src, save_dir)
                logging.info(f"Preserving source in {bag_src}")
            dest_bag = bagit.make_bag(bag_src, processes=n_processes, checksums=['sha512'])

        bag_errors: [] = []
        # If the given folder is not a test_bag, make one from it
        if not validate_bag(dest_bag, bag_errors, n_processes):
            log_bag_errors(bag_errors)
            sys.exit(1)

        dest_bag.info['BDRC-RID'] = dest_base_name  # Assume it's the RID
        dest_bag.save(manifests=True, processes=n_processes)

        # Create a zip that contains top level folders named WXXXX.test_bag

        archive_root: Path = Path(dest_base_name + BAG_SRC_SUFFIX )
        output_archive_path: Path = Path(bag_dest, archive_root.name + ".zip") if not do_append else Path(append_dest)
        archive_mode = 'w' if not do_append else 'a'
        logging.info(f"{'Creating' if not do_append else 'Appending'} {output_archive_path}")
        # if os.path.exists(output_archive_path):
        #     os.remove(output_archive_path)

        # We don't bother with compression - it takes
        # too long, and the image files don't compress a lot
        try:
            with zipfile.ZipFile(output_archive_path,  archive_mode) as zf:
                zf.write(bag_src, arcname=archive_root)
                for root, dirs, files in os.walk(bag_src):
                    # Write the dirs first
                    for zip_dir in dirs:
                        dn: Path = Path(root, zip_dir)
                        adn: Path = Path(archive_root, dn.relative_to(bag_src))
                        zf.write(dn, arcname=adn)
                    for file in files:
                        fn: Path = Path(root, file)
                        afn: Path = Path(archive_root, fn.relative_to(bag_src))
                        zf.write(fn, arcname=afn)
        except:
            ei = sys.exc_info()
            logging.error(ei[1], exc_info=1)
