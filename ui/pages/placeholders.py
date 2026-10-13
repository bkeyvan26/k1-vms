# -*- coding: utf-8 -*-
"""K1 VMS — Placeholder pages (i18n)"""
from ui.pages import PlaceholderPage
from core.i18n import t


class AlarmsPage(PlaceholderPage):
    def __init__(self, parent=None):
        super().__init__(
            key="alarms",
            title=t("rail.alarms").split("(")[0].strip(),
            icon_name="bell",
            subtitle="مدیریت هشدارها — فاز ۵",
            parent=parent
        )


class AIPage(PlaceholderPage):
    def __init__(self, parent=None):
        super().__init__(
            key="ai",
            title=t("rail.ai").split("(")[0].strip(),
            icon_name="cpu",
            subtitle="تحلیل هوشمند ویدیو — فاز ۶",
            parent=parent
        )


class SearchPage(PlaceholderPage):
    def __init__(self, parent=None):
        super().__init__(
            key="search",
            title=t("rail.search").split("(")[0].strip(),
            icon_name="search",
            subtitle="جستجو در دوربین‌ها و رویدادها",
            parent=parent
        )


class MapPage(PlaceholderPage):
    def __init__(self, parent=None):
        super().__init__(
            key="map",
            title=t("rail.map").split("(")[0].strip(),
            icon_name="map",
            subtitle="نمای نقشه دوربین‌ها",
            parent=parent
        )


class ReportsPage(PlaceholderPage):
    def __init__(self, parent=None):
        super().__init__(
            key="reports",
            title=t("rail.reports").split("(")[0].strip(),
            icon_name="bar-chart",
            subtitle="گزارش‌ها و آمار سیستم",
            parent=parent
        )


class UsersPage(PlaceholderPage):
    def __init__(self, parent=None):
        super().__init__(
            key="users",
            title=t("rail.users"),
            icon_name="users",
            subtitle="مدیریت کاربران و دسترسی‌ها — فاز ۷",
            parent=parent
        )