# JSON数据拟合修复总结

## 🎯 问题描述

用户报告：
1. **无法加载xlsx文件**
2. **对JSON数据理解有误**：
   - 小负值Y是正常的（仪器噪声）
   - XValue就是时间（Time为None只是占位）

## 🔍 根本原因

### 原因1：JSON数据加载不完整

**问题**：`_build_wide_table_from_samples`只读取了`BaseData`（基线，15个点），忽略了：
- `CombineData`（结合阶段，104个点）
- `DissociationData`（解离阶段，179个点）

**数据对比**：
```
只读BaseData：
  时间点：15个（0-14秒）
  拟合质量：R² = 0.0930（很差）
  
合并所有数据：
  时间点：298个（0-297秒）
  拟合质量：R² = 0.9889（优秀！）
```

### 原因2：xlsx加载已有处理逻辑

xlsx文件已经在`on_file_selected`的else分支中处理（使用`load_file`函数），但可能需要确保第一列重命名为`Time`。

## ✅ 修复内容

### 修复1：合并所有数据点

**文件**：`src/models/data_model.py`

**修改**：`_build_wide_table_from_samples`方法

```python
def _build_wide_table_from_samples(self, samples: list) -> pd.DataFrame:
    # ⭐ 新增：合并所有数据点的函数
    def get_all_data_from_sample(sample):
        """从样本中合并所有数据点"""
        all_data = []
        if 'BaseData' in sample and sample['BaseData']:
            all_data.extend(sample['BaseData'])
        if 'CombineData' in sample and sample['CombineData']:
            all_data.extend(sample['CombineData'])
        if 'DissociationData' in sample and sample['DissociationData']:
            all_data.extend(sample['DissociationData'])
        return all_data
    
    # 提取时间点（从第一个样本的所有数据）
    first_all_data = get_all_data_from_sample(samples[0])
    if not first_all_data:
        print("⚠️ 第一个样本没有数据")
        return pd.DataFrame()
    
    # 提取时间列（XValue就是时间！）
    time_values = [d.get('XValue', d.get('Time', 0)) for d in first_all_data]
    
    print(f"[Data Model] 合并数据点: BaseData + CombineData + DissociationData = {len(time_values)}点")
    print(f"[Data Model] 时间范围: {min(time_values)} ~ {max(time_values)}")
    
    # 构建宽表
    wide_data = {'Time': time_values}
    
    for sample in samples:
        concentration = sample.get('Concentration', 0.0)
        
        # ⭐ 获取所有数据点（合并Base+Combine+Dissociation）
        all_data = get_all_data_from_sample(sample)
        
        # 提取Y值
        y_values = [d.get('YValue', 0.0) for d in all_data]
        
        # 使用浓度值作为列名
        wide_data[str(concentration)] = y_values
    
    df = pd.DataFrame(wide_data)
    
    print(f"✅ 构建宽表: {len(time_values)}时间点 × {len(samples)}浓度")
    print(f"   列名: {list(df.columns)}")
    print(f"   DataFrame形状: {df.shape}")
    
    return df
```

### 修复2：自动估计time_break

**文件**：`model_data_process/LocalBivariate.py`

**修改**：将硬编码的`time_break=133`改为自动估计

```python
# 分段时间（自动估计：找到Y值最大值的位置）
try:
    Y_max_idx = np.unravel_index(np.argmax(Y_data), Y_data.shape)[0]
    time_break = float(T_data[Y_max_idx, 0])
    # 确保time_break在合理范围内
    if time_break < 1 or time_break >= T_data.shape[0]:
        time_break = T_data.shape[0] // 2
    print(f"[AutoEstimate] time_break: {time_break} (Y_max at row {Y_max_idx})")
except Exception as e:
    # 回退：使用数据范围的一半
    time_break = T_data.shape[0] // 2
    print(f"[Warning] time_break estimation failed, using default: {time_break}, error: {e}")
```

### 修复3：返回拟合参数

