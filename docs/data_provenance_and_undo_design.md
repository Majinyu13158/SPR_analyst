# 数据血缘（Provenance）与撤回/重做（Undo/Redo）设计文档

## 1. 核心概念

### 1.1 数据血缘（Data Provenance）
**目标**：追踪每个数据对象的来源和处理历史

```
示例：
原始数据(Excel) 
  → [导入操作] 
  → Data#0 
  → [拟合操作] 
  → Result#0 + Data#1(拟合曲线) + Figure#0(对比图)
```

**关键信息**：
- 操作类型（import, fit, transform, delete）
- 输入对象（data_id, figure_id等）
- 输出对象
- 参数（method, file_path等）
- 时间戳
- 执行用户（可选）

### 1.2 撤回/重做（Undo/Redo）
**目标**：允许用户撤销错误操作，恢复到之前状态

**核心设计模式**：Command Pattern

```python
class ICommand(ABC):
    @abstractmethod
    def execute(self) -> bool:
        """执行操作，返回是否成功"""
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """撤销操作，返回是否成功"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """返回操作描述，用于UI显示"""
        pass
```

## 2. 架构设计

### 2.1 现有系统分析

**当前已有的组件**：
```
DataManager      - 管理Data对象
FigureManager    - 管理Figure对象  
ResultManager    - 管理Result对象
LinkManager      - 管理对象间的链接关系
ProjectManager   - 管理项目和会话
```

**现有LinkManager的局限**：
- 只记录**静态关系**（data→result, result→figure）
- 没有**操作记录**（谁创建了这个link？什么时候？用什么参数？）
- 没有**因果顺序**（操作的先后关系）

### 2.2 新增组件

#### 2.2.1 OperationLog（操作日志）
```python
@dataclass
class OperationLog:
    """单个操作的完整记录"""
    op_id: str                    # 操作唯一ID（UUID）
    op_type: str                  # 操作类型：import, fit, transform, delete, create_figure
    timestamp: str                # ISO格式时间戳
    
    # 输入输出
    inputs: Dict[str, Any]        # {'data_id': 0, 'method': 'LocalBivariate'}
    outputs: Dict[str, Any]       # {'result_id': 1, 'fitted_data_id': 2, 'figure_id': 3}
    
    # 元数据
    description: str              # 人类可读描述："拟合数据#0，使用LocalBivariate"
    user: Optional[str]           # 用户标识（可选）
    
    # 状态
    status: str                   # 'success', 'failed', 'reverted'
    error: Optional[str]          # 错误信息（如果失败）
```

#### 2.2.2 ProvenanceManager（血缘管理器）
```python
class ProvenanceManager:
    """管理操作历史和数据血缘"""
    
    def __init__(self):
        self._operations: List[OperationLog] = []
        self._object_lineage: Dict[Tuple[str, int], List[str]] = {}
        # key: ('data', 0) -> value: [op_id1, op_id2, ...]  # 影响这个对象的所有操作
    
    def record_operation(self, op_log: OperationLog):
        """记录一个操作"""
        self._operations.append(op_log)
        self._update_lineage(op_log)
    
    def get_lineage(self, obj_type: str, obj_id: int) -> List[OperationLog]:
        """获取某个对象的完整血缘"""
        op_ids = self._object_lineage.get((obj_type, obj_id), [])
        return [op for op in self._operations if op.op_id in op_ids]
    
    def export_lineage(self, format: str = 'json') -> str:
        """导出血缘图（JSON/DOT格式）"""
        pass
```

