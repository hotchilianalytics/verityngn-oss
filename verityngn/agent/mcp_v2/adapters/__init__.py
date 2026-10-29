"""Engine and provider adapters behind verityngn-mcp v2 tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from verityngn.agent.mcp_v2.adapters.disclosure import DisclosureEngine, load_disclosure_engine
from verityngn.agent.mcp_v2.adapters.edgar import EdgarClient
from verityngn.agent.mcp_v2.adapters.news import EventRegistryNews, GdeltNews
from verityngn.agent.mcp_v2.adapters.sanctions import OpenSanctions
from verityngn.agent.mcp_v2.adapters.video import VerityNgnVideoEngine, VideoEngine
from verityngn.agent.mcp_v2.adapters.youtube import OwnedChannelRegistry, YouTubeUploads


@dataclass
class Adapters:
    disclosure: DisclosureEngine = field(default_factory=load_disclosure_engine)
    video: VideoEngine = field(default_factory=VerityNgnVideoEngine)
    edgar: Any = field(default_factory=EdgarClient)
    youtube: Any = field(default_factory=YouTubeUploads)
    channels: Any = field(default_factory=OwnedChannelRegistry)
    event_registry: Any = field(default_factory=EventRegistryNews)
    gdelt: Any = field(default_factory=GdeltNews)
    sanctions: Any = field(default_factory=OpenSanctions)


__all__ = ["Adapters"]
