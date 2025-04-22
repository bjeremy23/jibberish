"""
Job control plugin for managing background processes.
"""
import os
import signal
import psutil
import click
import subprocess
from plugin_system import BuiltinCommand, BuiltinCommandRegistry

# Global dictionary to track background jobs
# Format: {job_id: {"pid": pid, "command": command, "running": True/False}}
background_jobs = {}
job_counter = 1

def register_background_job(pid, command):
    """Register a new background job"""
    global job_counter
    job_id = job_counter
    background_jobs[job_id] = {
        "pid": pid,
        "command": command,
        "running": True
    }
    job_counter += 1
    return job_id

def update_job_status():
    """Update status of all registered jobs"""
    for job_id in background_jobs:
        job = background_jobs[job_id]
        if job["running"]:
            try:
                process = psutil.Process(job["pid"])
                # Get process status for debugging
                status = process.status()
                click.echo(click.style(f"Job {job_id} (PID {job['pid']}): {job['command']} - Status: {status}", fg="blue"))
                
                # Only mark as not running if it's truly terminated
                # Running, sleeping, and disk wait are all considered "running" for our purposes
                if status in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                    job["running"] = False
                    click.echo(click.style(f"Marked job {job_id} as done", fg="yellow"))
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                click.echo(click.style(f"Job {job_id}: Process error - {str(e)}", fg="red"))
                job["running"] = False

class JobControlCommand(BuiltinCommand):
    """Plugin for job control commands (jobs, fg, bg)"""
    
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
BuiltinCommandRegistry.register(JobControlCommand())
