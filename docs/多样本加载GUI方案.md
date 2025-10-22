# 多样本加载GUI实现方案

## ✅ 已实现（核心功能）

### 1. 自动检测多样本并构建宽表

**代码位置**：`src/models/data_model.py` 第140-153行

**功能**：
- 自动检测JSON中的样本数量
- 如果`len(samples) > 1`：自动构建宽表
- 如果`len(samples) == 1`：保持原有逻辑

**示例输出**：
```
✅ 从JSON加载多浓度数据: 8个样本 → 宽表 (多循环igg (8浓度))
✅ 构建宽表: 15时间点 × 8浓度
   列名: ['Time', '0.0', '1.0167e-09', '2.0833e-09', '4.1667e-09', 
          '8.3333e-09', '1.6667e-08', '3.3333e-08', '6.6667e-08']
```

### 2. `_build_wide_table_from_samples`方法

**代码位置**：`src/models/data_model.py` 第167-224行

**功能**：
- 提取所有样本的Time和YValue
- 使用Concentration作为列名
- 自动检查数据点对齐
- 返回标准宽表DataFrame

**数据格式**：
```
Time | 0.0      | 1.02e-09 | 2.08e-09 | ... | 6.67e-08
0.0  | -0.43    | -0.46    | ...      | ... | ...
1.0  | -0.62    | -0.70    | ...      | ... | ...
2.0  | -0.32    | -0.37    | ...      | ... | ...
...
```

### 3. 修复fitting_wrapper的格式检查

**代码位置**：`src/utils/fitting_wrapper.py` 第114-138行

**修改**：
- 移除了错误的"单样本转宽表"逻辑（浓度=0的bug）
- 简化为只检查宽表格式
- 清晰的错误提示

---

## 🎨 GUI显示方案

### 方案A：数据列表显示（当前建议） ✅

**效果**：
```
┌────────────────────────────────────────┐
│ 数据管理                                │
├────────────────────────────────────────┤
│ [📊] 多循环igg (8浓度)                  │ ← 单个条目
│      15个时间点                         │
│      浓度范围: 0 ~ 6.67e-08 M           │
└────────────────────────────────────────┘
```

**优点**：
- 用户体验简单
- 一次加载，一次拟合
- 符合科研习惯

**需要修改的GUI组件**：
1. **数据列表** (`project_tree.py` 或类似)：
   - 显示数据名称时，如果名称包含"(Nconc)"，使用不同的图标
   - 在tooltip中显示详细信息（浓度列表、时间点数等）

2. **数据预览** (新增或增强现有)：
   - 点击数据时，显示宽表的预览
   - 可选：绘制所有浓度曲线（多条线，不同颜色）

### 方案B：树状展开显示（可选）

**效果**：
```
┌────────────────────────────────────────┐
│ [+] 多循环igg (8浓度)                   │ ← 可展开
│ │   ├─ 0.0 M                            │
│ │   ├─ 1.02e-09 M                       │
│ │   ├─ 2.08e-09 M                       │
│ │   └─ ...                              │
└────────────────────────────────────────┘
```

**优点**：
- 可以查看各浓度明细
- 可选择性加载部分浓度

**缺点**：
- 实现复杂
- 对于标准SPR实验，几乎不需要

---

## 🔄 拟合流程（已修复）

### 当前流程：

```
1. 用户选择数据 → 点击"拟合"
   ↓
2. Controller.on_fit_data
   - 获取Data对象
   - 检查dataframe是否是宽表格式 ✅
   ↓
3. FittingWrapper._fit_local_bivariate
   - DataFrame格式检查（Time + 浓度列） ✅
   - 保存为临时Excel
   ↓
4. LocalBivariate.model_runner
   - 读取Excel → 宽表 (n_time × n_concentration)
   - 同时拟合所有浓度曲线 ✅
   - 返回 (T_data, Y_data, Y_pred)，都是 (n_time × n_concentration) 的二维数组
   ↓
5. 返回Controller
   - Y_pred.flatten() → 一维数组
   - 创建拟合曲线Data对象
```

### 关键修复：

✅ **修复1**：自动构建宽表（浓度>0）  
✅ **修复2**：移除错误的单样本转换逻辑  
✅ **修复3**：使用原始model_runner（time_break=133硬编码）  