#### 2.2.3 CommandManager（命令管理器）
```python
class CommandManager:
    """管理可撤销的命令"""
    
    def __init__(self, provenance_mgr: ProvenanceManager):
        self._undo_stack: List[ICommand] = []
        self._redo_stack: List[ICommand] = []
        self._provenance = provenance_mgr
        self._max_history = 50  # 最多保留50步历史
    
    def execute(self, command: ICommand) -> bool:
        """执行命令并记录"""
        success = command.execute()
        if success:
            self._undo_stack.append(command)
            self._redo_stack.clear()  # 执行新命令后，清空redo栈
            # 自动记录到血缘
            self._provenance.record_operation(command.to_operation_log())
        return success
    
    def undo(self) -> bool:
        """撤销最近一次操作"""
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        success = cmd.undo()
        if success:
            self._redo_stack.append(cmd)
        return success
    
    def redo(self) -> bool:
        """重做最近一次撤销"""
        if not self._redo_stack:
            return False
        cmd = self._redo_stack.pop()
        success = cmd.execute()
        if success:
            self._undo_stack.append(cmd)
        return success
    
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0
    
    def get_undo_description(self) -> Optional[str]:
        """获取下一个可撤销操作的描述"""
        return self._undo_stack[-1].get_description() if self._undo_stack else None
    
    def get_redo_description(self) -> Optional[str]:
        """获取下一个可重做操作的描述"""
        return self._redo_stack[-1].get_description() if self._redo_stack else None
```

## 3. 具体Command实现

### 3.1 ImportDataCommand（导入数据）
```python
class ImportDataCommand(ICommand):
    """导入数据文件的可撤销命令"""
    
    def __init__(self, file_path: str, data_manager, project_manager):
        self.file_path = file_path
        self.data_manager = data_manager
        self.project_manager = project_manager
        
        # 执行后保存的状态
        self.created_data_ids: List[int] = []
        self.op_id = str(uuid.uuid4())
    
    def execute(self) -> bool:
        """执行导入"""
        try:
            # 调用现有导入逻辑
            data_ids = self._import_file(self.file_path)
            self.created_data_ids = data_ids
            return True
        except Exception as e:
            self.error = str(e)
            return False
    
    def undo(self) -> bool:
        """撤销导入：删除所有创建的数据"""
        try:
            for data_id in self.created_data_ids:
                self.data_manager.remove_data(data_id)
            return True
        except Exception:
            return False
    
    def get_description(self) -> str:
        filename = os.path.basename(self.file_path)
        return f"导入文件: {filename} ({len(self.created_data_ids)}个数据)"
    
    def to_operation_log(self) -> OperationLog:
        return OperationLog(
            op_id=self.op_id,
            op_type='import',
            timestamp=datetime.now().isoformat(),
            inputs={'file_path': self.file_path},
            outputs={'data_ids': self.created_data_ids},
            description=self.get_description(),
            status='success'
        )
```

