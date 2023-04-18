# This script will be mounted into the worker container and
# will install apt packages and python libraries needed by
# the customised metadata-worker

# Please add needed packages and libraries below

echo "Installing apt packages"

# example for installing xsltproc
#apt-get install -y xsltproc

echo "Installing python libraries"

# installing python packages
poetry add httpx
poetry add psycopg2-binary