---

## 📊 绘图增强（建议）

### 1. 多浓度曲线预览

在数据加载后，自动绘制所有浓度的原始曲线：

```python
# figure_model.py 或 canvas_widget.py
def plot_multiconcentration_data(self, data: Data):
    """绘制多浓度数据的所有曲线"""
    df = data.dataframe
    cols = df.columns
    
    if len(cols) >= 2:
        time_col = cols[0]
        conc_cols = cols[1:]
        
        for conc in conc_cols:
            self.ax.plot(df[time_col], df[conc], 
                        label=f'{conc} M', alpha=0.7)
        
        self.ax.legend()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Response (RU)')
        self.ax.set_title(data.name)
```

### 2. 拟合对比图

拟合完成后，显示：
- 原始数据（多条彩色线）
- 拟合曲线（多条虚线）
- 参数标注（Rmax, kon, koff, KD）

---

## 🧪 测试清单

### 测试1：加载多浓度JSON

```bash
py app_full.py
→ 打开文件 → 选择 "多循环igg_20240918163627L.json"
→ 检查数据列表是否显示 "多循环igg (8浓度)"
→ 检查控制台输出是否包含 "✅ 构建宽表: 15时间点 × 8浓度"
```

### 测试2：拟合多浓度数据

```bash
→ 选中数据 → 右键 → "拟合"
→ 选择方法 "LocalBivariate"
→ 检查控制台输出:
   [FittingWrapper] ✅ DataFrame是宽表格式
   时间列: Time
   浓度列: [0.0, 1.0167e-09, 2.0833e-09, ...]
   Rmax: XX.XXXX
   kon: X.XXXXe+XX
   koff: X.XXXXe+XX
→ 检查拟合曲线是否不再是直线/零线
```

### 测试3：查看拟合结果

```bash
→ 检查结果列表是否显示 "多循环igg (8浓度) - LocalBivariate"
→ 点击结果 → 查看参数（Rmax, kon, koff）
→ 检查拟合曲线图
```

---

## 🎯 下一步行动

### 立即测试（阶段1）

1. ✅ 运行 `py app_full.py`
2. ✅ 加载多循环JSON
3. ✅ 执行LocalBivariate拟合
4. ✅ 验证拟合结果不再是零线/直线

### 功能完善（阶段2）

1. 🔲 添加多浓度曲线预览
2. 🔲 在数据列表显示浓度范围
3. 🔲 改进拟合结果图表（多曲线对比）

### 高级功能（阶段3）

1. 🔲 树状展开查看各浓度
2. 🔲 批量加载多个JSON
3. 🔲 实验分组管理

---

## 📝 关键代码片段

### 检测宽表格式（fitting_wrapper.py）

```python
# 第119-138行
if len(df.columns) >= 2:
    first_col = df.columns[0]
    if first_col in ['Time', 'time', 'XValue', 'X']:
        other_cols = df.columns[1:]
        try:
            concentrations = [float(str(col)) for col in other_cols]
            is_valid_format = True
            print(f"[FittingWrapper] ✅ DataFrame是宽表格式")
            print(f"   浓度列: {concentrations}")
        except:
            is_valid_format = False
```

### 构建宽表（data_model.py）

```python
# 第167-224行
def _build_wide_table_from_samples(self, samples: list):
    time_values = [d.get('XValue') for d in samples[0]['BaseData']]
    wide_data = {'Time': time_values}
    
    for sample in samples:
        concentration = sample['Concentration']
        y_values = [d.get('YValue') for d in sample['BaseData']]
        wide_data[str(concentration)] = y_values
    
    return pd.DataFrame(wide_data)
```

---

## 🎉 预期效果

修复后，您应该看到：

1. **加载时**：
   ```
   ✅ 从JSON加载多浓度数据: 8个样本 → 宽表 (多循环igg (8浓度))
   ✅ 构建宽表: 15时间点 × 8浓度
   ```

2. **拟合时**：
   ```
   [FittingWrapper] ✅ DataFrame是宽表格式
   Rmax: 45.2340
   kon: 1.2345e+05
   koff: 2.3456e-03
   KD: 1.9012e-08
   ```

3. **拟合曲线**：不再是零线/直线，而是符合SPR动力学的多条曲线！