### 3.2 FitDataCommand（拟合数据）
```python
class FitDataCommand(ICommand):
    """拟合数据的可撤销命令"""
    
    def __init__(self, data_id: int, method: str, 
                 data_manager, result_manager, figure_manager, link_manager):
        self.data_id = data_id
        self.method = method
        self.data_manager = data_manager
        self.result_manager = result_manager
        self.figure_manager = figure_manager
        self.link_manager = link_manager
        
        # 执行后保存的状态
        self.result_id: Optional[int] = None
        self.fitted_data_id: Optional[int] = None
        self.figure_id: Optional[int] = None
        self.created_links: List[Tuple] = []  # [(src_type, src_id, tgt_type, tgt_id), ...]
        self.op_id = str(uuid.uuid4())
    
    def execute(self) -> bool:
        """执行拟合（调用现有Controller逻辑）"""
        try:
            # 1. 拟合
            data = self.data_manager.get_data(self.data_id)
            x_data, y_data = data.get_xy_data(auto_sort=False)
            fit_result = fit_data(self.method, x_data, y_data, 
                                 dataframe=data.dataframe, data_obj=data)
            
            if not fit_result['success']:
                self.error = fit_result.get('error', 'Unknown error')
                return False
            
            # 2. 创建结果对象
            self.result_id = self.result_manager.add_result(
                f"{data.name} - {self.method}", self.method)
            result = self.result_manager.get_result(self.result_id)
            result.set_parameters(fit_result['parameters'])
            result.set_statistics(rmse=fit_result['statistics'].get('rmse'))
            result.set_data_source(self.data_id)
            
            # 记录链接
            link = self.link_manager.create_link(
                'data', self.data_id, 'result', self.result_id, 
                link_type='fitting_output')
            self.created_links.append(('data', self.data_id, 'result', self.result_id))
            
            # 3. 创建拟合曲线
            if fit_result.get('y_pred') is not None:
                fitted_df = pd.DataFrame({
                    'XValue': x_data, 
                    'YValue': fit_result['y_pred']
                })
                self.fitted_data_id = self.data_manager.add_data(
                    f"{data.name} - 拟合曲线({self.method})", fitted_df)
                
                self.link_manager.create_link(
                    'result', self.result_id, 'data', self.fitted_data_id,
                    link_type='result_data')
                self.created_links.append(('result', self.result_id, 'data', self.fitted_data_id))
            
            # 4. 创建对比图
            if self.fitted_data_id:
                self.figure_id = self.figure_manager.add_figure(
                    f"{data.name} - 拟合对比", 'fitting')
                figure = self.figure_manager.get_figure(self.figure_id)
                figure.add_data_source(self.data_id, {'label': '实验数据'})
                figure.add_data_source(self.fitted_data_id, {'label': '拟合曲线'})
                figure.set_result_source(self.result_id)
                
                self.link_manager.create_link(
                    'result', self.result_id, 'figure', self.figure_id,
                    link_type='visualization')
                self.created_links.append(('result', self.result_id, 'figure', self.figure_id))
            
            return True
        except Exception as e:
            self.error = str(e)
            return False
    
    def undo(self) -> bool:
        """撤销拟合：删除所有创建的对象"""
        try:
            # 删除链接
            for src_type, src_id, tgt_type, tgt_id in self.created_links:
                self.link_manager.remove_link(src_type, src_id, tgt_type, tgt_id)
            
            # 删除对象（逆序）
            if self.figure_id is not None:
                self.figure_manager.remove_figure(self.figure_id)
            if self.fitted_data_id is not None:
                self.data_manager.remove_data(self.fitted_data_id)
            if self.result_id is not None:
                self.result_manager.remove_result(self.result_id)
            
            return True
        except Exception:
            return False
    
    def get_description(self) -> str:
        data = self.data_manager.get_data(self.data_id)
        name = data.name if data else f"数据#{self.data_id}"
        return f"拟合: {name} ({self.method})"
    
    def to_operation_log(self) -> OperationLog:
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
```

### 3.3 DeleteItemCommand（删除对象）
```python
class DeleteItemCommand(ICommand):
    """删除数据/图表/结果的可撤销命令"""
    
    def __init__(self, item_type: str, item_id: int, managers: dict):
        self.item_type = item_type  # 'data', 'figure', 'result'
        self.item_id = item_id
        self.managers = managers
        
        # 保存状态用于恢复
        self.saved_object = None
        self.saved_links = []
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
            
            # 2. 保存相关链接
            self.saved_links = self.managers['link'].get_links_for_object(
                self.item_type, self.item_id)
            
            # 3. 删除链接
            for link in self.saved_links:
                self.managers['link'].remove_link(
                    link['source_type'], link['source_id'],
                    link['target_type'], link['target_id'])
            
            # 4. 删除对象
            if self.item_type == 'data':
                self.managers['data'].remove_data(self.item_id)
            elif self.item_type == 'figure':
                self.managers['figure'].remove_figure(self.item_id)
            elif self.item_type == 'result':
                self.managers['result'].remove_result(self.item_id)
            
            return True
        except Exception as e:
            self.error = str(e)
            return False
    
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
            
            # 2. 恢复链接
            for link in self.saved_links:
                self.managers['link'].create_link(
                    link['source_type'], link['source_id'],
                    link['target_type'], link['target_id'],
                    link_type=link.get('link_type'),
                    metadata=link.get('metadata'))
            
            return True
        except Exception:
            return False
    
    def get_description(self) -> str:
        type_name = {'data': '数据', 'figure': '图表', 'result': '结果'}[self.item_type]
        obj_name = getattr(self.saved_object, 'name', f'#{self.item_id}')
        return f"删除{type_name}: {obj_name}"
```

