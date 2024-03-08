#!/usr/bin/env bash
#
# Builds a standalone executable from the sources


ME_DIR=$(dirname "$0")
srcDir="src/bdrc-bag"
pushd=
if [[ $ME_DIR != "." ]] ;then
  pushd  "${ME_DIR}" 2>&1 /dev/null || echo "${ME_DIR}" can\'t be found ; exit 1 ;
  pushd=1
fi
cp $srcDir/bag_main.py $srcDir/bag_ops.py ./bagSync
# Build the executable from sources
python3 -m zipapp bagSync/  -m "bag_main:main" -o bdrc-bag -p "/usr/bin/env python3"

# Keep Shellcheck happy

if [[ -n $pushd ]] ; then
popd || exit 1
fi