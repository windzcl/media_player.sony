"""Support for Sony MediaPlayer devices via Legacy API."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
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
    """Set up the Sony Media Player entity from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SONY_COORDINATOR]
    async_add_entities([SonyMediaPlayerEntity(coordinator, config_entry)])


class SonyMediaPlayerEntity(CoordinatorEntity, MediaPlayerEntity):
    """Representation of a Sony Media Player Device."""

    _attr_has_entity_name = True
    _attr_name = None  # Uses device name from DeviceInfo

    _attr_supported_features = (
        MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.PLAY
    )

    def __init__(self, coordinator: Any, config_entry: ConfigEntry) -> None:
        """Initialize the Sony entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_media_player"
        
        # Device Info for proper grouping in HA UI
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, getattr(coordinator.api, "mac", config_entry.entry_id))},
            name=getattr(coordinator.api, "nickname", "Sony Device"),
            manufacturer="Sony",
            model=coordinator.data.get("model", "Sony Media Player"),
        )

    @property
    def state(self) -> str | None:
        """Return the state of the device from coordinator data."""
        return self.coordinator.data.get("state", STATE_OFF)

    # --- Async Service Commands ---

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        await self.hass.async_add_executor_job(self.coordinator.api.power, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn off media player."""
        await self.hass.async_add_executor_job(self.coordinator.api.power, False)
        await self.coordinator.async_request_refresh()

    async def async_media_play(self) -> None:
        """Send play command."""
        await self.hass.async_add_executor_job(self.coordinator.api.play)
        await self.coordinator.async_request_refresh()

    async def async_media_pause(self) -> None:
        """Send pause command."""
        await self.hass.async_add_executor_job(self.coordinator.api.pause)
        await self.coordinator.async_request_refresh()

    async def async_media_stop(self) -> None:
        """Send stop command."""
        await self.hass.async_add_executor_job(self.coordinator.api.stop)
        await self.coordinator.async_request_refresh()

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self.hass.async_add_executor_job(self.coordinator.api.next)

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        await self.hass.async_add_executor_job(self.coordinator.api.prev)

    async def async_volume_up(self) -> None:
        """Step volume up."""
        await self.hass.async_add_executor_job(self.coordinator.api.volume_up)

    async def async_volume_down(self) -> None:
        """Step volume down."""
        await self.hass.async_add_executor_job(self.coordinator.api.volume_down)

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        await self.hass.async_add_executor_job(self.coordinator.api.mute)