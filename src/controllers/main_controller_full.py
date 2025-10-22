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
        # 让View能在关闭时回调控制器
        try:
            self.view.controller = self
        except Exception:
            pass
    
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
        if hasattr(self.view, 'auto_save_toggle_action'):
            self.view.auto_save_toggle_action.setChecked(self.session_manager.auto_save_enabled)
            self.view.auto_save_toggle_action.triggered.connect(self._on_toggle_auto_save)
        if hasattr(self.view, 'auto_save_interval_action'):
            self.view.auto_save_interval_action.triggered.connect(self._on_set_auto_save_interval)
        # 文件菜单/工具栏：新建/导入数据/打开会话/保存
        if hasattr(self.view, 'menu_new_action'):
            self.view.menu_new_action.triggered.connect(self._on_menu_new)
        if hasattr(self.view, 'menu_import_data_action'):
            self.view.menu_import_data_action.triggered.connect(self._on_menu_import_data)
        if hasattr(self.view, 'menu_open_session_action'):
            self.view.menu_open_session_action.triggered.connect(self._on_menu_open)
        if hasattr(self.view, 'menu_save_action'):
            self.view.menu_save_action.triggered.connect(self._on_menu_save)
        if hasattr(self.view, 'menu_save_as_action'):
            self.view.menu_save_as_action.triggered.connect(self._on_menu_save_as)
        if hasattr(self.view, 'recent_menu'):
            self._init_recent_menu()
        if hasattr(self.view, 'menu_rename_session_action'):
            self.view.menu_rename_session_action.triggered.connect(self._on_rename_session)
        if hasattr(self.view, 'toolbar_import_action'):
            self.view.toolbar_import_action.triggered.connect(self._on_menu_import_data)
        if hasattr(self.view, 'toolbar_open_session_action'):
            self.view.toolbar_open_session_action.triggered.connect(self._on_menu_open)
        if hasattr(self.view, 'toolbar_save_action'):
            self.view.toolbar_save_action.triggered.connect(self._on_menu_save)
        if hasattr(self.view, 'toolbar_save_as_action'):
            self.view.toolbar_save_as_action.triggered.connect(self._on_menu_save_as)
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
            # ⭐ 新增：将JSON解析得到的宽表导出为Excel并自动导入
            try:
                import os
                import pandas as pd
                base_name = os.path.splitext(file_name)[0]
                export_dir = os.path.join(os.getcwd(), 'Json2excel')
                os.makedirs(export_dir, exist_ok=True)
                export_path = os.path.join(export_dir, f"{base_name}.xlsx")
                # 仅在是宽表(Time+多列)时导出；否则仍导出以统一流程
                df_to_save = df.copy()
                df_to_save.to_excel(export_path, index=False)
                print(f"[Controller] ✅ 已将JSON转换为Excel: {export_path} (shape={df_to_save.shape})")
                # 作为父宽表节点导入（仅一次），并让 on_data_added 负责生成子节点
                excel_display_name = f"{base_name} (宽表)"
                df_to_save.attrs['wide_parent_children_cols'] = [str(c) for c in list(df_to_save.columns)[1:]]
                df_to_save.attrs['wide_parent_base_name'] = base_name
                excel_parent_id = self.data_manager.add_data(excel_display_name, df_to_save)
                # 链接：json file → data(excel父)
                self.link_manager.create_link(
                    'file', file_path,
                    'data', excel_parent_id,
                    link_type='json_to_excel',
                    metadata={
                        'generated_excel_path': export_path,
                        'note': 'JSON解析生成的宽表Excel'
                    }
                )
                # 项目挂载
                project = self.project_manager.get_current_project()
                if project:
                    project.add_data(excel_parent_id)
                # 显示父节点数据到表格
                self.view.data_table.load_data(df_to_save)
                print(f"[Controller] 已导入宽表父节点: data_id={excel_parent_id}，子节点由on_data_added创建")
            except Exception as e:
                print(f"[Controller] ⚠️ JSON→Excel转换失败: {e}")
            
            # 4. 不再创建“JSON直读”的多样本节点结构；仅保留“Excel父+子”结构
            data_ids = []
            
            # 6. 添加到当前项目
            project = self.project_manager.get_current_project()
            if project:
                for data_id in data_ids:
                    project.add_data(data_id)
            
            # 7. 显示父宽表（上面已显示），此处不再覆盖为原始JSON点表
            
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
            
            # ========= 宽表Excel：创建父+子节点结构（不保留单独总节点） =========
            try:
                import pandas as pd
                cols = list(df.columns)
                is_wide = ('Time' in cols and len(cols) >= 2)
                display_name = os.path.splitext(file_name)[0]
                if is_wide:
                    # 将子列信息写入attrs，交给on_data_added统一创建父/子节点，避免重复
                    df.attrs['wide_parent_children_cols'] = [str(c) for c in cols[1:]]
                    df.attrs['wide_parent_base_name'] = display_name
                    parent_id = self.data_manager.add_data(f"{display_name} (宽表)", df)
                    self.link_manager.create_link('file', file_path, 'data', parent_id, link_type='import', metadata={'file_name': file_name})
                    project = self.project_manager.get_current_project()
                    if project:
                        project.add_data(parent_id)
                    # 显示父表
                    self.view.data_table.load_data(df)
                    self.view.update_status(f"已加载: {display_name} (宽表)")
                    print(f"[Controller] Excel宽表导入完成，父节点已创建: parent={parent_id}（子节点由on_data_added负责）")
                    return
            except Exception as e:
                print(f"[Controller] 宽表Excel节点构建失败，退回单节点: {e}")

            # ========= 退回单节点导入 =========
            display_name = file_name
            if hasattr(df, 'attrs') and 'sample_name' in df.attrs:
                sample_name = df.attrs['sample_name']
                if sample_name:
                    display_name = sample_name
            data_id = self.data_manager.add_data(display_name, df)
            self.link_manager.create_link('file', file_path, 'data', data_id, link_type='import', metadata={'file_name': file_name})
            project = self.project_manager.get_current_project()
            if project:
                project.add_data(data_id)
            self.view.data_table.load_data(df)
            self.view.update_status(f"已加载: {display_name}")
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
        3. 宽表父节点：由此创建子节点（split_sample），避免重复创建
        """
        data = self.data_manager.get_data(data_id)
        if not data:
            return
        
        # 若这是一个宽表父节点且还未生成子节点，则在此生成
        if (data.dataframe is not None and not data.dataframe.empty and hasattr(data.dataframe, 'attrs')):
            attrs = data.dataframe.attrs
            if 'wide_parent_children_cols' in attrs and 'wide_parent_base_name' in attrs:
                try:
                    import pandas as pd
                    base_name = attrs['wide_parent_base_name']
                    cols = list(attrs['wide_parent_children_cols'])
                    time_vals = data.dataframe['Time'].values
                    # 在树上创建父节点（若还未创建）
                    parent_item = self.view.project_tree.add_data_item(data_id, data.name)
                    for col in cols:
                        sub_df = pd.DataFrame({'XValue': pd.to_numeric(time_vals, errors='coerce'),
                                               'YValue': pd.to_numeric(data.dataframe[str(col)].values, errors='coerce')})
                        child_name = f"{base_name} - {str(col)}"
                        child_id = self.data_manager.add_data(child_name, sub_df)
                        # 父→子链接
                        self.link_manager.create_link('data', data_id, 'data', child_id, link_type='split_sample', metadata={'column': str(col)})
                        self.view.project_tree.add_data_item(child_id, child_name, parent_item=parent_item)
                        # 为每个新子节点自动创建并显示一幅图像（单曲线）
                        try:
                            figure_id = self.figure_manager.add_figure(f"{child_name} - 数据图", "line")
                            figure = self.figure_manager.get_figure(figure_id)
                            figure.add_data_source(child_id, {
                                'label': child_name,
                                'color': '#1a73e8',
                                'linewidth': 2.0,
                                'marker': 'o',
                                'markersize': 3.0
                            })
                            self.link_manager.create_link('data', child_id, 'figure', figure_id, link_type='visualize')
                        except Exception:
                            pass
                    # 避免重复生成
                    del attrs['wide_parent_children_cols']
                    del attrs['wide_parent_base_name']
                    print(f"[Controller] 已为宽表父节点生成子节点: parent={data_id}")
                    # 同时为父节点创建一张多曲线图
                    try:
                        parent_figure_id = self.figure_manager.add_figure(f"{data.name} - 多曲线", "line")
                        fig = self.figure_manager.get_figure(parent_figure_id)
                        fig.add_data_source(data_id, {
                            'label': data.name,
                            'color': '#1a73e8',
                            'linewidth': 2.0,
                            'marker': 'none'
                        })
                        self.link_manager.create_link('data', data_id, 'figure', parent_figure_id, link_type='visualize')
                        self.on_figure_selected(parent_figure_id)
                    except Exception:
                        pass
                    return
                except Exception as e:
                    print(f"[Controller] 生成子节点失败: {e}")
        
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
            # ===== ⭐ 新增：拟合前数据验证 =====
            validation = data.validate_xy_extraction()
            
            # 检查是否有严重错误
            if 'error' in validation:
                self.view.show_error("数据验证失败", validation['error'])
                self.view.update_status("拟合失败：数据无效")
                return
            
            # 显示警告信息（如果有）
            if validation['warnings']:
                warning_msg = "数据验证警告：\n\n"
                warning_msg += "\n".join(f"• {w}" for w in validation['warnings'])
                warning_msg += f"\n\n将使用列：\n"
                warning_msg += f"• X列: {validation['x_col']}\n"
                warning_msg += f"• Y列: {validation['y_col']}\n"
                warning_msg += f"• 有效数据点: {validation['valid_both']} / {validation['total_points']}\n"
                
                if validation['y_candidates'] and len(validation['y_candidates']) > 1:
                    warning_msg += f"\n备选Y列: {', '.join(validation['y_candidates'])}\n"
                
                warning_msg += "\n是否继续拟合？"
                
                # 如果数据点<3，强制阻止拟合
                if validation['valid_both'] < 3:
                    self.view.show_error("数据不足", warning_msg.replace("是否继续拟合？", "拟合已取消"))
                    self.view.update_status("拟合失败：数据点不足")
                    return
                
                # 其他警告：询问用户
                from PySide6.QtWidgets import QMessageBox
                reply = QMessageBox.warning(
                    self.view,
                    "数据验证警告",
                    warning_msg,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No  # 默认为No
                )
                
                if reply != QMessageBox.Yes:
                    self.view.update_status("用户取消拟合")
                    return
            
            # 获取X, Y数据
            # ⚠️ 注意：拟合时使用 auto_sort=False 保持原始顺序
            # 某些算法可能依赖于数据的原始时间顺序
            x_data, y_data = data.get_xy_data(auto_sort=False)
            
            print(f"[Controller] 拟合数据: X列={validation['x_col']}, Y列={validation['y_col']}, 数据点={len(x_data)}")
            
            # ⭐ 执行拟合（传递DataFrame和Data对象用于获取SPR参数）
            fit_result = fit_data(method, x_data, y_data, dataframe=data.dataframe, data_obj=data)
            
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
            # 附加元信息：数据源与方法
            params_with_meta = dict(fit_result['parameters']) if isinstance(fit_result.get('parameters'), dict) else {}
            try:
                data_source_name = data.get_name() if hasattr(data, 'get_name') else getattr(data, 'name', str(data_id))
            except Exception:
                data_source_name = str(data_id)
            params_with_meta = {
                'DataSource': (data_source_name, None, ''),
                'Method': (method, None, ''),
                **params_with_meta
            }
            result.set_parameters(params_with_meta)
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
                y_pred = fit_result['y_pred']
                
                # ⭐ 调试：验证拟合结果
                print(f"[Controller] 拟合结果验证:")
                print(f"  - X数据（前5个）: {x_data[:5]}")
                print(f"  - Y原始（前5个）: {y_data[:5]}")
                print(f"  - Y预测（前5个）: {y_pred[:5]}")
                
                # 检查是否Y预测等于X（这会导致直线）
                if len(y_pred) == len(x_data):
                    is_y_equal_x = all(abs(y_pred[i] - x_data[i]) < 1e-10 for i in range(min(5, len(x_data))))
                    if is_y_equal_x:
                        print(f"[Controller] ⚠️ 警告：Y预测值等于X值！这会画成直线！")
                
                # 如果返回了矩阵形式的预测以及时间向量，则生成“宽表拟合曲线”
                if isinstance(y_pred, (list, tuple)) or hasattr(y_pred, 'ndim'):
                    y_pred_matrix = fit_result.get('y_pred_matrix')
                    time_vector = fit_result.get('time_vector')
                    headers = fit_result.get('headers')
                else:
                    y_pred_matrix, time_vector, headers = None, None, None

                if y_pred_matrix is not None and hasattr(y_pred_matrix, 'ndim') and y_pred_matrix.ndim == 2 and time_vector is not None and headers is not None:
                    # 将矩阵预测写成宽表：Time | conc1 | conc2 | ...
                    try:
                        data_dict = {'Time': time_vector}
                        for idx, col_name in enumerate(headers):
                            data_dict[str(col_name)] = y_pred_matrix[:, idx]
                        fitted_df = pd.DataFrame(data_dict)
                    except Exception:
                        # 退化到一维曲线
                        fitted_df = pd.DataFrame({'XValue': x_data, 'YValue': y_pred})
                else:
                    fitted_df = pd.DataFrame({'XValue': x_data, 'YValue': y_pred})
                fitted_df.attrs['source_type'] = 'fitted_curve'
                fitted_df.attrs['result_id'] = result_id
                fitted_df.attrs['original_data_id'] = data_id
                fitted_df.attrs['method'] = method
                
                print(f"[Controller] 拟合曲线DataFrame:")
                print(fitted_df.head())
                
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
    
    def on_fitting_requested_multi(self, data_ids: list, method: str):
        """
        合并多个数据后进行拟合（LocalBivariate多浓度支持）
        
        参数:
            data_ids: 数据ID列表
            method: 拟合方法
        """
        import pandas as pd
        import numpy as np
        
        if not data_ids:
            self.view.show_error("拟合失败", "未选择任何数据")
            return
        
        print(f"[Controller] 合并拟合: 数据ID={data_ids}, 方法={method}")
        
        try:
            # ========== 步骤1：收集所有数据的DataFrame ==========
            all_dataframes = []
            data_names = []
            
            for data_id in data_ids:
                data = self.data_manager.get_data(data_id)
                if not data or data.dataframe is None or data.dataframe.empty:
                    print(f"[Controller] 跳过空数据: data_id={data_id}")
                    continue
                all_dataframes.append(data.dataframe.copy())
                data_names.append(data.get_name() if hasattr(data, 'get_name') else str(data_id))
            
            if not all_dataframes:
                self.view.show_error("拟合失败", "所有选中的数据都为空")
                return
            
            # ========== 步骤2：合并为宽表 ==========
            print(f"[Controller] 合并{len(all_dataframes)}个DataFrame...")
            
            # 检查是否都已经是宽表格式（Time + 浓度列）
            merged_df = None
            time_col = None
            
            # 宽表优先：若DataFrame含有Time且≥2列，则直接按浓度列横向追加
            for idx, df in enumerate(all_dataframes):
                cols = list(df.columns)
                if len(cols) < 2:
                    print(f"[Controller] 数据{idx}列数不足，跳过")
                    continue
                if 'Time' in cols:
                    if idx == 0:
                        merged_df = df.copy()
                    else:
                        for col in cols[1:]:
                            new_col = str(col)
                            while merged_df is not None and new_col in merged_df.columns:
                                new_col = new_col + "_dup"
                            merged_df[new_col] = df[col].values
                else:
                    # 回退：若不是宽表，尝试只取(XValue,YValue)并先转为单列宽表（不推荐）
                    if idx == 0:
                        if 'XValue' in cols and 'YValue' in cols:
                            merged_df = pd.DataFrame({'Time': df['XValue'].values, '0.0': df['YValue'].values})
                    else:
                        if 'YValue' in cols:
                            new_col = f"{idx}"
                            merged_df[new_col] = df['YValue'].values
            
            if merged_df is None or merged_df.empty:
                self.view.show_error("拟合失败", "数据合并失败")
                return
            
            print(f"[Controller] 合并后的DataFrame形状: {merged_df.shape}")
            print(f"[Controller] 列名: {list(merged_df.columns)}")
            
            # ========== 步骤3：创建临时Data对象 ==========
            combined_name = f"合并数据({len(data_names)}组): {', '.join(data_names[:3])}" + ("..." if len(data_names) > 3 else "")
            
            combined_data_id = self.data_manager.add_data(
                name=combined_name,
                dataframe=merged_df
            )
            
            print(f"[Controller] 创建合并数据: data_id={combined_data_id}, name={combined_name}")
            
            # ========== 步骤4：调用单次拟合 ==========
            self.on_fitting_requested(combined_data_id, method)
            
            print(f"[Controller] ⭐ 多数据合并拟合完成")
            
        except Exception as e:
            self.view.show_error("合并拟合出错", f"{str(e)}\n\n请确保所有数据格式一致")
            self.view.update_status("合并拟合失败")
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
        # 清除未保存标记
        if hasattr(self.view, 'setProperty'):
            self.view.setProperty('_dirty', False)
        if hasattr(self.view, 'set_session_name'):
            self.view.set_session_name(self.session_manager.session_name)
    
    @Slot(str)
    def on_session_loaded(self, file_path: str):
        """会话加载成功时的处理"""
        import os
        file_name = os.path.basename(file_path)
        self.view.update_status(f"已加载: {file_name}")
        self.view.setWindowTitle(f"SPR Data Analyst - {file_name}")
        if hasattr(self.view, 'setProperty'):
            self.view.setProperty('_dirty', False)
        if hasattr(self.view, 'set_session_name'):
            self.view.set_session_name(self.session_manager.session_name)
        # 重建UI：清空树并填充加载的数据/图表/结果
        try:
            # 清空树
            if hasattr(self.view, 'project_tree') and hasattr(self.view.project_tree, 'clear_all'):
                self.view.project_tree.clear_all()

            # 添加数据
            first_data_id = None
            for data_id, data in self.data_manager._data_dict.items():
                self.view.add_data_to_tree(data_id, data.name)
                if first_data_id is None:
                    first_data_id = data_id

            # 添加图表
            for fig in self.figure_manager.get_all_figures():
                self.view.add_figure_to_tree(fig.id, fig.name)

            # 添加结果
            for res in self.result_manager.get_all_results():
                self.view.add_result_to_tree(res.id, res.name)

            # 显示首个数据到表格并尝试绘图
            if first_data_id is not None:
                self.current_data_id = first_data_id
                data = self.data_manager.get_data(first_data_id)
                if data and data.dataframe is not None and not data.dataframe.empty:
                    # 表格
                    self.view.show_data_table(data.dataframe)
                    # 尝试绘图（使用已稳定的MiniPlot通道）
                    try:
                        x_data, y_data = data.get_xy_data()
                        self.view.show_plot(x_data, y_data, label=data.name)
                    except Exception:
                        pass
            
        except Exception as e:
            # 仅记录日志，不阻塞
            print(f"[Controller] 重新构建UI失败: {e}")
    
    # ========== 公共方法 ==========
    
    def start_fitting(self, method: str = "LocalBivariate"):
        """开始拟合（快捷方法）"""
        if self.current_data_id is None:
            self.view.show_error("操作失败", "请先选择数据")
            return
        
        self.on_fitting_requested(self.current_data_id, method)

    def _on_fit_from_menu(self):
        """菜单/工具栏：开始拟合（弹出方法选择，无需预先选中数据）"""
        try:
            from src.views.dialogs import select_fitting_method
            method, parameters, selected_data_ids = select_fitting_method(self.view, data_manager=self.data_manager, preselect_data_id=self.current_data_id)
            if not method:
                return
            # 允许未预先选中任何数据节点
            if not selected_data_ids:
                self.view.show_error("操作失败", "请在对话框中至少选择一个数据源")
                return
        except Exception:
            # 若对话框不存在，使用默认方法
            method = "LocalBivariate"
            selected_data_ids = [self.current_data_id] if self.current_data_id is not None else []
        # 多数据合并拟合
        if len(selected_data_ids) > 1:
            self.on_fitting_requested_multi(selected_data_ids, method)
        elif len(selected_data_ids) == 1:
            self.on_fitting_requested(selected_data_ids[0], method)
    
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

    # ========== 菜单动作：打开/保存 ========== 
    def _on_menu_open(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "打开会话文件",
            "",
            "SPR 会话文件 (*.sprx);;所有文件 (*.*)"
        )
        if file_path:
            self.load_session(file_path)
            self._add_recent_file(file_path)

    def _on_menu_import_data(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "导入数据文件",
            "",
            "数据文件 (*.json *.csv *.xlsx *.xls);;JSON (*.json);;CSV (*.csv);;Excel (*.xlsx *.xls);;所有文件 (*.*)"
        )
        if file_path:
            # 复用现有加载文件流程
            self.on_file_selected(file_path)

    def _on_menu_save(self):
        from PySide6.QtWidgets import QFileDialog
        # 若已有路径，直接保存；否则询问保存为
        if self.session_manager.current_file_path:
            self.save_session(self.session_manager.current_file_path)
            self._add_recent_file(self.session_manager.current_file_path)
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "保存会话为",
            "session.sprx",
            "SPR 会话文件 (*.sprx);;所有文件 (*.*)"
        )
        if file_path:
            self.save_session(file_path)
            self._add_recent_file(file_path)

    def _on_menu_save_as(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "另存为",
            "session.sprx",
            "SPR 会话文件 (*.sprx);;所有文件 (*.*)"
        )
        if file_path:
            self.save_session(file_path)
            self._add_recent_file(file_path)

    def _on_menu_new(self):
        from PySide6.QtWidgets import QMessageBox
        if self.session_manager.is_modified:
            reply = QMessageBox.question(
                self.view,
                "未保存的更改",
                "当前会话有未保存的更改，是否继续新建？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        # 新建会话并清空UI
        self.session_manager.new_session("新会话")
        if hasattr(self.view, 'project_tree') and hasattr(self.view.project_tree, 'clear_all'):
            self.view.project_tree.clear_all()
        self.view.update_status("已新建会话")
        self.view.setWindowTitle("SPR Data Analyst - 新会话")
        if hasattr(self.view, 'set_session_name'):
            self.view.set_session_name(self.session_manager.session_name)

    # ========== 最近打开 ========== 
    def _init_recent_menu(self):
        try:
            self._recent_files = []
            self._refresh_recent_menu()
        except Exception:
            self._recent_files = []

    def _add_recent_file(self, path: str):
        if not hasattr(self, '_recent_files'):
            self._recent_files = []
        # 放到前面，去重，保留最多8个
        path = str(path)
        self._recent_files = [p for p in self._recent_files if p != path]
        self._recent_files.insert(0, path)
        self._recent_files = self._recent_files[:8]
        self._refresh_recent_menu()

    def _refresh_recent_menu(self):
        if not hasattr(self.view, 'recent_menu'):
            return
        menu = self.view.recent_menu
        menu.clear()
        if not getattr(self, '_recent_files', None):
            from PySide6.QtWidgets import QAction
            act = QAction("（空）", self.view)
            act.setEnabled(False)
            menu.addAction(act)
            return
        from PySide6.QtWidgets import QAction
        for p in self._recent_files:
            act = QAction(p, self.view)
            act.triggered.connect(lambda checked=False, path=p: self.load_session(path))
            menu.addAction(act)

    def _on_rename_session(self):
        from PySide6.QtWidgets import QInputDialog
        current = self.session_manager.session_name
        name, ok = QInputDialog.getText(self.view, "重命名会话", "会话名称：", text=current)
        if ok and name:
            self.session_manager.session_name = name
            # 更新标题/状态栏
            title = self.view.windowTitle().split(' - ')[0]
            self.view.setWindowTitle(f"{title} - {name}")
            self.view.update_status(f"会话已重命名为：{name}")
            if hasattr(self.view, 'set_session_name'):
                self.view.set_session_name(name)
    
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
        if hasattr(self.view, 'setProperty'):
            self.view.setProperty('_dirty', False)
    
    def print_session_stats(self):
        """打印会话统计信息（调试用）"""
        self.session_manager.print_session_info()
        self.link_manager.print_summary()
        self.link_manager.print_all_links()

    # ========== 自动保存控制 ==========
    def _on_toggle_auto_save(self, checked: bool):
        self.session_manager.enable_auto_save(checked, self.session_manager.auto_save_interval)
        self.view.update_status("自动保存：开启" if checked else "自动保存：关闭")

    def _on_set_auto_save_interval(self):
        from PySide6.QtWidgets import QInputDialog
        interval, ok = QInputDialog.getInt(
            self.view,
            "设置自动保存间隔",
            "间隔（秒）：",
            value=self.session_manager.auto_save_interval,
            min=30,
            max=3600,
            step=30
        )
        if ok:
            self.session_manager.enable_auto_save(True, interval)
            if hasattr(self.view, 'auto_save_toggle_action'):
                self.view.auto_save_toggle_action.setChecked(True)
            self.view.update_status(f"自动保存：间隔已设为 {interval} 秒")
    
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
        
        # 显示拟合方法选择对话框（带数据源选择）
        from src.views.dialogs import select_fitting_method
        method, parameters, selected_data_ids = select_fitting_method(self.view, data_manager=self.data_manager, preselect_data_id=data_id)
        
        if method is None:
            print("[Controller] 用户取消了拟合方法选择")
            return
        
        print(f"[Controller] 用户选择拟合方法: {method}, 参数: {parameters}")
        
        # 允许多选数据
        if not selected_data_ids:
            selected_data_ids = [data_id]
        
        if len(selected_data_ids) > 1:
            self.on_fitting_requested_multi(selected_data_ids, method)
        else:
            self.on_fitting_requested(selected_data_ids[0], method)
    
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

    # ========== 关闭前保存提示 ==========
    def try_handle_close(self) -> bool:
        """处理窗口关闭前的未保存提示，返回是否允许关闭"""
        from PySide6.QtWidgets import QMessageBox, QFileDialog
        if not self.session_manager.is_modified:
            return True
        reply = QMessageBox.question(
            self.view,
            "未保存的更改",
            "当前会话有未保存的更改。是否保存？",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )
        if reply == QMessageBox.Cancel:
            return False
        if reply == QMessageBox.Discard:
            return True
        # Save
        path = self.session_manager.current_file_path
        if not path:
            file_path, _ = QFileDialog.getSaveFileName(
                self.view,
                "保存会话为",
                "session.sprx",
                "SPR 会话文件 (*.sprx);;所有文件 (*.*)"
            )
            if not file_path:
                return False
            path = file_path
        ok = self.save_session(path)
        return bool(ok)
    
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

