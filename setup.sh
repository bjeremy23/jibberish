#!/bin/bash
# Script to set up a Python virtual environment and install Jibberish

# Parse command line arguments
INTERACTIVE=true
INSTALL_AZURE=false
AUTO_YES=false
DEV_INSTALL=false
PACKAGE_INSTALL=false
USER_INSTALL=false
REORGANIZE=false

# Process command line options
while [[ $# -gt 0 ]]; do
  case $1 in
    --non-interactive)
      INTERACTIVE=false
      AUTO_YES=true
      shift
      ;;
    --with-azure)
      INSTALL_AZURE=true
      shift
      ;;
    --yes|-y)
      AUTO_YES=true
      shift
      ;;
    --dev)
      DEV_INSTALL=true
      shift
      ;;
    --package)
      PACKAGE_INSTALL=true
      shift
      ;;
    --user)
      USER_INSTALL=true
      shift
      ;;
    --reorganize)
      REORGANIZE=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --non-interactive    Run without prompts (assumes yes for all questions)"
      echo "  --with-azure         Install Azure OpenAI dependencies"
      echo "  --yes, -y            Answer yes to all prompts"
      echo "  --dev                Install in development mode (pip install -e)"
      echo "  --package            Build a pip package (wheel)"
      echo "  --user               Install for current user only (pip install --user)"
      echo "  --reorganize         Reorganize files for proper Python packaging"
      echo "  --help, -h           Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help to see available options."
      exit 1
      ;;
  esac
done

set -e  # Exit on any error

# Text formatting
BOLD="\033[1m"
RESET="\033[0m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
BLUE="\033[34m"

echo -e "${BOLD}${GREEN}====== Jibberish Setup ======${RESET}"
echo -e "This script will set up ${BOLD}Jibberish${RESET}, an AI-powered Linux Shell that allows"
echo -e "you to generate commands from natural language, ask questions, and more."

# Display mode information
if [ "$INTERACTIVE" = false ]; then
    echo -e "${YELLOW}Running in non-interactive mode${RESET}"
fi
if [ "$INSTALL_AZURE" = true ]; then
    echo -e "${YELLOW}Azure OpenAI dependencies will be installed${RESET}"
fi
if [ "$AUTO_YES" = true ]; then
    echo -e "${YELLOW}Auto-confirming all prompts${RESET}"
fi
if [ "$DEV_INSTALL" = true ]; then
    echo -e "${YELLOW}Installing in development mode${RESET}"
fi
if [ "$PACKAGE_INSTALL" = true ]; then
    echo -e "${YELLOW}Building pip package${RESET}"
fi
if [ "$USER_INSTALL" = true ]; then
    echo -e "${YELLOW}Installing for current user only${RESET}"
fi
if [ "$REORGANIZE" = true ]; then
    echo -e "${YELLOW}Will reorganize files for proper Python packaging${RESET}"
fi
echo

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d" " -f2)
echo -e "${BLUE}Detected Python version:${RESET} $python_version"

# Define the function to check for Python development headers
check_python_dev() {
    # First check if we can already install psutil without development headers
    # This works when pre-compiled wheels are available (most common case)
    if python3 -m pip install --dry-run psutil >/dev/null 2>&1; then
        echo -e "${GREEN}Pre-compiled packages are available - no development headers needed.${RESET}"
        return 0
    # If that fails, check for development headers
    elif [ -f "/usr/include/python3.h" ] || [ -d "/usr/include/python$python_version" ]; then
        echo -e "${GREEN}Python development headers are installed.${RESET}"
        return 0
    else
        echo -e "${YELLOW}Python development headers may not be installed.${RESET}"
        echo -e "${YELLOW}Some packages like psutil require Python headers to compile.${RESET}"
        echo -e "${YELLOW}If package installation fails, you may need to install:${RESET}"
        echo -e "  ${BLUE}sudo apt-get install python3-dev${RESET}  # For Debian/Ubuntu"
        echo -e "  ${BLUE}sudo dnf install python3-devel${RESET}  # For Fedora/RHEL/CentOS"
        return 1
    fi
}

# Quick development headers check
# Don't exit if this fails - just show the warning
check_python_dev || true

