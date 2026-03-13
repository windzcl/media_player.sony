"""Support for Sony Remote via Legacy API."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Iterable

from homeassistant.components.remote import (
    ATTR_DELAY_SECS,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    DEFAULT_NUM_REPEATS,
    RemoteEntity,
    RemoteEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SONY_COORDINATOR

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Sony Remote entity from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SONY_COORDINATOR]
    async_add_entities([SonyRemoteEntity(coordinator, config_entry)])


class SonyRemoteEntity(CoordinatorEntity, RemoteEntity):
    """Representation of a Sony Remote Control."""

    _attr_has_entity_name = True
    _attr_name = "Remote"
    _attr_icon = "mdi:remote-tv"
    _attr_supported_features = RemoteEntityFeature.ACTIVITY

    def __init__(self, coordinator: Any, config_entry: ConfigEntry) -> None:
        """Initialize the Sony remote."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_remote"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, getattr(coordinator.api, "mac", config_entry.entry_id))},
            name=getattr(coordinator.api, "nickname", "Sony Device"),
            manufacturer="Sony",
            model=coordinator.data.get("model", "Sony Media Player"),
        )

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self.coordinator.data.get("state") != STATE_OFF

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        await self.hass.async_add_executor_job(self.coordinator.api.power, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        await self.hass.async_add_executor_job(self.coordinator.api.power, False)
        await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs: Any) -> None:
        """Toggle the power of the device."""
        current_state = self.coordinator.data.get("state")
        new_state = current_state == STATE_OFF
        await self.hass.async_add_executor_job(self.coordinator.api.power, new_state)
        await self.coordinator.async_request_refresh()

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send IRCC commands to the Sony device."""
        num_repeats = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        delay_secs = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)

        for _ in range(num_repeats):
            for single_command in command:
                _LOGGER.debug("Sending command %s to Sony device", single_command)
                # We use executor_job because _send_command is a blocking HTTP call
                await self.hass.async_add_executor_job(
                    self.coordinator.api._send_command, single_command
                )
                if delay_secs > 0:
                    await asyncio.sleep(delay_secs)