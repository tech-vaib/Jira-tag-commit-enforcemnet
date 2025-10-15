#!/usr/bin/env bash
# Setup script to configure shared git hooks directory

set -e

HOOKS_DIR="$(dirname "$0")"
git config core.hooksPath "$HOOKS_DIR"

echo "✅ Git hooks configured successfully to use: $HOOKS_DIR"
