from setuptools import setup, find_packages

#
# Simpler than simple:
# python setup.py install
# And then you have in your $PYTHON/bin (on MacOS)
# ls -l $(dirname $(which getNamedWorks))
# (py361) jimk@Druk:BdrcDbLib$ ls -l $(dirname $(which getNamedWorks))
# total 312
# ...
# -rwxr-xr-x   1 jimk  staff   413 Jun 19 17:31 getNamedWorks
# and this is an executable script which wraps the entry points
#
# Debian

# Default, if there is no readme
long_description = ('#BDRC specific bagging and debagging\n')

# https://stackoverflow.com/questions/63416546/twine-is-defaulting-long-description-content-type-to-text-x-rst
long_description_content_type='text/x-rst'
try:
    import pypandoc

    long_description = pypandoc.convert_file('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README.md').read()
    long_description_content_type = 'text/markdown'

import os
print(os.getcwd())
for dd in os.scandir('.'):
    print(dd)

print(find_packages('./src'))
setup(
    name='bdrc-bag-jimk-test',

    version='0.0.01',

    packages=find_packages(),
    author='jimk',
    author_email='jimk@bdrc.io',
    description='BDRC Bagging',
    long_description_content_type=long_description_content_type,
    long_description=long_description,
    install_requires=['bdrc-util', 'bagit'],
    python_requires='>=3.7',
    classifiers=["Programming Language :: Python :: 3",
                 "License :: OSI Approved :: GNU GPL v3",
                 "Operating System :: OS Independent",
                 "Intended Audience :: System Administrators",
                 "Development Status :: 4 - Beta"],
    # entry_points={
    #     'console_scripts': [
    #         'locate_archive = archive_ops.shell_ws:locate_archive',
    #         'migrate_works.locker = migrate_works.MigrateLocks:migration_lock_control',
    #         'migrate_works = migrate_works.migrate_works:migrate_works_shell',
    #         'log_dip = archive_ops.DipLog:dip_log_shell',
    #         'get_works_for_activity = archive_ops.GetReadyWorksForStates:get_works_states_shell',
    #         'update_work_facts = archive_ops.SaveWorkFacts:save_work_facts_shell',
    #         'disk_igs_for_work = util_lib.GetFromBUDA:get_ig_folders_from_igs',
    #         'buda_ig_from_disk = util_lib.GetFromBUDA:buda_ig_from_disk',
    #         'disk_ig_from_buda = util_lib.GetFromBUDA:disk_ig_from_buda',
    #         'get_buda_image_count = util_lib.GetFromBUDA:get_image_count',
    #         'validate_glacier = migrate_works.measure_archive_fixity:maf_main'
    #     ]
    # }
)
