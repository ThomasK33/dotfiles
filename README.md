# dotfiles

My personal dotfiles. [chezmoi](https://www.chezmoi.io/) owns the files
(templates + age-encrypted secrets); [`mise bootstrap`](https://mise.jdx.dev/bootstrap.html)
owns machine setup, declared in `mise_config.toml` (= `~/.config/mise/config.toml`):

- `[bootstrap.packages]` — brew formulas
- `[bootstrap.repos]` — third-party checkouts (tpm), converged on every run
- `[bootstrap.hooks.pre-packages]` — installs Homebrew itself
- `[tools]` — everything else, pinned
- `[tasks.bootstrap]` — one-time clones of self-managed repos (nvim config,
  jj-ai), darwin-only formulas and all casks via real brew, agent-skill
  symlinks

## Setup

```sh
git clone https://github.com/ThomasK33/dotfiles.git ~/.local/share/chezmoi
~/.local/share/chezmoi/install.sh
```

`install.sh` installs chezmoi and mise if missing (or if mise predates
`bootstrap`, 2026.7), applies the dotfiles, and finishes with
`mise bootstrap --yes`. It's non-interactive: the git email comes from
`GIT_AUTHOR_EMAIL`/`EMAIL`/global git config, falling back to
`whoami@hostname` — on a brand-new personal machine, run it as
`GIT_AUTHOR_EMAIL=you@example.com ./install.sh`.

Day-to-day, `chezmoi apply` converges the files and — via a `run_onchange`
bridge script — re-runs `mise bootstrap --yes` whenever `mise_config.toml` or
the synced skills changed, so pulling config changes on another machine still
installs its packages. Run `mise bootstrap --yes` directly to force a
converge, or `mise bootstrap status` to inspect state; topgrade also runs it
as a custom command.

## Coder workspaces / GitHub Codespaces

Point them at this repo as your dotfiles source. `install.sh` runs automatically:

- Installs chezmoi
- Pulls the age key from 1Password if `op` is signed in (used to decrypt `~/.aws/config` and `~/.ssh/config`)
- Runs `chezmoi init --apply --force` (non-interactive: overwrites drifted managed files)
- Installs mise if missing or too old, then runs `mise bootstrap --yes`

If `op` isn't available, the encrypted files are skipped via `.chezmoiignore`. Everything else still applies.

## Encryption

The AWS and SSH configs are encrypted with [age](https://github.com/FiloSottile/age). To use them on a new machine:

1. Create a 1Password Secure Note in the `Private` vault titled `chezmoi-age-key`, paste the contents of `~/.config/chezmoi/key.txt` into the notes field.
2. On the new machine, sign into `op` CLI.
3. Run `install.sh` (or just `op read 'op://Private/chezmoi-age-key/notesPlain' > ~/.config/chezmoi/key.txt && chmod 600 ~/.config/chezmoi/key.txt`).
4. `chezmoi apply`.

Override the 1Password reference by setting `CHEZMOI_AGE_KEY_OP_REF` before running `install.sh`.

The age **public** key (recipient) lives in `.chezmoi.toml.tmpl` and is safe to share. The private key never goes in this repo.
