#!/usr/bin/env bash

# ============================================================================
# macOS Python Development Environment Setup Script
# ============================================================================
# This script sets up a complete Python development environment including:
# - Pyenv + Python 3.11.10
# - Poetry (dependency management)
# - UV (fast package manager)
# - Node.js + NPM
# - PIPX (isolated Python app installer)
# - Essential Python dev tools (Ruff, MyPy, etc.)
#
# Prerequisites: macOS with Homebrew, Git, and VSCode already installed
# Usage: chmod +x setup_python_dev_env.sh && ./setup_python_dev_env.sh
# ============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.11.10"
SHELL_CONFIG=""

# ============================================================================
# Utility Functions
# ============================================================================

print_step() {
    echo -e "\n${BLUE}==>${NC} ${1}"
}

print_success() {
    echo -e "${GREEN}✓${NC} ${1}"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} ${1}"
}

print_error() {
    echo -e "${RED}✗${NC} ${1}"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

detect_shell() {
    local shell_name
    shell_name=$(basename "$SHELL")

    case "$shell_name" in
        bash)
            if [[ -f "$HOME/.bash_profile" ]]; then
                SHELL_CONFIG="$HOME/.bash_profile"
            elif [[ -f "$HOME/.bashrc" ]]; then
                SHELL_CONFIG="$HOME/.bashrc"
            else
                SHELL_CONFIG="$HOME/.bash_profile"
            fi
            ;;
        zsh)
            SHELL_CONFIG="$HOME/.zshrc"
            ;;
        *)
            print_warning "Unsupported shell: $shell_name. Defaulting to .zshrc"
            SHELL_CONFIG="$HOME/.zshrc"
            ;;
    esac

    print_success "Detected shell: $shell_name, config: $SHELL_CONFIG"
}

# ============================================================================
# Installation Functions
# ============================================================================

install_pyenv_dependencies() {
    print_step "Installing Python build dependencies via Homebrew..."

    local deps=(
        "openssl"
        "readline"
        "sqlite3"
        "xz"
        "zlib"
        "tcl-tk"
        "libb2"
        "zstd"
    )

    for dep in "${deps[@]}"; do
        if brew list "$dep" &>/dev/null; then
            print_success "$dep already installed"
        else
            print_step "Installing $dep..."
            brew install "$dep" || {
                print_warning "Failed to install $dep, continuing anyway..."
            }
        fi
    done
}

install_pyenv() {
    print_step "Installing pyenv via Homebrew..."

    if command_exists pyenv; then
        print_success "pyenv already installed: $(pyenv --version)"
        return 0
    fi

    brew install pyenv || {
        print_error "Failed to install pyenv"
        return 1
    }
    print_success "pyenv installed successfully"
}