# Check if we're in a corporate environment
if [[ -n $http_proxy || -n $https_proxy || -d /usr/local/share/ca-certificates/extra ]]; then
    echo -e "${YELLOW}Corporate environment detected.${RESET}"
    echo -e "You might need to configure pip to use your corporate proxy/certificates."
    echo -e "If you encounter SSL errors, you may need to set:"
    echo -e "  ${BLUE}export REQUESTS_CA_BUNDLE=/path/to/your/certificate.pem${RESET}"
    echo
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${RESET}"
    # Check if venv module is available
    if ! python3 -c "import venv" 2>/dev/null; then
        echo -e "${RED}Error: Python venv module not found.${RESET}"
        echo "Please install the Python venv package:"
        echo "  Debian/Ubuntu: sudo apt-get install python3-venv"
        echo "  RHEL/CentOS/Fedora: sudo dnf install python3-virtualenv"
        exit 1
    fi
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${RESET}"
source venv/bin/activate

# Run the rename script if requested
if [ "$REORGANIZE" = true ]; then
    echo -e "${GREEN}Reorganizing files for proper Python packaging...${RESET}"
    if [ -f "rename_script.sh" ]; then
        ./rename_script.sh
    else
        echo -e "${RED}Error: rename_script.sh not found!${RESET}"
        exit 1
    fi
fi

# Install dependencies
echo -e "${GREEN}Installing dependencies...${RESET}"
pip install --upgrade pip setuptools wheel build

# Update version information in package files
echo -e "${GREEN}Updating version information...${RESET}"
python update_toml_version.py

