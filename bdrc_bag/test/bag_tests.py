#!/usr/bin/env python3
import os
import tempfile
from pathlib import Path
from pprint import pp

import pytest
from tempfile import TemporaryDirectory

# This imports from site-packages
# from bdrc_bag.src.bdrc_bag import bag_ops
from bdrc_bag.src.bdrc_bag import bag_ops

_bag: Path
test_bag_work: Path

media: [str] = ["images", "archive"]


@pytest.fixture(autouse=True)
def build_bag():
    """
    Create the config file used in the tests
    """
    global _bag
    global test_bag_work
    _bag = Path(TemporaryDirectory().name)
    test_bag_work = _bag / "Work1"
    for medium in media:
        for ig in range(1, 3):
            bag_src_home: Path = test_bag_work / "images" / f"w1-ig{ig}"
            os.makedirs(bag_src_home, exist_ok=True)
            # Create a couple of file
            for i in range(1, 4):
                with open(bag_src_home / f"ig{ig}{i:0>4}.txt", "w") as f:
                    f.write(f"I'm file{i}.txt")

    # make other non ig related
    for non_ig_media in ["meta", "sources"]:
        for non_ig in range(1, 3):
            non_ig_dir: Path = test_bag_work / non_ig_media / f"{non_ig_media}_files{non_ig}"
            os.makedirs(non_ig_dir, exist_ok=True)
            for i in range(1, 5):
                with open(non_ig_dir / f"ig{non_ig}{i:0>4}.txt", "w") as f:
                    f.write(f"I'm file{i}.txt")


@pytest.mark.parametrize("is_daemon", [True, False])
def test_bag(is_daemon: bool):
    assert Path.exists(test_bag_work)
    # Make a destination
    with TemporaryDirectory() as td:
        bag_dst = Path(td)
        bag_ops.bag(str(test_bag_work), str(bag_dst), True, in_daemon=is_daemon)
        assert Path.exists(bag_dst)
        assert bag_dst.is_dir()
        assert bag_dst / "data" / "w1-ig1" / "ig10001.txt"
        # Unbag it
        with TemporaryDirectory() as td2:
            bag_ops.debag(str(bag_dst / "Work1.bag.zip"), td2, is_daemon)
            test_root: Path = Path(td2) / "Work1" / "images" / "w1-ig1"
            assert Path.exists(test_root / "ig10001.txt")
            assert Path.exists(test_root / "ig10002.txt")
            assert Path.exists(test_root / "ig10003.txt")
            assert not Path.exists(Path(td2) / "data")


@pytest.mark.parametrize("is_daemon", [True, False])
def test_debag(is_daemon: bool):
    bag_artifact = "Work1.bag.zip"
    assert Path.exists(test_bag_work)
    # Make a destination
    with TemporaryDirectory() as td:
        bag_dst = Path(td)
        bag_ops.bag(str(test_bag_work), str(bag_dst), True, in_daemon=False)
        assert Path.exists(bag_dst)
        assert bag_dst.is_dir()

        created_bag_path: Path = bag_dst / bag_artifact
        assert Path.exists(created_bag_path)
        # The above created 'Work1.bag.zip" in bag_dst
        # Unbag it
        with TemporaryDirectory() as td2:
            bag_ops.debag(str(created_bag_path), td2, is_daemon)
            extracted_bag_images = Path(td2, "Work1", "images")
            for i in range(1, 3):
                assert Path.exists(extracted_bag_images / "w1-ig1" / f"ig1{i:0>4}.txt")
            assert Path.exists(Path(td2) / "bags")



def test_segmented():
    """
    Test internal of appending bags to a zipped bag.
    :param do_append:append to existing file?
    :type do_append:bool
    :param append_to_name:where to append to
    :type append_to_name:Path
    :return:
    """
    assert Path.exists(test_bag_work)
    # Make a destination
    td = tempfile.mkdtemp()
#     with TemporaryDirectory(dir=append_to_name) as td:
    bag_parent_path = Path(td)

    # exclude list, for later
    exclude_list:[] = []
    #
    # create bags for media subdirs of test_bag_work
    # TODO: next, test inverted media
    for medium in media:
        to_bag: Path = test_bag_work / medium
        if not os.path.exists(to_bag):
            continue
        bag_ops.bag(str(to_bag), str(bag_parent_path), True, in_daemon=False, do_append=False)
        assert Path.exists(bag_parent_path /f"{medium}.bag.zip")
        exclude_list.append(test_bag_work / medium)
    assert bag_parent_path.is_dir()


    # Build a bag out of the other things
    # Append the bag to a named zip in the directory

    append_dest: Path = bag_parent_path / f"{test_bag_work.name}.bag.zip"
    for non_wig_media in os.listdir(test_bag_work):
        non_wig_path: Path = Path(non_wig_media)
        if non_wig_media in media:
            pp(f"Skipping {non_wig_path}")
            continue
        bag_ops.bag(str(test_bag_work / non_wig_path), str(bag_parent_path), True, in_daemon=False, do_append=True,append_dest = append_dest)
    assert Path.exists(bag_parent_path)
    assert bag_parent_path.is_dir()

    assert Path.exists(append_dest)
    # The above created 'Work1.bag.zip" in bag_dst
    # Unbag it
    with TemporaryDirectory() as td2:
        #
        # Debag all zips in the assembly directory
        for zip_file in os.listdir(bag_parent_path):
            bag_ops.debag(str(bag_parent_path / zip_file), td2, False)
        # bag_ops.debag(str(append_dest), td2, False)

        # Find the images
        extracted_bag_images = Path(td2,  "images")
        for i in range(1, 3):
            assert Path.exists(extracted_bag_images / "w1-ig1" / f"ig1{i:0>4}.txt")

        # Find the non ig media
        for non_ig_media in ["meta", "sources"]:
            for non_ig in range(1, 3):
                non_ig_dir: Path = Path(td2) / non_ig_media / f"{non_ig_media}_files{non_ig}"
                for i in range(1, 5):
                    assert Path.exists(non_ig_dir / f"ig{non_ig}{i:0>4}.txt")
        # And make sure the debagged bags are there
        assert Path.exists(Path(td2) / "bags")
        assert (Path(td2) / "bags").is_dir()