## 4. Controller集成

### 4.1 修改MainControllerFull

```python
class MainControllerFull:
    def __init__(self, view, parent=None):
        # 现有managers...
        
        # 新增
        self.provenance_manager = ProvenanceManager()
        self.command_manager = CommandManager(self.provenance_manager)
    
    def on_file_selected(self, file_path: str):
        """导入文件（改造为Command）"""
        cmd = ImportDataCommand(
            file_path=file_path,
            data_manager=self.data_manager,
            project_manager=self.project_manager
        )
        
        if self.command_manager.execute(cmd):
            self.view.update_status(f"导入成功: {os.path.basename(file_path)}")
            # UI更新...
        else:
            self.view.show_error("导入失败", cmd.error)
    
    def on_fitting_requested(self, data_id: int, method: str):
        """拟合（改造为Command）"""
        cmd = FitDataCommand(
            data_id=data_id,
            method=method,
            data_manager=self.data_manager,
            result_manager=self.result_manager,
            figure_manager=self.figure_manager,
            link_manager=self.link_manager
        )
        
        if self.command_manager.execute(cmd):
            self.view.update_status(f"拟合成功: {method}")
            # UI更新...
        else:
            self.view.show_error("拟合失败", cmd.error)
    
    def on_undo_requested(self):
        """撤销操作"""
        if self.command_manager.can_undo():
            desc = self.command_manager.get_undo_description()
            if self.command_manager.undo():
                self.view.update_status(f"已撤销: {desc}")
                self._refresh_ui()
            else:
                self.view.show_error("撤销失败", "无法撤销此操作")
    
    def on_redo_requested(self):
        """重做操作"""
        if self.command_manager.can_redo():
            desc = self.command_manager.get_redo_description()
            if self.command_manager.redo():
                self.view.update_status(f"已重做: {desc}")
                self._refresh_ui()
            else:
                self.view.show_error("重做失败", "无法重做此操作")
    
    def _refresh_ui(self):
        """刷新所有UI（撤销/重做后）"""
        # 清空树
        self.view.project_tree.clear_all()
        
        # 重新添加所有对象
        for data_id, data in self.data_manager._data_dict.items():
            self.view.add_data_to_tree(data_id, data.name)
        
        for figure in self.figure_manager.get_all_figures():
            self.view.add_figure_to_tree(figure.id, figure.name)
        
        for result in self.result_manager.get_all_results():
            self.view.add_result_to_tree(result.id, result.name)
```

## 5. UI集成

### 5.1 菜单和快捷键

```python
# 在MainWindowFull中添加
class MainWindowFull(QMainWindow):
    def _create_menu_bar(self):
        # 现有菜单...
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        self.undo_action = QAction("撤销(&U)", self)
        self.undo_action.setShortcut(QKeySequence.Undo)  # Ctrl+Z
        self.undo_action.setEnabled(False)
        edit_menu.addAction(self.undo_action)
        
        self.redo_action = QAction("重做(&R)", self)
        self.redo_action.setShortcut(QKeySequence.Redo)  # Ctrl+Y
        self.redo_action.setEnabled(False)
        edit_menu.addAction(self.redo_action)
        
        edit_menu.addSeparator()
        
        self.history_action = QAction("操作历史(&H)...", self)
        edit_menu.addAction(self.history_action)
```

### 5.2 历史面板（可选）