# Install Jibberish
if [ "$PACKAGE_INSTALL" = true ]; then
    # Build the package
    echo -e "${GREEN}Building pip package...${RESET}"
    python -m build
    echo -e "${GREEN}Package built successfully!${RESET}"
    echo -e "${YELLOW}Wheel package available in ./dist/ directory${RESET}"
    
    # Optionally install from the built package
    if [[ "$INTERACTIVE" = true && "$AUTO_YES" = false ]]; then
        echo -e "${YELLOW}Do you want to install the built package?${RESET}"
        read -p "Install package? [y/N]: " install_pkg
    elif [ "$AUTO_YES" = true ]; then
        install_pkg="y"
    else
        install_pkg="n"
    fi
    
    if [[ $install_pkg == "y" || $install_pkg == "Y" ]]; then
        echo -e "${GREEN}Installing Jibberish from wheel...${RESET}"
        # Find the wheel file
        wheel_file=$(ls -t dist/*.whl | head -1)
        if [ -n "$wheel_file" ]; then
            if [ "$USER_INSTALL" = true ]; then
                pip install --user "$wheel_file"
            else
                pip install "$wheel_file"
            fi
            echo -e "${GREEN}Jibberish installed from wheel!${RESET}"
        else
            echo -e "${RED}Wheel file not found!${RESET}"
        fi
    fi
elif [ "$DEV_INSTALL" = true ]; then
    # Install in development mode
    echo -e "${GREEN}Installing Jibberish in development mode...${RESET}"
    if [ "$USER_INSTALL" = true ]; then
        pip install --user -e .
    else
        pip install -e .
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Jibberish installed in development mode!${RESET}"
    else
        echo -e "${RED}Failed to install Jibberish in development mode!${RESET}"
        exit 1
    fi
else
    # Regular installation from setup.py
    echo -e "${GREEN}Installing Jibberish...${RESET}"
    if [ "$USER_INSTALL" = true ]; then
        pip install --user .
    else
        pip install .
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Jibberish installed successfully!${RESET}"
    else
        echo -e "${RED}Failed to install Jibberish!${RESET}"
        exit 1
    fi
fi

# Azure OpenAI support (optional)
install_azure="n"
if [ "$INSTALL_AZURE" = true ]; then
    install_azure="y"
elif [ "$INTERACTIVE" = true ]; then
    echo -e "${YELLOW}Do you want to install Azure OpenAI support?${RESET}"
    read -p "Install Azure support? [y/N]: " install_azure
elif [ "$AUTO_YES" = true ]; then
    echo -e "${YELLOW}Auto-installing Azure OpenAI support (--yes flag provided)${RESET}"
    install_azure="y"
fi

if [[ $install_azure == "y" || $install_azure == "Y" ]]; then
    echo -e "${GREEN}Installing Azure OpenAI dependencies...${RESET}"
    
    # Install Azure dependencies using the extras_require from setup.py
    if [ "$USER_INSTALL" = true ]; then
        pip install --user ".[azure]"
    else
        pip install ".[azure]"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Successfully installed Azure OpenAI support!${RESET}"
        # Create a note about the installation outcome
        echo "# Azure OpenAI support installation attempted on $(date)" >> .azure_install_attempt
        echo "# Installation was successful" >> .azure_install_attempt
    else
        echo -e "${RED}Warning: Could not install Azure OpenAI support.${RESET}"
        echo -e "${YELLOW}You may need to manually install the correct packages:${RESET}"
        echo -e "  ${BLUE}pip install azure-identity azure-ai-openai${RESET}"
        echo -e "  ${BLUE}pip install azure-identity azure-openai${RESET}"
        echo -e "  ${BLUE}pip install \"openai[azure]\"${RESET}"
        echo
        echo -e "${YELLOW}Continuing with standard openai package...${RESET}"
        echo -e "${YELLOW}Note: Azure functionality may be limited.${RESET}"
        # Create a note about the installation outcome
        echo "# Azure OpenAI support installation attempted on $(date)" >> .azure_install_attempt
        echo "# Installation failed - manual installation required" >> .azure_install_attempt
    fi
fi

# Create ~/.jbrsh if it doesn't exist
if [ ! -f ~/.jbrsh ]; then
    if [ -f ".jbrsh" ]; then
        echo -e "${GREEN}Creating ~/.jbrsh configuration file...${RESET}"
        cp .jbrsh ~/.jbrsh
        echo -e "${YELLOW}Please edit ~/.jbrsh to set your API keys and preferences.${RESET}"
    else
        echo -e "${RED}Warning: .jbrsh template file not found!${RESET}"
        echo -e "${YELLOW}Creating a minimal ~/.jbrsh file...${RESET}"
        cat > ~/.jbrsh << EOL
# Jibberish configuration file
# Please update with your API keys and preferences

AI_CHOICE="openai"

# OpenAI API Key - Replace with your actual key
OPEN_API_KEY=<your-api-key-here>
OPEN_API_MODEL=gpt-4

# Set to true to be prompted before executing AI-generated commands
PROMPT_AI_COMMANDS=true

# List of commands that will prompt before executing
WARN_LIST="rm, rmdir, mv, cp, ln, chmod, chown, chgrp, kill, pkill, killall"
EOL
        echo -e "${YELLOW}Created a minimal ~/.jbrsh file. Please edit it to add your API keys.${RESET}"
    fi
else
    echo -e "${YELLOW}~/.jbrsh configuration file already exists.${RESET}"
fi

# Make sure the main script is executable
if [ ! -x "jibberish.py" ]; then
    echo -e "${GREEN}Making jibberish.py executable...${RESET}"
    chmod +x jibberish.py
fi

# Verify plugins directory
if [ ! -d "plugins" ]; then
    echo -e "${RED}Warning: 'plugins' directory not found!${RESET}"
    echo -e "Jibberish might not function correctly without plugins."
else
    echo -e "${GREEN}Verifying plugins...${RESET}"
    plugin_count=$(find plugins -name "*.py" | wc -l)
    echo -e "Found ${BLUE}$plugin_count${RESET} plugin files."
    
    # Make sure plugins/__init__.py exists
    if [ ! -f "plugins/__init__.py" ]; then
        echo -e "${YELLOW}Creating plugins/__init__.py...${RESET}"
        echo "# Jibberish plugins package" > plugins/__init__.py
    fi
    
    # Check for plugin dependencies
    echo -e "${GREEN}Checking plugin dependencies...${RESET}"
    
    # Check for job_control_command.py which needs psutil
    if [ -f "plugins/job_control_command.py" ]; then
        echo -e "${BLUE}Found job_control_command.py which requires psutil...${RESET}"
        
        # Try multiple methods to install psutil, starting with pre-compiled wheels
        echo -e "${BLUE}Installing psutil package...${RESET}"
        
        # First try a pre-compiled wheel for better compatibility (this worked for the user)
        echo -e "${BLUE}Trying to install pre-compiled wheel...${RESET}"
        if pip install psutil; then
            echo -e "${GREEN}Successfully installed psutil!${RESET}"
        else
            echo -e "${YELLOW}Standard installation failed, trying alternatives...${RESET}"
            
            # Try pip3 explicitly
            if command -v pip3 >/dev/null; then
                pip3 install psutil
                if python -c "import psutil" 2>/dev/null; then
                    echo -e "${GREEN}Successfully installed psutil using pip3!${RESET}"
                else
                    echo -e "${RED}Warning: Could not install psutil.${RESET}"
                    echo -e "${YELLOW}Job control features might not work correctly.${RESET}"
                    echo -e "${YELLOW}For more detailed error information, try running:${RESET}"
                    echo -e "${BLUE}  pip install psutil -v${RESET}"
                    echo -e "${YELLOW}You may need to install development packages:${RESET}"
                    echo -e "${BLUE}  sudo apt-get install python3-dev${RESET}  # For Debian/Ubuntu"
                    echo -e "${BLUE}  sudo dnf install python3-devel${RESET}  # For Fedora/RHEL"
                fi
            else
                echo -e "${RED}Warning: pip3 command not found.${RESET}"
                echo -e "${YELLOW}Try manually installing with: pip install psutil${RESET}"
            fi
        fi
    fi
fi

echo
echo -e "${BOLD}${GREEN}====== Setup Complete ======${RESET}"
echo

# Instructions for using Jibberish
echo -e "${BOLD}Using Jibberish:${RESET}"

if [ "$PACKAGE_INSTALL" = true ] || [ "$DEV_INSTALL" = true ] || [ "$USER_INSTALL" = true ]; then
    # For pip-installed packages
    echo -e "1. Activate the virtual environment (if not already done):"
    echo -e "   ${BLUE}source venv/bin/activate${RESET}"
    echo -e "2. Run Jibberish:"
    echo -e "   ${BLUE}jibberish${RESET}"
    echo -e "   (Or with options, e.g.: ${BLUE}jibberish --version${RESET})"
else
    # For local development
    echo -e "1. Activate the virtual environment (if not already done):"
    echo -e "   ${BLUE}source venv/bin/activate${RESET}"
    echo -e "2. Run Jibberish:"
    echo -e "   ${BLUE}python jibberish.py${RESET}"
fi
echo

# Verify installation
verify_install="n"
if [ "$INTERACTIVE" = true ]; then
    echo -e "${YELLOW}Would you like to verify the installation by running Jibberish with --version?${RESET}"
    read -p "Verify installation? [y/N]: " verify_install
elif [ "$AUTO_YES" = true ]; then
    echo -e "${YELLOW}Auto-verifying installation (--yes flag provided)${RESET}"
    verify_install="y"
else
    echo -e "${YELLOW}Skipping verification in non-interactive mode.${RESET}"
    if [ "$PACKAGE_INSTALL" = true ] || [ "$DEV_INSTALL" = true ] || [ "$USER_INSTALL" = true ]; then
        echo -e "${YELLOW}You can verify later with: jibberish --version${RESET}"
    else
        echo -e "${YELLOW}You can verify later with: python jibberish.py --version${RESET}"
    fi
fi

if [[ $verify_install == "y" || $verify_install == "Y" ]]; then
    if [ "$PACKAGE_INSTALL" = true ] || [ "$DEV_INSTALL" = true ] || [ "$USER_INSTALL" = true ]; then
        echo -e "${GREEN}Running: jibberish --version${RESET}"
        jibberish --version
    else
        echo -e "${GREEN}Running: python jibberish.py --version${RESET}"
        python jibberish.py --version
    fi
    
    # Also check if plugins load correctly
    echo -e "${GREEN}Checking plugin loading...${RESET}"
    if [ "$PACKAGE_INSTALL" = true ] || [ "$DEV_INSTALL" = true ] || [ "$USER_INSTALL" = true ]; then
        plugin_output=$(python -c "import jibberish.plugin_system; print('Plugin system imported successfully')" 2>&1)
    else
        plugin_output=$(python -c "import os, sys; sys.path.insert(0, os.getcwd()); import plugin_system; print('Plugin system imported successfully')" 2>&1)
    fi
    
    if [[ $plugin_output == *"Plugin system imported successfully"* ]]; then
        echo -e "${GREEN}Plugin system loaded successfully!${RESET}"
    else
        echo -e "${RED}Warning: Plugin system may have issues.${RESET}"
        echo -e "${YELLOW}Error output: ${RESET}"
        echo "$plugin_output"
    fi
    
    echo -e "${GREEN}If you see a version number above, Jibberish is installed correctly!${RESET}"
fi

echo -e "For more information, see ${BLUE}README.md${RESET}"
echo
echo -e "${BOLD}${GREEN}Enjoy using Jibberish!${RESET}"
