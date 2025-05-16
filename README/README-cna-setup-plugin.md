# CNA Commands Plugin for Jibberish

This is a specialized plugin for the A40PacketCore group enabling Container Network Architecture (CNA) development environment.
## Usage

Most 'cna' commands are handled through normal execution. This plugin specifically handles only these two commands:

```
[jbrsh] user@hostname:~$ cna-setup
[jbrsh] user@hostname:~$ cna enter-build
```

The `cna enter-build` command will provide an interactive shell inside the build container.

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

3. **Docker login and interactive commands**
   - Interactive commands like `cna enter-build` are now supported using the `script` utility
   - The plugin automatically detects interactive commands and creates a proper TTY environment
   - If you still experience issues with Docker login, run it in a bash terminal first
   - Once logged in, the credentials should persist for future Jibberish usage

4. **"ERROR: expected CNA_TOOLS to be set; cannot setup CNA environment"**
   - The script requires the `CNA_TOOLS` environment variable to be set
   - The plugin will now automatically set this to `/localdata/$USER/.vm-tools`
   - If that's not correct, set it manually in your `.jbrsh` file or `.bashrc`

5. **"fatal: destination path '/localdata/$USER/.vm-tools' already exists and is not an empty directory"**
   - This is not actually an error - it's just Git reporting that it can't clone because the directory already exists
   - The plugin will now properly handle this case by using the existing directory
   - You can safely ignore this message

### Checking Script Location

If you're experiencing issues, verify the script exists and is executable:

```bash
ls -la /localdata/$USER/.vm-tools/interface/bin/cna-setup.sh
```

### Interactive Commands Support

The plugin has special handling for interactive commands:

1. `cna enter-build` - Enters an interactive Docker container
   - The plugin will detect this command and do one of the following:
     - In a graphical environment (when DISPLAY is set):
       - Try to launch a new terminal window with optimized settings for each terminal type:
         - `gnome-terminal` - Standard GNOME terminal
         - `xterm` - With medium font size (12pt) and high contrast colors
     - In a non-graphical environment (SSH sessions, terminals without DISPLAY):
       - Automatically fall back to the `script` utility to create a TTY
     - If terminal launch fails for any reason, also falls back to the `script` utility