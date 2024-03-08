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
