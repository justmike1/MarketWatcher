#!/bin/bash

p_args=(--write)
p_log="Running prettier"

log="Running black & isort"
if [[ "$1" = "--check" || "$1" = "-c" ]]; then
	log="$log in check only mode"
	p_log="$p_log in check only mode"
	args=(--check)
	p_args=(--check)
fi

echo "$log..."

black . "${args[@]}"
isort . "${args[@]}"

echo "$p_log..."

npx prettier . "${p_args[@]}"
