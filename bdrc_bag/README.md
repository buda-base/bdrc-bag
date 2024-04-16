# Packaging BDRC Bag applications
BDRC has been packaging its internal utilities as `pip` modules,
but you can build and ship standalone modules which contain all their requirements.

They get large, so we'd have to package multiple commands into a module.
Since you can only specify one entry point (unlike pip, where you can emit many commands using the same module, you can only have one entry point per archive,
you c

(Deprecated) - Direct file system access on Synology NAS
is unknown - SYnology embeds their share control files in the
target file systems.
Installing bdrc-bag utility on Synology NAS

- install Python3 package using DSM
- Connect to your Synology NAS through ssh
- Install pip
- wget https://bootstrap.pypa.io/get-pip.py
- sudo python3 get-pip.py
- Script will let you know where 'pip' is now installed.  Make sure to add to your PATH.

** Hyper important. The build system has changed:
```bash
pip install --upgrade build
python -m build
```

The `setup.py` is deprecated.  The new build system is `pyproject.toml` 

# Changelog
| version | commit                                                                                               | description                             |
|---------|------------------------------------------------------------------------------------------------------|-----------------------------------------|
| 0.0.04  | [d9d656df](https://github.com/buda-base/archive-ops/commit/d9d656df90e5db0fd8cacff81e002b6a56609111) | Incrementally add a bag to its zip      | 
| 0.0.03  | [ec875566](https://github.com/buda-base/archive-ops/commit/ec875566a0c389da6af4c5583ba8182f45a47c59) | Support single process to run in docker | 