# -*- coding: utf-8 -*-
"""
具体的Command实现

提供导入、拟合、删除等可撤销操作
"""
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd

from .commands import ICommand
from .provenance import OperationLog


class ImportDataCommand(ICommand):
    """导入数据文件的可撤销命令"""
    
    def __init__(self, file_path: str, data_manager, project_manager):
        """
        Args:
            file_path: 文件路径
            data_manager: DataManager实例
            project_manager: ProjectManager实例
        """
        super().__init__()
        self.file_path = file_path
        self.data_manager = data_manager
        self.project_manager = project_manager
        
        # 执行后保存的状态
        self.created_data_ids: List[int] = []
        self.op_id = str(uuid.uuid4())
    
    def execute(self) -> bool:
        """执行导入"""
        try:
            # 调用现有导入逻辑（来自Controller）
            self.created_data_ids = self._import_file(self.file_path)
            return len(self.created_data_ids) > 0
        except Exception as e:
            self.error = str(e)
            return False
    
    def _import_file(self, file_path: str) -> List[int]:
        """导入文件（复用Controller逻辑）"""
        from src.utils.json_reader import read_json
        import pandas as pd
        
        created_ids = []
        
        if file_path.endswith('.json'):
            # JSON导入
            json_data = read_json(file_path)
            if json_data and 'data' in json_data:
                for key, value in json_data['data'].items():
                    df = pd.DataFrame(value)
                    data_id = self.data_manager.add_data(f"JSON_{key}", df)
                    created_ids.append(data_id)
                    
                    # 添加到当前项目
                    project = self.project_manager.get_current_project()
                    if project:
                        project.add_data(data_id)
        
        elif file_path.endswith(('.xlsx', '.xls')):
            # Excel导入
            try:
                df = pd.read_excel(file_path)
                
                # 检查是否是宽表格式
                if len(df.columns) > 2 and 'Time' in df.columns:
                    # 宽表：创建父节点
                    display_name = os.path.splitext(os.path.basename(file_path))[0]
                    
                    # 在attrs中保存子节点信息
                    df.attrs['wide_parent_children_cols'] = [c for c in df.columns if c != 'Time']
                    df.attrs['wide_parent_base_name'] = display_name
                    
                    parent_id = self.data_manager.add_data(f"{display_name} (宽表)", df)
                    created_ids.append(parent_id)
                    
                    # 添加到项目
                    project = self.project_manager.get_current_project()
                    if project:
                        project.add_data(parent_id)
                else:
                    # 普通表：直接添加
                    display_name = os.path.splitext(os.path.basename(file_path))[0]
                    data_id = self.data_manager.add_data(display_name, df)
                    created_ids.append(data_id)
                    
                    project = self.project_manager.get_current_project()
                    if project:
                        project.add_data(data_id)
            
            except Exception as e:
                raise Exception(f"Excel导入失败: {e}")
        
        else:
            raise ValueError(f"不支持的文件格式: {file_path}")
        
        return created_ids
    
    def undo(self) -> bool:
        """撤销导入：删除所有创建的数据"""
        try:
            project = self.project_manager.get_current_project()
            
            for data_id in self.created_data_ids:
                # 从项目移除
                if project and data_id in project.data_ids:
                    project.data_ids.remove(data_id)
                
                # 删除数据
                self.data_manager.remove_data(data_id)
            
            return True
        except Exception as e:
            self.error = f"撤销导入失败: {e}"
            return False
    
    def get_description(self) -> str:
        """返回操作描述"""
        filename = os.path.basename(self.file_path)
        count = len(self.created_data_ids)
        return f"导入文件: {filename} ({count}个数据)"
    
    def to_operation_log(self) -> OperationLog:
        """转换为操作日志"""
        return OperationLog(
            op_id=self.op_id,
            op_type='import',
            timestamp=datetime.now().isoformat(),
            inputs={'file_path': self.file_path},
            outputs={'data_ids': self.created_data_ids},
            description=self.get_description(),
            status='success'
        )