configure_pyenv_shell() {
    print_step "Configuring shell environment for pyenv..."

    local pyenv_config='
# Pyenv configuration
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"'

    if ! grep -q "PYENV_ROOT" "$SHELL_CONFIG" 2>/dev/null; then
        echo "$pyenv_config" >> "$SHELL_CONFIG"
        print_success "Added pyenv configuration to $SHELL_CONFIG"
    else
        print_success "pyenv already configured in $SHELL_CONFIG"
    fi

    # Source the configuration for current session
    export PYENV_ROOT="$HOME/.pyenv"
    [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
    if command_exists pyenv; then
        eval "$(pyenv init -)"
    fi

    # Set up pyenv for current session without sourcing entire shell config
    print_warning "Setting up pyenv for current session..."
    # Temporarily disable strict mode to avoid issues with Oh My Zsh variables
    set +u
    if [[ -f "$SHELL_CONFIG" ]]; then
        # Only source pyenv-related configuration, not the entire file
        source <(grep -A 10 -B 2 "PYENV_ROOT\|pyenv init" "$SHELL_CONFIG" 2>/dev/null || echo "# No pyenv config found")
    fi
    set -u
}

install_python() {
    print_step "Installing Python $PYTHON_VERSION via pyenv..."

    # Ensure pyenv is available
    if ! command_exists pyenv; then
        print_error "pyenv not found in PATH. Please restart terminal and run script again."
        return 1
    fi

    if pyenv versions 2>/dev/null | grep -q "$PYTHON_VERSION"; then
        print_success "Python $PYTHON_VERSION already installed"
    else
        print_step "This may take several minutes as Python is compiled from source..."
        pyenv install "$PYTHON_VERSION" || {
            print_error "Failed to install Python $PYTHON_VERSION"
            return 1
        }
        print_success "Python $PYTHON_VERSION installed successfully"
    fi

    print_step "Setting Python $PYTHON_VERSION as global default..."
    pyenv global "$PYTHON_VERSION"
    pyenv rehash

    # Verify installation
    sleep 2  # Give pyenv a moment to update
    local current_version
    current_version=$(pyenv exec python --version 2>&1 | cut -d' ' -f2)
    if [[ "$current_version" == "$PYTHON_VERSION" ]]; then
        print_success "Python $PYTHON_VERSION is now active: $(pyenv exec python --version)"
    else
        print_error "Failed to set Python $PYTHON_VERSION as active. Current: $current_version"
        return 1
    fi
}

install_pipx() {
    print_step "Installing pipx for isolated Python applications..."

    if command_exists pipx; then
        print_success "pipx already installed: $(pipx --version)"
        return 0
    fi

    # Install pipx via Homebrew (recommended for macOS)
    brew install pipx || {
        print_error "Failed to install pipx"
        return 1
    }

    # Ensure pipx path is configured
    pipx ensurepath || print_warning "pipx ensurepath failed, PATH may need manual configuration"

    # Refresh PATH for current session
    eval "$(pipx completion --shell bash 2>/dev/null || true)"

    print_success "pipx installed successfully"
}

install_poetry() {
    print_step "Installing Poetry via pipx..."

    if command_exists poetry; then
        print_success "Poetry already installed: $(poetry --version)"
        return 0
    fi

    pipx install poetry || {
        print_error "Failed to install Poetry"
        return 1
    }

    # Refresh PATH
    hash -r 2>/dev/null || true

    print_success "Poetry installed successfully: $(poetry --version 2>/dev/null || echo 'installed')"
}

install_uv() {
    print_step "Installing UV (fast Python package manager) via Homebrew..."

    if command_exists uv; then
        print_success "UV already installed: $(uv --version)"
        return 0
    fi

    brew install uv || {
        print_error "Failed to install UV"
        return 1
    }
    print_success "UV installed successfully: $(uv --version)"
}

install_nodejs() {
    print_step "Installing Node.js and NPM via Homebrew..."

    if command_exists node && command_exists npm; then
        print_success "Node.js already installed: $(node --version)"
        print_success "NPM already installed: $(npm --version)"
        return 0
    fi

    brew install node || {
        print_error "Failed to install Node.js"
        return 1
    }
    print_success "Node.js installed: $(node --version)"
    print_success "NPM installed: $(npm --version)"
}

install_python_dev_tools() {
    print_step "Installing essential Python development tools via pipx..."

    local tools=(
        "ruff"              # Fast linter/formatter (replaces black, flake8, isort)
        "mypy"              # Static type checker
        "pre-commit"        # Git hook framework
        "pytest"            # Testing framework
        "cookiecutter"      # Project templating
        "httpie"            # HTTP client
        "rich-cli"          # Rich text rendering
    )

    for tool in "${tools[@]}"; do
        if pipx list 2>/dev/null | grep -q "$tool"; then
            print_success "$tool already installed"
        else
            print_step "Installing $tool..."
            pipx install "$tool" || {
                print_warning "Failed to install $tool, continuing..."
            }
        fi
    done

    # Refresh PATH after installations
    hash -r 2>/dev/null || true
}

update_tools() {
    print_step "Updating all tools to latest versions..."

    print_step "Updating Homebrew..."
    brew update && brew upgrade || print_warning "Homebrew update failed"

    print_step "Updating pipx applications..."
    pipx upgrade-all || print_warning "pipx upgrade-all failed"

    print_success "Tools update completed"
}

verify_installation() {
    print_step "Verifying installation..."

    local all_good=true

    # Check Python via pyenv
    if pyenv exec python --version 2>/dev/null | grep -q "$PYTHON_VERSION"; then
        print_success "Python: $(pyenv exec python --version)"
    else
        print_error "Python $PYTHON_VERSION not active"
        all_good=false
    fi

    # Check pyenv
    if command_exists pyenv; then
        print_success "Pyenv: $(pyenv --version)"
    else
        print_error "Pyenv not found"
        all_good=false
    fi

    # Check Poetry
    if command_exists poetry; then
        print_success "Poetry: $(poetry --version 2>/dev/null || echo 'installed but version check failed')"
    else
        print_error "Poetry not found"
        all_good=false
    fi

    # Check UV
    if command_exists uv; then
        print_success "UV: $(uv --version)"
    else
        print_error "UV not found"
        all_good=false
    fi

    # Check Node.js/NPM
    if command_exists node && command_exists npm; then
        print_success "Node.js: $(node --version)"
        print_success "NPM: $(npm --version)"
    else
        print_error "Node.js/NPM not found"
        all_good=false
    fi

    # Check pipx
    if command_exists pipx; then
        print_success "Pipx: $(pipx --version)"
    else
        print_error "Pipx not found"
        all_good=false
    fi

    # Check essential tools
    local tools=("ruff" "mypy" "pre-commit" "pytest")
    for tool in "${tools[@]}"; do
        if command_exists "$tool"; then
            print_success "$tool: available"
        else
            print_warning "$tool not found in PATH (may need terminal restart)"
        fi
    done

    if [[ "$all_good" == true ]]; then
        print_success "All core tools installed and verified successfully!"
    else
        print_warning "Some tools failed verification. You may need to restart your terminal."
    fi
}

display_next_steps() {
    print_step "Installation complete! Next steps:"

    cat << EOF

${GREEN}✓ Your Python development environment is ready!${NC}

${BLUE}To get started:${NC}

1. ${YELLOW}Restart your terminal${NC} or run: source $SHELL_CONFIG

2. ${YELLOW}Verify everything works:${NC}
   python --version          # Should show $PYTHON_VERSION
   poetry --version          # Poetry for dependency management
   uv --version              # UV for fast package operations
   ruff --version            # Ruff for linting and formatting
   mypy --version            # MyPy for type checking

3. ${YELLOW}Create your first project:${NC}
   mkdir my_project && cd my_project
   poetry init               # Initialize Poetry project
   # OR
   uv init                   # Initialize UV project

4. ${YELLOW}Install packages:${NC}
   poetry add requests       # Using Poetry
   # OR
   uv add requests          # Using UV

5. ${YELLOW}Set up code quality tools:${NC}
   pre-commit install       # Enable git hooks
   ruff check .             # Lint your code
   ruff format .            # Format your code
   mypy .                   # Type check your code

${BLUE}Useful commands:${NC}
   pyenv versions           # List installed Python versions
   pyenv install --list    # List available Python versions
   poetry env info          # Show virtual environment info
   pipx list               # List installed Python applications
   uv pip list             # List packages in current environment

${BLUE}Configuration files to customize:${NC}
   ~/.pyenvrc              # Pyenv configuration
   pyproject.toml          # Poetry/UV project configuration
   .pre-commit-config.yaml # Pre-commit hooks configuration
   ruff.toml              # Ruff linter/formatter settings

${GREEN}Happy coding! 🐍${NC}
EOF
}

# ============================================================================
# Main Installation Process
# ============================================================================

main() {
    clear
    cat << "EOF"
 ____        _   _                   ____
|  _ \ _   _| |_| |__   ___  _ __   |  _ \  _____   __
| |_) | | | | __| '_ \ / _ \| '_ \  | | | |/ _ \ \ / /
|  __/| |_| | |_| | | | (_) | | | | | |_| |  __/\ V /
|_|    \__, |\__|_| |_|\___/|_| |_| |____/ \___| \_/
       |___/
    _____ _         _                                   _
   | ____| |_ __   _(_)_ __ ___  _ __  _ __ ___   ___ _ __| |_
   |  _| | | '_ \ \ / / | '__/ _ \| '_ \| '_ ` _ \ / _ \ '__| __|
   | |___| | | | \ V /| | | | (_) | | | | | | | | |  __/ |  | |_
   |_____|_|_| |_|\_/ |_|_|  \___/|_| |_|_| |_|_|\___|_|   \__|

    ____       _                  ____            _       _
   / ___|  ___| |_ _   _ _ __     / ___|  ___ _ __(_)_ __ | |_
   \___ \ / _ \ __| | | | '_ \    \___ \ / __| '__| | '_ \| __|
    ___) |  __/ |_| |_| | |_) |    ___) | (__| |  | | |_) | |_
   |____/ \___|\__|\__,_| .__/    |____/ \___|_|  |_| .__/ \__|
                        |_|                         |_|

EOF

    echo -e "${BLUE}Setting up a complete Python development environment...${NC}"
    echo -e "${YELLOW}This will install: Pyenv, Python 3.11.10, Poetry, UV, Node.js, PIPX, and dev tools${NC}"
    echo ""

    # Verify prerequisites
    if ! command_exists brew; then
        print_error "Homebrew is required but not installed. Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi

    if ! command_exists git; then
        print_error "Git is required but not installed. Please install Git first."
        exit 1
    fi

    print_success "Prerequisites verified (Homebrew, Git)"

    # Detect shell and configuration file
    detect_shell

    # Create shell config file if it doesn't exist
    touch "$SHELL_CONFIG"

    # Main installation sequence
    install_pyenv_dependencies || exit 1
    install_pyenv || exit 1
    configure_pyenv_shell || exit 1
    install_python || exit 1
    install_pipx || exit 1
    install_poetry || exit 1
    install_uv || exit 1
    install_nodejs || exit 1
    install_python_dev_tools

    # Final steps
    update_tools
    verify_installation
    display_next_steps

    print_success "Setup completed successfully! 🎉"
    echo -e "${YELLOW}Please restart your terminal or run: source ${SHELL_CONFIG}${NC}"
}

# Only run main if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
