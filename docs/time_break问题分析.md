# time_break硬编码问题分析

## 问题根源

**拟合结果是直线的真正原因**：

在 `model_data_process/LocalBivariate.py` 第117行：
```python
time_break = 133  # 硬编码！
```

这个`time_break`是**SPR实验的结合-解离分割时间点**，对拟合结果影响巨大！

---

## SPR实验原理

SPR实验分为两个阶段：
1. **结合阶段** (0 → time_break)：配体与受体结合，信号上升
2. **解离阶段** (time_break → end)：配体解离，信号下降

拟合模型（第48-70行）：
```python
def model_local_in_one(..., Time0):  # Time0就是time_break
    # 判断时间段
    T_flag_diss = (T_array > Time0)  # 解离
    T_flag_ass = (T_array <= Time0)  # 结合
    
    # 分段计算
    Y = YatTime0 * exp(-koff*(T-Time0)) * T_flag_diss  # 解离
      + Eq * (1-exp(-Kob*T)) * T_flag_ass             # 结合
```

**如果time_break设置错误**：
- 数据点全部被当作结合阶段或解离阶段
- 模型退化为单指数函数
- 拟合结果接近直线或不合理

---

## 正确的time_break来源

### JSON中的参数

```json
{
  "CalculateDataList": [{
    "CombineStartIndex": 0,
    "CombineEndIndex": 200,      ← 结合阶段结束（应该是time_break）
    "DissociationEndIndex": 400  ← 解离阶段结束
  }]
}
```

### Data对象中的attributes

```python
data.attributes['calculatedatalist_combineendindex']  # 应该使用这个值！
```

---

## 修复方案

### 方案1：从Data对象获取time_break ✅ 推荐

```python
# 在fitting_wrapper中
data_obj = kwargs.get('data_obj', None)
time_break = None

if data_obj and hasattr(data_obj, 'attributes'):
    combine_end = data_obj.attributes.get('calculatedatalist_combineendindex')
    if combine_end is not None and combine_end > 0:
        time_break = float(combine_end)
    else:
        # 回退：从XValue数据估计
        time_break = estimate_time_break_from_data(x_data, y_data)
```

### 方案2：从数据自动估计

```python
def estimate_time_break_from_data(x_data, y_data):
    """
    从数据估计time_break：
    - 找到Y值的最大值位置
    - 或者检测Y值开始下降的点
    """
    max_idx = np.argmax(y_data)
    return float(x_data[max_idx])
```

### 方案3：修改model_runner接受参数

创建一个wrapper：
```python
def model_runner_with_params(filename, time_break=None):
    # 读取Excel
    df = pd.read_excel(filename)
    
    # 如果没有提供time_break，估计一个
    if time_break is None:
        time_break = 133  # 默认值
    
    # 调用核心拟合逻辑（复制model_runner的代码）
    ...
```

---

## 当前实现状态

已实现：
- ✅ Controller传递data_obj给fit_data
- ✅ fitting_wrapper从data_obj提取time_break

待实现：
- ⚠️ 需要一种方法将time_break传递给model_runner
- ⚠️ 或者实现estimate_time_break_from_data作为回退

---

## 临时解决方案

在调用model_runner之前，可以：

1. **检查Data的attributes**，打印time_break值
2. **如果为None或0**，从数据估计
3. **创建修改版的LocalBivariate脚本**，接受time_break参数

---

## 测试检查点

运行拟合时应该看到：
```
[FittingWrapper] ✅ 从Data获取time_break=200.0
[FittingWrapper] DataFrame是单样本格式，需要转换为宽表
[FittingWrapper] ✅ 单样本已转换为宽表: ['Time', '0.0']
```

**如果time_break=None或0**：
```
[FittingWrapper] ⚠️ CombineEndIndex=None，将使用默认值
```
→ 这种情况下拟合仍然会用硬编码的133，可能不正确！

---

## 建议

1. **立即检查**：打印data.attributes看CombineEndIndex的实际值
2. **如果值正确**：需要修改model_runner使其接受time_break参数
3. **如果值为None**：需要从数据估计或让用户设置

