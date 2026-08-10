# Repository Agent Instructions

本文件适用于整个仓库。

## WSL

- 文件阅读、搜索、修改和普通轻量操作在 WSL 中完成。
- 所有 Git 操作都在 WSL 中完成，包括提交、分支、合并和远程同步。
- 使用 WSL 中的 Git 配置、身份、凭据和签名。

## Windows PowerShell

- 安装依赖、运行项目、测试、检查、构建和打包必须在 Windows 上执行。
- Python、uv、pytest、pnpm、npm、Node.js、Cargo、Rust、Tauri、FFmpeg 等项目
  命令，统一由 WSL 调用 `pwsh.exe` 执行。
- PowerShell 中使用当前仓库的实际 Windows 路径，不得使用 `/mnt/c/...` 路径。
  实际调用时直接写入该路径；本文档不记录特定设备上的路径。
- Windows 命令不可用或执行失败时，直接报告，不得改用 WSL 版本。

通用调用方式：

```bash
pwsh.exe -NoLogo -NoProfile -WorkingDirectory "<仓库的 Windows 路径>" -Command '$ErrorActionPreference = "Stop"; $PSNativeCommandUseErrorActionPreference = $true; <command>'
```
