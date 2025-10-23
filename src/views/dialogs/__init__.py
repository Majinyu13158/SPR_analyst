# -*- coding: utf-8 -*-
"""
对话框组件
"""
from .settings_dialog import SettingsDialog
from .about_dialog import AboutDialog
from .link_data_dialog import LinkDataDialog, select_data
from .fitting_method_dialog import FittingMethodDialog, select_fitting_method
from .export_dialog import ExportDialog
from .export_figure_dialog import ExportFigureDialog
from .batch_fitting_dialog import BatchFittingDialog
from .lineage_dialog import LineageDialog
from .comparison_dialog import ComparisonDialog
from .style_editor_dialog import StyleEditorDialog, PlotStyle

__all__ = [
    'SettingsDialog',
    'AboutDialog',
    'LinkDataDialog',
    'select_data',
    'FittingMethodDialog',
    'select_fitting_method',
    'ExportDialog',
    'ExportFigureDialog',
    'BatchFittingDialog',
    'LineageDialog',
    'ComparisonDialog',
    'StyleEditorDialog',
    'PlotStyle'
]

