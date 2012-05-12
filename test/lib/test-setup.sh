# Set-up code for testing; meant to be sourced

# Author: Walker Hale (hale@bcm.edu), 2012
#         Human Genome Sequencing Center, Baylor College of Medicine
#
# This file is part of Pipe-o-matic.
#
# Pipe-o-matic is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pipe-o-matic is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pipe-o-matic.  If not, see <http://www.gnu.org/licenses/>.

if [[ "$TEST_SETUP_INVOKED" ]]; then
    return
fi

echo
echo ======================================================================
date

export TEST_SETUP_INVOKED=Y
if [[ "$1" == '-v' ]]; then
    export VERBOSE=1
else
    export VERBOSE=''
fi
export PROJECT_ROOT=$(dirname "$TEST_ROOT")
export PMATIC_BASE="$TEST_ROOT"/pmatic_base

export TEST_PYTHONPATH="$PROJECT_ROOT"/lib:"$PROJECT_ROOT"/test/lib
export TEST_PYTHONPATH="$TEST_PYTHONPATH":"$PROJECT_ROOT"/local/lib

# Install PyYAML into local if missing.
if [[ ! -d "$PROJECT_ROOT"/local/lib/yaml ]]; then
    echo 'Building local/lib...'
    mkdir -p "$PROJECT_ROOT"/local/downloads "$PROJECT_ROOT"/local/lib
    cd "$PROJECT_ROOT"/local/downloads
    curl -O http://pyyaml.org/download/pyyaml/PyYAML-3.10.tar.gz
    tar xzf PyYAML-3.10.tar.gz
    cd ..
    ln -s ../downloads/PyYAML-3.10/lib/yaml lib
    cd ..
    echo 'done'
fi

if [[ "$VERBOSE" ]]; then
    echo TEST_SETUP_INVOKED=$TEST_SETUP_INVOKED
    echo "TEST_PYTHONPATH=$TEST_PYTHONPATH"
fi

cd "$TEST_ROOT"
