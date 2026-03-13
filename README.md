Sony Legacy API (Updated for HA 2026)
This is a refactored and stabilized version of the Sony Legacy API integration for Home Assistant. It is specifically designed to work with newer versions of Home Assistant (2026.2+) and addresses several long-standing stability issues found in earlier forks.

Key Improvements in this Fork
Recursion Fix: Resolved the maximum recursion depth exceeded error that caused integration crashes when devices were offline or on unstable Wi-Fi.

Asynchronous Architecture: Refactored to use async/await and DataUpdateCoordinator, preventing blocking calls that slow down Home Assistant.

Wi-Fi Stability: Optimized polling intervals and timeouts to better support Sony players (like the UBP-X700) connected via wireless networks.

Clean Code: Removed legacy code and unmaintained platforms to reduce the footprint and improve performance.

Installation
Via HACS (Recommended)
Go to HACS -> Integrations.

Click the three dots in the top right and select Custom repositories.

Paste the URL of this repository: https://github.com/windzcl/media_player.sony

Select Integration as the category and click Add.

Find "Sony Legacy API (Custom)" in HACS and click Download.

Restart Home Assistant.

Manual
Copy the custom_components/sony_custom/ folder to your <config>/custom_components/ directory.

Restart Home Assistant.

Configuration
Go to Settings -> Devices & Services.

Click Add Integration and search for Sony Legacy API.

Enter the IP Address of your device.

Follow the on-screen instructions to enter the PIN shown on your device.

Note: The device must be on the same subnet as your Home Assistant instance. For better stability, it is recommended to enable "Remote Start" (Inicio Remoto) in your Sony device settings.

Supported Features
Media Player: Play, Pause, Stop, Previous/Next Track, Volume, and Power control.

Remote Control: Send IRCC commands via the remote.send_command service.