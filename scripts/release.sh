#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/app/.env"
IMAGE_NAME="${IMAGE_NAME:-aleximurdoch/wyze-bridge}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
GITHUB_SHA="$(git -C "${ROOT_DIR}" rev-parse HEAD 2>/dev/null || echo "unknown")"
PUSH="${PUSH:-true}"
NO_CACHE="${NO_CACHE:-false}"

if [ ! -f "${ROOT_DIR}/docker/Dockerfile" ]; then
    echo "❌ Error: docker/Dockerfile not found. Run from project root."
    exit 1
fi

if [ ! -f "${ENV_FILE}" ]; then
    echo "❌ Error: app/.env not found."
    exit 1
fi

VERSION="$(grep '^VERSION=' "${ENV_FILE}" | cut -d'=' -f2-)"
if [ -z "${VERSION}" ]; then
    echo "❌ Error: VERSION is not set in app/.env."
    exit 1
fi

if [[ ! "${VERSION}" =~ ^wyze-[0-9]+\.[0-9]+\.[0-9]+([.-][A-Za-z0-9]+)?$ ]]; then
    echo "❌ Error: VERSION must look like wyze-x.y.z. Found '${VERSION}'."
    exit 1
fi

declare -a TAGS
if [ "$#" -gt 0 ]; then
    TAGS=("$@")
else
    TAGS=("${VERSION}" "latest")
fi

declare -a TAG_ARGS
for tag in "${TAGS[@]}"; do
    TAG_ARGS+=(-t "${IMAGE_NAME}:${tag}")
done

declare -a BUILD_CMD=(
    docker buildx build
    --platform "${PLATFORMS}"
    --build-arg "BUILD_DATE=${BUILD_DATE}"
    --build-arg "BUILD_VERSION=${VERSION}"
    --build-arg "GITHUB_SHA=${GITHUB_SHA}"
)

if [ "${NO_CACHE}" = "true" ]; then
    BUILD_CMD+=(--no-cache)
fi

if [ "${PUSH}" = "true" ]; then
    BUILD_CMD+=(--push)
fi

BUILD_CMD+=("${TAG_ARGS[@]}" -f "${ROOT_DIR}/docker/Dockerfile" "${ROOT_DIR}")

echo "════════════════════════════════════════════════════════"
echo "🚀 Docker Wyze Bridge Release"
echo "════════════════════════════════════════════════════════"
echo "Image:      ${IMAGE_NAME}"
echo "Version:    ${VERSION}"
echo "Tags:       ${TAGS[*]}"
echo "Platforms:  ${PLATFORMS}"
echo "Build Date: ${BUILD_DATE}"
echo "Commit:     ${GITHUB_SHA}"
echo "Push:       ${PUSH}"
echo "════════════════════════════════════════════════════════"
echo ""
echo "🔨 Running release build..."
"${BUILD_CMD[@]}"

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Release Build Complete"
echo "════════════════════════════════════════════════════════"
for tag in "${TAGS[@]}"; do
    echo "docker pull ${IMAGE_NAME}:${tag}"
done
