#!/bin/bash
# Bumps all manifest.json versions in custom_components/ to match the given version tag.
# Usage: ./scripts/bump-manifest.sh <version>
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

VERSION="$1"
MANIFEST_DIR="custom_components"

if [ ! -d "$MANIFEST_DIR" ]; then
    echo "Error: $MANIFEST_DIR not found"
    exit 1
fi

find "$MANIFEST_DIR" -name "manifest.json" | while read -r manifest; do
    component=$(basename "$(dirname "$manifest")")
    # Use python for portable JSON editing
    python3 -c "
import json, sys
with open('$manifest', 'r+') as f:
    data = json.load(f)
    old = data.get('version', 'unknown')
    data['version'] = '$VERSION'
    f.seek(0)
    json.dump(data, f, indent=2)
    f.truncate()
print(f'$component: {old} → $VERSION')
"
done

echo "---"
echo "Run: git add -A && git commit -m 'chore: bump to v$VERSION' && git tag v$VERSION && git push origin main --tags"
