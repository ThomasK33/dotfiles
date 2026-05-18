#!/bin/bash
set -euo pipefail

if ! command -v curl >/dev/null 2>&1; then
  echo "curl not found; cannot bootstrap toolchain" >&2
  exit 1
fi

brew_installed=0
for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew /home/linuxbrew/.linuxbrew/bin/brew; do
  if [[ -x "$candidate" ]]; then
    brew_installed=1
    break
  fi
done
if [[ "$brew_installed" -eq 0 ]]; then
  echo "Installing Homebrew..."
  NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

if [[ ! -x "$HOME/.local/bin/mise" ]] && ! command -v mise >/dev/null 2>&1; then
  echo "Installing mise..."
  curl -fsSL https://mise.run | sh
fi
