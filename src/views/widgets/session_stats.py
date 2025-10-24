# -*- coding: utf-8 -*-
"""
会话统计面板 - 显示当前会话的关键统计信息

显示内容：
- 会话名称、保存状态、当前文件
- 对象数量：数据/图表/结果/项目/链接
- 近似内存占用（DataFrame总计）

用法：
  widget.set_session_manager(session_manager)  # 内部定时刷新
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
from PySide6.QtCore import QTimer, Qt


class SessionStatsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._session_manager = None
        self._timer = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.title_label = QLabel("📊 会话统计")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setStyleSheet("font-weight: 700; font-size: 14px;")
        layout.addWidget(self.title_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)

        def add_row(r, name):
            label = QLabel(name)
            label.setStyleSheet("color:#555;")
            value = QLabel("-")
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(label, r, 0)
            grid.addWidget(value, r, 1)
            return value

        row = 0
        self.session_name_val = add_row(row, "会话名称") ; row += 1
        self.file_path_val   = add_row(row, "当前文件") ; row += 1
        self.modified_val    = add_row(row, "修改状态") ; row += 1
        self.data_count_val  = add_row(row, "数据对象") ; row += 1
        self.figure_count_val= add_row(row, "图表对象") ; row += 1
        self.result_count_val= add_row(row, "结果对象") ; row += 1
        self.project_count_val=add_row(row, "项目对象") ; row += 1
        self.link_count_val  = add_row(row, "链接数量") ; row += 1
        self.memory_val      = add_row(row, "内存占用") ; row += 1

        layout.addLayout(grid)
        layout.addStretch(1)

        self.setStyleSheet("""
            QLabel { font-size: 12px; }
        """)

    def set_session_manager(self, session_manager):
        self._session_manager = session_manager
        # 启动/重启定时刷新
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._refresh)
        self._timer.start(1500)
        self._refresh()

    def _refresh(self):
        sm = self._session_manager
        if sm is None:
            return
        try:
            info = sm.get_session_info()
            self.session_name_val.setText(str(info.get('name') or '-'))
            self.file_path_val.setText(str(info.get('file_path') or '未保存'))
            self.modified_val.setText('已修改 *' if info.get('is_modified') else '未修改')
            self.data_count_val.setText(str(info.get('data_count', 0)))
            self.figure_count_val.setText(str(info.get('figure_count', 0)))
            self.result_count_val.setText(str(info.get('result_count', 0)))
            self.project_count_val.setText(str(info.get('project_count', 0)))
            self.link_count_val.setText(str(info.get('link_count', 0)))

            # 估算DataFrame内存占用
            total_bytes = 0
            try:
                data_dict = getattr(sm.data_manager, '_data_dict', {})
                for _id, data_obj in data_dict.items():
                    df = getattr(data_obj, 'dataframe', None)
                    if df is not None:
                        try:
                            total_bytes += int(df.memory_usage(deep=True).sum())
                        except Exception:
                            pass
            except Exception:
                pass
            mb = total_bytes / (1024 * 1024) if total_bytes else 0
            self.memory_val.setText(f"{mb:.1f} MB")
        except Exception:
            pass


