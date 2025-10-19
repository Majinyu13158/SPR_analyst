# -*- coding: utf-8 -*-
"""
主控制器 - 完整功能版

从旧版本迁移：spr_controller_main.py
协调MainWindowFull、所有Model和业务逻辑
"""
from PySide6.QtCore import QObject, Slot
from typing import Optional
from datetime import datetime
import pandas as pd
from src.views import MainWindowFull
from src.models import SessionManager
from src.utils import load_file, fit_data


class MainControllerFull(QObject):
    """
    主控制器 - 完整功能版
    
    职责：
        1. 连接View和Model
        2. 处理用户操作
        3. 协调业务逻辑
        4. 更新UI显示
    """
    
    def __init__(self, view: MainWindowFull, parent=None):
        super().__init__(parent)
        
        # View
        self.view = view
        
        # ✨ 使用 SessionManager 统一管理所有数据和链接
        self.session_manager = SessionManager(self)
        
        # 快捷访问各个Manager
        self.data_manager = self.session_manager.data_manager
        self.figure_manager = self.session_manager.figure_manager
        self.result_manager = self.session_manager.result_manager
        self.project_manager = self.session_manager.project_manager
        self.link_manager = self.session_manager.link_manager
        
        # 当前选中的ID
        self.current_data_id: Optional[int] = None
        self.current_figure_id: Optional[int] = None
        self.current_result_id: Optional[int] = None
        
        # 连接信号
        self._connect_signals()
        
        # 初始化
        self._initialize()
    
    def _connect_signals(self):
        """连接信号槽"""
        # View -> Controller
        self.view.file_selected.connect(self.on_file_selected)
        self.view.data_item_selected.connect(self.on_data_selected)
        self.view.figure_item_selected.connect(self.on_figure_selected)
        self.view.result_item_selected.connect(self.on_result_selected)
        self.view.fitting_requested.connect(self.on_fitting_requested)
        
        # 树形控件 -> Controller
        self.view.project_tree.new_item_created.connect(self.on_new_item_created)
        self.view.project_tree.create_figure_from_data.connect(self.on_create_figure_from_data)
        self.view.project_tree.fit_data_requested.connect(self.on_fit_data_requested)
        self.view.project_tree.change_figure_source.connect(self.on_change_figure_source)
        self.view.project_tree.view_linked_data.connect(self.on_view_linked_data)
        self.view.project_tree.export_item.connect(self.on_export_item)
        
        # Model -> Controller
        self.data_manager.data_added.connect(self.on_data_added)
        self.figure_manager.figure_added.connect(self.on_figure_added)
        self.result_manager.result_added.connect(self.on_result_added)
        
        # ✨ LinkManager -> Controller（新增）
        self.link_manager.link_created.connect(self.on_link_created)
        self.link_manager.link_removed.connect(self.on_link_removed)
        
        # ✨ SessionManager -> Controller（新增）
        self.session_manager.session_modified.connect(self.on_session_modified)
        self.session_manager.session_saved.connect(self.on_session_saved)
        self.session_manager.session_loaded.connect(self.on_session_loaded)
        
        # ✨ 工具菜单 -> Controller（Phase 2+）
        self.view.stats_action.triggered.connect(self.on_view_stats)
        self.view.links_action.triggered.connect(self.on_view_links)
        self.view.clear_action.triggered.connect(self.on_clear_all)
        self.view.export_graph_action.triggered.connect(self.on_export_graph)
        self.view.test_guide_action.triggered.connect(self.on_show_test_guide)
        # 分析菜单/工具栏的“开始拟合”接入当前数据（默认LocalBivariate）
        if hasattr(self.view, 'fit_action'):
            self.view.fit_action.triggered.connect(self._on_fit_from_menu)
        if hasattr(self.view, 'toolbar_fit_action'):
            self.view.toolbar_fit_action.triggered.connect(self._on_fit_from_menu)
    
    def _initialize(self):
        """初始化"""
        # 创建默认项目
        project_id = self.project_manager.create_project("默认项目")
        self.view.update_status("系统就绪")
    
    # ========== 槽函数 ==========
    
    @Slot(str)
    def on_file_selected(self, file_path: str):
        """
        处理文件选择（完全参考原项目spr_controller_main.py）
        
        原项目流程（spr_controller_main.py第186-191行）：
        1. data = json_reader.json_reader(file_path)
        2. self.model.add_new_data(data, 'file')
        3. self.view.items_data[data_count].data_in_from_json(data)
        """
        self.view.update_status(f"正在加载: {file_path}")
        
        import os
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # 判断文件类型
        if file_ext == '.json':
            # JSON文件：使用原项目的方式
            print(f"[Controller] 检测到JSON文件，使用原项目方式加载")
            
            # 1. 使用json_reader读取原始字典（参考原项目）
            from src.utils.json_reader import read_json
            json_data = read_json(file_path)
            
            if not json_data:
                self.view.show_error("加载失败", "无法读取JSON文件")
                self.view.update_status("加载失败")
                return
            
            # 2. 提取元信息
            display_name = file_name
            sample_name = None
            concentration = None
            concentration_unit = None
            
            if 'CalculateDataList' in json_data and json_data['CalculateDataList']:
                first_sample = json_data['CalculateDataList'][0]
                sample_name = first_sample.get('SampleName')
                concentration = first_sample.get('Concentration')
                concentration_unit = first_sample.get('ConcentrationUnit', 'M')
                
                if sample_name:
                    display_name = sample_name
                    print(f"[Controller] 使用SampleName: {sample_name}")
            
            # 3. 转换为DataFrame（用于后续处理，如拟合）
            success, df, error = load_file(file_path)
            if not success:
                self.view.show_error("DataFrame转换失败", error)
                self.view.update_status("加载失败")
                return
            
            # 4. ⭐ 需求1：为每个样本创建独立的Data对象（带分组）
            data_ids = []
            group_item = None  # 用于存储组节点
            
            if 'CalculateDataList' in json_data and len(json_data['CalculateDataList']) > 0:
                calc_list = json_data['CalculateDataList']
                
                if len(calc_list) == 1:
                    # 单样本：直接使用完整DataFrame，不创建分组
                    data_id = self.data_manager.add_data(display_name, df)
                    data_ids.append(data_id)
                    
                    # 创建链接
                    self.link_manager.create_link(
                        'file', file_path,
                        'data', data_id,
                        link_type='import',
                        metadata={
                            'file_name': file_name,
                            'import_time': datetime.now().isoformat(),
                            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else None
                        }
                    )
                    
                    print(f"[Controller] 单样本模式：创建1个Data对象")
                else:
                    # ⭐ 多样本：创建分组结构
                    print(f"[Controller] ⭐ 多样本模式：发现{len(calc_list)}个样本")
                    
                    # 创建组节点（文件名作为组名）
                    group_name = os.path.splitext(file_name)[0]  # 去掉扩展名
                    group_item = self.view.project_tree.add_data_group(f"{group_name} ({len(calc_list)}个样本)")
                    print(f"[Controller] 创建数据组: {group_name}")
                    
                    # 为每个样本创建子节点
                    for i, sample in enumerate(calc_list):
                        sample_name = sample.get('SampleName', f'样本{i+1}')
                        sample_conc = sample.get('Concentration', 0.0)
                        sample_unit = sample.get('ConcentrationUnit', 'M')
                        
                        # 提取该样本的数据
                        sample_data = []
                        if 'BaseData' in sample:
                            sample_data.extend(sample['BaseData'])
                        if 'CombineData' in sample:
                            sample_data.extend(sample['CombineData'])
                        if 'DissociationData' in sample:
                            sample_data.extend(sample['DissociationData'])
                        
                        if sample_data:
                            # 转换为DataFrame
                            sample_df = pd.DataFrame(sample_data)
                            sample_df.attrs['sample_name'] = sample_name
                            sample_df.attrs['concentration'] = sample_conc
                            sample_df.attrs['concentration_unit'] = sample_unit
                            sample_df.attrs['sample_index'] = i
                            sample_df.attrs['group_name'] = group_name  # 保存组名
                            
                            # 添加到数据管理器
                            sample_data_id = self.data_manager.add_data(sample_name, sample_df)
                            data_ids.append(sample_data_id)
                            
                            # ⭐ 添加为组的子节点
                            self.view.project_tree.add_data_item(sample_data_id, sample_name, parent_item=group_item)
                            
                            # 创建链接
                            self.link_manager.create_link(
                                'file', file_path,
                                'data', sample_data_id,
                                link_type='import',
                                metadata={
                                    'file_name': file_name,
                                    'group_name': group_name,
                                    'sample_index': i,
                                    'sample_name': sample_name,
                                    'concentration': f"{sample_conc} {sample_unit}",
                                    'import_time': datetime.now().isoformat()
                                }
                            )
                            
                            print(f"[Controller]   - 样本{i+1}: {sample_name} ({len(sample_data)}行, 浓度={sample_conc}{sample_unit})")
            else:
                # 兜底：使用完整DataFrame
                data_id = self.data_manager.add_data(display_name, df)
                data_ids.append(data_id)
            
            # 6. 添加到当前项目
            project = self.project_manager.get_current_project()
            if project:
                for data_id in data_ids:
                    project.add_data(data_id)
            
            # 7. ⭐ 关键：使用原始JSON字典填充表格（参考原项目）
            self.view.data_table.load_data(json_data)
            
            # 8. 统计信息
            total_rows = 0
            if 'CalculateDataList' in json_data:
                for sample in json_data['CalculateDataList']:
                    total_rows += len(sample.get('BaseData', []))
                    total_rows += len(sample.get('CombineData', []))
                    total_rows += len(sample.get('DissociationData', []))
            
            self.view.update_status(f"已加载: {display_name}")
            
            # 显示数据信息
            info = f"文件: {file_name}\n"
            info += f"数据名称: {display_name}\n"
            info += f"样本数: {len(json_data.get('CalculateDataList', []))}\n"
            info += f"数据行数: {total_rows}\n"
            
            if sample_name:
                info += f"样本名称: {sample_name}\n"
            if concentration is not None:
                info += f"浓度: {concentration} {concentration_unit}\n"
            
            # ✅ 不弹窗，改为状态栏关键信息
            self.view.update_status(info.replace('\n', ' | '))
            
            print(f"[Controller] JSON文件导入完成，已创建链接: file:{file_path} → data:{data_id}")
            print(f"[Controller] 实际显示数据行数: {total_rows}")
            
        else:
            # 其他文件类型：使用通用方式
            print(f"[Controller] 使用通用方式加载文件")
            
            success, df, error = load_file(file_path)
            
            if not success:
                self.view.show_error("加载失败", error)
                self.view.update_status("加载失败")
                return
            
            # 获取显示名称
            display_name = file_name
            if hasattr(df, 'attrs') and 'sample_name' in df.attrs:
                sample_name = df.attrs['sample_name']
                if sample_name:
                    display_name = sample_name
            
            # 添加到数据管理器
            data_id = self.data_manager.add_data(display_name, df)
            
            # 创建链接
            self.link_manager.create_link(
                'file', file_path,
                'data', data_id,
                link_type='import',
                metadata={
                    'file_name': file_name,
                    'import_time': datetime.now().isoformat(),
                    'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else None
                }
            )
            
            # 添加到当前项目
            project = self.project_manager.get_current_project()
            if project:
                project.add_data(data_id)
            
            # 显示数据（DataFrame方式）
            self.view.data_table.load_data(df)
            
            self.view.update_status(f"已加载: {display_name}")
            
            info = f"文件: {file_name}\n"
            info += f"数据名称: {display_name}\n"
            info += f"数据行数: {len(df)}\n"
            info += f"数据列: {', '.join(df.columns.tolist())}"
            
            if hasattr(df, 'attrs'):
                if 'concentration' in df.attrs:
                    info += f"\n浓度: {df.attrs['concentration']}"
                if 'concentration_unit' in df.attrs:
                    info += f" {df.attrs['concentration_unit']}"
            
            # ✅ 不弹窗，改为状态栏关键信息
            self.view.update_status(info.replace('\n', ' | '))
            
            print(f"[Controller] 文件导入完成，已创建链接: file:{file_path} → data:{data_id}")
    
    @Slot(str, str)
    def on_new_item_created(self, item_type: str, item_name: str):
        """
        处理树中新建节点
        
        参数:
            item_type: 节点类型（data/figure/result/project）
            item_name: 节点名称
        """
        print(f"[Controller] 新建节点: 类型={item_type}, 名称={item_name}")
        
        # 根据类型创建相应的对象
        if item_type == 'data':
            # 创建空数据对象
            data_id = self.data_manager.add_data(item_name, None)
            self.view.update_status(f"已创建数据: {item_name}")
            
        elif item_type == 'figure':
            # 创建图表对象
            figure_id = self.figure_manager.add_figure(item_name, 'line')
            self.view.update_status(f"已创建图表: {item_name}")
            
        elif item_type == 'result':
            # 创建结果对象
            result_id = self.result_manager.add_result(item_name, 'unknown')
            self.view.update_status(f"已创建结果: {item_name}")
            
        elif item_type == 'project':
            # 创建项目
            project_id = self.project_manager.create_project(item_name)
            self.view.update_status(f"已创建项目: {item_name}")
    
    @Slot(int)
    def on_data_added(self, data_id: int):
        """
        数据添加后
        
        ⭐需求2修复：统一由此方法添加节点到树
        
        节点添加时机：
        1. 手动点击"新建"：dataframe为空 → 添加到树
        2. 单样本JSON：dataframe不为空 → 添加到树
        3. 多样本JSON：有group_name属性 → 已在on_file_selected中添加，跳过
        """
        data = self.data_manager.get_data(data_id)
        if not data:
            return
        
        # 情况3：多样本JSON，已经通过group_item添加
        if (data.dataframe is not None and 
            not data.dataframe.empty and 
            hasattr(data.dataframe, 'attrs') and 
            'group_name' in data.dataframe.attrs):
            print(f"[Controller] 多样本数据已添加到组中，跳过: {data.name}")
            return
        
        # 情况1和2：添加到树
        self.view.add_data_to_tree(data_id, data.name)
        print(f"[Controller] 添加数据到树: {data.name}")
    
    @Slot(int)
    def on_data_selected(self, data_id: int):
        """
        数据被选中
        
        ⭐ 阶段2修复：增强绘图错误显示和刷新机制
        """
        self.current_data_id = data_id
        data = self.data_manager.get_data(data_id)
        
        if not data:
            self.view.update_status("数据不存在")
            return
        
        if data.dataframe is None or data.dataframe.empty:
            self.view.update_status("数据为空")
            return
        
        # 显示数据表格
        self.view.show_data_table(data.dataframe)
        
        # ⭐ 尝试自动绘图（带详细错误信息）
        try:
            x_data, y_data = data.get_xy_data()
            self.view.show_plot(x_data, y_data, label=data.name)
            self.view.update_status(f"已显示数据: {data.name} ({len(x_data)}个数据点)")
            print(f"[Controller] ✅ 绘图成功: {data.name}, {len(x_data)}个数据点")
        except ValueError as e:
            error_msg = f"数据格式错误: {str(e)}"
            self.view.update_status(error_msg)
            self.view.show_error("绘图失败", error_msg)
            print(f"[Controller] ❌ 绘图失败: {error_msg}")
            print(f"   DataFrame列: {list(data.dataframe.columns)}")
        except Exception as e:
            error_msg = f"绘图出错: {str(e)}"
            self.view.update_status(error_msg)
            print(f"[Controller] ❌ 绘图异常: {error_msg}")
            import traceback
            traceback.print_exc()
    
    @Slot(int)
    def on_figure_added(self, figure_id: int):
        """图表添加后"""
        figure = self.figure_manager.get_figure(figure_id)
        if figure:
            self.view.add_figure_to_tree(figure_id, figure.name)
    
    @Slot(int)
    def on_figure_selected(self, figure_id: int):
        """
        图表被选中
        
        ⭐ 阶段1改进：使用Figure.get_plot_data动态获取数据
        """
        self.current_figure_id = figure_id
        figure = self.figure_manager.get_figure(figure_id)
        
        if not figure:
            return
        
        # ⭐ 动态获取绘图数据
        plot_data = figure.get_plot_data(self.data_manager)
        
        if not plot_data:
            # ✅ 不弹窗，改为状态栏提示
            self.view.update_status("该图表没有关联的数据源")
            return
        
        # 根据数据源数量选择绘图方式
        if len(plot_data) == 1:
            # 单数据源：普通绘图
            d = plot_data[0]
            label = d['label']
            
            # 应用样式
            style = d['style']
            self.view.show_plot(
                d['x'], d['y'],
                label=label,
                color=style.get('color', '#1a73e8'),
                linewidth=style.get('linewidth', 2.0),
                marker=style.get('marker', 'o'),
                markersize=style.get('markersize', 4.0)
            )
            print(f"[Controller] 绘制单数据源图表: {label}")
            
        else:
            # 多数据源：对比绘图
            data_dict = {}
            for d in plot_data:
                data_dict[d['label']] = (d['x'], d['y'])
            
            self.view.canvas_widget.plot_multi_curves(data_dict)
            print(f"[Controller] 绘制多数据源对比图: {len(plot_data)}条曲线")
        
        # 应用图表配置（注：grid已在plot_line中设置）
        if hasattr(self.view, 'canvas_widget'):
            cfg = figure.plot_config
            self.view.canvas_widget.set_title(cfg.get('title', ''))
            self.view.canvas_widget.set_xlabel(cfg.get('xlabel', 'Time (s)'))
            self.view.canvas_widget.set_ylabel(cfg.get('ylabel', 'Response (RU)'))
    
    @Slot(int)
    def on_result_added(self, result_id: int):
        """结果添加后"""
        result = self.result_manager.get_result(result_id)
        if result:
            self.view.add_result_to_tree(result_id, result.name)
    
    @Slot(int)
    def on_result_selected(self, result_id: int):
        """结果被选中"""
        self.current_result_id = result_id
        result = self.result_manager.get_result(result_id)
        
        if not result:
            return
        
        # 显示结果
        self.view.show_result(result.parameters)
        
        # 如果有关联的图表，显示图表
        if result.figure_id:
            self.on_figure_selected(result.figure_id)
    
    @Slot(int, str)
    def on_fitting_requested(self, data_id: int, method: str):
        """
        请求拟合（增强版：自动创建链接）
        
        数据流：
        data:X → result:Y → figure:Z
        
        链接类型：
        - data → result: fitting_output
        - result → figure: visualization
        """
        data = self.data_manager.get_data(data_id)
        
        if not data:
            self.view.show_error("拟合失败", "数据不存在")
            return
        
        self.view.update_status(f"正在拟合: {method}")
        
        try:
            # 获取X, Y数据
            x_data, y_data = data.get_xy_data()
            
            # ⭐ 执行拟合（传递DataFrame用于某些需要完整数据的算法）
            fit_result = fit_data(method, x_data, y_data, dataframe=data.dataframe)
            
            if not fit_result['success']:
                self.view.show_error("拟合失败", fit_result.get('error', '未知错误'))
                self.view.update_status("拟合失败")
                return
            
            # ========== 创建结果对象 ==========
            result_id = self.result_manager.add_result(
                f"{data.name} - {method}",
                method
            )
            result = self.result_manager.get_result(result_id)
            result.set_parameters(fit_result['parameters'])
            result.set_statistics(rmse=fit_result['statistics'].get('rmse'))
            result.set_data_source(data_id)  # 使用新方法设置数据源
            
            # ✨ 创建链接：data → result
            self.link_manager.create_link(
                'data', data_id,
                'result', result_id,
                link_type='fitting_output',
                metadata={
                    'method': method,
                    'fit_time': datetime.now().isoformat(),
                    'parameters': fit_result.get('parameters', {}),
                    'rmse': fit_result['statistics'].get('rmse')
                }
            )
            
            # ========== ⭐ 步骤3：将拟合曲线保存为新的Data对象 ==========
            fitted_data_id = None
            if fit_result.get('y_pred') is not None:
                # 创建拟合曲线Data对象
                import pandas as pd
                fitted_df = pd.DataFrame({
                    'XValue': x_data,
                    'YValue': fit_result['y_pred']
                })
                fitted_df.attrs['source_type'] = 'fitted_curve'
                fitted_df.attrs['result_id'] = result_id
                fitted_df.attrs['original_data_id'] = data_id
                fitted_df.attrs['method'] = method
                
                fitted_data_id = self.data_manager.add_data(
                    name=f"{data.name} - 拟合曲线({method})",
                    dataframe=fitted_df
                )
                
                # 创建链接：result → fitted_data
                self.link_manager.create_link(
                    'result', result_id,
                    'data', fitted_data_id,
                    link_type='result_data',
                    metadata={
                        'data_type': 'fitted_curve',
                        'method': method,
                        'created_time': datetime.now().isoformat()
                    }
                )
                
                print(f"[Controller] ⭐ 拟合曲线已保存为Data对象: data_id={fitted_data_id}")
            
            # ========== ⭐ 创建对比图表（原始数据 vs 拟合曲线） ==========
            figure_id = None
            if fitted_data_id is not None:
                figure_id = self.figure_manager.add_figure(
                    f"{data.name} - 拟合对比",
                    "fitting"
                )
                figure = self.figure_manager.get_figure(figure_id)
                
                # ⭐ 使用新API：添加两个数据源
                figure.add_data_source(data_id, {
                    'label': '实验数据',
                    'color': '#1a73e8',
                    'linewidth': 1.5,
                    'marker': 'o',
                    'markersize': 4.0,
                    'linestyle': 'none'
                })
                
                figure.add_data_source(fitted_data_id, {
                    'label': f'拟合曲线({method})',
                    'color': '#ea4335',
                    'linewidth': 2.5,
                    'marker': 'none',
                    'linestyle': '-'
                })
                
                figure.set_result_source(result_id)  # 标记关联的结果
                
                # 创建链接：result → figure
                self.link_manager.create_link(
                    'result', result_id,
                    'figure', figure_id,
                    link_type='visualization',
                    metadata={
                        'figure_type': 'fitting_comparison',
                        'created_time': datetime.now().isoformat()
                    }
                )
                
                # 关联结果和图表
                result.figure_id = figure_id
                
                # 添加图表到项目
                project = self.project_manager.get_current_project()
                if project:
                    project.add_figure(figure_id)
                
                # ⭐ 使用新的绘图逻辑显示图表
                self.on_figure_selected(figure_id)
            
            # ========== 添加结果到项目 ==========
            project = self.project_manager.get_current_project()
            if project:
                project.add_result(result_id)
            
            # ========== 显示结果 ==========
            self.view.show_result(result.parameters)
            
            self.view.update_status(f"拟合完成: {method}")
            
            # ⭐ 显示完整的数据流信息
            link_info = f"拟合方法: {method}\n"
            link_info += f"结果ID: {result_id}\n"
            if fitted_data_id is not None:
                link_info += f"拟合曲线Data ID: {fitted_data_id}\n"
            if figure_id is not None:
                link_info += f"对比图表ID: {figure_id}\n"
            link_info += f"\n⭐ 数据流（Prism风格）:\n"
            link_info += f"原始数据(data:{data_id})\n"
            link_info += f"  → 拟合分析(result:{result_id})\n"
            if fitted_data_id is not None:
                link_info += f"    → 拟合曲线(data:{fitted_data_id})\n"
            if figure_id is not None:
                link_info += f"    → 对比图表(figure:{figure_id})\n"
            
            self.view.show_message("拟合完成", link_info)
            
            print(f"[Controller] ⭐ 拟合完成，数据流: data:{data_id} → result:{result_id} → data:{fitted_data_id} → figure:{figure_id}")
            
        except Exception as e:
            self.view.show_error("拟合出错", str(e))
            self.view.update_status("拟合失败")
            import traceback
            traceback.print_exc()
    
    # ========== 链接管理槽函数 ==========
    
    @Slot(str, object, str, object)
    def on_link_created(self, source_type: str, source_id, target_type: str, target_id):
        """链接创建时的处理"""
        print(f"[Controller] 链接已创建: {source_type}:{source_id} → {target_type}:{target_id}")
        # 可以在这里添加额外的UI更新逻辑
    
    @Slot(str, object, str, object)
    def on_link_removed(self, source_type: str, source_id, target_type: str, target_id):
        """链接删除时的处理"""
        print(f"[Controller] 链接已删除: {source_type}:{source_id} → {target_type}:{target_id}")
    
    # ========== 会话管理槽函数 ==========
    
    @Slot()
    def on_session_modified(self):
        """会话被修改时的处理"""
        # 更新窗口标题显示未保存标记
        current_title = self.view.windowTitle()
        if not current_title.endswith('*'):
            self.view.setWindowTitle(current_title + ' *')
    
    @Slot(str)
    def on_session_saved(self, file_path: str):
        """会话保存成功时的处理"""
        import os
        file_name = os.path.basename(file_path)
        self.view.update_status(f"已保存: {file_name}")
        # 移除窗口标题的未保存标记
        current_title = self.view.windowTitle().rstrip(' *')
        self.view.setWindowTitle(f"{current_title} - {file_name}")
    
    @Slot(str)
    def on_session_loaded(self, file_path: str):
        """会话加载成功时的处理"""
        import os
        file_name = os.path.basename(file_path)
        self.view.update_status(f"已加载: {file_name}")
        self.view.setWindowTitle(f"SPR Data Analyst - {file_name}")
        # TODO: 更新UI显示加载的数据
    
    # ========== 公共方法 ==========
    
    def start_fitting(self, method: str = "LocalBivariate"):
        """开始拟合（快捷方法）"""
        if self.current_data_id is None:
            self.view.show_error("操作失败", "请先选择数据")
            return
        
        self.on_fitting_requested(self.current_data_id, method)

    def _on_fit_from_menu(self):
        """菜单/工具栏：开始拟合（弹出方法选择，默认LocalBivariate）"""
        if self.current_data_id is None:
            self.view.show_error("操作失败", "请先在左侧选择一个数据节点")
            return
        try:
            from src.views.dialogs import select_fitting_method
            method, parameters = select_fitting_method(self.view)
            if not method:
                return
        except Exception:
            # 若对话框不存在，使用默认方法
            method = "LocalBivariate"
        self.on_fitting_requested(self.current_data_id, method)
    
    def save_session(self, file_path: Optional[str] = None):
        """
        保存会话
        
        参数：
            file_path: 保存路径，如果为None则使用当前文件路径
        """
        if file_path is None:
            file_path = self.session_manager.current_file_path
        
        if file_path is None:
            self.view.show_error("保存失败", "请先指定保存路径")
            return False
        
        success = self.session_manager.save_to_file(file_path)
        
        if success:
            self.view.show_message("保存成功", f"会话已保存到:\n{file_path}")
        else:
            self.view.show_error("保存失败", "保存会话时发生错误")
        
        return success
    
    def load_session(self, file_path: str):
        """
        加载会话
        
        参数：
            file_path: 文件路径
        """
        success = self.session_manager.load_from_file(file_path)
        
        if success:
            self.view.show_message("加载成功", f"会话已从以下位置加载:\n{file_path}")
            # TODO: 刷新UI显示所有加载的数据
        else:
            self.view.show_error("加载失败", "加载会话时发生错误")
        
        return success
    
    def new_session(self):
        """创建新会话"""
        # 检查是否有未保存的修改
        if self.session_manager.is_modified:
            # TODO: 显示确认对话框
            pass
        
        self.session_manager.new_session("新会话")
        self.view.setWindowTitle("SPR Data Analyst - 新会话")
        self.view.update_status("新建会话")
        # TODO: 清空UI显示
    
    def print_session_stats(self):
        """打印会话统计信息（调试用）"""
        self.session_manager.print_session_info()
        self.link_manager.print_summary()
        self.link_manager.print_all_links()
    
    # ========== 右键菜单槽函数 ==========
    
    @Slot(int)
    def on_create_figure_from_data(self, data_id: int):
        """
        从数据创建图表（右键菜单）
        
        ⭐ 阶段1改进：使用Figure.add_data_source而不是直接设置数据
        
        参数:
            data_id: 数据ID
        """
        print(f"[Controller] 从数据创建图表: data_id={data_id}")
        
        # 获取数据
        data = self.data_manager.get_data(data_id)
        if not data:
            self.view.show_error("错误", f"找不到数据 ID={data_id}")
            return
        
        # 检查数据是否为空
        if data.dataframe is None or data.dataframe.empty:
            self.view.show_error("错误", "数据为空，无法创建图表")
            return
        
        # ⭐ 创建图表（使用新API）
        figure_id = self.figure_manager.add_figure(
            f"{data.name} - 数据图",
            "line"
        )
        figure = self.figure_manager.get_figure(figure_id)
        
        # ⭐ 使用新API添加数据源（而不是设置数据副本）
        figure.add_data_source(data_id, {
            'label': data.name,
            'color': '#1a73e8',
            'linewidth': 2.0,
            'marker': 'o',
            'markersize': 4.0
        })
        
        # 创建链接：data → figure
        self.link_manager.create_link(
            'data', data_id,
            'figure', figure_id,
            link_type='visualize',
            metadata={
                'figure_type': 'line',
                'created_time': datetime.now().isoformat()
            }
        )
        
        # ⭐ 显示图表（通过调用on_figure_selected）
        self.on_figure_selected(figure_id)
        
        # 高亮图表节点
        self.view.highlight_tree_item('figure', figure_id)
        
        self.view.update_status(f"已创建图表: {figure.name}")
        print(f"[Controller] 图表创建完成: figure_id={figure_id}, 数据源={data_id}")
    
    @Slot(int)
    def on_fit_data_requested(self, data_id: int):
        """
        请求拟合数据（右键菜单）
        
        参数:
            data_id: 数据ID
        """
        print(f"[Controller] 请求拟合数据: data_id={data_id}")
        
        # 显示拟合方法选择对话框
        from src.views.dialogs import select_fitting_method
        method, parameters = select_fitting_method(self.view)
        
        if method is None:
            print("[Controller] 用户取消了拟合方法选择")
            return
        
        print(f"[Controller] 用户选择拟合方法: {method}, 参数: {parameters}")
        
        # 调用现有的拟合函数
        self.on_fitting_requested(data_id, method)
    
    @Slot(int)
    def on_change_figure_source(self, figure_id: int):
        """
        更改图表数据源（右键菜单）
        
        参数:
            figure_id: 图表ID
        """
        print(f"[Controller] 更改图表数据源: figure_id={figure_id}")
        
        # 显示数据选择对话框
        from src.views.dialogs import select_data
        new_data_id = select_data(self.data_manager, self.view)
        
        if new_data_id is None:
            print("[Controller] 用户取消了数据选择")
            return
        
        # 获取图表
        figure = self.figure_manager.get_figure(figure_id)
        if not figure:
            self.view.show_error("错误", f"找不到图表 ID={figure_id}")
            return
        
        # 获取旧的数据源
        old_data_id = figure.get_data_source()
        
        # 删除旧链接
        if old_data_id is not None:
            self.link_manager.remove_link('data', old_data_id, 'figure', figure_id)
        
        # 设置新数据源
        figure.set_data_source(new_data_id)
        
        # 创建新链接
        self.link_manager.create_link(
            'data', new_data_id,
            'figure', figure_id,
            link_type='plot_source',
            metadata={
                'changed_time': datetime.now().isoformat(),
                'previous_data_id': old_data_id
            }
        )
        
        # 获取新数据并更新图表
        data = self.data_manager.get_data(new_data_id)
        if data:
            df = data.get_processed_data()
            if not df.empty and len(df.columns) >= 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
                self.view.show_plot(df[x_col].values, df[y_col].values, data.get_name())
        
        self.view.update_status(f"已更改图表数据源: {figure.name}")
        print(f"[Controller] 数据源已更改: {old_data_id} → {new_data_id}")
    
    @Slot(str, int)
    def on_view_linked_data(self, item_type: str, item_id: int):
        """
        查看关联数据（右键菜单）
        
        参数:
            item_type: 项目类型（data/figure/result）
            item_id: 项目ID
        """
        print(f"[Controller] 查看关联数据: {item_type}:{item_id}")
        
        # 获取正向链接（派生对象）
        targets = self.link_manager.get_targets(item_type, item_id)
        
        # 获取反向链接（源对象）
        sources = self.link_manager.get_sources(item_type, item_id)
        
        # 构建信息文本
        info_lines = []
        info_lines.append(f"对象类型: {item_type}")
        info_lines.append(f"对象ID: {item_id}")
        info_lines.append("")
        
        # 源对象
        info_lines.append("📥 源对象（来源）:")
        if sources:
            for source_key in sources:
                info_lines.append(f"  ← {source_key}")
                # 获取链接元数据
                parts = source_key.split(':', 1)
                if len(parts) == 2:
                    src_type, src_id = parts[0], parts[1]
                    try:
                        src_id_int = int(src_id) if src_id.isdigit() else src_id
                        link_info = self.link_manager.get_link_metadata(
                            src_type, src_id_int, item_type, item_id
                        )
                        if link_info:
                            info_lines.append(f"      类型: {link_info.get('link_type', 'unknown')}")
                    except:
                        pass
        else:
            info_lines.append("  （无）")
        
        info_lines.append("")
        
        # 派生对象
        info_lines.append("📤 派生对象（输出）:")
        if targets:
            for target_key in targets:
                info_lines.append(f"  → {target_key}")
                # 获取链接元数据
                parts = target_key.split(':', 1)
                if len(parts) == 2:
                    tgt_type, tgt_id = parts[0], parts[1]
                    try:
                        tgt_id_int = int(tgt_id) if tgt_id.isdigit() else tgt_id
                        link_info = self.link_manager.get_link_metadata(
                            item_type, item_id, tgt_type, tgt_id_int
                        )
                        if link_info:
                            info_lines.append(f"      类型: {link_info.get('link_type', 'unknown')}")
                    except:
                        pass
        else:
            info_lines.append("  （无）")
        
        info_lines.append("")
        info_lines.append("=" * 50)
        info_lines.append("💡 提示: 点击对应节点可以查看详情")
        
        # 显示信息对话框
        self.view.show_message("关联对象", "\n".join(info_lines))
    
    @Slot(str, int)
    def on_export_item(self, item_type: str, item_id: int):
        """
        导出项目（右键菜单）
        
        参数:
            item_type: 项目类型
            item_id: 项目ID
        """
        print(f"[Controller] 导出项目: {item_type}:{item_id}")
        
        # TODO: 实现导出功能
        self.view.show_message(
            "功能开发中",
            f"导出功能正在开发中\n\n类型: {item_type}\nID: {item_id}"
        )
    
    # ========== 工具菜单槽函数 ==========
    
    @Slot()
    def on_view_stats(self):
        """查看会话统计信息"""
        print("[Controller] 查看会话统计")
        
        # 收集统计信息
        stats_lines = []
        stats_lines.append("📊 会话统计信息")
        stats_lines.append("=" * 60)
        stats_lines.append("")
        
        # 会话基本信息
        stats_lines.append(f"会话名称: {self.session_manager.session_name}")
        stats_lines.append(f"当前文件: {self.session_manager.current_file_path or '未保存'}")
        stats_lines.append(f"修改状态: {'已修改 *' if self.session_manager.is_modified else '未修改'}")
        stats_lines.append("")
        
        # 对象统计
        stats_lines.append("对象数量:")
        stats_lines.append(f"  📄 数据对象: {len(self.data_manager._data_dict)}")
        stats_lines.append(f"  📊 图表对象: {len(self.figure_manager._figures)}")
        stats_lines.append(f"  ✓ 结果对象: {len(self.result_manager._results)}")
        stats_lines.append(f"  📁 项目对象: {len(self.project_manager._projects)}")
        stats_lines.append("")
        
        # 链接统计
        all_links = self.link_manager.get_all_links()
        stats_lines.append(f"🔗 链接总数: {len(all_links)}")
        
        # 按类型统计链接
        link_types = {}
        for link in all_links:
            link_type = link.get('link_type', 'unknown')
            link_types[link_type] = link_types.get(link_type, 0) + 1
        
        if link_types:
            stats_lines.append("  链接类型分布:")
            for link_type, count in sorted(link_types.items()):
                stats_lines.append(f"    - {link_type}: {count}")
        
        stats_lines.append("")
        stats_lines.append("=" * 60)
        
        # 显示统计信息
        self.view.show_message("会话统计", "\n".join(stats_lines))
        
        # 同时输出到控制台
        self.session_manager.print_session_info()
    
    @Slot()
    def on_view_links(self):
        """查看所有链接信息"""
        print("[Controller] 查看所有链接")
        
        all_links = self.link_manager.get_all_links()
        
        if not all_links:
            self.view.show_message("链接信息", "当前没有任何链接")
            return
        
        # 构建链接信息
        links_lines = []
        links_lines.append("🔗 所有链接关系")
        links_lines.append("=" * 60)
        links_lines.append(f"总链接数: {len(all_links)}")
        links_lines.append("")
        
        # 按源对象分组
        grouped_links = {}
        for link in all_links:
            src_key = f"{link['source_type']}:{link['source_id']}"
            if src_key not in grouped_links:
                grouped_links[src_key] = []
            grouped_links[src_key].append(link)
        
        # 显示分组链接
        for src_key, links in sorted(grouped_links.items()):
            links_lines.append(f"📍 {src_key}")
            for link in links:
                tgt_key = f"{link['target_type']}:{link['target_id']}"
                link_type = link.get('link_type', 'unknown')
                created_at = link.get('created_at', 'N/A')
                links_lines.append(f"   → {tgt_key} [{link_type}]")
                links_lines.append(f"      创建时间: {created_at}")
            links_lines.append("")
        
        links_lines.append("=" * 60)
        links_lines.append("💡 提示: 右键节点→查看关联对象 可查看详情")
        
        # 显示链接信息
        self.view.show_message("所有链接", "\n".join(links_lines))
        
        # 同时输出到控制台
        self.link_manager.print_all_links()
    
    @Slot()
    def on_clear_all(self):
        """清空所有数据"""
        print("[Controller] 清空所有数据")
        
        from PySide6.QtWidgets import QMessageBox
        
        # 确认对话框
        reply = QMessageBox.question(
            self.view,
            "确认清空",
            "确定要清空所有数据吗？\n\n此操作将删除：\n- 所有数据对象\n- 所有图表对象\n- 所有结果对象\n- 所有链接关系\n\n此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 创建新会话（相当于清空）
            self.session_manager.new_session("新会话")
            
            # 清空UI
            self.view.project_tree.clear_all()
            
            self.view.update_status("已清空所有数据")
            self.view.show_message("清空完成", "所有数据已清空，开始新会话")
            
            print("[Controller] 所有数据已清空")
    
    @Slot()
    def on_export_graph(self):
        """导出链接图"""
        print("[Controller] 导出链接图")
        
        try:
            # 生成DOT格式的链接图
            dot_lines = []
            dot_lines.append("digraph DataLineage {")
            dot_lines.append("    rankdir=LR;")
            dot_lines.append("    node [shape=box, style=rounded];")
            dot_lines.append("")
            
            # 定义节点样式
            dot_lines.append("    // 节点定义")
            for data_id in self.data_manager._data_dict.keys():
                dot_lines.append(f'    data_{data_id} [label="Data {data_id}", fillcolor="#e3f2fd", style="filled,rounded"];')
            
            for figure_id in self.figure_manager._figures.keys():
                dot_lines.append(f'    figure_{figure_id} [label="Figure {figure_id}", fillcolor="#fff3e0", style="filled,rounded"];')
            
            for result_id in self.result_manager._results.keys():
                dot_lines.append(f'    result_{result_id} [label="Result {result_id}", fillcolor="#f3e5f5", style="filled,rounded"];')
            
            dot_lines.append("")
            dot_lines.append("    // 链接关系")
            
            # 添加链接
            for link in self.link_manager.get_all_links():
                src = f"{link['source_type']}_{link['source_id']}"
                tgt = f"{link['target_type']}_{link['target_id']}"
                link_type = link.get('link_type', '')
                dot_lines.append(f'    {src} -> {tgt} [label="{link_type}"];')
            
            dot_lines.append("}")
            
            dot_content = "\n".join(dot_lines)
            
            # 保存到文件
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self.view,
                "导出链接图",
                "data_lineage.dot",
                "Graphviz DOT (*.dot);;所有文件 (*.*)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(dot_content)
                
                self.view.show_message(
                    "导出成功",
                    f"链接图已导出到:\n{file_path}\n\n"
                    "提示: 使用Graphviz工具可以可视化此文件:\n"
                    "  dot -Tpng data_lineage.dot -o data_lineage.png"
                )
                print(f"[Controller] 链接图已导出: {file_path}")
        
        except Exception as e:
            self.view.show_error("导出失败", f"导出链接图时发生错误:\n{str(e)}")
            print(f"[Controller] 导出失败: {e}")
    
    @Slot()
    def on_show_test_guide(self):
        """显示测试指南"""
        print("[Controller] 显示测试指南")
        
        import os
        guide_path = "QUICK_TEST_GUIDE.md"
        
        if os.path.exists(guide_path):
            # 尝试用默认程序打开
            import subprocess
            import platform
            
            try:
                if platform.system() == 'Windows':
                    os.startfile(guide_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', guide_path])
                else:  # Linux
                    subprocess.run(['xdg-open', guide_path])
                
                self.view.update_status("已打开测试指南")
            except Exception as e:
                self.view.show_message(
                    "测试指南",
                    f"测试指南文件位于:\n{os.path.abspath(guide_path)}\n\n"
                    "请手动打开查看"
                )
        else:
            self.view.show_message(
                "测试指南",
                "测试指南包含8个测试场景:\n\n"
                "1. 文件导入 + 自动链接\n"
                "2. 右键菜单 - 创建图表\n"
                "3. 右键菜单 - 拟合分析\n"
                "4. 查看关联对象\n"
                "5. 更改图表数据源\n"
                "6. 节点高亮功能\n"
                "7. 重命名和删除\n"
                "8. 会话保存/加载\n\n"
                "详细说明请查看项目根目录的QUICK_TEST_GUIDE.md"
            )

