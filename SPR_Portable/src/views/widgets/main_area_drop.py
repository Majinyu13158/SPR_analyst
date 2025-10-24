# -*- coding: utf-8 -*-
"""
主工作区拖拽文件过滤器

用途：为中间主区域（含Tab）提供拖入文件导入能力。
行为：
- 仅接受本地文件（urls）
- 支持常见数据后缀：.json/.csv/.xlsx/.xls
- 放下后调用父View的 file_selected 信号
"""
from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent


class MainAreaDropFilter(QObject):
    def __init__(self, view, parent=None):
        super().__init__(parent)
        self.view = view  # 期望有 file_selected 信号 和 update_status 方法

    def eventFilter(self, obj, event):
        et = event.type()
        if et == QEvent.DragEnter or et == QEvent.DragMove:
            mime = event.mimeData()
            if mime and mime.hasUrls():
                # 检查是否包含支持的文件后缀
                for url in mime.urls():
                    if url.isLocalFile():
                        path = url.toLocalFile()
                        if self._is_supported(path):
                            event.acceptProposedAction()
                            return True
            return False

        if et == QEvent.Drop:
            mime = event.mimeData()
            if mime and mime.hasUrls():
                for url in mime.urls():
                    if url.isLocalFile():
                        path = url.toLocalFile()
                        if self._is_supported(path):
                            try:
                                # 交给View统一处理
                                if hasattr(self.view, 'file_selected'):
                                    self.view.file_selected.emit(path)
                                if hasattr(self.view, 'update_status'):
                                    self.view.update_status(f"已拖入文件: {path}")
                                # 首次使用后移除覆盖提示层
                                overlay = getattr(self.view, 'data_overlay', None)
                                if overlay is not None:
                                    try:
                                        overlay.hide()
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            event.acceptProposedAction()
                            return True
            return False

        return False

    def _is_supported(self, path: str) -> bool:
        p = path.lower()
        return any(p.endswith(ext) for ext in ['.json', '.csv', '.xlsx', '.xls'])