class FitDataCommand(ICommand):
    """拟合数据的可撤销命令"""
    
    def __init__(self, data_id: int, method: str, 
                 data_manager, result_manager, figure_manager, 
                 link_manager, project_manager):
        """
        Args:
            data_id: 数据ID
            method: 拟合方法
            data_manager: DataManager实例
            result_manager: ResultManager实例
            figure_manager: FigureManager实例
            link_manager: LinkManager实例
            project_manager: ProjectManager实例
        """
        super().__init__()
        self.data_id = data_id
        self.method = method
        self.data_manager = data_manager
        self.result_manager = result_manager
        self.figure_manager = figure_manager
        self.link_manager = link_manager
        self.project_manager = project_manager
        
        # 保存数据名称（用于重做时查找）
        data = data_manager.get_data(data_id)
        self.data_name = data.name if data else f"Data#{data_id}"
        
        # 执行后保存的状态
        self.result_id: Optional[int] = None
        self.fitted_data_id: Optional[int] = None
        self.figure_id: Optional[int] = None
        self.created_links: List[Tuple[str, int, str, int]] = []
        self.op_id = str(uuid.uuid4())
    
    def execute(self) -> bool:
        """执行拟合"""
        try:
            from src.utils.fitting_wrapper import fit_data
            
            # 1. 获取数据并拟合
            data = self.data_manager.get_data(self.data_id)
            
            # 如果原data_id不存在（可能是重做时ID已变），尝试通过名称查找
            if not data:
                for data_id, d in self.data_manager._data_dict.items():
                    if d.name == self.data_name:
                        data = d
                        self.data_id = data_id  # 更新为新的ID
                        break
            
            if not data:
                self.error = f"数据不存在: data_name={self.data_name}, data_id={self.data_id}"
                return False
            
            # 验证数据
            validation = data.validate_xy_extraction()
            if 'error' in validation:
                self.error = validation['error']
                return False
            
            if validation.get('valid_both', 0) < 3:
                self.error = "有效数据点不足"
                return False
            
            # 获取XY数据
            x_data, y_data = data.get_xy_data(auto_sort=False)
            
            # 执行拟合
            fit_result = fit_data(self.method, x_data, y_data, 
                                 dataframe=data.dataframe, data_obj=data)
            
            if not fit_result.get('success'):
                self.error = fit_result.get('error', '拟合失败')
                return False
            
            # 2. 创建结果对象
            self.result_id = self.result_manager.add_result(
                f"{data.name} - {self.method}",
                self.method
            )
            result = self.result_manager.get_result(self.result_id)
            
            # 设置参数
            params_with_meta = dict(fit_result.get('parameters', {}))
            params_with_meta = {
                'DataSource': (data.name, None, ''),
                'Method': (self.method, None, ''),
                **params_with_meta
            }
            result.set_parameters(params_with_meta)
            
            # 设置统计信息
            stats = fit_result.get('statistics', {}) or {}
            result.set_statistics(rmse=stats.get('rmse'))
            result.set_data_source(self.data_id)
            
            # 创建链接：data → result
            self.link_manager.create_link(
                'data', self.data_id,
                'result', self.result_id,
                link_type='fitting_output',
                metadata={
                    'method': self.method,
                    'fit_time': datetime.now().isoformat(),
                    'parameters': fit_result.get('parameters', {}),
                    'rmse': stats.get('rmse')
                }
            )
            self.created_links.append(('data', self.data_id, 'result', self.result_id))
            
            # 3. 创建拟合曲线数据
            if fit_result.get('y_pred') is not None:
                y_pred = fit_result['y_pred']
                y_pred_matrix = fit_result.get('y_pred_matrix')
                time_vector = fit_result.get('time_vector')
                headers = fit_result.get('headers')
                
                # 判断是否是矩阵形式
                if (y_pred_matrix is not None and 
                    getattr(y_pred_matrix, 'ndim', 1) == 2 and 
                    time_vector is not None and 
                    headers is not None):
                    # 宽表格式
                    fitted_df = pd.DataFrame({'Time': time_vector})
                    for i, col in enumerate(headers):
                        fitted_df[f"Y_pred_{col}"] = y_pred_matrix[:, i]
                else:
                    # 简单两列格式
                    fitted_df = pd.DataFrame({
                        'XValue': x_data,
                        'YValue': y_pred
                    })
                
                # 添加元数据标记
                fitted_df.attrs['source_type'] = 'fitted_curve'
                fitted_df.attrs['result_id'] = self.result_id
                fitted_df.attrs['original_data_id'] = self.data_id
                fitted_df.attrs['method'] = self.method
                
                self.fitted_data_id = self.data_manager.add_data(
                    f"{data.name} - 拟合曲线({self.method})",
                    fitted_df
                )
                
                # 创建链接：result → fitted_data
                self.link_manager.create_link(
                    'result', self.result_id,
                    'data', self.fitted_data_id,
                    link_type='result_data',
                    metadata={
                        'data_type': 'fitted_curve',
                        'method': self.method,
                        'created_time': datetime.now().isoformat()
                    }
                )
                self.created_links.append(('result', self.result_id, 'data', self.fitted_data_id))
            
            # 4. 创建对比图
            if self.fitted_data_id is not None:
                self.figure_id = self.figure_manager.add_figure(
                    f"{data.name} - 拟合对比",
                    "fitting"
                )
                figure = self.figure_manager.get_figure(self.figure_id)
                
                # 添加数据源
                figure.add_data_source(self.data_id, {
                    'label': '实验数据',
                    'color': '#1a73e8',
                    'linewidth': 1.5,
                    'marker': 'o',
                    'markersize': 4.0,
                    'linestyle': 'none'
                })
                
                figure.add_data_source(self.fitted_data_id, {
                    'label': f'拟合曲线({self.method})',
                    'color': '#ea4335',
                    'linewidth': 2.5,
                    'marker': 'none',
                    'linestyle': '-'
                })
                
                figure.set_result_source(self.result_id)
                
                # 创建链接：result → figure
                self.link_manager.create_link(
                    'result', self.result_id,
                    'figure', self.figure_id,
                    link_type='visualization',
                    metadata={
                        'figure_type': 'fitting_comparison',
                        'created_time': datetime.now().isoformat()
                    }
                )
                self.created_links.append(('result', self.result_id, 'figure', self.figure_id))
                
                # 添加到项目
                project = self.project_manager.get_current_project()
                if project:
                    project.add_figure(self.figure_id)
            
            # 5. 将结果添加到项目
            project = self.project_manager.get_current_project()
            if project:
                project.add_result(self.result_id)
            
            return True
            
        except Exception as e:
            import traceback
            self.error = f"拟合失败: {str(e)}\n{traceback.format_exc()}"
            return False
    
    def undo(self) -> bool:
        """撤销拟合：删除所有创建的对象"""
        try:
            project = self.project_manager.get_current_project()
            
            # 1. 删除链接（逆序）
            for src_type, src_id, tgt_type, tgt_id in reversed(self.created_links):
                try:
                    self.link_manager.remove_link(src_type, src_id, tgt_type, tgt_id)
                except Exception:
                    pass  # 链接可能已经不存在
            
            # 2. 删除对象（逆序）
            if self.figure_id is not None:
                if project and self.figure_id in project.figure_ids:
                    project.figure_ids.remove(self.figure_id)
                self.figure_manager.remove_figure(self.figure_id)
            
            if self.fitted_data_id is not None:
                self.data_manager.remove_data(self.fitted_data_id)
            
            if self.result_id is not None:
                if project and self.result_id in project.result_ids:
                    project.result_ids.remove(self.result_id)
                self.result_manager.remove_result(self.result_id)
            
            return True
        except Exception as e:
            self.error = f"撤销拟合失败: {e}"
            return False
    
    def get_description(self) -> str:
        """返回操作描述"""
        data = self.data_manager.get_data(self.data_id)
        name = data.name if data else f"数据#{self.data_id}"
        return f"拟合: {name} ({self.method})"
    
    def to_operation_log(self) -> OperationLog:
        """转换为操作日志"""
        return OperationLog(
            op_id=self.op_id,
            op_type='fit',
            timestamp=datetime.now().isoformat(),
            inputs={'data_id': self.data_id, 'method': self.method},
            outputs={
                'result_id': self.result_id,
                'fitted_data_id': self.fitted_data_id,
                'figure_id': self.figure_id
            },
            description=self.get_description(),
            status='success'
        )