```python
class HistoryPanel(QDockWidget):
    """显示操作历史的面板"""
    
    def __init__(self, command_manager: CommandManager, parent=None):
        super().__init__("操作历史", parent)
        self.command_manager = command_manager
        
        # 列表显示
        self.history_list = QListWidget()
        self.setWidget(self.history_list)
        
        self.refresh()
    
    def refresh(self):
        """刷新历史列表"""
        self.history_list.clear()
        
        # 显示undo栈（可撤销的操作）
        for cmd in self.command_manager._undo_stack:
            item = QListWidgetItem(f"✓ {cmd.get_description()}")
            self.history_list.addItem(item)
        
        # 当前位置
        if self.command_manager._redo_stack:
            item = QListWidgetItem("─ 当前位置 ─")
            item.setFlags(Qt.NoItemFlags)
            self.history_list.addItem(item)
        
        # 显示redo栈（可重做的操作）
        for cmd in reversed(self.command_manager._redo_stack):
            item = QListWidgetItem(f"○ {cmd.get_description()}")
            item.setForeground(QColor('gray'))
            self.history_list.addItem(item)
```

## 6. 实施计划

### 阶段1：基础框架（1-2天）
1. ✅ 创建 `OperationLog` 数据类
2. ✅ 实现 `ProvenanceManager`
3. ✅ 实现 `ICommand` 接口
4. ✅ 实现 `CommandManager`

### 阶段2：核心Command（2-3天）
1. ✅ `ImportDataCommand`
2. ✅ `FitDataCommand`  
3. ✅ `DeleteItemCommand`
4. ✅ 测试每个Command的execute/undo

### 阶段3：Controller集成（1-2天）
1. ✅ 修改 `on_file_selected` 使用Command
2. ✅ 修改 `on_fitting_requested` 使用Command
3. ✅ 添加 `on_undo_requested` 和 `on_redo_requested`
4. ✅ 实现 `_refresh_ui` 方法

### 阶段4：UI集成（1天）
1. ✅ 添加撤销/重做菜单和快捷键
2. ✅ 动态更新菜单状态（enable/disable）
3. ✅ （可选）添加历史面板

### 阶段5：血缘可视化（1天）
1. ✅ 实现血缘导出为JSON
2. ✅ （可选）实现血缘图可视化

### 阶段6：测试与完善（1-2天）
1. ✅ 单元测试
2. ✅ 集成测试
3. ✅ 边界情况处理
4. ✅ 文档更新

## 7. 注意事项

### 7.1 性能考虑
- 限制历史栈大小（默认50步）
- 大对象考虑使用引用而非深拷贝
- 延迟加载历史面板

### 7.2 数据一致性
- Command执行失败时回滚部分状态
- 撤销失败时提示用户并保持当前状态
- 关键操作前备份状态

### 7.3 用户体验
- 清晰的操作描述
- 撤销/重做后自动刷新UI
- 状态栏显示当前可撤销/重做的操作
- 快捷键支持（Ctrl+Z, Ctrl+Y）

## 8. 未来扩展

### 8.1 高级功能
- [ ] 操作历史保存到文件（支持跨会话撤销）
- [ ] 操作历史导出为报告
- [ ] 血缘图交互式可视化
- [ ] 批量撤销/重做
- [ ] 事务（一组操作作为一个整体撤销）

### 8.2 数据科学友好
- [ ] 导出为Python脚本（重现分析流程）
- [ ] 导出为Jupyter Notebook
- [ ] 与版本控制系统集成（Git）

---

## 附录A：关键代码骨架

参见上述各章节的代码示例。

## 附录B：测试用例

```python
def test_fit_command_execute_undo():
    # 准备
    cmd = FitDataCommand(data_id=0, method='LocalBivariate', ...)
    
    # 执行
    assert cmd.execute() == True
    assert cmd.result_id is not None
    
    # 验证创建的对象存在
    assert result_manager.get_result(cmd.result_id) is not None
    
    # 撤销
    assert cmd.undo() == True
    
    # 验证对象被删除
    assert result_manager.get_result(cmd.result_id) is None
```

