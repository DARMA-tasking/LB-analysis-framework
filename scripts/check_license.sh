#!/usr/bin/env bash

path_to_lbaf=${1}
cd "$path_to_lbaf" || exit 1

for sub_dir in "src" "tests/unit" "tests/perf" "tutorial" "examples" "tools"
do
  "$path_to_lbaf/scripts/add-license-perl.pl" "$path_to_lbaf/$sub_dir" "$path_to_lbaf/scripts/license-template"
done

result=$(git diff --name-only)

if [ -n "$result" ]; then
  echo -e "Following files have incorrect license!\n"
  echo "$result"
  exit 1
fi