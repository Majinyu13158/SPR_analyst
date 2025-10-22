# 智能XY提取与拟合算法兼容性分析

## 📊 问题分析

### 当前数据流：
```
JSON/Excel文件
    ↓
Data对象（dataframe存储）
    ↓
get_xy_data() 智能提取 → (x_data, y_data) numpy数组
    ↓
fit_data(method, x_data, y_data, dataframe=原始dataframe)
    ↓
拟合算法
```

---

## ⚠️ 潜在风险

### 风险1：列选择错误
**问题**：智能XY提取可能选错列

**场景**：
```python
# DataFrame有多个可能的Y列
df = pd.DataFrame({
    'Time': [0, 1, 2],
    'Response': [0.1, 0.2, 0.3],    # 用户想要这个
    'RU': [100, 200, 150],           # 但智能提取可能选这个（优先级更高）
    'Signal': [50, 60, 55]
})

x, y = data.get_xy_data()  # 可能选择了RU而不是Response
```

**影响**：拟合结果不符合用户预期

---

### 风险2：数据被排序
**问题**：`get_xy_data()` 会按X排序数据

**原代码**（data_model.py:350-352）：
```python
order = np.argsort(x_valid)
x_data = x_valid[order]
y_data = y_valid[order]
```

**影响**：
- 如果拟合算法依赖原始数据顺序（如按时间顺序的实验设计），会出错
- DataFrame的行索引与提取后的数据不对应

---

### 风险3：NaN过滤导致长度不一致
**问题**：智能提取会过滤掉NaN值

**原代码**（data_model.py:342-344）：
```python
mask = x_series.notna() & y_series.notna()
x_valid = x_series[mask].to_numpy(dtype=float)
y_valid = y_series[mask].to_numpy(dtype=float)
```

**影响**：
- 提取后的 `(x_data, y_data)` 长度 < DataFrame行数
- 如果拟合算法需要完整数据（包括缺失值标记），会出问题

---

### 风险4：DataFrame格式不匹配
**问题**：原项目拟合算法期望特定格式

**期望格式**（LocalBivariate）：
```python
# 原项目期望：第一列Time + 后续列名为浓度数值
   Time    0.0    10.0   50.0   100.0
0   0      0.1    0.2    0.3    0.4
1   1      0.15   0.25   0.35   0.45
```

**实际格式**（智能提取后）：
```python
# 新项目可能是：
   Time  Response
0   0     0.1
1   1     0.2
```

**影响**：
- `_fit_local_bivariate` 中的格式检查失败（fitting_wrapper.py:102-114）
- 回退到简化版拟合（线性拟合占位符）

---

## ✅ 解决方案建议

### 方案1：增强 `get_xy_data()` 灵活性 ⭐ 推荐

**增加参数控制：**
```python
def get_xy_data(
    self,
    x_col: Optional[str] = None,      # 手动指定X列
    y_col: Optional[str] = None,      # 手动指定Y列
    auto_sort: bool = True,            # 是否自动排序
    drop_na: bool = True,              # 是否删除NaN
    return_indices: bool = False       # 是否返回索引
) -> Union[Tuple[np.ndarray, np.ndarray], 
           Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """
    灵活的XY提取
    
    参数：
        x_col: 指定X列名（None=自动智能选择）
        y_col: 指定Y列名（None=自动智能选择）
        auto_sort: 是否按X排序（默认True）
        drop_na: 是否删除NaN（默认True）
        return_indices: 是否返回对应的原始索引
    
    返回：
        (x_data, y_data) 或 (x_data, y_data, indices)
    """
```

**优点**：
- 向后兼容（默认行为不变）
- 用户可以精确控制
- 适用于绘图和拟合两种场景

---

### 方案2：添加数据验证方法

**新增方法：**
```python
def validate_xy_extraction(self) -> Dict[str, Any]:
    """
    验证智能XY提取的结果
    
    返回：
        {
            'x_col': 'Time',
            'y_col': 'Response',
            'total_points': 100,
            'valid_points': 95,
            'dropped_na': 5,
            'is_sorted': True,
            'warnings': ['存在5个缺失值'],
            'alternatives': {
                'y_candidates': ['RU', 'Signal']  # 其他可选Y列
            }
        }
    """
```

**使用场景：**
```python
# 拟合前先验证
validation = data.validate_xy_extraction()
if validation['warnings']:
    print("警告：", validation['warnings'])
    print("可选Y列：", validation['alternatives']['y_candidates'])
    # 提示用户确认或手动选择
```

---

### 方案3：分离绘图和拟合的数据提取

**设计两个方法：**
```python
# 方法1：用于绘图（当前的智能提取）
def get_xy_data_for_plot(self) -> Tuple[np.ndarray, np.ndarray]:
    """用于绘图：智能提取、排序、过滤NaN"""
    # 当前逻辑
    pass

# 方法2：用于拟合（保持原始结构）
def get_xy_data_for_fitting(
    self, 
    x_col: str = 'Time', 
    y_col: str = 'Response'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    用于拟合：保持原始顺序，可选择是否保留NaN
    """
    df = self.dataframe
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"列不存在: {x_col} 或 {y_col}")
    
    x_data = df[x_col].to_numpy(dtype=float)
    y_data = df[y_col].to_numpy(dtype=float)
    
    # 不排序，保持原始顺序
    return x_data, y_data
```

**优点**：
- 职责分离，意图明确
- 避免绘图和拟合的需求冲突

---

### 方案4：在拟合前添加检查和警告 ⭐ 推荐

