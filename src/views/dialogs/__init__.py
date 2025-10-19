# -*- coding: utf-8 -*-
"""
对话框组件
"""
from .settings_dialog import SettingsDialog
from .about_dialog import AboutDialog
from .link_data_dialog import LinkDataDialog, select_data
from .fitting_method_dialog import FittingMethodDialog, select_fitting_method

__all__ = [
    'SettingsDialog',
    'AboutDialog',
    'LinkDataDialog',
    'select_data',
    'FittingMethodDialog',
    'select_fitting_method'
]

