# SPR Analysis 部署清单

## ✅ 打包前准备

- [x] 移除系列控件
- [x] 检查所有功能正常运行
- [x] 清理测试文件
- [x] 优化导入（移除未使用的库）
- [x] 配置PyInstaller spec文件
- [x] 排除PyQt5冲突

## ✅ 打包过程

### 1. 环境准备
```bash
.venv\Scripts\activate
pip install pyinstaller
```

### 2. 清理旧文件
```bash
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
```

### 3. 执行打包
```bash
pyinstaller build_exe.spec --noconfirm
```

### 4. 验证结果
```bash
Test-Path dist\SPR_Analysis.exe
Get-Item dist\SPR_Analysis.exe
```

## 📦 打包配置

### 包含的模块
- ✅ PySide6 (Qt框架)
- ✅ pyqtgraph (高性能绘图)
- ✅ numpy (数值计算)
- ✅ pandas (数据处理)
- ✅ scipy (科学计算)
- ✅ openpyxl (Excel支持)
- ✅ qfluentwidgets (UI美化)
- ✅ 所有 src 模块

### 排除的模块
- ❌ matplotlib (已弃用)
- ❌ PyQt5/PyQt6 (冲突)
- ❌ tkinter (未使用)
- ❌ IPython/jupyter (开发工具)

### 打包选项
- **模式**: 单文件 (onefile)
- **控制台**: 无 (console=False)
- **压缩**: UPX
- **图标**: 无（可后续添加）

## 🧪 测试清单

### 在开发环境测试
- [x] 导入数据（Excel, CSV, JSON）
- [x] 数据拟合
- [x] 批量拟合
- [x] 图表导出
- [x] 数据导出
- [x] 数据对比
- [x] 血缘图查看
- [x] 撤销/重做
- [x] 搜索功能
- [x] 样式编辑

### 在目标环境测试（无Python）
- [ ] 程序启动
- [ ] 导入数据
- [ ] 数据拟合
- [ ] 图表显示
- [ ] 导出功能
- [ ] 保存/加载会话
- [ ] 所有快捷键
- [ ] 右键菜单

## 📋 分发文件清单

### 必需文件
```
dist/
  ├── SPR_Analysis.exe   (主程序)
  └── README.txt         (使用说明)
```

### 可选文件
```
exports/                 (导出目录，可预创建)
sessions/                (会话保存目录)
```

## 📄 分发文档

### README.txt 内容
- [x] 快速开始
- [x] 主要功能
- [x] 快捷键列表
- [x] 注意事项
- [x] 系统要求
- [x] 技术支持

### 用户手册（可选）
- [ ] 详细功能说明
- [ ] 截图示例
- [ ] 常见问题FAQ
- [ ] 故障排除

## 🚀 分发方式

### 方式1: 直接分发
1. 将 `dist\SPR_Analysis.exe` 发送给用户
2. 附带 `README.txt`
3. 用户双击运行

### 方式2: 压缩包
```bash
# 创建压缩包
Compress-Archive -Path dist\SPR_Analysis.exe, dist\README.txt -DestinationPath SPR_Analysis_v1.0.zip
```

### 方式3: 安装程序（可选）
- 使用 NSIS 或 Inno Setup
- 创建开始菜单快捷方式
- 注册文件关联 (.sprx)

## ⚠️ 注意事项

### 文件大小
- 预计大小: 100-200 MB
- 首次启动较慢（解压临时文件）
- 后续启动正常

### 系统要求
- Windows 10/11 (64-bit)
- 最低2GB内存
- 100MB磁盘空间

### 已知限制
- 不支持Windows 7/8
- 需要.NET Framework（通常已预装）
- 杀毒软件可能误报（需添加白名单）

## 🔍 故障排除

### 问题1: 无法启动
- 检查是否被杀毒软件拦截
- 右键"以管理员身份运行"
- 查看Windows事件查看器

### 问题2: 缺少DLL
- 安装 Visual C++ Redistributable
- 重新打包（检查excludes配置）

### 问题3: 功能异常
- 检查数据文件格式
- 查看日志文件（如果有）
- 联系技术支持

## 📊 版本信息

- **版本号**: 1.0
- **构建日期**: 2025-01-23
- **Python版本**: 3.12.4
- **PySide6版本**: 6.8+
- **打包工具**: PyInstaller 6.10.0

## ✅ 发布前最终检查

- [ ] 可执行文件生成成功
- [ ] 文件大小合理
- [ ] 在干净环境测试通过
- [ ] 文档齐全
- [ ] 版本号正确
- [ ] 无敏感信息（密码/密钥）
- [ ] 无调试代码（print/console）
- [ ] 准备技术支持渠道

---

**当前状态**: 打包中...
**预计完成时间**: 3-5分钟
**输出位置**: `dist\SPR_Analysis.exe`

