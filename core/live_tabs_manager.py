# -*- coding: utf-8 -*-
"""K1 VMS — Live Tabs Manager"""
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict

import config


TABS_FILE = config.DATA_DIR / "live_tabs.json"


@dataclass
class LiveTab:
    uid: str
    name: str
    layout: str = "2x2"
    cells: Dict[str, str] = field(default_factory=dict)
    order: int = 0
    created_at: str = ""

    def to_dict(self):
        return {
            "uid": self.uid,
            "name": self.name,
            "layout": self.layout,
            "cells": dict(self.cells),
            "order": self.order,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            uid=d.get("uid") or str(uuid.uuid4())[:8],
            name=d.get("name") or "Untitled",
            layout=d.get("layout") or "2x2",
            cells=dict(d.get("cells") or {}),
            order=int(d.get("order") or 0),
            created_at=d.get("created_at") or "",
        )


class LiveTabsManager:
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.tabs: List[LiveTab] = []
        self.active_tab_uid: str = ""

    def load(self):
        try:
            if not TABS_FILE.exists():
                return
            data = json.loads(TABS_FILE.read_text(encoding="utf-8"))
            self.tabs = [LiveTab.from_dict(d) for d in data.get("tabs", [])]
            self.active_tab_uid = data.get("active_uid") or ""
            self._sort()
            print(f"[LiveTabsManager] loaded {len(self.tabs)} tabs")
        except Exception as e:
            print(f"[LiveTabsManager] load error: {e}")
            self.tabs = []
            self.active_tab_uid = ""

    def save(self):
        try:
            TABS_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "active_uid": self.active_tab_uid,
                "tabs": [t.to_dict() for t in self.tabs],
            }
            TABS_FILE.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8")
        except Exception as e:
            print(f"[LiveTabsManager] save error: {e}")

    def _sort(self):
        self.tabs.sort(key=lambda t: (t.order, t.created_at))

    def all(self) -> List[LiveTab]:
        return list(self.tabs)

    def get(self, uid: str) -> Optional[LiveTab]:
        for t in self.tabs:
            if t.uid == uid:
                return t
        return None

    def get_active(self) -> Optional[LiveTab]:
        return self.get(self.active_tab_uid)

    def create_tab(self, name: str = None, layout: str = "2x2") -> LiveTab:
        if name is None:
            name = f"تب {len(self.tabs) + 1}"
        tab = LiveTab(
            uid=str(uuid.uuid4())[:8],
            name=name,
            layout=layout,
            cells={},
            order=len(self.tabs),
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        self.tabs.append(tab)
        self.save()
        return tab

    def rename_tab(self, uid: str, new_name: str) -> bool:
        t = self.get(uid)
        if not t:
            return False
        t.name = (new_name or "").strip() or t.name
        self.save()
        return True

    def delete_tab(self, uid: str) -> bool:
        before = len(self.tabs)
        self.tabs = [t for t in self.tabs if t.uid != uid]
        if len(self.tabs) == before:
            return False
        for i, t in enumerate(self.tabs):
            t.order = i
        if self.active_tab_uid == uid:
            self.active_tab_uid = self.tabs[0].uid if self.tabs else ""
        self.save()
        return True

    def duplicate_tab(self, uid: str) -> Optional[LiveTab]:
        src = self.get(uid)
        if not src:
            return None
        new_tab = LiveTab(
            uid=str(uuid.uuid4())[:8],
            name=f"{src.name} (کپی)",
            layout=src.layout,
            cells=dict(src.cells),
            order=len(self.tabs),
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        self.tabs.append(new_tab)
        self.save()
        return new_tab

    def set_active(self, uid: str):
        if self.get(uid):
            self.active_tab_uid = uid
            self.save()

    def update_cells(self, uid: str, layout: str, cells: Dict[int, str]):
        t = self.get(uid)
        if not t:
            return
        t.layout = layout
        t.cells = {str(k): v for k, v in cells.items() if v}
        self.save()