# -*- coding: utf-8 -*-
"""
自定义UI组件
"""
from .draggable_label import DraggableLabel
from .project_tree import ProjectTreeWidget
from .data_tables import DataTableWidget, ResultTableWidget, ProjectDetailTableWidget
from .canvas_widget import CanvasWidget
from .series_tree import SeriesTreeWidget

__all__ = [
    'DraggableLabel',
    'ProjectTreeWidget',
    'DataTableWidget',
    'ResultTableWidget',
    'ProjectDetailTableWidget',
    'CanvasWidget',
    'SeriesTreeWidget'
]

