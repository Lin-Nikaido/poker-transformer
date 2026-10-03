#!/usr/bin/env bash

set -Eeuo pipefail

readonly GITLEAKS_VERSION="8.30.1"
readonly GITLEAKS_SHA256="551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"

readonly LOCAL_BIN="${HOME}/.local/bin"
readonly LOCAL_NPM="${HOME}/.local/npm"
readonly INIT_STATE_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/runtime"
readonly INIT_MARKER="${INIT_STATE_DIR}/initialized"

log() {
  printf '[claude-init] %s\n' "$*" >&2
}

fail() {
  printf '[claude-init] ERROR: %s\n' "$*" >&2

  exit 2
}

require_command() {
  local command_name="$1"

  command -v "$command_name" >/dev/null 2>&1 ||
    fail "Required command is not available: ${command_name}"
}

persist_environment() {
  if [[ -z "${CLAUDE_ENV_FILE:-}" ]]; then
    log "CLAUDE_ENV_FILE is not available; environment changes will not persist"
    return
  fi

  {
    printf 'export PATH="%s:%s/bin:$PATH"\n' \
      "$LOCAL_BIN" \
      "$LOCAL_NPM"

    printf 'export ENV="CI"\n'
    printf 'export UV_PROJECT_ENVIRONMENT="%s/.venv"\n' "$PROJECT_DIR"
  } >>"$CLAUDE_ENV_FILE"
}

install_uv() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi

  log "Installing uv"

  curl --proto '=https' --tlsv1.2 -LsSf \
    https://astral.sh/uv/install.sh |
    env UV_INSTALL_DIR="$LOCAL_BIN" sh

  export PATH="${LOCAL_BIN}:${PATH}"

  require_command uv
}

install_python_dependencies() {
  log "Ensuring Python 3.10 is available"

  uv python install 3.10

  log "Installing Python dependencies"

  uv sync \
    --frozen \
    --extra dev \
    --python 3.10
}

validate_node() {
  require_command node
  require_command npm

  local node_major
  node_major="$(node --version | sed -E 's/^v([0-9]+).*/\1/')"

  if [[ ! "$node_major" =~ ^[0-9]+$ ]]; then
    fail "Could not determine Node.js version: $(node --version)"
  fi

  if ((node_major < 22)); then
    fail "Node.js 22 or newer is required, but $(node --version) is installed"
  fi

  log "Using Node.js $(node --version)"
}

install_archgate() {
  export PATH="${LOCAL_NPM}/bin:${PATH}"

  if command -v archgate >/dev/null 2>&1; then
    log "Archgate is already installed"
    return
  fi

  log "Installing Archgate"

  mkdir -p "$LOCAL_NPM"
  npm install --global --prefix "$LOCAL_NPM" archgate

  require_command archgate
}

setup_archgate() {
  log "Configuring Archgate"

  mkdir -p .archgate

  ln -sfn ../docs/adrs .archgate/adrs
  ln -sfn ../docs/adrs/rules.d.ts .archgate/rules.d.ts
}

install_gitleaks() {
  export PATH="${LOCAL_BIN}:${PATH}"

  if command -v gitleaks >/dev/null 2>&1; then
    log "Gitleaks is already installed: $(gitleaks version)"
    return
  fi

  log "Installing Gitleaks ${GITLEAKS_VERSION}"

  local work_dir
  work_dir="$(mktemp -d)"

  trap 'rm -rf "$work_dir"' RETURN

  curl --proto '=https' --tlsv1.2 -fsSL \
    "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
    --output "${work_dir}/gitleaks.tar.gz"

  printf '%s  %s\n' \
    "$GITLEAKS_SHA256" \
    "${work_dir}/gitleaks.tar.gz" |
    sha256sum --check --status ||
    fail "Gitleaks archive checksum verification failed"

  tar \
    --extract \
    --gzip \
    --file "${work_dir}/gitleaks.tar.gz" \
    --directory "$work_dir" \
    gitleaks

  install \
    --mode 0755 \
    "${work_dir}/gitleaks" \
    "${LOCAL_BIN}/gitleaks"

  require_command gitleaks
  gitleaks version >&2
}

install_document_tools() {
  if command -v libreoffice >/dev/null 2>&1; then
    log "LibreOffice is already installed"
    return
  fi

  require_command sudo

  log "Installing LibreOffice and Japanese fonts"

  sudo env DEBIAN_FRONTEND=noninteractive apt-get update

  sudo env DEBIAN_FRONTEND=noninteractive apt-get install \
    --yes \
    --no-install-recommends \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    fonts-dejavu \
    fonts-ipafont-gothic \
    fonts-ipafont-mincho \
    fonts-noto-cjk \
    fonts-noto-cjk-extra
}

setup_lefthook() {
  require_command lefthook

  log "Installing Lefthook hooks"
  lefthook install
}

setup_rulesync() {
  local rulesync_script=".rulesync/rulesync.sh"

  [[ -f "$rulesync_script" ]] ||
    fail "Rulesync script does not exist: ${rulesync_script}"

  log "Running Rulesync"

  chmod +x "$rulesync_script"
  "$rulesync_script"
}

write_marker() {
  mkdir -p "$INIT_STATE_DIR"

  {
    printf 'initialized_at=%s\n' "$(date --utc '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'python=%s\n' "$(uv run python --version 2>&1)"
    printf 'node=%s\n' "$(node --version)"
    printf 'gitleaks=%s\n' "$(gitleaks version 2>&1 | head -n 1)"
  } >"$INIT_MARKER"
}

main() {
  PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
  readonly PROJECT_DIR

  cd "$PROJECT_DIR"

  mkdir -p "$LOCAL_BIN" "$LOCAL_NPM" "$INIT_STATE_DIR"

  export PATH="${LOCAL_BIN}:${LOCAL_NPM}/bin:${PATH}"
  export ENV="CI"

  log "Initializing project: ${PROJECT_DIR}"

  require_command curl
  require_command git

  install_uv
  validate_node

  install_python_dependencies
  install_archgate
  setup_archgate
  install_gitleaks
  install_document_tools
  setup_lefthook
  setup_rulesync

  persist_environment
  write_marker

  log "Initialization completed"
}

main "$@"