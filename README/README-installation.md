# Installing Jibberish

This document outlines the various methods to install and set up Jibberish, an AI-powered Linux Shell.

## Quick Installation with pip

```bash
# Basic installation
pip install git+https://github.com/bjeremy23/jibberish.git

# With Azure OpenAI support
pip install "jibberish[azure] @ git+https://github.com/bjeremy23/jibberish.git"

# If you encounter dependency issues with Azure packages,
# install them separately:
pip install git+https://github.com/bjeremy23/jibberish.git
pip install azure-identity azureopenai==0.0.1
```

### Installation from local repository

If you've already cloned the repository:

```bash
# Navigate to the jibberish directory
cd jibberish

# Standard installation
pip install .

# With Azure OpenAI support
pip install ".[azure]"
```

### Using Jibberish installed with pip

After pip installation, you can run Jibberish from anywhere using:

```bash
jibberish
```

You can also use the command-line options:

```bash
# Show version
jibberish -v

# Ask a question
jibberish -q "How do I find files modified in the last 24 hours?"

# Generate a command
jibberish -c "Find all Python files containing the word 'error'"
```

### Development Installation

For development, you may want to install in "editable" mode:

```bash
git clone https://github.com/bjeremy23/jibberish.git
cd jibberish
pip install -e .
```

## Manual Installation from Source

Jibberish provides a simple setup script to install all dependencies and configure your environment. This script will:

1. Create a Python virtual environment
2. Install all required dependencies
3. Configure the `.jbrsh` configuration file in your home directory
4. Verify the installation

```bash
git clone https://github.com/bjeremy23/jibberish.git
cd jibberish

# To enter Jibberish
source venv/bin/activate
python3 ./app/jibberish.py
```

### Installation Options

The setup script supports several command-line options:

```bash
Usage: ./setup.sh [options]
Options:
  --non-interactive    Run without prompts (assumes yes for all questions)
  --with-azure         Install Azure OpenAI dependencies
  --yes, -y            Answer yes to all prompts
  --help, -h           Show this help message
```

### Examples

```bash
# Install with Azure OpenAI support
./setup.sh --with-azure

# Non-interactive installation for CI/CD environments
./setup.sh --non-interactive

# Automatically answer yes to all prompts
./setup.sh --yes
```

After installation, you'll need to edit the `~/.jbrsh` file to add your API keys and customize settings. For detailed instructions on setting up your API credentials, see [README-ai-setup.md](README-ai-setup.md).

## ~/.jbrsh Configuration

- Add this file to your home directory
- This file contains environment variables used within the shell
- You will need to fill out ENV variables to connect to your AI service

For detailed instructions on setting up your API credentials, see [README-ai-setup.md](README-ai-setup.md).
