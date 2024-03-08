#!/usr/bin/env bash
#
# Builds a standalone executable from the sources


ME_DIR=$(dirname "$0")
PY_MODULE="bdrc_bag"
BAG_LIB=bagSync

srcDir="src/${PY_MODULE}"

if [[ $ME_DIR != "." ]] ;then
  pushd  "${ME_DIR}" 2>&1 /dev/null || echo "${ME_DIR}" can\'t be found ; exit 1 ;
  ppd=1
fi

mkdir -p ./"${BAG_LIB}"/"${PY_MODULE}"
cp $srcDir/bag_main.py $srcDir/bag_ops.py $srcDir/__init__.py ./"${BAG_LIB}"/"${PY_MODULE}"
# Build the executable from sources
python3 -m zipapp bagSync/  -m "bdrc_bag.bag_main:main" -o bdrc-bag -p "/usr/bin/env python3"

# Keep Shellcheck happy

if [[ -n $ppd ]] ; then
popd || exit 1
fi