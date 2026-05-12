# Project and worktree navigation helpers.
# Three groups: mux/tmux project flow, jj workspaces, git worktrees.

# Mux
cx() {
  local dir=$(find ~/.mux/src -mindepth 2 -maxdepth 2 -type d | sed "s|$HOME/.mux/src/||" | fzf)
  [ -n "$dir" ] && cd "$HOME/.mux/src/$dir" && tmux rename-window "$dir"
}

cdev() {
  local dir
  if [ -n "$1" ]; then
    dir="$1"
  else
    dir=$(find ~/.mux/src -mindepth 2 -maxdepth 2 -type d | sed "s|$HOME/.mux/src/||" | fzf)
  fi

  [ -z "$dir" ] && return 0

  local full_path="$HOME/.mux/src/$dir"
  [ ! -d "$full_path" ] && { echo "Directory not found: $full_path"; return 1; }

  # Allow direnv before cd so the hook can load the environment
  [ -f "$full_path/.envrc" ] && direnv allow "$full_path"

  # Change to the project directory - direnv hook fires here
  cd "$full_path" || return 1

  # Trigger nix-direnv cache build if needed
  nix-direnv-reload

  # Rename the window to the selected directory
  tmux rename-window "$dir"

  # Split horizontally to create right pane
  tmux split-window -h -c "$full_path"

  # Type make start in the right pane (without executing)
  tmux send-keys "make start"

  # Select the left pane and run make dev
  tmux select-pane -L
  tmux send-keys "make dev" Enter

  # Switch back to the right pane
  tmux select-pane -R
}

cdev-new() {
  local dir
  if [ -n "$1" ]; then
    dir="$1"
  else
    dir=$(find ~/.mux/src -mindepth 2 -maxdepth 2 -type d | sed "s|$HOME/.mux/src/||" | fzf)
  fi

  [ -z "$dir" ] && return 0

  local full_path="$HOME/.mux/src/$dir"
  [ ! -d "$full_path" ] && { echo "Directory not found: $full_path"; return 1; }

  # Create new tmux window in the project directory
  tmux new-window -c "$full_path" -n "$dir"

  # Allow direnv before the new window so hook loads env on cd
  [ -f "$full_path/.envrc" ] && direnv allow "$full_path"

  # nix-direnv-reload to build cache if needed
  tmux send-keys 'nix-direnv-reload' Enter
  sleep 1

  # Run make dev in the left pane
  tmux send-keys "make dev" Enter

  # Split horizontally to create right pane
  tmux split-window -h -c "$full_path"

  # Type make start in the right pane (without executing)
  tmux send-keys "make start"
}

cpull() {
  # Ensure we're in a git repo
  git rev-parse --git-dir > /dev/null 2>&1 || { echo "Not in a git repository"; return 1; }

  # Get project name from main worktree's folder name
  local main_worktree=$(git worktree list | head -1 | awk '{print $1}')
  local project=$(basename "$main_worktree")

  local pr_number branch

  if [ -n "$1" ]; then
    # Argument provided: look up PR by branch name
    branch="$1"
    pr_number=$(gh pr list --state open --head "$branch" --json number --jq '.[0].number')
    [ -z "$pr_number" ] && { echo "No open PR found for branch: $branch"; return 1; }
  else
    # No argument: use fzf to select PR
    local pr=$(gh pr list --state open --limit 100 --json number,title,headRefName \
      --template '{{range .}}{{.number}}	{{.headRefName}}	{{.title}}{{"\n"}}{{end}}' | \
      fzf --delimiter='\t' \
          --with-nth=1,2,3 \
          --preview 'gh pr view {1}' \
          --preview-window=right:60%:wrap)

    [ -z "$pr" ] && return 0

    # Extract PR number and branch name
    pr_number=$(echo "$pr" | cut -f1)
    branch=$(echo "$pr" | cut -f2)
  fi

  # Sanitize branch name (replace slashes with dashes)
  local safe_branch=$(echo "$branch" | tr '/' '-')

  # Determine worktree path
  local worktree_path="$HOME/.mux/src/$project/$safe_branch"

  # Check if worktree already exists - update it if so
  if [ -d "$worktree_path" ]; then
    echo "Worktree exists, updating: $worktree_path"
    git -C "$worktree_path" pull --ff-only
    local ret=$?
    echo "Run: cdev $project/$safe_branch"
    return $ret
  fi

  # Fetch the PR branch and create worktree
  git -C "$main_worktree" fetch origin "pull/$pr_number/head:$branch" 2>/dev/null || git -C "$main_worktree" fetch origin "$branch" 2>/dev/null

  # Create the worktree from main repo
  git -C "$main_worktree" worktree add "$worktree_path" "$branch"

  # Set upstream so git pull/push work without extra args
  git -C "$worktree_path" branch --set-upstream-to="origin/$branch"

  echo "Created worktree at: $worktree_path"
  echo "Run: cdev $project/$safe_branch"
}

