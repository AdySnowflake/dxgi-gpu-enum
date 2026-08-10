# dxgi_gpu_enum

一个面向 Windows x64 的现代 DXGI 显卡枚举器。项目由一个原生 C++ DLL 和一个
类型安全的 Python `ctypes` 封装组成。

原生构建产物名为 `dxgi_gpu_enum.dll`。

## 特点

- 在支持 DXGI 1.6 的系统上使用 `EnumAdapterByGpuPreference`，默认按高性能偏好排序。
- 默认排除软件适配器和远程适配器，可显式选择包含它们。
- 返回名称、硬件 ID、显存、共享内存、LUID 和适配器类型。
- C ABI 带版本和结构大小校验，未来可通过新增 V2 接口扩展。
- 采用先查询数量、再填充缓冲区的调用方式，且原生层始终遵守容量上限。
- COM 对象由 `ComPtr` 自动管理，每个 DXGI 调用都检查返回值。
- Release 构建启用优化、LTCG、ASLR、DEP 和 Control Flow Guard，并静态链接
  MSVC 运行库。

## 环境要求

- Windows 10 或 Windows 11，x64
- Python 3.10 或更新版本（仅 Python 调用时需要）
- Visual Studio C++ Build Tools（仅从源码构建时需要）

不要求预先安装 CMake。构建脚本通过 `vswhere.exe` 自动寻找 MSVC。

## 构建

在 Windows PowerShell 中执行：

```powershell
.\build.ps1 -Configuration Release
```

输出位于：

```text
build\Release\dxgi_gpu_enum.dll
```

Debug 构建：

```powershell
.\build.ps1 -Configuration Debug
```

## 使用

```python
from dxgi_gpu_enum import DxgiGpuEnumerator

enumerator = DxgiGpuEnumerator()
for gpu in enumerator.enumerate():
    print(gpu.name, gpu.dedicated_video_memory_gib, gpu.luid)
```

默认结果只包含本地硬件适配器，并按高性能偏好排序。包含软件适配器：

```python
adapters = enumerator.enumerate(include_software=True)
```

命令行输出：

```powershell
python .\dxgi_gpu_enum.py
python .\dxgi_gpu_enum.py --include-software
python .\dxgi_gpu_enum.py --json
```

也可以通过 `DXGI_GPU_ENUM_DLL` 环境变量或 `DxgiGpuEnumerator(dll_path=...)` 指定 DLL。

## C ABI

公开声明位于 `native/dxgi_gpu_enum.h`。主要入口是：

```c
int32_t DxgiGpuEnumEnumerateV1(
    const DxgiGpuEnumOptionsV1* options,
    DxgiGpuAdapterInfoV1* adapters,
    uint32_t capacity,
    uint32_t* adapter_count);
```

传入 `adapters = NULL, capacity = 0` 可查询所需数量。填充调用中如果容量不足，
函数返回 `DXGI_GPU_ENUM_STATUS_INSUFFICIENT_BUFFER`，在 `adapter_count` 中提供新的所需
数量，并且绝不会写出给定容量。

## 测试

先构建 Release DLL，然后在 Windows PowerShell 中执行：

```powershell
python -m unittest discover -s tests -v
```

测试覆盖 ABI 布局、真实硬件枚举、软件适配器过滤、错误 ABI，以及原生缓冲区
边界的 canary 检查。