class CreateFigureCommand(ICommand):
    """创建图表的可撤销命令"""
    
    def __init__(self, data_id: int, figure_name: str, figure_type: str,
                 data_manager, figure_manager, link_manager, project_manager):
        """
        Args:
            data_id: 数据ID
            figure_name: 图表名称
            figure_type: 图表类型 ('line', 'scatter', 'fitting')
            data_manager: DataManager实例
            figure_manager: FigureManager实例
            link_manager: LinkManager实例
            project_manager: ProjectManager实例
        """
        super().__init__()
        self.data_id = data_id
        self.figure_name = figure_name
        self.figure_type = figure_type
        self.data_manager = data_manager
        self.figure_manager = figure_manager
        self.link_manager = link_manager
        self.project_manager = project_manager
        
        # 保存数据名称（用于重做时查找）
        data = data_manager.get_data(data_id)
        self.data_name = data.name if data else f"Data#{data_id}"
        
        # 执行后保存的状态
        self.figure_id: Optional[int] = None
        self.op_id = str(uuid.uuid4())
    
    def execute(self) -> bool:
        """执行创建图表"""
        try:
            # 获取数据
            data = self.data_manager.get_data(self.data_id)
            
            # 如果原data_id不存在（可能是重做时ID已变），尝试通过名称查找
            if not data:
                for data_id, d in self.data_manager._data_dict.items():
                    if d.name == self.data_name:
                        data = d
                        self.data_id = data_id  # 更新为新的ID
                        break
            
            if not data:
                self.error = f"数据不存在: data_name={self.data_name}, data_id={self.data_id}"
                return False
            
            # 检查数据是否为空
            if data.dataframe is None or data.dataframe.empty:
                self.error = "数据为空，无法创建图表"
                return False
            
            # 创建图表
            self.figure_id = self.figure_manager.add_figure(
                self.figure_name,
                self.figure_type
            )
            figure = self.figure_manager.get_figure(self.figure_id)
            
            # 添加数据源
            figure.add_data_source(self.data_id, {
                'label': data.name,
                'color': '#1a73e8',
                'linewidth': 2.0,
                'marker': 'o',
                'markersize': 4.0
            })
            
            # 创建链接
            self.link_manager.create_link(
                'data', self.data_id,
                'figure', self.figure_id,
                link_type='visualize',
                metadata={
                    'figure_type': self.figure_type,
                    'created_time': datetime.now().isoformat()
                }
            )
            
            # 添加到项目
            project = self.project_manager.get_current_project()
            if project:
                project.add_figure(self.figure_id)
            
            return True
        except Exception as e:
            import traceback
            self.error = f"创建图表失败: {str(e)}\n{traceback.format_exc()}"
            return False
    
    def undo(self) -> bool:
        """撤销创建图表：删除图表和链接"""
        try:
            if self.figure_id is None:
                return True
            
            # 删除链接
            try:
                self.link_manager.remove_link('data', self.data_id, 'figure', self.figure_id)
            except Exception:
                pass
            
            # 从项目移除
            project = self.project_manager.get_current_project()
            if project and self.figure_id in project.figure_ids:
                project.figure_ids.remove(self.figure_id)
            
            # 删除图表
            self.figure_manager.remove_figure(self.figure_id)
            
            return True
        except Exception as e:
            self.error = f"撤销创建图表失败: {e}"
            return False
    
    def get_description(self) -> str:
        """返回操作描述"""
        data = self.data_manager.get_data(self.data_id)
        data_name = data.name if data else f"数据#{self.data_id}"
        return f"创建图表: {self.figure_name} (数据: {data_name})"
    
    def to_operation_log(self) -> OperationLog:
        """转换为操作日志"""
        return OperationLog(
            op_id=self.op_id,
            op_type='create_figure',
            timestamp=datetime.now().isoformat(),
            inputs={'data_id': self.data_id, 'figure_type': self.figure_type},
            outputs={'figure_id': self.figure_id},
            description=self.get_description(),
            status='success'
        )


