#!/usr/bin/env bash
# Bootstrap script auto-invoked by `coder dotfiles` and GitHub Codespaces.
# Installs chezmoi (if missing) and applies this repo's dotfiles.
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v chezmoi >/dev/null 2>&1; then
    BIN_DIR="${HOME}/.local/bin"
    mkdir -p "${BIN_DIR}"
    sh -c "$(curl -fsLS get.chezmoi.io)" -- -b "${BIN_DIR}"
    export PATH="${BIN_DIR}:${PATH}"
fi

# Link the cloned dotfiles into chezmoi's default source dir so subsequent
# `chezmoi` invocations work without --source.
CHEZMOI_SRC="${HOME}/.local/share/chezmoi"
if [[ "${SOURCE_DIR}" != "${CHEZMOI_SRC}" ]] && [[ ! -e "${CHEZMOI_SRC}" ]]; then
    mkdir -p "$(dirname "${CHEZMOI_SRC}")"
    ln -s "${SOURCE_DIR}" "${CHEZMOI_SRC}"
fi

# .chezmoi.toml.tmpl prompts for "git email"; resolve a value so init is non-interactive.
GIT_EMAIL="${GIT_AUTHOR_EMAIL:-${EMAIL:-}}"
if [[ -z "${GIT_EMAIL}" ]]; then
    GIT_EMAIL="$(git config --global --get user.email 2>/dev/null || true)"
fi
if [[ -z "${GIT_EMAIL}" ]] && [[ -n "${GITHUB_USER:-}" ]]; then
    GIT_EMAIL="${GITHUB_USER}@users.noreply.github.com"
fi
: "${GIT_EMAIL:=$(whoami)@$(hostname)}"

exec chezmoi init --apply --promptString "git email=${GIT_EMAIL}"
