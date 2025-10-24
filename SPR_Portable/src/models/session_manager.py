# -*- coding: utf-8 -*-
"""
会话管理器 - 管理运行时的所有数据和状态

功能：
1. 聚合所有Manager（DataManager, FigureManager等）
2. 管理LinkManager实例
3. 提供统一的save/load接口
4. 自动保存机制
5. 跟踪修改状态
"""
from PySide6.QtCore import QObject, Signal, QTimer
from typing import Optional, Dict, Any
from pathlib import Path
import json
import zipfile
import tempfile
import shutil
from datetime import datetime

from .data_model import DataManager, Data
from .figure_model import FigureManager
from .result_model import ResultManager
from .project_model import ProjectManager
from .link_manager import LinkManager


class SessionManager(QObject):
    """
    会话管理器
    
    管理当前工作会话的所有数据、状态和关联关系
    
    信号：
        session_modified: 会话被修改
        session_saved: 会话保存成功 (file_path)
        session_loaded: 会话加载成功 (file_path)
        auto_save_triggered: 自动保存触发
    """
    
    # 信号定义
    session_modified = Signal()
    session_saved = Signal(str)
    session_loaded = Signal(str)
    auto_save_triggered = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建各个子Manager
        self.data_manager = DataManager(self)
        self.figure_manager = FigureManager(self)
        self.result_manager = ResultManager(self)
        self.project_manager = ProjectManager(self)
        self.link_manager = LinkManager(self)
        
        # 会话状态
        self.is_modified = False
        self.current_file_path: Optional[str] = None
        self.session_name = "未命名会话"
        self.created_time = datetime.now()
        self.last_save_time: Optional[datetime] = None
        
        # 自动保存设置
        self.auto_save_enabled = True
        self.auto_save_interval = 300  # 秒（5分钟）
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._on_auto_save)
        
        # 连接子Manager的信号以追踪修改
        self._connect_modification_signals()
        
        # 启动自动保存定时器
        if self.auto_save_enabled:
            self.auto_save_timer.start(self.auto_save_interval * 1000)
        
        print("[SessionManager] 会话管理器初始化完成")
    
    # ========== 修改追踪 ==========
    
    def _connect_modification_signals(self):
        """连接所有会导致修改的信号"""
        # DataManager
        self.data_manager.data_added.connect(self.mark_modified)
        self.data_manager.data_removed.connect(self.mark_modified)
        
        # FigureManager
        self.figure_manager.figure_added.connect(self.mark_modified)
        self.figure_manager.figure_removed.connect(self.mark_modified)
        
        # ResultManager
        self.result_manager.result_added.connect(self.mark_modified)
        self.result_manager.result_removed.connect(self.mark_modified)
        
        # ProjectManager（修复：project_added 不是 project_created）
        self.project_manager.project_added.connect(self.mark_modified)
        self.project_manager.project_removed.connect(self.mark_modified)
        self.project_manager.project_updated.connect(self.mark_modified)
        
        # LinkManager
        self.link_manager.link_created.connect(self._on_link_modified)
        self.link_manager.link_removed.connect(self._on_link_modified)
    
    def mark_modified(self, *args):
        """
        标记会话已修改
        
        参数：
            *args: 接受任意参数（来自不同信号）
        """
        if not self.is_modified:
            self.is_modified = True
            self.session_modified.emit()
            print("[SessionManager] 会话已修改")
    
    def _on_link_modified(self, *args):
        """链接修改时的处理"""
        self.mark_modified()
    
    def clear_modified_flag(self):
        """清除修改标志（保存后调用）"""
        self.is_modified = False
    
    # ========== 自动保存 ==========
    
    def _on_auto_save(self):
        """自动保存触发"""
        if self.is_modified and self.current_file_path:
            print("[SessionManager] 触发自动保存...")
            self.auto_save_triggered.emit()
            self.save_to_file(self.current_file_path, auto_save=True)
    
    def enable_auto_save(self, enabled: bool = True, interval: int = 300):
        """
        启用/禁用自动保存
        
        参数：
            enabled: 是否启用
            interval: 自动保存间隔（秒）
        """
        self.auto_save_enabled = enabled
        self.auto_save_interval = interval
        
        if enabled:
            self.auto_save_timer.start(interval * 1000)
            print(f"[SessionManager] 自动保存已启用，间隔{interval}秒")
        else:
            self.auto_save_timer.stop()
            print("[SessionManager] 自动保存已禁用")
    
    # ========== 保存/加载 ==========
    
    def save_to_file(self, file_path: str, auto_save: bool = False) -> bool:
        """
        保存会话到文件
        
        参数：
            file_path: 保存路径（.sprx文件）
            auto_save: 是否为自动保存
        
        返回：
            bool: 是否成功保存
        
        文件格式：
            .sprx 文件是一个ZIP压缩包，包含：
            - manifest.json: 元数据
            - data.json: 数据对象
            - figures.json: 图表对象
            - results.json: 结果对象
            - projects.json: 项目对象
            - links.json: 链接关系
        """
        try:
            file_path = Path(file_path)
            
            # 确保文件扩展名为.sprx
            if file_path.suffix != '.sprx':
                file_path = file_path.with_suffix('.sprx')
            
            print(f"[SessionManager] 正在保存会话到: {file_path}")
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # 1. 保存manifest.json
                manifest = self._create_manifest()
                # 附加schema信息与要求文件
                manifest.update({
                    'schema_version': '1.0',
                    'required_files': [
                        'manifest.json', 'data.json', 'figures.json',
                        'results.json', 'projects.json', 'links.json'
                    ]
                })
                with open(temp_path / 'manifest.json', 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False)
                
                # 2. 保存数据帧文件（parquet优先，失败则csv），并记录映射
                (temp_path / 'data').mkdir(parents=True, exist_ok=True)
                data_files_map = {}
                for data_id, data in self.data_manager._data_dict.items():
                    # 统一取可用的DataFrame
                    df = getattr(data, 'dataframe', None)
                    if df is None or getattr(df, 'empty', True):
                        df = getattr(data, 'processed_data', None)
                    if df is None or getattr(df, 'empty', True):
                        continue
                    # 先尝试parquet
                    rel_name = f"data/{data_id}.parquet"
                    abs_path = temp_path / rel_name
                    ok = False
                    try:
                        df.to_parquet(abs_path, index=False)
                        ok = True
                    except Exception:
                        # 退化为csv
                        rel_name = f"data/{data_id}.csv"
                        abs_path = temp_path / rel_name
                        try:
                            df.to_csv(abs_path, index=False)
                            ok = True
                        except Exception:
                            ok = False
                    if ok:
                        data_files_map[str(data_id)] = rel_name

                # 3. 保存数据对象索引（包含文件映射）
                data_export = self._export_data_manager(file_map=data_files_map)
                with open(temp_path / 'data.json', 'w', encoding='utf-8') as f:
                    json.dump(data_export, f, indent=2, ensure_ascii=False)
                
                # 4. 保存图表对象
                figures_export = self._export_figure_manager()
                with open(temp_path / 'figures.json', 'w', encoding='utf-8') as f:
                    json.dump(figures_export, f, indent=2, ensure_ascii=False)
                
                # 5. 保存结果对象
                results_export = self._export_result_manager()
                with open(temp_path / 'results.json', 'w', encoding='utf-8') as f:
                    json.dump(results_export, f, indent=2, ensure_ascii=False)
                
                # 6. 保存项目对象
                projects_export = self._export_project_manager()
                with open(temp_path / 'projects.json', 'w', encoding='utf-8') as f:
                    json.dump(projects_export, f, indent=2, ensure_ascii=False)
                
                # 7. 保存链接关系
                links_export = self.link_manager.to_dict()
                with open(temp_path / 'links.json', 'w', encoding='utf-8') as f:
                    json.dump(links_export, f, indent=2, ensure_ascii=False)
                
                # 8. 创建ZIP文件
                with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file in temp_path.iterdir():
                        zipf.write(file, file.name)
                    # 写入子目录内容（如 data/*）
                    for subdir in temp_path.iterdir():
                        if subdir.is_dir():
                            for p in subdir.rglob('*'):
                                arcname = str(p.relative_to(temp_path))
                                zipf.write(p, arcname)
            
            # 更新状态
            self.current_file_path = str(file_path)
            self.last_save_time = datetime.now()
            self.clear_modified_flag()
            
            save_type = "自动保存" if auto_save else "手动保存"
            print(f"[SessionManager] {save_type}成功: {file_path}")
            
            self.session_saved.emit(str(file_path))
            
            return True
            
        except Exception as e:
            print(f"[SessionManager] 保存失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_from_file(self, file_path: str) -> bool:
        """
        从文件加载会话
        
        参数：
            file_path: 文件路径（.sprx文件）
        
        返回：
            bool: 是否成功加载
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                print(f"[SessionManager] 文件不存在: {file_path}")
                return False
            
            print(f"[SessionManager] 正在加载会话: {file_path}")
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # 1. 解压ZIP文件
                with zipfile.ZipFile(file_path, 'r') as zipf:
                    zipf.extractall(temp_path)
                # 1.1 校验包结构
                if not self._validate_unpacked(temp_path):
                    print("[SessionManager] 会话文件结构校验失败")
                    return False
                
                # 2. 加载manifest
                with open(temp_path / 'manifest.json', 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                self._load_manifest(manifest)
                
                # 3. 加载数据对象
                with open(temp_path / 'data.json', 'r', encoding='utf-8') as f:
                    data_export = json.load(f)
                self._import_data_manager(data_export, base_path=temp_path)
                
                # 4. 加载图表对象
                with open(temp_path / 'figures.json', 'r', encoding='utf-8') as f:
                    figures_export = json.load(f)
                self._import_figure_manager(figures_export)
                
                # 5. 加载结果对象
                with open(temp_path / 'results.json', 'r', encoding='utf-8') as f:
                    results_export = json.load(f)
                self._import_result_manager(results_export)
                
                # 6. 加载项目对象
                with open(temp_path / 'projects.json', 'r', encoding='utf-8') as f:
                    projects_export = json.load(f)
                self._import_project_manager(projects_export)
                
                # 7. 加载链接关系
                with open(temp_path / 'links.json', 'r', encoding='utf-8') as f:
                    links_export = json.load(f)
                self.link_manager.from_dict(links_export)
            
            # 更新状态
            self.current_file_path = str(file_path)
            self.clear_modified_flag()
            
            print(f"[SessionManager] 加载成功: {file_path}")
            self.session_loaded.emit(str(file_path))
            
            return True
            
        except Exception as e:
            print(f"[SessionManager] 加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ========== 导出/导入辅助方法 ==========
    
    def _create_manifest(self) -> Dict:
        """创建元数据"""
        return {
            'version': '1.0',
            'session_name': self.session_name,
            'created_time': self.created_time.isoformat(),
            'last_save_time': datetime.now().isoformat(),
            'data_count': len(self.data_manager._data_dict),
            'figure_count': len(self.figure_manager._figures),
            'result_count': len(self.result_manager._results),
            'project_count': len(self.project_manager._projects),
            'link_count': len(self.link_manager.link_metadata)
        }
    
    def _load_manifest(self, manifest: Dict):
        """加载元数据"""
        self.session_name = manifest.get('session_name', '未命名会话')
        created_str = manifest.get('created_time')
        if created_str:
            self.created_time = datetime.fromisoformat(created_str)
        # 可选：校验版本
        schema_version = manifest.get('schema_version')
        if schema_version and schema_version != '1.0':
            print(f"[SessionManager] 警告：不匹配的schema版本 {schema_version}")
    
    def _export_data_manager(self, file_map: Dict[str, str] = None) -> Dict:
        """导出DataManager数据"""
        # 简化版本：只导出基本信息
        data_list = []
        for data_id, data in self.data_manager._data_dict.items():
            data_info = {
                'id': data_id,
                'name': data.name,
                'type': type(data).__name__,
                # DataFrame不序列化到JSON，太大了
                # 可以考虑保存为单独的Parquet文件
            }
            data_list.append(data_info)
        
        return {
            'version': '1.0',
            'data_list': data_list,
            'counter': self.data_manager._counter,
            'files': file_map or {}
        }
    
    def _import_data_manager(self, data: Dict, base_path: Path = None):
        """导入DataManager数据"""
        # 从文件映射恢复DataFrame（优先parquet，退化csv）
        files_map: Dict[str, str] = data.get('files', {})
        recovered = 0
        if base_path is None:
            base_path = Path('.')
        for info in data.get('data_list', []):
            data_id = info.get('id')
            name = info.get('name', f"数据{data_id}")
            rel = files_map.get(str(data_id))
            df = None
            if rel:
                fpath = base_path / rel
                try:
                    if fpath.suffix.lower() == '.parquet':
                        import pandas as pd
                        df = pd.read_parquet(fpath)
                    elif fpath.suffix.lower() == '.csv':
                        import pandas as pd
                        df = pd.read_csv(fpath)
                except Exception:
                    df = None
            # 构造Data对象并保持原ID（使用融合版Data类）
            data_obj = Data(item=df, itemtype='dataframe', parent=self.data_manager)
            data_obj.set_name(name)
            self.data_manager._data_dict[int(data_id)] = data_obj
            recovered += 1
        # 恢复计数器
        # 优先使用保存的counter，否则设置为 max_id+1
        saved_counter = data.get('counter')
        if isinstance(saved_counter, int):
            self.data_manager._counter = saved_counter
        else:
            self.data_manager._counter = (max(self.data_manager._data_dict.keys()) + 1) if self.data_manager._data_dict else 0
        print(f"[SessionManager] 导入了 {recovered} 个数据对象（含DataFrame恢复）")
    
    def _export_figure_manager(self) -> Dict:
        """导出FigureManager数据"""
        figure_list = []
        for figure_id, figure in self.figure_manager._figures.items():
            figure_info = {
                'id': figure.id,
                'name': figure.name,
                'figure_type': figure.figure_type,
                'data_id': figure.data_id
            }
            figure_list.append(figure_info)
        
        return {
            'version': '1.0',
            'figure_list': figure_list,
            'next_id': self.figure_manager._next_id  # 修复：_next_id 不是 _counter
        }
    
    def _import_figure_manager(self, data: Dict):
        """导入FigureManager数据"""
        # 修复：使用next_id而不是counter
        self.figure_manager._next_id = data.get('next_id', data.get('counter', 1))
        # 简化版本：不恢复Figure对象
        print(f"[SessionManager] 导入了 {len(data.get('figure_list', []))} 个图表对象（简化版）")
    
    def _export_result_manager(self) -> Dict:
        """导出ResultManager数据"""
        result_list = []
        for result_id, result in self.result_manager._results.items():
            result_info = {
                'id': result.id,
                'name': result.name,
                'method': result.method,
                'parameters': result.parameters,
                'data_id': result.data_id
            }
            result_list.append(result_info)
        
        return {
            'version': '1.0',
            'result_list': result_list,
            'next_id': self.result_manager._next_id  # 修复：_next_id 不是 _counter
        }
    
    def _import_result_manager(self, data: Dict):
        """导入ResultManager数据"""
        # 修复：使用next_id而不是counter
        self.result_manager._next_id = data.get('next_id', data.get('counter', 1))
        print(f"[SessionManager] 导入了 {len(data.get('result_list', []))} 个结果对象（简化版）")
    
    def _export_project_manager(self) -> Dict:
        """导出ProjectManager数据"""
        project_list = []
        for project_id, project in self.project_manager._projects.items():
            project_info = {
                'id': project.id,
                'name': project.name,
                'data_ids': project.data_ids,
                'figure_ids': project.figure_ids,
                'result_ids': project.result_ids
            }
            project_list.append(project_info)
        
        return {
            'version': '1.0',
            'project_list': project_list,
            'next_id': self.project_manager._next_id,  # 修复：_next_id 不是 _counter
            'current_project_id': self.project_manager._current_project_id
        }
    
    def _import_project_manager(self, data: Dict):
        """导入ProjectManager数据"""
        # 修复：使用next_id而不是counter
        self.project_manager._next_id = data.get('next_id', data.get('counter', 1))
        self.project_manager._current_project_id = data.get('current_project_id')
        print(f"[SessionManager] 导入了 {len(data.get('project_list', []))} 个项目对象（简化版）")

    # ========== 基础校验 ==========
    def _validate_unpacked(self, base_path: Path) -> bool:
        """校验解压后的基础文件结构与JSON格式"""
        required = ['manifest.json', 'data.json', 'figures.json', 'results.json', 'projects.json', 'links.json']
        for name in required:
            p = base_path / name
            if not p.exists():
                print(f"[SessionManager] 缺少必要文件: {name}")
                return False
            # 基本JSON可读性校验
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    json.load(f)
            except Exception as e:
                print(f"[SessionManager] JSON无效: {name}: {e}")
                return False
        # data目录可选存在
        data_dir = base_path / 'data'
        if data_dir.exists() and not data_dir.is_dir():
            print("[SessionManager] data不是目录")
            return False
        return True
    
    # ========== 会话管理 ==========
    
    def new_session(self, session_name: str = "新会话"):
        """
        创建新会话（清空当前数据）
        
        参数：
            session_name: 会话名称
        """
        # 清空所有Manager
        self.data_manager._data_dict.clear()
        self.data_manager._counter = 0
        
        self.figure_manager._figures.clear()
        self.figure_manager._counter = 0
        
        self.result_manager._results.clear()
        self.result_manager._counter = 0
        
        self.project_manager._projects.clear()
        self.project_manager._counter = 0
        self.project_manager._current_project_id = None
        
        self.link_manager.clear()
        
        # 重置状态
        self.session_name = session_name
        self.current_file_path = None
        self.created_time = datetime.now()
        self.last_save_time = None
        self.clear_modified_flag()
        
        print(f"[SessionManager] 新建会话: {session_name}")
    
    def get_session_info(self) -> Dict:
        """获取会话信息"""
        return {
            'name': self.session_name,
            'file_path': self.current_file_path,
            'created_time': self.created_time.isoformat(),
            'last_save_time': self.last_save_time.isoformat() if self.last_save_time else None,
            'is_modified': self.is_modified,
            'data_count': len(self.data_manager._data_dict),
            'figure_count': len(self.figure_manager._figures),
            'result_count': len(self.result_manager._results),
            'project_count': len(self.project_manager._projects),
            'link_count': len(self.link_manager.link_metadata)
        }
    
    def print_session_info(self):
        """打印会话信息（调试用）"""
        info = self.get_session_info()
        print(f"\n{'='*50}")
        print(f"会话信息")
        print(f"{'='*50}")
        print(f"名称: {info['name']}")
        print(f"文件: {info['file_path'] or '未保存'}")
        print(f"修改状态: {'已修改' if info['is_modified'] else '未修改'}")
        print(f"创建时间: {info['created_time']}")
        print(f"最后保存: {info['last_save_time'] or '从未保存'}")
        print(f"\n对象统计:")
        print(f"  - 数据: {info['data_count']}")
        print(f"  - 图表: {info['figure_count']}")
        print(f"  - 结果: {info['result_count']}")
        print(f"  - 项目: {info['project_count']}")
        print(f"  - 链接: {info['link_count']}")
        print(f"{'='*50}\n")

