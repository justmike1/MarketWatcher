#!/bin/bash
# shellcheck disable=SC2181

scripts_folder=$(dirname "${BASH_SOURCE[0]}")
root_folder=$scripts_folder/..

success=0

./"$scripts_folder"/format_all.sh -c

echo -n "Running pylint..."
pylint "$root_folder/bot/marketwatcher.py" --rcfile="$root_folder"/.pylintrc
if [ $? -ne 0 ]; then
	success=1
fi

exit $success
