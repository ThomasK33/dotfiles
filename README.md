# dotfiles

My personal dotfiles, managed with [chezmoi](https://www.chezmoi.io/).

## Setup

```sh
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply ThomasK33/dotfiles
```

That installs chezmoi, clones this repo, and applies the dotfiles. You'll be prompted for a git email.

> **Fresh machine:** if Homebrew or mise weren't already installed, the first apply installs them but can't put them on `PATH` for the same run. Open a new shell (or `exec $SHELL`) and run `chezmoi apply` once more — the package install scripts hash-bust on `lookPath` and will pick up the toolchain on the second pass. `install.sh` (used by Coder/Codespaces) handles this automatically.

## Coder workspaces / GitHub Codespaces

Point them at this repo as your dotfiles source. `install.sh` runs automatically:

- Installs chezmoi
- Pulls the age key from 1Password if `op` is signed in (used to decrypt `~/.aws/config` and `~/.ssh/config`)
- Runs `chezmoi init --apply`

If `op` isn't available, the encrypted files are skipped via `.chezmoiignore`. Everything else still applies.

## Encryption

The AWS and SSH configs are encrypted with [age](https://github.com/FiloSottile/age). To use them on a new machine:

1. Create a 1Password Secure Note in the `Private` vault titled `chezmoi-age-key`, paste the contents of `~/.config/chezmoi/key.txt` into the notes field.
2. On the new machine, sign into `op` CLI.
3. Run `install.sh` (or just `op read 'op://Private/chezmoi-age-key/notesPlain' > ~/.config/chezmoi/key.txt && chmod 600 ~/.config/chezmoi/key.txt`).
4. `chezmoi apply`.

Override the 1Password reference by setting `CHEZMOI_AGE_KEY_OP_REF` before running `install.sh`.

The age **public** key (recipient) lives in `.chezmoi.toml.tmpl` and is safe to share. The private key never goes in this repo.
