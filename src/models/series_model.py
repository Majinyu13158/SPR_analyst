# -*- coding: utf-8 -*-
"""
系列模型（Series）与管理器（SeriesManager）

用途：对标 Prism 的“系列”概念，用于把多个数据(data_id)组织为一组，以便联动绘制/比较。
"""
from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal


class Series(QObject):
    """单个系列对象"""
    series_updated = Signal()

    def __init__(self, series_id: int, name: str, parent=None):
        super().__init__(parent)
        self.id = series_id
        self.name = name
        self.data_ids: List[int] = []

    def add_data(self, data_id: int) -> bool:
        if data_id not in self.data_ids:
            self.data_ids.append(data_id)
            self.series_updated.emit()
            return True
        return False

    def remove_data(self, data_id: int) -> bool:
        if data_id in self.data_ids:
            self.data_ids.remove(data_id)
            self.series_updated.emit()
            return True
        return False


class SeriesManager(QObject):
    """系列管理器"""

    series_added = Signal(int)      # series_id
    series_removed = Signal(int)    # series_id
    series_updated = Signal(int)    # series_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._series_map: Dict[int, Series] = {}
        self._next_id = 1

    def add_series(self, name: str) -> int:
        sid = self._next_id
        s = Series(sid, name, parent=self)
        s.series_updated.connect(lambda: self.series_updated.emit(sid))
        self._series_map[sid] = s
        self._next_id += 1
        self.series_added.emit(sid)
        return sid

    def remove_series(self, series_id: int) -> bool:
        if series_id in self._series_map:
            del self._series_map[series_id]
            self.series_removed.emit(series_id)
            return True
        return False

    def rename_series(self, series_id: int, new_name: str) -> bool:
        s = self._series_map.get(series_id)
        if not s:
            return False
        s.name = new_name
        self.series_updated.emit(series_id)
        return True

    def get_series(self, series_id: int) -> Optional[Series]:
        return self._series_map.get(series_id)

    def get_all_series(self) -> List[Series]:
        return list(self._series_map.values())


