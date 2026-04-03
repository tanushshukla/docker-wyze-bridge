#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(grep '^VERSION=' "${ROOT_DIR}/app/.env" | cut -d'=' -f2-)"

echo "⚠️  AMD64-only helper. Use scripts/release.sh for normal releases."
echo ""

declare -a TAG_ARGS
if [ "$#" -gt 0 ]; then
    TAG_ARGS=("$@")
else
    TAG_ARGS=("${VERSION}")
fi

IMAGE_NAME="${IMAGE_NAME:-aleximurdoch/wyze-bridge}" \
PLATFORMS="linux/amd64" \
PUSH="${PUSH:-true}" \
bash "${ROOT_DIR}/scripts/release.sh" "${TAG_ARGS[@]}"
