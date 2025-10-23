# 拟合重复触发问题分析

## 📊 信号链路梳理

### 1. 用户触发拟合
```
用户右键点击数据 → ProjectTree.fit_data_requested (信号)
  → MainControllerFull.on_fit_data_requested()
    → MainControllerFull.on_fitting_requested(data_id, method)
```

### 2. 拟合任务提交
```
on_fitting_requested() 
  → JobManager.submit_with_callbacks(run_fit_task, ..., on_done=_on_done)
    → QThreadPool.start(CallbackRunnable)  [线程池执行]
```

### 3. 拟合完成回调
```
CallbackRunnable.run() 完成
  → _on_done(job_id, result) [在工作线程]
    → _handle_fit_success(...)
      → DataManager.add_data("拟合曲线")
        → DataManager.data_added.emit(data_id)  [Qt信号]
          → MainControllerFull.on_data_added(data_id)
```

### 4. 图形创建链路
```
_handle_fit_success(...)
  → FigureManager.add_figure("对比图")
    → FigureManager.figure_added.emit(figure_id)  [Qt信号]
      → MainWindowFull.on_figure_added(figure_id)
```

## 🐛 已知问题

### 问题1: 旧回调累积
**症状**: `on_fitting_requested_multi _on_done` 被重复调用数十次
**原因**: 
- ProcessPoolExecutor 和 QThreadPool 的生命周期超过单次程序运行
- 旧的回调闭包仍然绑定在 future 对象上
- Python 模块热重载时,旧的 JobManager 实例未被销毁

**解决方案**:
1. 在 `app_full.py` 启动时调用 `JobManager.reset_instance()`
2. 强制关闭旧的进程池: `shutdown(wait=False, cancel_futures=True)`
3. 清空 JobManager._instance

### 问题2: data_added 信号的递归触发
**症状**: 每次拟合后会生成多个拟合曲线节点
**原因**:
- `on_data_added()` 会为"宽表"类型数据生成子节点
- 拟合曲线也是 Data 对象,也会触发 `data_added` 信号
- 如果没有正确设置 `source_type`,会导致递归生成

**解决方案**:
已在 `on_data_added()` 中添加检查:
```python
source_type = df.attrs.get('source_type')
if source_type in ['fitted_curve', 'child_of_wide_parent']:
    append_fit_trace(f"on_data_added: skip child generation for {source_type}")
    return
```

### 问题3: 永久锁机制未生效
**症状**: 即使设置了 `_fit_block_permanent[data_id] = True`,拟合仍然重复
**原因**:
- 永久锁只在 `on_fitting_requested()` 入口检查
- 旧的回调已经通过了入口检查,直接执行 `_handle_fit_success()`
- 永久锁无法拦截已提交的任务

**解决方案**:
必须从源头阻止旧回调执行 → 重置 JobManager

## 🔍 诊断步骤

### 第1步: 确认重置生效
运行程序并检查日志:
```bash
python app_full.py
# 导入数据 → 拟合一次
# 检查 fit_trace.log
```

预期:
- 只有1个 `on_fitting_requested ENTER`
- 只有1个 `on_fitting_requested _on_done`
- **不应出现** `on_fitting_requested_multi _on_done`

### 第2步: 检查调用栈
如果仍然出现重复,查看日志中的 `CALLSTACK`:
```
[时间] on_fitting_requested_multi _on_done ENTER: job=xxx
CALLSTACK:
  File "...", line X, in run
  File "...", line Y, in _callback
  ...
```

关键问题:
1. 回调是从哪个线程触发? (tid=?)
2. 回调是从哪个 future 对象触发?
3. job_id 是否是新生成的还是旧的?

### 第3步: 检查信号连接
如果是信号问题,检查:
```python
# 在 MainControllerFull.__init__ 中
self.data_manager.data_added.connect(self.on_data_added)  # 应该只连接1次
```

使用工具确认:
```python
receivers_count = self.data_manager.receivers(self.data_manager.data_added)
print(f"data_added信号的接收者数量: {receivers_count}")
```

## 🎯 终极解决方案

如果重置仍然无效,考虑:

### 方案A: 完全移除 submit_with_callbacks
改用传统的 QThread + 自定义信号:
```python
class FitWorker(QThread):
    finished = Signal(dict)
    
    def run(self):
        result = run_fit_task(...)
        self.finished.emit(result)

# 使用
worker = FitWorker(...)
worker.finished.connect(self._on_done)
worker.start()
```

优点: 完全控制生命周期
缺点: 无法使用进程池

### 方案B: 任务去重ID
为每个拟合任务生成唯一ID,在 `_on_done` 中验证:
```python
self._active_fit_tasks = {}  # {data_id: task_id}

def on_fitting_requested(self, data_id, method):
    task_id = uuid.uuid4().hex
    self._active_fit_tasks[data_id] = task_id
    
    def _on_done(jid, result):
        if self._active_fit_tasks.get(data_id) != task_id:
            append_fit_trace(f"STALE CALLBACK IGNORED: task_id={task_id}")
            return
        # ... 正常处理
```

### 方案C: 禁用多线程拟合
暂时回退到主线程拟合:
```python
def on_fitting_requested(self, data_id, method):
    # 直接在主线程执行
    result = run_fit_task(method, x_data, y_data, df)
    self._handle_fit_success(data_id, data, method, x_data, y_data, result)
```

优点: 100%可控,无并发问题
缺点: 拟合期间UI会卡顿

## 📝 测试清单

- [ ] 启动程序后,JobManager.reset_instance() 被调用
- [ ] 导入Excel/JSON文件,生成数据节点(不重复)
- [ ] 右键拟合数据,只执行1次拟合任务
- [ ] 拟合完成后,只生成1个拟合曲线节点
- [ ] 拟合完成后,只生成1个对比图
- [ ] fit_trace.log 中只有1个 `_on_done ENTER`
- [ ] 状态栏显示正确的进度信息
- [ ] 再次拟合同一数据,提示"已锁定"或"冷却中"

## 🚨 如果问题依然存在

请提供以下信息:
1. `fit_trace.log` 完整内容
2. 控制台输出(print语句)
3. 重复拟合的次数和时间间隔
4. Python 版本和 PySide6 版本
5. 是否使用了 Jupyter/IPython/热重载工具

