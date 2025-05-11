"""
Job control plugin for managing background processes.
"""
import os
import signal
import psutil
import click
import subprocess
import threading
import time
from plugin_system import BuiltinCommand, BuiltinCommandRegistry

# Global dictionary to track background jobs
# Format: {job_id: {"pid": pid, "command": command, "running": True/False}}
background_jobs = {}
job_counter = 1

# Flag to track if the monitor thread is running
job_monitor_thread = None
job_monitor_running = False

# Lock to protect background_jobs access from multiple threads
jobs_lock = threading.RLock()

def job_monitor_function():
    """Background thread function to monitor jobs"""
    global job_monitor_running
    
    try:
        while job_monitor_running:
            # Check for job completions every 1 second
            with jobs_lock:
                update_job_status(check_output=True)
            time.sleep(1)
    except Exception as e:
        # Log any errors but don't crash
        print(f"Error in job monitor thread: {e}")
    finally:
        job_monitor_running = False

def start_job_monitor():
    """Start the background job monitor if it's not already running"""
    global job_monitor_thread, job_monitor_running
    
    if job_monitor_thread is None or not job_monitor_thread.is_alive():
        job_monitor_running = True
        job_monitor_thread = threading.Thread(target=job_monitor_function, daemon=True)
        job_monitor_thread.start()

def register_background_job(pid, command, stdout_path=None, stderr_path=None):
    """Register a new background job"""
    global job_counter
    
    with jobs_lock:
        job_id = job_counter
        background_jobs[job_id] = {
            "pid": pid,
            "command": command,
            "running": True,
            "stdout_path": stdout_path,
            "stderr_path": stderr_path,
            "notified_completion": False,
            # Add tracking for streamed output
            "last_stdout_pos": 0,  # Track position in the stdout file
            "last_stderr_pos": 0,  # Track position in the stderr file
            "stream_output": True,  # Whether to stream output in real-time
            "stream_started": False,  # Whether we've started streaming this job
            "last_output_time": time.time()  # Track when we last showed output
        }
        job_counter += 1
        
        # Make sure the job monitor is running
        start_job_monitor()
        
        return job_id

def check_and_stream_output(job_id, job):
    """Check for and display any new output from a running background job"""
    has_new_output = False
    stdout_path = job.get("stdout_path")
    stderr_path = job.get("stderr_path")
    
    # Create a header for the job if this is the first output
    if not job.get("stream_started", False) and (job.get("stream_output", True)):
        # Print an initial header for this job's output stream
        click.echo("")
        click.echo(click.style(f"▶ Background job [{job_id}]: {job['command']}", fg="blue", bold=True))
        click.echo(click.style(f"  Output stream will update automatically... (PID: {job['pid']})", fg="blue"))
        job["stream_started"] = True
    
    # Check for new stdout
    if stdout_path and os.path.exists(stdout_path):
        try:
            current_size = os.path.getsize(stdout_path)
            last_pos = job.get("last_stdout_pos", 0)
            
            # If the file has grown since we last checked
            if current_size > last_pos:
                with open(stdout_path, 'r') as f:
                    f.seek(last_pos)
                    new_output = f.read()
                    if new_output:
                        # Output a line marker for streamed output
                        if job["stream_started"]:
                            click.echo(click.style(f"▶ [{job_id}] New output:", fg="blue"))
                        click.echo(new_output, nl=False)
                        has_new_output = True
                        job["last_output_time"] = time.time()
                
                # Update the position for next time
                job["last_stdout_pos"] = current_size
        except Exception as e:
            click.echo(click.style(f"Error reading stdout: {str(e)}", fg="red"))
    
    # Check for new stderr
    if stderr_path and os.path.exists(stderr_path):
        try:
            current_size = os.path.getsize(stderr_path)
            last_pos = job.get("last_stderr_pos", 0)
            
            # If the file has grown since we last checked
            if current_size > last_pos:
                with open(stderr_path, 'r') as f:
                    f.seek(last_pos)
                    new_error = f.read()
                    if new_error:
                        # Output a line marker for streamed error output
                        if job["stream_started"]:
                            click.echo(click.style(f"▶ [{job_id}] New error output:", fg="red"))
                        click.echo(click.style(new_error, fg="red"), nl=False)
                        has_new_output = True
                        job["last_output_time"] = time.time()
                
                # Update the position for next time
                job["last_stderr_pos"] = current_size
        except Exception as e:
            click.echo(click.style(f"Error reading stderr: {str(e)}", fg="red"))
    
    return has_new_output

