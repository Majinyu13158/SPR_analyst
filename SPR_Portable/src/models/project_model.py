# -*- coding: utf-8 -*-
"""
项目模型 - 从旧版本迁移

原始文件: spr_app_model_main.py - Project类
"""
from PySide6.QtCore import QObject, Signal
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProjectDetails:
    """
    项目详情类
    
    存储项目元信息
    """
    
    def __init__(self):
        self.experiment_id: str = ""
        self.experiment_time: str = ""
        self.project_name: str = ""
        self.operator: str = ""
        self.location: str = ""
        self.instrument: str = ""
        self.method: str = ""
        self.sample: str = ""
        self.purpose: str = ""
        
        # 其他字段
        self.notes: str = ""
        self.tags: List[str] = []
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'ExperimentID': self.experiment_id,
            'ExperimentTime': self.experiment_time,
            'Project': self.project_name,
            'Operator': self.operator,
            'Location': self.location,
            'Instrument': self.instrument,
            'Method': self.method,
            'Sample': self.sample,
            'Purpose': self.purpose,
            'Notes': self.notes,
            'Tags': self.tags
        }
    
    def from_dict(self, data: dict):
        """从字典加载"""
        self.experiment_id = data.get('ExperimentID', '')
        self.experiment_time = data.get('ExperimentTime', '')
        self.project_name = data.get('Project', '')
        self.operator = data.get('Operator', '')
        self.location = data.get('Location', '')
        self.instrument = data.get('Instrument', '')
        self.method = data.get('Method', '')
        self.sample = data.get('Sample', '')
        self.purpose = data.get('Purpose', '')
        self.notes = data.get('Notes', '')
        self.tags = data.get('Tags', [])


class Project(QObject):
    """
    项目类
    
    管理一个完整的SPR实验项目
    
    信号：
        project_updated: 项目更新
        data_added: 添加数据 (data_id)
        figure_added: 添加图表 (figure_id)
        result_added: 添加结果 (result_id)
    """
    
    project_updated = Signal()
    data_added = Signal(int)
    figure_added = Signal(int)
    result_added = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 基本信息
        self.id: int = 0
        self.name: str = "未命名项目"
        self.created_time: datetime = datetime.now()
        self.modified_time: datetime = datetime.now()
        
        # 项目详情
        self.details = ProjectDetails()
        
        # 关联的数据/图表/结果ID列表
        self.data_ids: List[int] = []
        self.figure_ids: List[int] = []
        self.result_ids: List[int] = []
        
        # 项目状态
        self.is_active: bool = True
    
    def add_data(self, data_id: int):
        """添加数据"""
        if data_id not in self.data_ids:
            self.data_ids.append(data_id)
            self.modified_time = datetime.now()
            self.data_added.emit(data_id)
            self.project_updated.emit()
    
    def add_figure(self, figure_id: int):
        """添加图表"""
        if figure_id not in self.figure_ids:
            self.figure_ids.append(figure_id)
            self.modified_time = datetime.now()
            self.figure_added.emit(figure_id)
            self.project_updated.emit()
    
    def add_result(self, result_id: int):
        """添加结果"""
        if result_id not in self.result_ids:
            self.result_ids.append(result_id)
            self.modified_time = datetime.now()
            self.result_added.emit(result_id)
            self.project_updated.emit()
    
    def remove_data(self, data_id: int):
        """移除数据"""
        if data_id in self.data_ids:
            self.data_ids.remove(data_id)
            self.modified_time = datetime.now()
            self.project_updated.emit()
    
    def remove_figure(self, figure_id: int):
        """移除图表"""
        if figure_id in self.figure_ids:
            self.figure_ids.remove(figure_id)
            self.modified_time = datetime.now()
            self.project_updated.emit()
    
    def remove_result(self, result_id: int):
        """移除结果"""
        if result_id in self.result_ids:
            self.result_ids.remove(result_id)
            self.modified_time = datetime.now()
            self.project_updated.emit()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'created_time': self.created_time.isoformat(),
            'modified_time': self.modified_time.isoformat(),
            'details': self.details.to_dict(),
            'data_ids': self.data_ids,
            'figure_ids': self.figure_ids,
            'result_ids': self.result_ids,
            'is_active': self.is_active
        }


class ProjectManager(QObject):
    """
    项目管理器
    
    管理所有项目
    
    信号：
        project_added: 项目添加 (project_id)
        project_removed: 项目删除 (project_id)
        project_updated: 项目更新 (project_id)
        current_project_changed: 当前项目变更 (project_id)
    """
    
    project_added = Signal(int)
    project_removed = Signal(int)
    project_updated = Signal(int)
    current_project_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._projects = {}  # {id: Project}
        self._next_id = 1
        self._current_project_id: Optional[int] = None
    
    def create_project(self, name: str = "新项目") -> int:
        """
        创建项目
        
        返回:
            project_id
        """
        project = Project(self)
        project.id = self._next_id
        project.name = name
        project.created_time = datetime.now()
        project.modified_time = datetime.now()
        
        self._projects[self._next_id] = project
        
        # 连接信号
        project.project_updated.connect(
            lambda: self.project_updated.emit(project.id)
        )
        
        self.project_added.emit(self._next_id)
        
        # 如果是第一个项目，设为当前项目
        if self._current_project_id is None:
            self.set_current_project(self._next_id)
        
        self._next_id += 1
        return project.id
    
    def get_project(self, project_id: int) -> Optional[Project]:
        """获取项目"""
        return self._projects.get(project_id)
    
    def get_current_project(self) -> Optional[Project]:
        """获取当前项目"""
        if self._current_project_id is not None:
            return self._projects.get(self._current_project_id)
        return None
    
    def set_current_project(self, project_id: int):
        """设置当前项目"""
        if project_id in self._projects:
            self._current_project_id = project_id
            self.current_project_changed.emit(project_id)
    
    def remove_project(self, project_id: int):
        """删除项目"""
        if project_id in self._projects:
            del self._projects[project_id]
            self.project_removed.emit(project_id)
            
            # 如果删除的是当前项目，清空当前项目
            if self._current_project_id == project_id:
                self._current_project_id = None
    
    def get_all_projects(self) -> List[Project]:
        """获取所有项目"""
        return list(self._projects.values())
    
    def clear(self):
        """清空所有项目"""
        self._projects.clear()
        self._next_id = 1
        self._current_project_id = None

