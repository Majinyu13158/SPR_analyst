# 🔄 GUI重启指南

## ✅ 代码修复已确认

所有修复都已在代码中：
- ✓ JSON数据合并（Base+Combine+Dissociation = 298点）
- ✓ time_break自动估计（不再硬编码133）
- ✓ model_runner返回完整参数（Rmax, kon, koff, KD）

---

## ⚠️ 问题诊断

您报告的问题：
1. Excel加载后没有生成节点
2. JSON拟合还是直线

**最可能的原因**：GUI还在运行旧代码（修改前的版本）

---

## 🔧 解决步骤

### 步骤1：完全关闭所有Python进程

```bash
# Windows - 在PowerShell或CMD中运行:
taskkill /F /IM python.exe
```

**或者手动关闭**：
1. 按 `Ctrl+Shift+Esc` 打开任务管理器
2. 找到所有 `python.exe` 进程
3. 右键 → 结束任务

### 步骤2：重新启动GUI

```bash
py app_full.py
```

### 步骤3：测试JSON加载

1. **加载JSON文件**：`多循环igg_20240918163627L.json`

2. **检查控制台输出**（关键！）

   **应该看到**：
   ```
   [Data Model] 合并数据点: BaseData + CombineData + DissociationData = 298点
   [Data Model] 时间范围: 0.0 ~ 297.0
   ✅ 构建宽表: 298时间点 × 8浓度
      列名: ['Time', '0.0', '1.0167e-09', ...]
      DataFrame形状: (298, 9)
   ✅ 从JSON加载多浓度数据: 8个样本 → 宽表 (多循环igg (8浓度))
   ```

   **如果看到的是**（旧版本）：
   ```
   ✅ 从JSON加载单样本数据: 15行 → DataFrame
   ```
   → 说明GUI还在运行旧代码！

3. **检查数据树**

   **应该显示**：
   - `多循环igg (8浓度)` ← 正确！

   **如果显示**：
   - `多循环igg` (没有"8浓度") ← 旧版本

### 步骤4：测试拟合

1. **选择JSON数据节点**
2. **分析 → 拟合 → LocalBivariate**
3. **检查控制台**

   **应该看到**：
   ```
   [AutoEstimate] time_break: 142.0 (Y_max at row 142)
   Rmax: 1391.8904
   kon: 1.3934e+05
   koff: 6.6580e-07
   KD: 4.7782e-12
   
   [FittingWrapper] ✅ 拟合成功:
      Rmax=1391.89 RU
      kon=1.3934e+05 1/(M*s)
      koff=6.6580e-07 1/s
      KD=4.7782e-12 M
   ```

4. **检查拟合曲线**

   **应该是**：典型SPR曲线（上升→峰值→下降）
   **不应该是**：直线

### 步骤5：测试Excel加载

1. **文件 → 打开数据**
2. **选择**：`ctla-4测Cad(150KD)-146st0.xlsx`
3. **检查控制台**

   **应该看到**：
   ```
   [Controller] 使用通用方式加载文件
   [load_file] 开始加载Excel文件: ...
   ✅ 数据已添加到DataManager: ID=X, Name=ctla-4测Cad(150KD)-146st0.xlsx, Type=dataframe
   [Controller] 添加数据到树: ctla-4测Cad(150KD)-146st0.xlsx
   ```

4. **检查数据树**

   **应该显示**：新的数据节点 `ctla-4测Cad(150KD)-146st0.xlsx`

---

## 🔍 如果问题仍然存在

### 检查项1：Python模块是否重新加载

运行以下脚本验证：
```bash
py test_current_code.py
```

应该全部显示 `[OK]`

### 检查项2：Excel文件是否损坏

在Python中直接测试：
```python
import pandas as pd
df = pd.read_excel('ctla-4测Cad(150KD)-146st0.xlsx')
print(df.shape)  # 应该是 (424, 7)
print(df.columns)  # 第一列应该是 'Unnamed: 0' 或类似
```

### 检查项3：查看完整日志

启动时使用详细模式：
```bash
py app_full.py > app_log.txt 2>&1
```

然后检查 `app_log.txt` 文件

---

## 📞 如果需要帮助

请提供：
1. 加载JSON后的控制台输出（前20行）
2. 加载Excel后的控制台输出
3. 拟合时的控制台输出
4. 数据树的截图

---

## ✅ 成功标志

- [ ] 控制台显示 "合并数据点: ... = 298点"
- [ ] 数据树显示 "(8浓度)"
- [ ] time_break自动估计为142
- [ ] 拟合参数显示完整（非N/A）
- [ ] 拟合曲线不是直线
- [ ] Excel数据节点正确添加

