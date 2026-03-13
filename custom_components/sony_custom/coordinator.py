"""Sony Legacy API integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import requests
from homeassistant.const import STATE_OFF, STATE_ON, STATE_PLAYING, STATE_PAUSED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from sonyapilib.device import SonyDevice, HttpMethod

from .const import DEVICE_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SonyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Data update coordinator for Sony Legacy API devices."""

    def __init__(self, hass: HomeAssistant, sony_device: SonyDevice) -> None:
        """Initialize the Coordinator."""
        super().__init__(
            hass,
            name=DOMAIN,
            logger=_LOGGER,
            update_interval=DEVICE_SCAN_INTERVAL,
        )
        self.hass = hass
        self.api: SonyDevice = sony_device
        self.device_data = SonyDeviceData(self)
        # self.data = {}  <-- ELIMINADO: El padre ya lo maneja

    async def _async_update_data(self) -> dict[str, Any]:
        """Get the latest data from the Sony device."""
        _LOGGER.debug("Sony device coordinator update")
        try:
            async with asyncio.timeout(10):
                await self.device_data.update_state()

            return {
                "state": self.device_data.state,
                "model": getattr(self.api, "modelName", "Sony Device"),
                "mac": getattr(self.api, "mac", "unknown"),
                "online": self.device_data._init,
            }

        except Exception as ex:
            _LOGGER.debug("Sony device unavailable or network timeout: %s", ex)
            raise UpdateFailed(f"Error updating {self.name}: {ex}") from ex

class SonyDeviceData:
    """Helper class to manage Sony device internal state and initialization."""

    def __init__(self, coordinator: SonyCoordinator):
        """Initialize the DeviceData helper."""
        self.coordinator = coordinator
        self.state = STATE_OFF
        self._init = False

    async def init_device(self):
        """Initialize the device by reading its DMR resources."""
        sony_device = self.coordinator.api
        try:
            # Check availability via DMR URL using the blocking requests library
            response = await self.coordinator.hass.async_add_executor_job(
                sony_device._send_http,
                sony_device.dmr_url,
                HttpMethod.GET
            )
        except requests.exceptions.ConnectionError:
            _LOGGER.debug("Sony device connection error, waiting for next call")
            response = None
        except requests.exceptions.RequestException as exc:
            _LOGGER.error("Failed to get DMR for %s: %s", self.coordinator.name, exc)
            return

        try:
            if response and response.status_code == 200:
                _LOGGER.debug("Sony device connection ready, proceeding to init")
                await self.coordinator.hass.async_add_executor_job(sony_device.init_device)
                self._init = True
            else:
                _LOGGER.debug("Sony device not ready (Offline)")
                self._init = False
        except Exception as ex:
            _LOGGER.error("Failed to get device information: %s", ex)
            self._init = False

    async def update_state(self) -> None:
        """Update power and playback status of the device."""
        if not self._init:
            await self.init_device()
            if not self._init:
                return

        _LOGGER.debug("Updating Sony device state via SonyDeviceData")
        
        # Power Check
        power_status = await self.coordinator.hass.async_add_executor_job(
            self.coordinator.api.get_power_status
        )
        
        if not power_status or power_status == "OFF":
            self.state = STATE_OFF
            self._init = False  # Reset init to force a clean re-check on next wake
            return

        self.state = STATE_ON

        # Playback Info Check
        try:
            playback_info = await self.coordinator.hass.async_add_executor_job(
                self.coordinator.api.get_playing_status
            )
            
            if playback_info == "PLAYING":
                self.state = STATE_PLAYING
            elif playback_info == "PAUSED_PLAYBACK":
                self.state = STATE_PAUSED
            else:
                self.state = STATE_ON

        except Exception as err:
            _LOGGER.debug("Could not retrieve playback status: %s", err)
            self.state = STATE_OFF
            self._init = False