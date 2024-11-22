# BDRC Bagging
Uses the Library of Congress bag standard, implemented by the python `bagit` project [bagit 1.8.1](https://pypi.org/project/bagit/) to create and unpack bags of BDRC works.

**Hyper important. The build system has changed**:
```bash
pip install --upgrade build
python -m build --wheel
```

The `setup.py` is deprecated.  The new build system is `pyproject.toml`


## Usage 

```bash
❯ bdrc-bag --help
usage: -[d|b] [-p] [-t] src dst

Unzips a LOC Bag, validates it, and extracts the payload

positional arguments:
src                   Source directory, if bagging, source zip if debagging
dst                   if bagging, container for zipped bag. If debagging, container for work

options:
-h, --help            show this help message and exit
-d, --debag           unzip and debag
-b, --bag             bag and zip
-v, --verbose         Verbose
-p, --preserve        Preserve Original Source
-t TEMPDIR, --tempdir TEMPDIR
Override system temporary directory. Created if not exists
-i, --in-daemon       We're in a daemon, so don't multiprocess - DONT USE ON COMMAND LINE!
``` 

# Packaging BDRC Bag applications
BDRC has been packaging its internal utilities as `pip` modules,
but you can build and ship standalone modules which contain all their requirements.

They get large, so we'd have to package multiple commands into a module.
Since you can only specify one entry point (unlike pip, where you can emit many commands using the same module, you can only have one entry point per archive,

To build a standalone executable, you run two programs in the `bdrc-bag` directory:
`./setup-bag-build.sh` which prepares the executable's self-contained runtime environment`
`./build-bag-exe.sh` which builds the executable

# Deprecated functionality
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

# Changelog
| version | commit                                                                                               | description                                              |
|---------|------------------------------------------------------------------------------------------------------|----------------------------------------------------------|
| 0.0.07  | [67985c1](https://github.com/buda-base/bdrc-bag/commit/67985c1a9c734155f266ea04e088eae506a75cb0)     | fix error handling bug                                   | 
| 0.0.06  | [b6b0f13](https://github.com/buda-base/bdrc-bag/commit/b6b0f139eed92316083098eeb963c46cec398209)     | transition to standalone and pyproject.toml installation | 
| 0.0.04  | [d9d656df](https://github.com/buda-base/archive-ops/commit/d9d656df90e5db0fd8cacff81e002b6a56609111) | Incrementally add a bag to its zip                       | 
| 0.0.03  | [ec875566](https://github.com/buda-base/archive-ops/commit/ec875566a0c389da6af4c5583ba8182f45a47c59) | Support single process to run in docker                  | 