class DeleteItemCommand(ICommand):
    """删除数据/图表/结果的可撤销命令"""
    
    def __init__(self, item_type: str, item_id: int, managers: Dict[str, Any]):
        """
        Args:
            item_type: 对象类型 ('data', 'figure', 'result')
            item_id: 对象ID
            managers: 管理器字典 {'data': DataManager, 'figure': FigureManager, ...}
        """
        super().__init__()
        self.item_type = item_type
        self.item_id = item_id
        self.managers = managers
        
        # 保存状态用于恢复
        self.saved_object = None
        self.saved_links: List[Dict[str, Any]] = []
        self.was_in_project = False
        self.op_id = str(uuid.uuid4())
    
    def execute(self) -> bool:
        """执行删除（保存状态）"""
        try:
            # 1. 保存对象
            if self.item_type == 'data':
                self.saved_object = self.managers['data'].get_data(self.item_id)
            elif self.item_type == 'figure':
                self.saved_object = self.managers['figure'].get_figure(self.item_id)
            elif self.item_type == 'result':
                self.saved_object = self.managers['result'].get_result(self.item_id)
            
            if self.saved_object is None:
                self.error = f"{self.item_type}#{self.item_id} 不存在"
                return False
            
            # 2. 检查是否在项目中
            project = self.managers['project'].get_current_project()
            if project:
                if self.item_type == 'data' and self.item_id in project.data_ids:
                    self.was_in_project = True
                elif self.item_type == 'figure' and self.item_id in project.figure_ids:
                    self.was_in_project = True
                elif self.item_type == 'result' and self.item_id in project.result_ids:
                    self.was_in_project = True
            
            # 3. 保存相关链接
            self.saved_links = self._get_all_links(self.item_type, self.item_id)
            
            # 4. 删除链接
            for link in self.saved_links:
                try:
                    self.managers['link'].remove_link(
                        link['source_type'], link['source_id'],
                        link['target_type'], link['target_id'])
                except Exception:
                    pass
            
            # 5. 从项目移除
            if project and self.was_in_project:
                if self.item_type == 'data' and self.item_id in project.data_ids:
                    project.data_ids.remove(self.item_id)
                elif self.item_type == 'figure' and self.item_id in project.figure_ids:
                    project.figure_ids.remove(self.item_id)
                elif self.item_type == 'result' and self.item_id in project.result_ids:
                    project.result_ids.remove(self.item_id)
            
            # 6. 删除对象
            if self.item_type == 'data':
                self.managers['data'].remove_data(self.item_id)
            elif self.item_type == 'figure':
                self.managers['figure'].remove_figure(self.item_id)
            elif self.item_type == 'result':
                self.managers['result'].remove_result(self.item_id)
            
            return True
        except Exception as e:
            import traceback
            self.error = f"删除失败: {str(e)}\n{traceback.format_exc()}"
            return False
    
    def _get_all_links(self, obj_type: str, obj_id: int) -> List[Dict[str, Any]]:
        """获取对象相关的所有链接"""
        all_links = []
        link_mgr = self.managers['link']
        
        # 获取所有链接
        for link in link_mgr.get_all_links():
            if ((link['source_type'] == obj_type and link['source_id'] == obj_id) or
                (link['target_type'] == obj_type and link['target_id'] == obj_id)):
                all_links.append(link.copy())
        
        return all_links
    
    def undo(self) -> bool:
        """撤销删除：恢复对象和链接"""
        try:
            # 1. 恢复对象
            if self.item_type == 'data':
                self.managers['data']._data_dict[self.item_id] = self.saved_object
            elif self.item_type == 'figure':
                self.managers['figure']._figures[self.item_id] = self.saved_object
            elif self.item_type == 'result':
                self.managers['result']._results[self.item_id] = self.saved_object
            
            # 2. 恢复到项目
            if self.was_in_project:
                project = self.managers['project'].get_current_project()
                if project:
                    if self.item_type == 'data' and self.item_id not in project.data_ids:
                        project.data_ids.append(self.item_id)
                    elif self.item_type == 'figure' and self.item_id not in project.figure_ids:
                        project.figure_ids.append(self.item_id)
                    elif self.item_type == 'result' and self.item_id not in project.result_ids:
                        project.result_ids.append(self.item_id)
            
            # 3. 恢复链接
            for link in self.saved_links:
                try:
                    self.managers['link'].create_link(
                        link['source_type'], link['source_id'],
                        link['target_type'], link['target_id'],
                        link_type=link.get('link_type'),
                        metadata=link.get('metadata'))
                except Exception:
                    pass  # 链接可能已经存在
            
            return True
        except Exception as e:
            self.error = f"撤销删除失败: {e}"
            return False
    
    def get_description(self) -> str:
        """返回操作描述"""
        type_names = {
            'data': '数据',
            'figure': '图表',
            'result': '结果'
        }
        type_name = type_names.get(self.item_type, self.item_type)
        obj_name = getattr(self.saved_object, 'name', f'#{self.item_id}')
        return f"删除{type_name}: {obj_name}"
    
    def to_operation_log(self) -> OperationLog:
        """转换为操作日志"""
        return OperationLog(
            op_id=self.op_id,
            op_type='delete',
            timestamp=datetime.now().isoformat(),
            inputs={f'{self.item_type}_id': self.item_id},
            outputs={},
            description=self.get_description(),
            status='success'
        )

