#!/bin/bash
# Script to set up a Python virtual environment and install Jibberish

# Parse command line arguments
INTERACTIVE=true
INSTALL_AZURE=false
AUTO_YES=false

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
    --help|-h)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --non-interactive    Run without prompts (assumes yes for all questions)"
      echo "  --with-azure         Install Azure OpenAI dependencies"
      echo "  --yes, -y            Answer yes to all prompts"
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

# Install dependencies
echo -e "${GREEN}Installing dependencies...${RESET}"
pip install --upgrade pip

# Check if requirements.txt exists and use it if available
if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}Installing dependencies from requirements.txt...${RESET}"
    pip install -r requirements.txt
else
    # Install core dependencies manually
    echo -e "${GREEN}Installing core dependencies...${RESET}"
    pip install click openai psutil
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
    
    # First, install azure-identity which is less likely to have issues
    pip install azure-identity
    
    # Try different options for Azure OpenAI support
    echo -e "${BLUE}Attempting to install Azure OpenAI package...${RESET}"
    
    # Try multiple package names with both pip and pip3 (in some environments they differ)
    azure_installed=false
    
    # List of package options to try
    azure_installed=false
    
    # Try azure-ai-openai
    echo -e "${BLUE}Trying: pip install azure-ai-openai${RESET}"
    if pip install azure-ai-openai 2>/dev/null; then
        echo -e "${GREEN}Successfully installed azure-ai-openai!${RESET}"
        azure_installed=true
    # Try azure-openai
    elif pip install azure-openai 2>/dev/null; then
        echo -e "${GREEN}Successfully installed azure-openai!${RESET}"
        azure_installed=true
    # Try openai[azure]
    elif pip install "openai[azure]" 2>/dev/null; then
        echo -e "${GREEN}Successfully installed openai[azure]!${RESET}"
        azure_installed=true
    # Try pip3 as a fallback
    elif command -v pip3 >/dev/null && pip3 install azure-ai-openai 2>/dev/null; then
        echo -e "${GREEN}Successfully installed azure-ai-openai using pip3!${RESET}"
        azure_installed=true
    elif command -v pip3 >/dev/null && pip3 install azure-openai 2>/dev/null; then
        echo -e "${GREEN}Successfully installed azure-openai using pip3!${RESET}"
        azure_installed=true
    elif command -v pip3 >/dev/null && pip3 install "openai[azure]" 2>/dev/null; then
        echo -e "${GREEN}Successfully installed openai[azure] using pip3!${RESET}"
        azure_installed=true
    fi
    
    if [ "$azure_installed" = false ]; then
        echo -e "${RED}Warning: Could not install any Azure OpenAI package.${RESET}"
        echo -e "${YELLOW}You may need to manually install the correct package based on your Python version.${RESET}"
        echo -e "${YELLOW}Try one of these commands later:${RESET}"
        echo -e "  ${BLUE}pip install azure-ai-openai${RESET}"
        echo -e "  ${BLUE}pip install azure-openai${RESET}"
        echo -e "  ${BLUE}pip install \"openai[azure]\"${RESET}"
        echo
        echo -e "${YELLOW}Continuing with standard openai package...${RESET}"
        echo -e "${YELLOW}Note: Azure functionality may be limited.${RESET}"
    fi
    
    # Create a note about the installation outcome
    echo "# Azure OpenAI support installation attempted on $(date)" >> .azure_install_attempt
    if [ "$azure_installed" = true ]; then
        echo "# Installation was successful" >> .azure_install_attempt
    else
        echo "# Installation failed - manual installation required" >> .azure_install_attempt
    fi
fi

# Create ~/.jbrsh if it doesn't exist
if [ ! -f ~/.jbrsh ]; then
    echo -e "${GREEN}Creating ~/.jbrsh configuration file...${RESET}"
    cp .jbrsh ~/.jbrsh
    echo -e "${YELLOW}Please edit ~/.jbrsh to set your API keys and preferences.${RESET}"

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
echo -e "1. Activate the virtual environment (if not already done):"
echo -e "   ${BLUE}source venv/bin/activate${RESET}"
echo -e "2. Run Jibberish:"
echo -e "   ${BLUE}python jibberish.py${RESET}"
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
    echo -e "${YELLOW}You can verify later with: python jibberish.py --version${RESET}"
fi

if [[ $verify_install == "y" || $verify_install == "Y" ]]; then
    echo -e "${GREEN}Running: python jibberish.py --version${RESET}"
    python jibberish.py --version
    
    # Also check if plugins load correctly
    echo -e "${GREEN}Checking plugin loading...${RESET}"
    plugin_output=$(python -c "import os, sys; sys.path.insert(0, os.getcwd()); import plugin_system; print('Plugin system imported successfully')" 2>&1)
    
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
