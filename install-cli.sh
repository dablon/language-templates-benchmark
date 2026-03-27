#!/bin/bash
# Install genlang globally from source

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$SCRIPT_DIR/scaffold-cli"

echo "🔨 Building genlang..."
cd "$CLI_DIR"

# Build and install globally
cargo install --path . --force

echo "✅ genlang installed globally!"
echo "Run 'genlang --help' to get started."