def update_job_status(check_output=True):
    """Update status of all registered jobs"""
    completed_jobs = []
    
    # First check running jobs for new output before handling completions
    if check_output:
        for job_id in background_jobs:
            job = background_jobs[job_id]
            if job["running"] and job.get("stream_output", True):
                check_and_stream_output(job_id, job)
    
    # Now check for job completions
    for job_id in background_jobs:
        job = background_jobs[job_id]
        if job["running"]:
            try:
                process = psutil.Process(job["pid"])
                # Get process status for debugging
                status = process.status()
                
                # Only mark as not running if it's truly terminated
                # Running, sleeping, and disk wait are all considered "running" for our purposes
                if status in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                    job["running"] = False
                    job["notified_completion"] = True
                    completed_jobs.append(job_id)
                    click.echo(click.style(f"\n[{job_id}] Done: {job['command']}", fg="green"))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process no longer exists, so mark it as completed
                job["running"] = False
                if not job.get("notified_completion", False):
                    completed_jobs.append(job_id)
                    job["notified_completion"] = True
                    # Print a blank line to separate from any existing output
                    click.echo("")
                    # Show a prominent divider to make it clear this is a job completion notification
                    click.echo(click.style("="*60, fg="green"))
                    click.echo(click.style(f"[{job_id}] Completed: {job['command']}", fg="green", bold=True))
    
    # Display output of newly completed jobs if requested
    if check_output and completed_jobs:
        for job_id in completed_jobs:
            job = background_jobs[job_id]
            
            # Check if we have output files for this job
            stdout_path = job.get("stdout_path")
            stderr_path = job.get("stderr_path")
            
            # Create a "foreground" effect for the completed job
            click.echo(click.style(f"Job output:", fg="green"))
            
            # Always show a command prompt style line to make it clear this was from a background job
            click.echo(click.style(f"$ {job['command']}", fg="yellow", bold=True))
            
            # Check if there's output to display
            has_output = False
            
            if stdout_path and os.path.exists(stdout_path):
                # Check if there's output to display
                if os.path.getsize(stdout_path) > 0:
                    try:
                        with open(stdout_path, 'r') as f:
                            output = f.read()
                            click.echo(output)
                            has_output = True
                    except Exception as e:
                        click.echo(click.style(f"Error reading output: {str(e)}", fg="red"))
            
            if stderr_path and os.path.exists(stderr_path):
                # Check if there's error output to display
                if os.path.getsize(stderr_path) > 0:
                    try:
                        with open(stderr_path, 'r') as f:
                            error_output = f.read()
                            click.echo(click.style(error_output, fg="red"))
                            has_output = True
                    except Exception as e:
                        click.echo(click.style(f"Error reading error output: {str(e)}", fg="red"))
            
            if not has_output:
                click.echo(click.style("(No output)", fg="cyan"))
                
            click.echo(click.style("Press the <ENTER> key", fg="cyan"))

