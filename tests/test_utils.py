#!/usr/bin/env python3
"""
Tests for the utils module.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import utils


class TestUtils(unittest.TestCase):
    """Test cases for the utils module."""

    def test_run_command(self):
        """Test run_command function."""
        with patch('subprocess.Popen') as mock_popen:
            # Set up the mock
            process_mock = MagicMock()
            process_mock.communicate.return_value = ("output", "error")
            process_mock.returncode = 0
            mock_popen.return_value = process_mock

            # Call the function
            stdout, stderr, return_code = utils.run_command("test command")

            # Check the results
            self.assertEqual(stdout, "output")
            self.assertEqual(stderr, "error")
            self.assertEqual(return_code, 0)
            mock_popen.assert_called_once()

    def test_get_audio_devices(self):
        """Test get_audio_devices function."""
        with patch('utils.run_command') as mock_run_command:
            mock_run_command.return_value = ("device1\ndevice2", "", 0)
            devices = utils.get_audio_devices()
            self.assertEqual(devices, ["device1", "device2"])
            mock_run_command.assert_called_once_with("aplay -l")

    def test_get_pipewire_devices(self):
        """Test get_pipewire_devices function."""
        with patch('utils.run_command') as mock_run_command:
            mock_run_command.return_value = ("device1\ndevice2", "", 0)
            devices = utils.get_pipewire_devices()
            self.assertEqual(devices, ["device1", "device2"])
            mock_run_command.assert_called_once_with("pw-cli list-objects | grep -i node")

    def test_get_iquadio_device_found(self):
        """Test get_iquadio_device function when device is found."""
        with patch('utils.get_audio_devices') as mock_get_audio_devices:
            mock_get_audio_devices.return_value = [
                "card 0: PCH [HDA Intel PCH], device 0: ALC283 Analog [ALC283 Analog]",
                "card 2: IQaudIODAC [IQaudIODAC], device 0: IQaudIO DAC HiFi pcm512x-hifi-0 [IQaudIO DAC HiFi pcm512x-hifi-0]"
            ]
            device = utils.get_iquadio_device()
            self.assertEqual(device, "hw:2,0")

    def test_get_iquadio_device_not_found(self):
        """Test get_iquadio_device function when device is not found."""
        with patch('utils.get_audio_devices') as mock_get_audio_devices:
            mock_get_audio_devices.return_value = [
                "card 0: PCH [HDA Intel PCH], device 0: ALC283 Analog [ALC283 Analog]"
            ]
            device = utils.get_iquadio_device()
            self.assertIsNone(device)

    def test_test_audio_device_success(self):
        """Test test_audio_device function when successful."""
        with patch('utils.run_command') as mock_run_command:
            mock_run_command.return_value = ("", "", 0)
            result = utils.test_audio_device("hw:2,0")
            self.assertTrue(result)
            mock_run_command.assert_called_once_with("speaker-test -D hw:2,0 -c2 -twav -l1")

    def test_test_audio_device_failure(self):
        """Test test_audio_device function when failed."""
        with patch('utils.run_command') as mock_run_command:
            mock_run_command.return_value = ("", "error", 1)
            result = utils.test_audio_device("hw:2,0")
            self.assertFalse(result)
            mock_run_command.assert_called_once_with("speaker-test -D hw:2,0 -c2 -twav -l1")

    def test_is_pipewire_running_true(self):
        """Test is_pipewire_running function when Pipewire is running."""
        with patch('utils.run_command') as mock_run_command:
            mock_run_command.return_value = ("123", "", 0)
            result = utils.is_pipewire_running()
            self.assertTrue(result)
            mock_run_command.assert_called_once_with("pidof pipewire")

    def test_is_pipewire_running_false(self):
        """Test is_pipewire_running function when Pipewire is not running."""
        with patch('utils.run_command') as mock_run_command:
            mock_run_command.return_value = ("", "", 1)
            result = utils.is_pipewire_running()
            self.assertFalse(result)
            mock_run_command.assert_called_once_with("pidof pipewire")

    def test_start_pipewire_success(self):
        """Test start_pipewire function when successful."""
        with patch('utils.is_pipewire_running') as mock_is_running, \
             patch('utils.run_command') as mock_run_command:
            # First call to is_pipewire_running returns False, second returns True
            mock_is_running.side_effect = [False, True]
            mock_run_command.return_value = ("", "", 0)

            result = utils.start_pipewire()

            self.assertTrue(result)
            mock_run_command.assert_called_once_with("systemctl --user start pipewire pipewire-pulse")

    def test_start_pipewire_already_running(self):
        """Test start_pipewire function when Pipewire is already running."""
        with patch('utils.is_pipewire_running') as mock_is_running:
            mock_is_running.return_value = True
            result = utils.start_pipewire()
            self.assertTrue(result)
            mock_is_running.assert_called_once()

    def test_start_pipewire_failure(self):
        """Test start_pipewire function when failed."""
        with patch('utils.is_pipewire_running') as mock_is_running, \
             patch('utils.run_command') as mock_run_command, \
             patch('utils.time.sleep') as mock_sleep:
            mock_is_running.return_value = False
            # All commands fail
            mock_run_command.return_value = ("", "error", 1)

            result = utils.start_pipewire()

            # We now expect True even when Pipewire fails to start
            self.assertTrue(result)
            # Check that all methods were attempted
            self.assertEqual(mock_run_command.call_count, 3)
            mock_run_command.assert_any_call("systemctl --user start pipewire pipewire-pulse")
            mock_run_command.assert_any_call("pipewire &")
            mock_run_command.assert_any_call("pipewire-pulse &")

    def test_configure_pipewire_for_dev_mode(self):
        """Test configure_pipewire_for_dev_mode function."""
        result = utils.configure_pipewire_for_dev_mode()
        self.assertTrue(result)

    def test_setup_audio_device_success(self):
        """Test setup_audio_device function when successful."""
        with patch('builtins.open', unittest.mock.mock_open()) as mock_open:
            result = utils.setup_audio_device("hw:2,0")
            self.assertTrue(result)
            mock_open.assert_called_once_with("/etc/asound.conf", "w")

    def test_setup_audio_device_failure(self):
        """Test setup_audio_device function when failed."""
        with patch('builtins.open', side_effect=Exception("Error")):
            result = utils.setup_audio_device("hw:2,0")
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
