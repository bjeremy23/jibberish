# CNA Setup Plugin for Jibberish

This is a specialized plugin for the A40PacketCore group enabling Container Network Architecture (CNA) development environment.

## Features

- Executes the CNA setup functionality using multiple approaches:
  1. Looks for script files in standard locations
  2. Tries to execute as a bash shell function
  3. Searches in your PATH for executables
- Works with `cna-setup` or `cna_setup` command names
- Passes through all command-line arguments
- Displays output and error messages in a user-friendly format
- Reports success or failure based on the exit code

## Usage

```
[jbrsh] user@hostname:~$ cna-setup
```

## Enabling the Plugin

This is an optional plugin. By default, it is enabled. To explicitly enable or disable it:

Add the following to your `~/.jbrsh` file:

```
# Enable the CNA Setup plugin
PLUGIN_CNA_SETUP_COMMAND_ENABLED=y
```

Or to disable it:

```
# Disable the CNA Setup plugin
PLUGIN_CNA_SETUP_COMMAND_ENABLED=n
```

## Requirements

- The `cna-setup.sh` script must be present in one of the following locations (where $USER is your username):
  - `/$USER/.vm-tools/interface/bin/cna-setup.sh`

- The `CNA_TOOLS` environment variable is required by the script
  - The plugin will automatically set it to `/localdata/$USER/.vm-tools` if not already set
  - You can set it manually in your `.jbrsh` or `.bashrc` file if needed:
    ```
    export CNA_TOOLS=/path/to/your/vm-tools
    ```
  
- Alternatively, a `cna-setup` or `cna_setup` function must be defined in your bash environment

## Troubleshooting

### Common Issues

1. **"Error executing cna-setup: [Errno 8] Exec format error"**
   - This happens because the cna-setup.sh script is designed to be sourced, not executed directly
   - The updated plugin now properly sources the script instead of executing it

2. **"cna-setup: command not found"**
   - Make sure the script exists in one of the expected locations and has executable permissions

3. **Docker login errors: "Cannot perform an interactive login from a non TTY device"**
   - This is a limitation of running docker login commands in a non-interactive session
   - For initial setup with docker login, run `cna-setup` directly in a bash terminal first
   - Once logged in, the credentials should persist for future Jibberish usage

4. **"ERROR: expected CNA_TOOLS to be set; cannot setup CNA environment"**
   - The script requires the `CNA_TOOLS` environment variable to be set
   - The plugin will now automatically set this to `/localdata/$USER/.vm-tools`
   - If that's not correct, set it manually in your `.jbrsh` file or `.bashrc`

### Checking Script Location

If you're experiencing issues, verify the script exists and is executable:

```bash
ls -la /localdata/$USER/.vm-tools/interface/bin/cna-setup.sh
```

### Advanced Troubleshooting

The plugin uses a two-step approach:
1. First attempts to run the command as a bash function (sourced from your profile)
2. If that fails, tries to source the script file from standard locations

This ensures the command works regardless of whether it's available as a shell function or as a script that needs to be sourced.