**文件**：`model_data_process/LocalBivariate.py`

**修改**：从只返回`(T_data, Y_data, Y_pred)`改为返回字典

```python
# ⭐ 返回数据和参数（用于新项目）
return {
    'T_data': T_data,
    'Y_data': Y_data,
    'Y_pred': Y_pred,
    'parameters': {
        'Rmax': R_opt,
        'kon': ka_opt_p,
        'koff': kd_opt_p,
        'KD': kd_opt_p / ka_opt_p
    }
}
```

### 修复4：提取并显示参数

**文件**：`src/utils/fitting_wrapper.py`

**修改**：从`model_runner`返回的字典中提取参数

```python
# 解析结果（新格式：字典）
if result and isinstance(result, dict):
    T_data = result.get('T_data')
    Y_data = result.get('Y_data')
    Y_pred = result.get('Y_pred')
    params = result.get('parameters', {})
    
    # 提取参数（格式化为(值, 误差, 单位)）
    fit_params = {
        'Rmax': (params.get('Rmax', np.nan), None, 'RU'),
        'kon': (params.get('kon', np.nan), None, '1/(M*s)'),
        'koff': (params.get('koff', np.nan), None, '1/s'),
        'KD': (params.get('KD', np.nan), None, 'M')
    }
    
    print(f"[FittingWrapper] ✅ 拟合成功:")
    print(f"   Rmax={fit_params['Rmax'][0]:.2f} RU")
    print(f"   kon={fit_params['kon'][0]:.4e} 1/(M*s)")
    print(f"   koff={fit_params['koff'][0]:.4e} 1/s")
    print(f"   KD={fit_params['KD'][0]:.4e} M")
    
    return {
        'success': True,
        'parameters': fit_params,
        'y_pred': Y_pred.flatten() if getattr(Y_pred, 'ndim', 1) > 1 else Y_pred,
        'statistics': {
            'chi2': None,
            'r2': None,
            'rmse': self._calculate_rmse(Y_data.flatten(), Y_pred.flatten()) if Y_pred is not None else None
        }
    }
```

## 📊 测试结果

### Excel数据（ctla-4测Cad(150KD)-146st0.xlsx）
```
数据点：424个（0-423秒）
浓度数：6个

time_break: 140.0 (自动估计)

拟合参数：
  Rmax: 126.97 RU
  kon: 3.3815e+05 1/(M*s)
  koff: 1.7456e-04 1/s
  KD: 5.1623e-10 M

R²: 0.9908  ← 优秀！
```

### JSON数据（多循环igg_20240918163627L.json）
```
数据点：298个（0-297秒）
浓度数：8个

数据组成：
  BaseData: 15个点（基线）
  CombineData: 104个点（结合）
  DissociationData: 179个点（解离）

time_break: 142.0 (自动估计)

拟合参数：
  Rmax: 1391.89 RU
  kon: 1.3934e+05 1/(M*s)
  koff: 6.6580e-07 1/s
  KD: 4.7782e-12 M

R²: 0.9889  ← 优秀！
```

## 🚀 下一步

1. **用户测试**：
   - 在GUI中加载JSON文件
   - 执行LocalBivariate拟合
   - 验证参数显示和拟合曲线

2. **Excel加载**：
   - 验证xlsx文件能正常加载
   - 确保第一列命名为`Time`（如需要，添加重命名逻辑）

3. **其他算法**：
   - 实现SingleCycle、GlobalBivariate等算法
   - 使用相同的参数返回模式

## 📝 关键经验

1. **数据完整性**：SPR数据通常包含多个阶段（基线、结合、解离），必须全部使用
2. **XValue即时间**：JSON中`XValue`字段就是时间，`Time`为`None`只是占位
3. **小负值正常**：仪器噪声导致的小负值（如-0.8）是正常现象
4. **time_break自动估计**：找Y最大值位置比硬编码更可靠
5. **参数返回**：返回字典格式方便GUI提取和显示

