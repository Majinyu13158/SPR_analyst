# SPR Analysis 打包说明

## 快速打包

### 方法1: 使用批处理脚本（推荐）

```bash
build.bat
```

这会自动完成所有步骤，生成 `dist\SPR_Analysis.exe`

---

### 方法2: 手动打包

#### 步骤1: 激活虚拟环境
```bash
.venv\Scripts\activate
```

#### 步骤2: 安装 PyInstaller
```bash
pip install pyinstaller
```

#### 步骤3: 打包
```bash
pyinstaller build_exe.spec
```

#### 步骤4: 查找可执行文件
```
dist\SPR_Analysis.exe
```

---

## 打包配置

### 包含的文件
- ✅ 所有Python源代码
- ✅ 所有依赖库（PySide6, pyqtgraph, numpy, pandas, scipy, openpyxl等）
- ✅ 应用图标 (icon.png)

### 排除的文件
- ❌ matplotlib（已不使用）
- ❌ tkinter
- ❌ Jupyter相关

---

## 打包选项说明

- **单文件模式**: 所有内容打包到一个exe文件中
- **无控制台**: 运行时不显示黑色控制台窗口
- **UPX压缩**: 减小文件大小
- **应用图标**: 使用 icon.png 作为程序图标

---

## 打包后测试

1. 将 `dist\SPR_Analysis.exe` 复制到另一台没有Python环境的电脑
2. 双击运行
3. 测试核心功能：
   - 导入数据文件
   - 数据拟合
   - 图表导出
   - 数据对比
   - 样式编辑

---

## 常见问题

### Q: 打包后文件很大？
A: 单文件打包会包含所有依赖，大小通常在100-200MB左右，这是正常的。

### Q: 运行时提示缺少DLL？
A: 确保在Windows上打包，并且使用了正确的Python版本（建议Python 3.9+）。

### Q: 打包失败？
A: 
1. 检查是否在虚拟环境中
2. 确保所有依赖都已安装
3. 查看错误日志

### Q: 如何减小文件大小？
A: 可以修改 `build_exe.spec`，排除更多不需要的库。

---

## 分发

将 `dist\SPR_Analysis.exe` 分发给用户即可，无需额外安装Python或依赖库。

**注意**: 首次运行可能需要几秒钟时间解压临时文件。

