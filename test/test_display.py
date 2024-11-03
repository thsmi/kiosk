"""
Test the cron file logic.
"""

from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

from src.display import CMD_GET_SCREENS, Display, DisplayException, Screen

class TestDisplay(unittest.TestCase):
    """
    Test the display logic.
    """

    def test_get_screens(self):
        with patch("subprocess.run") as mock_run:

            data = ""
            with (Path(__file__).parent / "xrandr-no-screen-connected.txt").open("r") as f:
                data = f.read()

            mock_run.return_value = MagicMock(stdout=data)

            display = Display()
            screens = display.get_screens()

            hdmi1 = screens[0]
            self.assertEqual("disconnected", hdmi1.get_status())
            self.assertTrue(hdmi1.is_primary())
            self.assertEqual(3840, hdmi1.get_x_resolution())
            self.assertEqual(2160, hdmi1.get_y_resolution())
            self.assertEqual("normal", hdmi1.get_orientation())

            hdmi2 = screens[1]
            self.assertEqual("disconnected", hdmi2.get_status())
            self.assertFalse(hdmi2.is_primary())
            self.assertEqual(0, hdmi2.get_x_resolution())
            self.assertEqual(0, hdmi2.get_y_resolution())
            self.assertEqual("normal", hdmi2.get_orientation())



class TestScreen(unittest.TestCase):
    """
    Test the screen logic.
    """

    def test_invalid_screen_name(self):
        """
        Creates a screen with an invalid name.
        """

        with self.assertRaises(DisplayException) as context:
            Screen("HDMI 1")

        self.assertEqual(
            str(context.exception), "Invalid screen name HDMI 1")            

    def test_no_screens_connected(self):
        """
        Test if no screens are connected.
        """

        with patch("subprocess.run") as mock_run:

            data = ""
            with (Path(__file__).parent / "xrandr-no-screen-connected.txt").open("r") as f:
                data = f.read()

            mock_run.return_value = MagicMock(stdout=data)

            hdmi1 = Screen("HDMI-1").load()
            self.assertEqual("HDMI-1", hdmi1.get_name())
            self.assertEqual("disconnected", hdmi1.get_status())
            self.assertFalse(hdmi1.is_connected())
            self.assertTrue(hdmi1.is_primary())
            self.assertEqual(3840, hdmi1.get_x_resolution())
            self.assertEqual(2160, hdmi1.get_y_resolution())
            self.assertEqual("normal", hdmi1.get_orientation())

            hdmi2 = Screen("HDMI-2").load()
            self.assertEqual("HDMI-2", hdmi2.get_name())
            self.assertEqual("disconnected", hdmi2.get_status())
            self.assertFalse(hdmi2.is_connected())
            self.assertFalse(hdmi2.is_primary())
            self.assertEqual(0, hdmi2.get_x_resolution())
            self.assertEqual(0, hdmi2.get_y_resolution())
            self.assertEqual("normal", hdmi2.get_orientation())

            with self.assertRaises(DisplayException) as context:
                Screen("HDMI-3").load()

            self.assertEqual(
                str(context.exception), "No screen HDMI-3 found")

            mock_run.assert_called_with(
                  CMD_GET_SCREENS, shell=True,
                  capture_output=True, text=True, check=True)

    def test_hdmi1_connected(self):
        """
        Checks if HDMI1 is connected.
        """

        with patch("subprocess.run") as mock_run:

            data = ""
            with (Path(__file__).parent / "xrandr-hdmi1-connected.txt").open("r") as f:
                data = f.read()

            mock_run.return_value = MagicMock(stdout=data)

            hdmi1 = Screen("HDMI-1").load()
            self.assertEqual("HDMI-1", hdmi1.get_name())
            self.assertEqual("connected", hdmi1.get_status())
            self.assertTrue(hdmi1.is_connected())
            self.assertTrue(hdmi1.is_primary())
            self.assertEqual(3840, hdmi1.get_x_resolution())
            self.assertEqual(2160, hdmi1.get_y_resolution())
            self.assertEqual("normal", hdmi1.get_orientation())

            hdmi2 = Screen("HDMI-2").load()
            self.assertEqual("HDMI-2", hdmi2.get_name())
            self.assertEqual("disconnected", hdmi2.get_status())
            self.assertFalse(hdmi2.is_connected())
            self.assertFalse(hdmi2.is_primary())
            self.assertEqual(0, hdmi2.get_x_resolution())
            self.assertEqual(0, hdmi2.get_y_resolution())
            self.assertEqual("normal", hdmi2.get_orientation())

            with self.assertRaises(DisplayException) as context:
                Screen("HDMI-3").load()

            self.assertEqual(
                str(context.exception), "No screen HDMI-3 found")

            mock_run.assert_called_with(
                  CMD_GET_SCREENS, shell=True,
                  capture_output=True, text=True, check=True)


    def test_hdmi2_connected(self):
        """
        Checks if HDMI2 is connected.
        """

        with patch("subprocess.run") as mock_run:

            data = ""
            with (Path(__file__).parent / "xrandr-hdmi2-connected.txt").open("r") as f:
                data = f.read()

            mock_run.return_value = MagicMock(stdout=data)

            hdmi1 = Screen("HDMI-1").load()
            self.assertEqual("HDMI-1", hdmi1.get_name())
            self.assertEqual("disconnected", hdmi1.get_status())
            self.assertFalse(hdmi1.is_connected())
            self.assertTrue(hdmi1.is_primary())
            self.assertEqual(3840, hdmi1.get_x_resolution())
            self.assertEqual(2160, hdmi1.get_y_resolution())
            self.assertEqual("normal", hdmi1.get_orientation())

            hdmi2 = Screen("HDMI-2").load()
            self.assertEqual("HDMI-2", hdmi2.get_name())
            self.assertEqual("connected", hdmi2.get_status())
            self.assertTrue(hdmi2.is_connected())
            self.assertFalse(hdmi2.is_primary())
            self.assertEqual(0, hdmi2.get_x_resolution())
            self.assertEqual(0, hdmi2.get_y_resolution())
            self.assertEqual("normal", hdmi2.get_orientation())

            with self.assertRaises(DisplayException) as context:
                Screen("HDMI-3").load()

            self.assertEqual(
                str(context.exception), "No screen HDMI-3 found")

            mock_run.assert_called_with(
                  CMD_GET_SCREENS, shell=True,
                  capture_output=True, text=True, check=True)


if __name__ == '__main__':
    unittest.main()
