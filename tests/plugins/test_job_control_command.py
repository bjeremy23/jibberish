#!/usr/bin/env python
"""
Unittest-based test script for testing the job_control_command plugin of Jibberish shell.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the plugin to test
from app.plugins import job_control_command
from app.plugins.job_control_command import JobControlPlugin, register_background_job, update_job_status
from tests.utils.test_utils import CaptureOutput, mock_click_echo
from tests import test_helper

class TestJobControlPlugin(unittest.TestCase):
    """Tests for the JobControlPlugin plugin."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Reset the global state before each test
        job_control_command.background_jobs = {}
        job_control_command.job_counter = 1
        
        # Create an instance of the plugin
        self.job_control_plugin = JobControlPlugin()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Mock click.style to return the text unchanged
        self.click_style_patcher = patch('click.style', lambda text, **kwargs: text)
        self.mock_click_style = self.click_style_patcher.start()
        
        # Mock psutil for process detection
        self.psutil_patcher = patch('app.plugins.job_control_command.psutil')
        self.mock_psutil = self.psutil_patcher.start()
        
        # Mock os.system for executing commands
        self.os_system_patcher = patch('os.system')
        self.mock_os_system = self.os_system_patcher.start()
        
        # Mock subprocess.Popen for background processes
        self.popen_patcher = patch('subprocess.Popen')
        self.mock_popen = self.popen_patcher.start()
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("12345", "")
        self.mock_popen.return_value = mock_process
    
    def tearDown(self):
        """Clean up after each test method."""
        # Stop the patchers
        self.click_echo_patcher.stop()
        self.click_style_patcher.stop()
        self.psutil_patcher.stop()
        self.os_system_patcher.stop()
        self.popen_patcher.stop()
    
    def test_can_handle(self):
        """Test the can_handle method recognizes job control commands."""
        # Should handle job control commands
        self.assertTrue(self.job_control_plugin.can_handle("jobs"), 
                      "Should handle 'jobs' command")
        self.assertTrue(self.job_control_plugin.can_handle("fg"), 
                      "Should handle 'fg' command")
        self.assertTrue(self.job_control_plugin.can_handle("bg"), 
                      "Should handle 'bg' command")
        
        # Should not handle other commands
        self.assertFalse(self.job_control_plugin.can_handle("echo"), 
                       "Should not handle 'echo' command")
        self.assertFalse(self.job_control_plugin.can_handle("job"), 
                       "Should not handle 'job' command")
    
    def test_execute_dispatches_commands(self):
        """Test the execute method dispatches to the correct handler."""
        with patch.object(self.job_control_plugin, '_jobs_command') as mock_jobs, \
             patch.object(self.job_control_plugin, '_fg_command') as mock_fg, \
             patch.object(self.job_control_plugin, '_bg_command') as mock_bg:
            
            # Test jobs command
            self.job_control_plugin.execute("jobs")
            mock_jobs.assert_called_once()
            mock_fg.assert_not_called()
            mock_bg.assert_not_called()
            
            # Reset mocks
            mock_jobs.reset_mock()
            mock_fg.reset_mock()
            mock_bg.reset_mock()
            
            # Test fg command
            self.job_control_plugin.execute("fg 1")
            mock_fg.assert_called_once_with(['1'])
            mock_jobs.assert_not_called()
            mock_bg.assert_not_called()
            
            # Reset mocks
            mock_jobs.reset_mock()
            mock_fg.reset_mock()
            mock_bg.reset_mock()
            
            # Test bg command
            self.job_control_plugin.execute("bg 2")
            mock_bg.assert_called_once_with(['2'])
            mock_jobs.assert_not_called()
            mock_fg.assert_not_called()
    
    def test_register_background_job(self):
        """Test registering a background job."""
        # Register a job
        job_id = register_background_job(12345, "test command")
        
        # Check it was registered properly
        self.assertEqual(job_id, 1, "First job should have ID 1")
        self.assertIn(1, job_control_command.background_jobs)
        self.assertEqual(job_control_command.background_jobs[1]["pid"], 12345)
        self.assertEqual(job_control_command.background_jobs[1]["command"], "test command")
        self.assertTrue(job_control_command.background_jobs[1]["running"])
        
        # Register a second job
        job_id = register_background_job(67890, "another command")
        
        # Check it was registered with incremented ID
        self.assertEqual(job_id, 2, "Second job should have ID 2")
        self.assertIn(2, job_control_command.background_jobs)
    
    def test_jobs_command_with_no_jobs(self):
        """Test jobs command with no background jobs."""
        # Call the jobs command
        result = self.job_control_plugin._jobs_command()
        
        # Should return True
        self.assertTrue(result)
        
        # Check output
        self.mock_click_echo.assert_called_with("No background jobs")
    
    def test_jobs_command_with_jobs(self):
        """Test jobs command with background jobs."""
        # Register some jobs
        register_background_job(12345, "tail -f file1.txt")
        register_background_job(67890, "sleep 100")
        
        # Set up mock for process status
        mock_process = MagicMock()
        mock_process.status.return_value = "sleeping"
        self.mock_psutil.Process.return_value = mock_process
        
        # Call the jobs command
        result = self.job_control_plugin._jobs_command()
        
        # Should return True
        self.assertTrue(result)
        
        # Should list both jobs
        self.mock_click_echo.assert_any_call("Jobs:")
        # Last two calls should be for the job listings with PID info
        calls = self.mock_click_echo.call_args_list[-2:]
        self.assertIn("[1] Running", str(calls[0]))
        self.assertIn("(PID: 12345)", str(calls[0]))
        self.assertIn("tail -f file1.txt", str(calls[0]))
        self.assertIn("[2] Running", str(calls[1]))
    
    def test_fg_command_no_jobs(self):
        """Test fg command with no jobs."""
        # Call fg command
        result = self.job_control_plugin._fg_command([])
        
        # Should return True
        self.assertTrue(result)
        
        # Should show no jobs message
        self.mock_click_echo.assert_any_call("No background jobs registered in Jibberish")
    
    def test_fg_command_with_job_id(self):
        """Test fg command with specific job ID."""
        # Register a job
        register_background_job(12345, "tail -f file1.txt")
        
        # Set up mock for process status
        mock_process = MagicMock()
        mock_process.status.return_value = "sleeping"
        self.mock_psutil.Process.return_value = mock_process
        
        # Mock input to simulate user declining to view content
        with patch('builtins.input', return_value='n'):
            # Call fg with job ID
            result = self.job_control_plugin._fg_command(['1'])
            
            # Should return True
            self.assertTrue(result)
            
            # Should show bringing job to foreground
            self.mock_click_echo.assert_any_call("Bringing job 1 (tail -f file1.txt) to foreground")
    
    def test_fg_command_with_invalid_job_id(self):
        """Test fg command with invalid job ID."""
        # Register a job
        register_background_job(12345, "tail -f file1.txt")
        
        # Call fg with non-existent job ID
        result = self.job_control_plugin._fg_command(['999'])
        
        # Should return True
        self.assertTrue(result)
        
        # Should show no such job message
        self.mock_click_echo.assert_any_call("No such job: 999")
    
    def test_bg_command(self):
        """Test bg command (currently just shows jobs)."""
        # Register a job
        register_background_job(12345, "tail -f file1.txt")
        
        # Set up mock for process status
        mock_process = MagicMock()
        mock_process.status.return_value = "sleeping"
        self.mock_psutil.Process.return_value = mock_process
        
        # Call bg command
        with patch.object(self.job_control_plugin, '_jobs_command') as mock_jobs:
            result = self.job_control_plugin._bg_command(['1'])
            
            # Should call jobs command
            mock_jobs.assert_called_once()
    
    def test_update_job_status(self):
        """Test updating job status."""
        # Register jobs
        register_background_job(12345, "command1")
        register_background_job(67890, "command2")
        
        # Mock process for running job
        running_process = MagicMock()
        running_process.status.return_value = "sleeping"
        
        # Create proper exception classes for psutil exceptions
        class MockNoSuchProcess(Exception):
            def __init__(self, pid=None, name=None, msg=None):
                self.pid = pid
                self.name = name
                self.msg = msg
        
        class MockAccessDenied(Exception):
            def __init__(self, pid=None, name=None, msg=None):
                self.pid = pid
                self.name = name
                self.msg = msg
        
        # Assign our mock exception classes to the mock psutil module
        self.mock_psutil.NoSuchProcess = MockNoSuchProcess
        self.mock_psutil.AccessDenied = MockAccessDenied
        
        # Mock psutil.Process to return different processes
        def mock_get_process(pid):
            if pid == 12345:
                return running_process
            else:
                raise MockNoSuchProcess(pid=67890)
        
        self.mock_psutil.Process.side_effect = mock_get_process
        self.mock_psutil.STATUS_ZOMBIE = "zombie"
        self.mock_psutil.STATUS_DEAD = "dead"
        
        # Call update_job_status
        update_job_status()
        
        # First job should still be running, second should be marked as not running
        self.assertTrue(job_control_command.background_jobs[1]["running"])
        self.assertFalse(job_control_command.background_jobs[2]["running"])

if __name__ == '__main__':
    unittest.main()
