#!/usr/bin/env python3
import os
from pathlib import Path

import pytest
from tempfile import TemporaryDirectory

from bdrc_bag.src.bdrc_bag import bag_ops

_bag: Path
test_bag_work: Path


@pytest.fixture(autouse=True)
def build_bag():
    """
    Create the config file used in the tests
    """
    global _bag
    global test_bag_work
    _bag = Path(TemporaryDirectory().name)
    test_bag_work = _bag / "Work1"
    bag_src_home: Path = test_bag_work / "images" / "w1-ig1"
    os.makedirs(bag_src_home, exist_ok=True)
    # Create a couple of file
    for i in range(1, 4):
        with open(bag_src_home / f"ig1{i:0>4}.txt", "w") as f:
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
            extracted_bag_images = Path(td2 , "Work1" , "images")
            for i in range(1,3):
                assert Path.exists(extracted_bag_images / "w1-ig1" / f"ig1{i:0>4}.txt")
            assert Path.exists(Path(td2) / "bags")