class JobControlPlugin(BuiltinCommand):
    """Plugin for job control commands (jobs, fg, bg)"""
    
    # Plugin attributes
    plugin_name = "job_control_command"  # Name of the plugin
    is_required = True  # Job control is an optional plugin
    is_enabled = True  # Enabled by default, can be overridden by environment variable
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        cmd = command.strip().split()[0] if command.strip().split() else ""
        return cmd in ["jobs", "fg", "bg"]
    
    def execute(self, command):
        """Execute job control commands"""
        parts = command.strip().split()
        cmd = parts[0]
        
        if cmd == "jobs":
            return self._jobs_command()
        elif cmd == "fg":
            return self._fg_command(parts[1:])
        elif cmd == "bg":
            return self._bg_command(parts[1:])
        
        return True
    
    def _jobs_command(self):
        """List all background jobs"""
        update_job_status()
        
        if not background_jobs:
            click.echo("No background jobs")
            return True
            
        click.echo("Jobs:")
        for job_id, job in background_jobs.items():
            status = "Running" if job["running"] else "Done"
            pid_info = f"(PID: {job['pid']})" if job["running"] else ""
            click.echo(f"[{job_id}] {status} {pid_info} {job['command']}")
            
        return True
    
    def _fg_command(self, args):
        """Bring a job to the foreground"""
        update_job_status()
        
        if not background_jobs:
            click.echo(click.style("No background jobs registered in Jibberish", fg="red"))
            click.echo(click.style("Note: Jobs started before job control was added won't be tracked.", fg="yellow"))
            return True
            
        # If no job id provided, use the most recent job
        job_id = None
        if not args:
            # Find the highest job_id that's still running
            running_jobs = [jid for jid, job in background_jobs.items() if job["running"]]
            if running_jobs:
                job_id = max(running_jobs)
            else:
                click.echo(click.style("No running jobs found", fg="red"))
                self._jobs_command()  # Show all jobs for reference
                return True
        else:
            try:
                # Remove % prefix if present (bash compatibility)
                job_arg = args[0]
                if job_arg.startswith('%'):
                    job_arg = job_arg[1:]
                job_id = int(job_arg)
            except ValueError:
                click.echo(click.style(f"Invalid job ID: {args[0]}", fg="red"))
                return True
                
        if job_id not in background_jobs:
            click.echo(click.style(f"No such job: {job_id}", fg="red"))
            self._jobs_command()  # Show all jobs for reference
            return True
            
        job = background_jobs[job_id]
        
        if not job["running"]:
            click.echo(click.style(f"Job {job_id} ({job['command']}) has completed", fg="yellow"))
            return True
            
        try:
            # Try to attach the process to the terminal
            click.echo(click.style(f"Bringing job {job_id} ({job['command']}) to foreground", fg="green"))
            
            # Check if the process actually exists
            try:
                process = psutil.Process(job["pid"])
                click.echo(click.style(f"Process is {process.status()}", fg="blue"))
            except psutil.NoSuchProcess:
                click.echo(click.style(f"Process {job['pid']} no longer exists", fg="red"))
                job["running"] = False
                return True
                
            # In a more advanced implementation, we would try to attach to the process
            # For now we'll just inform the user about the limitation and alternatives
            click.echo(click.style(
                "Note: Full job control is limited in Jibberish shell. "
                "Here are your options:", 
                fg="yellow"
            ))
            click.echo(click.style(
                f"1. Process ID: {job['pid']} - You can use 'kill -{signal.SIGTERM} {job['pid']}' to terminate if needed", 
                fg="yellow"
            ))
            
            # For specific commands, provide specialized handling
            if "tail" in job["command"]:
                # For tail commands, offer to restart in foreground or show file content
                if "tail -f " in job["command"]:
                    file_path = job["command"].replace("tail -f ", "").strip()
                    choice = input(click.style(f"Do you want to see the content of {file_path} now? (y/n): ", fg="blue"))
                    if choice.lower() == 'y':
                        click.echo(click.style(f"\n--- Content of {file_path} ---", fg="green"))
                        # Kill the background process more forcefully
                        try:
                            # First try a clean terminate
                            process.terminate()
                            # Wait a bit for it to terminate
                            try:
                                process.wait(timeout=1)
                            except:
                                # If it doesn't respond to terminate, try kill
                                process.kill()
                                try:
                                    process.wait(timeout=1)
                                except:
                                    pass
                            
                            # Also try using kill command to be extra sure
                            click.echo(click.style(f"Terminating old process (PID: {job['pid']})", fg="yellow"))
                            os.system(f"kill -9 {job['pid']} 2>/dev/null || true")
                        except:
                            pass  # Ignore errors in termination
                            
                        # Mark the job as not running in our tracking system
                        job["running"] = False
                            
                        # Restart the command without background
                        foreground_cmd = job["command"].replace(" &", "")
                        click.echo(click.style(f"Executing: {foreground_cmd}", fg="green"))
                        click.echo(click.style("Press Ctrl+C to stop and return to the shell", fg="yellow"))
                        
                        try:
                            # Run the command and wait for it to complete or be interrupted
                            os.system(foreground_cmd)  # This will block until interrupted
                        except KeyboardInterrupt:
                            pass  # Handle Ctrl+C gracefully
                        finally:
                            # After the foreground process is interrupted, offer to restart it in background
                            click.echo("\n")
                            bg_choice = input(click.style(f"Restart '{foreground_cmd}' in the background? (y/n): ", fg="blue"))
                            if bg_choice.lower() == 'y':
                                # Launch it in the background using the same technique as in executor.py
                                # This ensures the PID is captured and registered properly
                                click.echo(click.style(f"Restarting in background: {foreground_cmd}", fg="green"))
                                
                                # Use nohup to ensure the process continues even if the terminal closes
                                # and echo $! to get the PID of the background process
                                process = subprocess.Popen(
                                    f"nohup {foreground_cmd} > /dev/null 2>&1 & echo $!",
                                    shell=True,
                                    executable='/bin/bash',
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True
                                )
                                
                                # Get the actual PID of the background process
                                output, _ = process.communicate()
                                try:
                                    # Extract the PID from the output
                                    new_pid = int(output.strip())
                                    
                                    # Register the job with our job control system
                                    new_job_id = register_background_job(new_pid, foreground_cmd)
                                    click.echo(click.style(f"[{new_job_id}] Running in background: {foreground_cmd} (PID: {new_pid})", fg="blue"))
                                except (ValueError, TypeError):
                                    click.echo(click.style(f"Running in background: {foreground_cmd} (unable to track PID)", fg="blue"))
                                
                        return True
                else:
                    click.echo(click.style(
                        "For tail commands: You can start a new tail process in the foreground: " +
                        job["command"].replace(" &", ""), 
                        fg="green"
                    ))
            elif "vim" in job["command"] or "gvim" in job["command"]:
                click.echo(click.style(
                    "For vim/gvim: It's best to just open a new editor session for the file.", 
                    fg="green"
                ))
            
            return True
        except Exception as e:
            click.echo(click.style(f"Error bringing job to foreground: {str(e)}", fg="red"))
            return True
    
    def _bg_command(self, args):
        """Continue a stopped job in the background"""
        update_job_status()
        
        if not background_jobs:
            click.echo(click.style("No background jobs", fg="red"))
            return True
            
        # Limited implementation - just show jobs since we can't really control them
        return self._jobs_command()

# Register the plugin with the registry
BuiltinCommandRegistry.register(JobControlPlugin())
