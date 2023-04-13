# This script will be mounted into the worker container and
# will install apt packages and python libraries needed by
# the customised metadata-worker

# Please add needed packages and libraries below

echo "Installing apt packages"

# example for installing xsltproc
apt-get install -y xsltproc

echo "Installing python libraries"

# example for installing python library lxml
poetry add lxml
