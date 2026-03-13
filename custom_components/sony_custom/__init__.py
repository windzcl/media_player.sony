"""The Sony Legacy API integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from sonyapilib.device import SonyDevice, AuthenticationResult

from .const import (
    DOMAIN, 
    CONF_HOST, 
    CONF_APP_PORT, 
    CONF_IRCC_PORT, 
    CONF_DMR_PORT, 
    SONY_COORDINATOR,
    SONY_API, 
    DEFAULT_DEVICE_NAME
)
from .coordinator import SonyCoordinator

_LOGGER: logging.Logger = logging.getLogger(__package__)

# We keep both platforms as they exist in your file structure
PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.REMOTE
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sony Legacy device from a config entry."""
    try:
        # Initialize the API client with the data from the config entry
        sony_device = SonyDevice(
            entry.data[CONF_HOST], 
            DEFAULT_DEVICE_NAME,
            psk=None, 
            app_port=entry.data[CONF_APP_PORT],
            dmr_port=entry.data[CONF_DMR_PORT], 
            ircc_port=entry.data[CONF_IRCC_PORT]
        )
        
        pin = entry.data.get("pin")
        sony_device.pin = pin
        sony_device.mac = entry.data.get("mac_address")

        # Handling registration/PIN logic
        if not pin or pin == "0000":
            register_result = await hass.async_add_executor_job(sony_device.register)
            if register_result == AuthenticationResult.PIN_NEEDED:
                raise ConfigEntryAuthFailed("Authentication required: Please check your Sony device for a PIN")
        
    except Exception as ex:
        _LOGGER.error("Could not connect to Sony device at %s: %s", entry.data[CONF_HOST], ex)
        raise ConfigEntryNotReady(f"Device not reachable: {ex}") from ex

    # Create the Coordinator to manage all polling/state updates
    coordinator = SonyCoordinator(hass, sony_device)
    
    # Store both for access by media_player.py and remote.py
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        SONY_COORDINATOR: coordinator,
        SONY_API: sony_device,
    }

    # Reduce log noise from the library
    logging.getLogger("sonyapilib").setLevel(logging.CRITICAL)

    # Initial data fetch before setting up platforms
    await coordinator.async_config_entry_first_refresh()

    # Launch media_player and remote platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register listener for future config changes
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry safely."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
