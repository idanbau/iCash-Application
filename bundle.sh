#!/usr/bin/env bash

OUTPUT="project_bundle.txt"

# Empty the output file if it exists
: > "$OUTPUT"

# Find all .py, .html, .css files, ignoring any hidden (.something) directories at any depth
find . \
  -path '*/.*' -prune -o \
  -type f \( -name "*.py" -o -name "*.html" -o -name "*.css" \) -print |
  sort |
  while IFS= read -r file
do
  {
    echo "===== FILE: $file ====="
    cat "$file"
    echo
    echo
  } >> "$OUTPUT"
done