**在 `main_controller_full.py` 中：**
```python
def on_fit_data(self, data_id: int, method: str):
    """拟合数据"""
    data = self.data_manager.get_data(data_id)
    
    # ===== 新增：拟合前检查 =====
    try:
        x_data, y_data = data.get_xy_data()
        
        # 检查1：数据点数量
        if len(x_data) < 3:
            self.view.show_warning(
                "数据点过少",
                f"仅有{len(x_data)}个有效数据点，拟合可能不准确"
            )
        
        # 检查2：与原始数据比较
        original_length = len(data.dataframe)
        if len(x_data) < original_length:
            dropped = original_length - len(x_data)
            self.view.show_warning(
                "数据已过滤",
                f"智能XY提取已过滤{dropped}个数据点（NaN或无效值）\n"
                f"原始数据：{original_length}点 → 有效数据：{len(x_data)}点"
            )
        
        # 检查3：列选择提示
        # 调用validate方法获取详细信息
        # ...
        
    except Exception as e:
        self.view.show_error("数据提取失败", str(e))
        return
    
    # 执行拟合（传入dataframe供高级算法使用）
    fit_result = fit_data(method, x_data, y_data, dataframe=data.dataframe)
```

---

### 方案5：为拟合算法添加格式适配器

**在 `fitting_wrapper.py` 中：**
```python
def _prepare_data_for_algorithm(
    self, 
    method: str, 
    x_data, 
    y_data, 
    dataframe=None
) -> Dict[str, Any]:
    """
    根据算法要求准备数据格式
    
    参数：
        method: 拟合方法名
        x_data, y_data: numpy数组
        dataframe: 原始DataFrame（可选）
    
    返回：
        适配后的数据字典
    """
    if method == 'LocalBivariate':
        # LocalBivariate需要特定DataFrame格式
        if dataframe is not None and self._is_valid_bivariate_format(dataframe):
            # 格式符合，使用原始DataFrame
            return {'dataframe': dataframe}
        else:
            # 格式不符，重构DataFrame
            reconstructed_df = pd.DataFrame({
                'Time': x_data,
                '0.0': y_data  # 假设浓度为0
            })
            return {'dataframe': reconstructed_df}
    
    elif method in ['SingleCycle', 'SimpleFit']:
        # 简单算法只需要数组
        return {'x_array': x_data, 'y_array': y_data}
    
    else:
        return {'x_array': x_data, 'y_array': y_data}

def _is_valid_bivariate_format(self, df: pd.DataFrame) -> bool:
    """检查DataFrame是否符合LocalBivariate要求"""
    if len(df.columns) < 2:
        return False
    
    first_col = df.columns[0]
    if first_col not in ['Time', 'time']:
        return False
    
    # 检查后续列名是否为数值
    try:
        [float(str(col)) for col in df.columns[1:]]
        return True
    except (ValueError, TypeError):
        return False
```

---

## 🎯 推荐实施方案（综合）

### 第一阶段：增加灵活性（兼容性修复）

1. **增强 `get_xy_data()` 方法**（方案1）
   - 添加可选参数：`x_col`, `y_col`, `auto_sort`, `drop_na`
   - 保持默认行为不变（向后兼容）

2. **添加 `validate_xy_extraction()` 方法**（方案2）
   - 提供提取结果的详细信息
   - 列出备选列

3. **在拟合前添加检查**（方案4）
   - 数据点数量检查
   - 过滤情况提示
   - 列选择确认

### 第二阶段：长期优化

4. **分离绘图和拟合接口**（方案3）
   - 创建专用方法
   - 文档明确说明

5. **算法格式适配**（方案5）
   - 自动检测和转换数据格式
   - 提供算法要求的文档

---

## 📋 实施清单

- [ ] 修改 `get_xy_data()` 添加参数
- [ ] 新增 `validate_xy_extraction()` 方法
- [ ] 在 Controller 中添加拟合前检查
- [ ] 更新拟合算法调用逻辑
- [ ] 编写测试用例
- [ ] 更新文档

---

## 🧪 测试用例

```python
def test_xy_extraction_compatibility():
    """测试XY提取与拟合的兼容性"""
    
    # 测试1：手动指定列
    df = pd.DataFrame({
        'Time': [0, 1, 2],
        'Response': [0.1, 0.2, 0.3],
        'RU': [100, 200, 150]
    })
    data = Data(item=df, itemtype='dataframe')
    
    # 智能提取（可能选RU）
    x1, y1 = data.get_xy_data()
    
    # 手动指定Response
    x2, y2 = data.get_xy_data(y_col='Response')
    
    assert not np.array_equal(y1, y2)  # 应该不同
    
    # 测试2：保留原始顺序
    df_unsorted = pd.DataFrame({
        'Time': [2, 0, 1],  # 故意乱序
        'Signal': [0.3, 0.1, 0.2]
    })
    data2 = Data(item=df_unsorted, itemtype='dataframe')
    
    x_sorted, y_sorted = data2.get_xy_data(auto_sort=True)
    x_raw, y_raw = data2.get_xy_data(auto_sort=False)
    
    assert np.array_equal(x_sorted, [0, 1, 2])
    assert np.array_equal(x_raw, [2, 0, 1])
    
    # 测试3：NaN处理
    df_with_nan = pd.DataFrame({
        'Time': [0, 1, 2, 3],
        'Value': [0.1, np.nan, 0.3, 0.4]
    })
    data3 = Data(item=df_with_nan, itemtype='dataframe')
    
    x_dropped, y_dropped = data3.get_xy_data(drop_na=True)
    x_kept, y_kept = data3.get_xy_data(drop_na=False)
    
    assert len(x_dropped) == 3
    assert len(x_kept) == 4
```

