# -*- coding: utf-8 -*-
"""
主控制器 - MVP简化版
"""
from PySide6.QtCore import QObject, Slot
from typing import Optional
import traceback

from ..models import DataManager
from ..views import MainWindow
from ..utils.json_reader import json_reader


class MainController(QObject):
    """
    主控制器 - MVP简化版
    
    职责:
        1. 连接View的信号到Model的方法
        2. 监听Model的变化更新View
        3. 处理业务逻辑
    """
    
    def __init__(self, view: MainWindow, parent=None):
        super().__init__(parent)
        
        # View和Model实例
        self.view = view
        self.data_manager = DataManager(self)
        
        # 连接信号槽
        self._connect_signals()
        
        print("✅ Controller初始化完成")
    
    def _connect_signals(self):
        """连接信号槽"""
        # View信号 -> Controller槽
        self.view.file_selected.connect(self.on_file_selected)
        
        # Model信号 -> Controller槽
        self.data_manager.data_added.connect(self.on_data_added)
        self.data_manager.data_removed.connect(self.on_data_removed)
        
        print("✅ 信号槽连接完成")
    
    # ========== View信号的槽函数 ==========
    
    @Slot(str)
    def on_file_selected(self, file_path: str):
        """
        处理文件选择
        
        流程:
            1. 读取文件
            2. 添加到DataManager
            3. 显示数据详情
        """
        print(f"📁 文件选择: {file_path}")
        
        try:
            # 1. 判断文件类型
            if file_path.endswith('.json'):
                # 读取JSON文件
                data = json_reader(file_path)
                print(f"✅ JSON文件读取成功，包含 {len(data)} 个字段")
                
                # 2. 添加到DataManager
                data_id = self.data_manager.add_data(data, 'file')
                print(f"✅ 数据已添加，ID: {data_id}")
                
                # 3. 显示数据详情
                data_obj = self.data_manager.get_data(data_id)
                if data_obj:
                    detail = self._format_data_detail(data_obj, data)
                    self.view.show_data_detail(detail)
                
                self.view.show_message("成功", f"文件加载成功！\n数据ID: {data_id}")
                
            elif file_path.endswith('.xlsx'):
                # Excel文件处理（简化版）
                self.view.show_message("提示", "Excel文件支持将在后续版本中实现")
            
            else:
                self.view.show_error("错误", "不支持的文件类型\n\n仅支持 .json 和 .xlsx 文件")
        
        except Exception as e:
            error_msg = f"文件处理失败:\n\n{str(e)}\n\n详细信息:\n{traceback.format_exc()}"
            print(f"❌ 错误: {error_msg}")
            self.view.show_error("错误", error_msg)
    
    # ========== Model信号的槽函数 ==========
    
    @Slot(int, str)
    def on_data_added(self, data_id: int, data_name: str):
        """数据添加后更新View"""
        print(f"📊 数据添加通知: ID={data_id}, Name={data_name}")
        self.view.add_data_to_list(data_id, data_name)
    
    @Slot(int)
    def on_data_removed(self, data_id: int):
        """数据删除后更新View"""
        print(f"🗑️ 数据删除通知: ID={data_id}")
        # TODO: 从View的列表中移除
    
    # ========== 辅助方法 ==========
    
    def _format_data_detail(self, data_obj, raw_data: dict) -> str:
        """格式化数据详情用于显示"""
        detail_lines = [
            "=" * 60,
            f"数据名称: {data_obj.get_name()}",
            f"数据ID: {id(data_obj)}",
            f"数据类型: {data_obj.itemtype}",
            "=" * 60,
            "",
            "📋 主要字段:",
            ""
        ]
        
        # 显示前20个字段
        for i, (key, value) in enumerate(list(raw_data.items())[:20]):
            detail_lines.append(f"  {key}: {value}")
            if i >= 19:
                detail_lines.append(f"\n  ... 还有 {len(raw_data) - 20} 个字段")
                break
        
        detail_lines.extend([
            "",
            "=" * 60,
            f"总字段数: {len(raw_data)}",
            "=" * 60
        ])
        
        return "\n".join(detail_lines)

