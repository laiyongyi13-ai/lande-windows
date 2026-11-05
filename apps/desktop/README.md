# Windows 桌面应用

本目录为 Flutter 界面与 Windows 原生工程。运行时依赖仓库根目录的 `engine/python`、`src`、`scripts`、`models`、数据库 schema，以及 `packages/bhe_core` 和 `packages/bhe_l10n`，请保持目录结构。

Windows 开发与运行步骤见 [根目录说明](../../README.md)。

准备依赖后可在此目录执行 `flutter analyze`、`flutter test`、`flutter run -d windows`。可移植发布包使用根目录 `scripts/build_windows_release.ps1` 构建。