px() {
  local plan=$(find ~/.mux/plans -mindepth 2 -maxdepth 2 -type f -name "*.md" | sed "s|$HOME/.mux/plans/||" | fzf)
  [ -n "$plan" ] && nvim "$HOME/.mux/plans/$plan"
}

# JJ Workspace shortcuts
jx() {
  local dir=$(find ~/.jj-workdirs/ -mindepth 1 -maxdepth 1 -type d | sed "s|$HOME/.jj-workdirs/||" | fzf)
  [ -n "$dir" ] && cd "$HOME/.jj-workdirs/$dir"
}

jn() {
  [ -z "$1" ] && { echo "Usage: jn <workspace-name>"; return 1; }
  jj workspace add "$HOME/.jj-workdirs/$1" && cd "$HOME/.jj-workdirs/$1"
}

jd() {
  local dir=$(find ~/.jj-workdirs/ -mindepth 1 -maxdepth 1 -type d | sed "s|$HOME/.jj-workdirs/||" | fzf --prompt="Delete workspace> ")
  [ -z "$dir" ] && return 0
  echo -n "Delete workspace '$dir'? [y/N] "
  read -r confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Cancelled"; return 0; }
  local project_dir=$(cat "$HOME/.jj-workdirs/$dir/.jj/repo" 2>/dev/null | sed 's|/.jj/repo$||')
  jj workspace forget "$dir" && rm -rf "$HOME/.jj-workdirs/$dir" && echo "Deleted workspace '$dir'"
  [ -n "$project_dir" ] && [ -d "$project_dir" ] && cd "$project_dir"
}

jroot() {
  local repo_file="$PWD/.jj/repo"
  [ -f "$repo_file" ] || { echo "Not in a jj workspace"; return 1; }
  local main_dir=$(cat "$repo_file" 2>/dev/null | sed 's|/.jj/repo$||')
  [ -d "$main_dir" ] && cd "$main_dir" || { echo "Main repo not found: $main_dir"; return 1; }
}

# Git Worktree shortcuts
gx() {
  git rev-parse --git-dir &>/dev/null || { echo "Not in a git repo"; return 1; }
  local dir=$(git worktree list | fzf --prompt="Worktree> " | awk '{print $1}')
  [ -n "$dir" ] && cd "$dir"
}

gn() {
  [ -z "$1" ] && { echo "Usage: gn <branch-name>"; return 1; }
  git rev-parse --git-dir &>/dev/null || { echo "Not in a git repo"; return 1; }
  local repo=$(basename "$(git rev-parse --show-toplevel)")
  local target="$HOME/.git-worktrees/$repo/$1"
  git worktree add "$target" "$1" 2>/dev/null || git worktree add -b "$1" "$target"
  cd "$target"
}

gd() {
  git rev-parse --git-dir &>/dev/null || { echo "Not in a git repo"; return 1; }
  local entry=$(git worktree list | tail -n +2 | fzf --prompt="Delete worktree> ")
  [ -z "$entry" ] && return 0
  local dir=$(echo "$entry" | awk '{print $1}')
  echo -n "Delete worktree '$dir'? [y/N] "
  read -r confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Cancelled"; return 0; }
  local main_dir=$(git worktree list | head -1 | awk '{print $1}')
  [[ "$PWD" == "$dir"* ]] && cd "$main_dir"
  git worktree remove "$dir" && echo "Deleted worktree '$dir'"
}

groot() {
  git rev-parse --git-dir &>/dev/null || { echo "Not in a git repo"; return 1; }
  local main_dir=$(git worktree list | head -1 | awk '{print $1}')
  [ -d "$main_dir" ] && cd "$main_dir" || { echo "Main worktree not found"; return 1; }
}
