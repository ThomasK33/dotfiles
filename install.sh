#!/usr/bin/env bash
# Bootstrap script auto-invoked by `coder dotfiles` and GitHub Codespaces.
# Installs chezmoi (if missing), fetches the age key from 1Password when
# available, applies this repo's dotfiles, then hands machine setup
# (Homebrew, brew packages, repo clones, tools) to `mise bootstrap`.
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

# Pull the age private key from 1Password so chezmoi can decrypt the
# encrypted files. Skipped silently when `op` isn't installed or no
# session is active (typical for Coder workspaces / Codespaces); the
# .chezmoiignore gate then excludes the encrypted files from apply.
# Override the reference by setting CHEZMOI_AGE_KEY_OP_REF in the environment.
AGE_KEY_FILE="${HOME}/.config/chezmoi/key.txt"
OP_AGE_KEY_REF="${CHEZMOI_AGE_KEY_OP_REF:-op://Private/chezmoi-age-key/notesPlain}"
if [[ ! -f "${AGE_KEY_FILE}" ]] &&
  command -v op >/dev/null 2>&1 &&
  op whoami </dev/null >/dev/null 2>&1; then
  mkdir -p "$(dirname "${AGE_KEY_FILE}")"
  if op read "${OP_AGE_KEY_REF}" </dev/null >"${AGE_KEY_FILE}.tmp" 2>/dev/null &&
    [[ -s "${AGE_KEY_FILE}.tmp" ]]; then
    chmod 600 "${AGE_KEY_FILE}.tmp"
    mv "${AGE_KEY_FILE}.tmp" "${AGE_KEY_FILE}"
  else
    rm -f "${AGE_KEY_FILE}.tmp"
  fi
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

# --force: provisioning runs non-interactively (Coder rebuilds, Codespaces),
# so overwrite drifted targets instead of prompting — same semantics as the
# `chezmoi apply --force` the pre-mise-bootstrap version of this script ran.
# DOTFILES_DEFER_BOOTSTRAP keeps the converge-machine bridge script from
# running `mise bootstrap` mid-apply; we run it ourselves below.
DOTFILES_DEFER_BOOTSTRAP=1 chezmoi init --apply --force --promptString "git email=${GIT_EMAIL}"

# The apply above put ~/.config/mise/config.toml in place; `mise bootstrap`
# does the rest in one ordered pass: Homebrew via the pre-packages hook,
# [bootstrap.packages], [bootstrap.repos], [tools], and the bootstrap task.
# The subcommand needs mise >= 2026.7, so install/refresh mise when it's
# missing or too old (mise.run installs to ~/.local/bin, which is first on
# PATH here and therefore wins over any older mise elsewhere).
export PATH="${HOME}/.local/bin:${PATH}"
MISE_VERSION="$(mise version 2>/dev/null | cut -d' ' -f1 || true)"
if [[ "$(printf '%s\n2026.7.0\n' "${MISE_VERSION}" | sort -V | head -n1)" != "2026.7.0" ]]; then
  echo "Installing mise..."
  curl -fsSL https://mise.run | sh
fi
cd "${HOME}"
exec mise bootstrap --yes
