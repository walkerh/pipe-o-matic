# Set-up code for gray-box testing; automatically sourced via BASH_ENV.

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

if [[ "$VERBOSE" ]]; then
    PMATIC_OPTS='-v'
    exec 3>&1  # File handle 3 either goes to stdout or to /dev/null
else
    exec 3>/dev/null
fi

exec 2>&1

export PYTHONPATH="$TEST_PYTHONPATH"

setup() {
    set -e  # Exit upon error.
    output_path="$1"
    test_name=$(basename "$1")
    expect_path="$output_path"/expect
    execute_path="$output_path"/execute
    bin_path="$PROJECT_ROOT"/bin
    pmaticrun="$bin_path"/pmaticrun
    pmaticstatus="$bin_path"/pmaticstatus
}

check_expected() {
    if [[ $? != 0 ]]; then
        echo "Error generating $test_name/expect"
        exit 1
    fi
}

check_execute() {
    if [[ $? != 0 ]]; then
        echo "Error generating $test_name/execute"
        exit 2
    fi
}

should_fail() {
    error_id=$1
    shift
    ("$@" >&3 2>&3)  # Run command from remaining arguments
    if [[ $? == 0 ]]; then
        echo "Missing error $error_id in $test_name"
        exit 3
    elif [[ "$VERBOSE" ]]; then
        echo "Expected error $error_id received"
    fi
}

compare() {
    # ls spaz
    (diff -x pmatic -x .pmatic -qr "$expect_path" "$execute_path")
    if [[ $? != 0 ]]; then
        echo "Failed results in $test_name"
        exit 4
    fi
}
