#!/usr/bin/env bash
set -euo pipefail

# we only want to run duroc_hog on staged files
FILES=$(git diff --staged --name-only)
OUTPUT="[]"

for FILE in $FILES; do
  RESULT=$(duroc_hog --entropy "$FILE")
  if echo "$RESULT" | jq empty > /dev/null 2>&1; then
    # Check if the result is a valid JSON object and append it to OUTPUT
    OUTPUT=$(echo "$OUTPUT" | jq ". + $RESULT")
  else
    echo "Warning: Invalid JSON from duroc_hog for file $FILE" >&2
  fi
done

# exit with an error if OUTPUT is not empty
if [ "$OUTPUT" != "[]" ]; then
  echo "$OUTPUT"
  exit 1
fi

exit 0