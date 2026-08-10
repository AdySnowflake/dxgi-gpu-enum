# dxgi_gpu_enum

[![Build](https://github.com/AdySnowflake/dxgi-gpu-enum/actions/workflows/build.yml/badge.svg)](https://github.com/AdySnowflake/dxgi-gpu-enum/actions/workflows/build.yml)

面向 Windows x64 的现代 DXGI 显卡枚举库，提供稳定的原生 C ABI 和类型安全的
Python `ctypes` 封装。

## 功能

- 在支持 DXGI 1.6 的系统上使用 `EnumAdapterByGpuPreference`。
- 默认按高性能偏好排序，并排除软件、远程适配器。
- 返回名称、硬件 ID、显存、共享内存、LUID 和适配器类型。
- 版本化 C ABI，结构大小在编译期和运行时双重校验。
- 两阶段缓冲区 API，容量不足时绝不越界写入。
- `ComPtr` 管理 COM 生命周期，每个 DXGI 调用均检查错误。
- Release 构建启用 LTO、ASLR、DEP、Control Flow Guard，并静态链接 MSVC Runtime。

## 环境要求

- Windows 10/11 x64
- Visual Studio C++ Build Tools
- CMake 3.25+
- Ninja
- Python 3.10+（运行 Python API 和测试时需要）

Visual Studio 自带的 CMake 与 Ninja 可以使用。执行下列命令前，请先初始化 MSVC
x64 开发环境，并确认 `cl.exe`、`cmake` 和 `ninja` 均可在当前终端中直接运行。

## 快速开始

在任意已配置好 MSVC、CMake 和 Ninja 的终端中执行：

```bash
cmake --workflow --preset windows-release
python list_gpus.py
```

输出示例：

```text
GPU 0: NVIDIA GeForce RTX 3050 OEM
GPU 1: Intel(R) UHD Graphics 770
```

构建输出：

```text
build/windows-release/bin/dxgi_gpu_enum.dll
```

安装输出：

```text
dist/windows-release/
├── bin/dxgi_gpu_enum.dll
├── include/dxgi_gpu_enum.h
└── lib/
    ├── dxgi_gpu_enum.lib
    └── cmake/dxgi_gpu_enum/...
```

## 标准 CMake 工作流

在已经配置好 MSVC、CMake 和 Ninja 的终端中执行：

```bash
cmake --preset windows-release
cmake --build --preset windows-release
ctest --preset windows-release
cmake --install build/windows-release
```

也可以一次完成配置、构建和测试：

```bash
cmake --workflow --preset windows-release
```

Debug 对应的 Preset 名称为 `windows-debug`。

## CI 工件

手动触发 GitHub Actions 工作流时，它会构建并测试 Windows x64 Release，然后上传
名为 `dxgi_gpu_enum-windows-x64-release` 的工件。工件内容与
`dist/windows-release` 安装树一致，包含 DLL、公开头文件、导入库和 CMake 包配置；
工作流不会创建 GitHub Release 或 Tag。

## Python API

```python
from dxgi_gpu_enum import DxgiGpuEnumerator

enumerator = DxgiGpuEnumerator()
for number, gpu in enumerate(enumerator.enumerate()):
    print(number, gpu.name)
```

简单的一次性调用：

```python
from dxgi_gpu_enum import enumerate_gpus

for number, gpu in enumerate(enumerate_gpus()):
    print(f"GPU {number}: {gpu.name}")
```

默认只返回本地硬件适配器。包含软件适配器：

```python
adapters = enumerator.enumerate(include_software=True)
```

命令行支持普通文本和 JSON：

```bash
python dxgi_gpu_enum.py
python dxgi_gpu_enum.py --include-software
python dxgi_gpu_enum.py --json
```

可通过 `DXGI_GPU_ENUM_DLL` 环境变量或 `DxgiGpuEnumerator(dll_path=...)` 指定 DLL。

## C/C++ API

公开头文件为 `native/dxgi_gpu_enum.h`。主要入口：

```c
int32_t DxgiGpuEnumEnumerateV1(
    const DxgiGpuEnumOptionsV1* options,
    DxgiGpuAdapterInfoV1* adapters,
    uint32_t capacity,
    uint32_t* adapter_count);
```

传入 `adapters = NULL, capacity = 0` 查询所需数量。容量不足时函数返回
`DXGI_GPU_ENUM_STATUS_INSUFFICIENT_BUFFER`，并在 `adapter_count` 中提供新的所需数量。

安装后，其他 CMake 项目可以直接使用导出的包：

```cmake
find_package(dxgi_gpu_enum 1 CONFIG REQUIRED)
target_link_libraries(my_app PRIVATE dxgi_gpu_enum::dxgi_gpu_enum)
```

完整消费示例位于 `examples/cpp`。

## 测试

```bash
ctest --preset windows-release
```

CTest 会执行 Python ABI/边界测试和 CLI 实机枚举。测试覆盖：

- C/Python ABI 布局一致性
- 本地硬件枚举与软件适配器过滤
- 非法 ABI 拒绝
- 容量不足和 canary 越界保护
- 简单调用程序端到端执行

## 项目结构

```text
cmake/                 CMake 包配置模板
examples/              Python 与已安装 C++ 消费示例
native/                DLL 源码和公开 C ABI
tests/                 Python/原生边界测试
CMakeLists.txt         唯一构建规则来源
CMakePresets.json      Debug/Release 配置、构建和测试 Presets
dxgi_gpu_enum.py       Python API 与 CLI
list_gpus.py           最简调用示例
```
