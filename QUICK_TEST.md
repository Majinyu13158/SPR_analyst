# 快速测试 - Excel数据拟合

## 立即测试

```bash
# 1. 启动GUI
py app_full.py

# 2. 在GUI中：
#    - 文件 → 打开数据 → ctla-4测Cad(150KD)-146st0.xlsx
#    - 分析 → 拟合
#    - 数据源：选择已加载的Excel数据
#    - 方法：LocalBivariate
#    - 点击"确定"

# 3. 查看结果：
#    - 控制台应显示：Rmax, kon, koff, KD参数
#    - 结果对话框应显示参数（非N/A）
#    - 拟合曲线应该拟合良好（R²≈0.99）
```

## 预期结果

```
time_break: 140.0 (自动估计)

Rmax: 126.9734 RU
kon: 3.3815e+05 1/(M*s)
koff: 1.7456e-04 1/s
KD: 5.1623e-10 M

R²: 0.9908 ✅
```

## 如果遇到问题

查看详细指南：`docs/Excel数据拟合测试指南.md`

