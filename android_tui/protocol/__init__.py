"""
LocalSend Protocol and Persistent Connection module for AndroidTUI.
Implements LocalSend v2 UDP multicast/broadcast discovery, HTTP peer registration,
and persistent heartbeat connection manager between PC and Android devices.
"""
from .localsend import (
    LocalSendDevice,
    LocalSendDiscovery,
    PersistentConnectionManager,
    LOCALSEND_MULTICAST_GROUP,
    LOCALSEND_PORT,
)

__all__ = [
    "LocalSendDevice",
    "LocalSendDiscovery",
    "PersistentConnectionManager",
    "LOCALSEND_MULTICAST_GROUP",
    "LOCALSEND_PORT",
]
