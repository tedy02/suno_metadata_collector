#!/usr/bin/env bash
set -euo pipefail
# Normalize CRLF to LF for common text files
exts=(py sh yml yaml md json toml cfg ini txt csv)
for ext in "${exts[@]}"; do
  # Use perl for portability across BSD/GNU
  find . -type f -name "*.${ext}" -print0 | xargs -0 perl -i -pe 's/\r$//'
done
# Handle dotfiles explicitly
for name in .gitignore .gitattributes; do
  if [ -f "$name" ]; then perl -i -pe 's/\r$//' "$name"; fi
done
echo "Normalized LF line endings."
