# 篮得剪 · Windows 桌面版

基于 Basketball Highlight Editor 优化的篮球进球视频剪辑工具。本仓库内容仅用于 Windows 桌面版开发，包含界面、Python 分析引擎、共用组件和必要模型。

## 下载使用

无需配置开发环境的用户，请从 [Windows 发布版本](https://github.com/laiyongyi13-ai/lande-windows/releases/tag/windows-2026-11-05) 下载 `Lande-Windows-x64-2026-11-05.zip`，完整解压后打开 `BHE/BHE.exe`。

Code → Download ZIP 下载的是源码，需要准备开发环境，不是可直接运行的程序包。

## 源码目录

- `apps/desktop/`：Flutter 界面、Windows 工程、资源和界面测试。
- `packages/bhe_core/`、`packages/bhe_l10n/`：桌面版依赖的领域模型和多语言资源。
- `engine/python/`、`src/`、`scripts/`：视频分析、审核、导出和 Windows 构建工具。
- `models/`：识别模型；`docs/architecture/SQLITE_SCHEMA_V1.sql`：项目数据库结构。
- `tests/`：Python 引擎与共用工具测试。

不包含网页版、移动端应用、macOS 工程、Rust 移动端运行时、网站、私人视频、用户数据、依赖环境或编译产物。共用代码可能保留平台兼容分支；`scripts/export_mobile_model.py` 虽然带 mobile 字样，Windows DirectML 模型转换也会调用它，因此保留。

## Windows 开发

需要 Python 3.12、Flutter（Dart >= 3.12.2）、Visual Studio 的“使用 C++ 的桌面开发”组件、Windows SDK、FFmpeg/FFprobe，并开启 Windows 开发人员模式。

在仓库根目录的 PowerShell 中执行（先准备上述工具）：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
$env:BHE_REPO_ROOT = (Get-Location).Path
$env:BHE_PYTHON = Join-Path $env:BHE_REPO_ROOT '.venv\Scripts\python.exe'
# 将 ffmpeg.exe 和 ffprobe.exe 放入仓库 bin 目录，或加入 PATH。
Set-Location apps/desktop
flutter pub get
flutter run -d windows
```

可选 DirectML 依赖见 `requirements-dml.txt`。自动环境准备脚本为 `scripts/setup_windows.ps1`，运行前请阅读其安装行为。

## 构建发布包

`scripts/build_windows_release.ps1` 会编译 Windows 界面并准备运行时。使用前需准备已安装 Python 依赖的便携 Python 目录，以及 FFmpeg/FFprobe；参数见脚本开头。普通虚拟环境不能替代可携带的 Python 发行版。

## 来源与许可

原项目：[fly7632785/basketball-highlight-editor](https://github.com/fly7632785/basketball-highlight-editor)。保留原项目 `LICENSE` 与 `NOTICE`；第三方软件和模型的说明见 `docs/THIRD_PARTY_NOTICES.md` 与 `docs/MODEL_AND_DATA_LICENSES.md`。
