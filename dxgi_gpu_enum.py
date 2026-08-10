"""Safe Python bindings for dxgi_gpu_enum.dll."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import sys
from dataclasses import asdict, dataclass
from enum import IntEnum, IntFlag
from pathlib import Path
from typing import Sequence


ABI_VERSION = 1
ADAPTER_NAME_LENGTH = 128

_STATUS_OK = 0
_STATUS_INSUFFICIENT_BUFFER = 1

_OPTION_INCLUDE_SOFTWARE = 1 << 0
_OPTION_INCLUDE_REMOTE = 1 << 1


class DxgiGpuPreference(IntEnum):
    """Ordering requested from DXGI when DXGI 1.6 is available."""

    UNSPECIFIED = 0
    MINIMUM_POWER = 1
    HIGH_PERFORMANCE = 2


class AdapterFlags(IntFlag):
    NONE = 0
    SOFTWARE = 1 << 0
    REMOTE = 1 << 1


class DxgiGpuEnumError(RuntimeError):
    """Raised when the native enumerator reports an error."""

    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"dxgi_gpu_enum error {status}: {message}")


@dataclass(frozen=True, slots=True)
class DxgiGpuAdapter:
    """A single DXGI graphics adapter."""

    name: str
    enumeration_index: int
    vendor_id: int
    device_id: int
    subsystem_id: int
    revision: int
    flags: AdapterFlags
    dedicated_video_memory: int
    dedicated_system_memory: int
    shared_system_memory: int
    luid_low: int
    luid_high: int

    @property
    def is_software(self) -> bool:
        return bool(self.flags & AdapterFlags.SOFTWARE)

    @property
    def is_remote(self) -> bool:
        return bool(self.flags & AdapterFlags.REMOTE)

    @property
    def is_hardware(self) -> bool:
        return not self.is_software and not self.is_remote

    @property
    def vendor_name(self) -> str:
        return {
            0x1002: "AMD",
            0x10DE: "NVIDIA",
            0x1414: "Microsoft",
            0x8086: "Intel",
        }.get(self.vendor_id, "Unknown")

    @property
    def luid(self) -> str:
        high = self.luid_high & 0xFFFFFFFF
        return f"{high:08X}:{self.luid_low:08X}"

    @property
    def dedicated_video_memory_gib(self) -> float:
        return self.dedicated_video_memory / (1024**3)

    @property
    def shared_system_memory_gib(self) -> float:
        return self.shared_system_memory / (1024**3)

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["flags"] = [
            flag.name.lower()
            for flag in AdapterFlags
            if flag is not AdapterFlags.NONE and flag & self.flags
        ]
        result["vendor_name"] = self.vendor_name
        result["luid"] = self.luid
        result["is_hardware"] = self.is_hardware
        return result


class _DxgiGpuEnumOptionsV1(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("preference", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
    ]


class _DxgiGpuAdapterInfoV1(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("name", ctypes.c_wchar * ADAPTER_NAME_LENGTH),
        ("enumeration_index", ctypes.c_uint32),
        ("vendor_id", ctypes.c_uint32),
        ("device_id", ctypes.c_uint32),
        ("subsystem_id", ctypes.c_uint32),
        ("revision", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("dedicated_video_memory", ctypes.c_uint64),
        ("dedicated_system_memory", ctypes.c_uint64),
        ("shared_system_memory", ctypes.c_uint64),
        ("luid_low", ctypes.c_uint32),
        ("luid_high", ctypes.c_int32),
        ("reserved", ctypes.c_uint64 * 4),
    ]


def _candidate_dll_paths() -> list[Path]:
    module_directory = Path(__file__).resolve().parent
    paths: list[Path] = []

    override = os.environ.get("DXGI_GPU_ENUM_DLL")
    if override:
        paths.append(Path(override))

    paths.extend(
        [
            module_directory / "dxgi_gpu_enum.dll",
            module_directory / "build" / "Release" / "dxgi_gpu_enum.dll",
            module_directory / "build" / "Debug" / "dxgi_gpu_enum.dll",
            Path(sys.executable).resolve().parent / "dxgi_gpu_enum.dll",
        ]
    )

    temporary_bundle = getattr(sys, "_MEIPASS", None)
    if temporary_bundle:
        paths.append(Path(temporary_bundle) / "dxgi_gpu_enum.dll")

    # Keep the error message compact if two candidates resolve to the same path.
    return list(dict.fromkeys(paths))


def _find_dll(explicit_path: str | os.PathLike[str] | None) -> Path:
    if explicit_path is not None:
        path = Path(explicit_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"dxgi_gpu_enum DLL not found: {path}")
        return path

    candidates = _candidate_dll_paths()
    for path in candidates:
        if path.is_file():
            return path
    searched = "\n  ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        "dxgi_gpu_enum.dll was not found. Searched:\n  " + searched
    )


class DxgiGpuEnumerator:
    """Loads the native library and enumerates DXGI adapters safely."""

    def __init__(self, dll_path: str | os.PathLike[str] | None = None):
        if os.name != "nt":
            raise OSError("dxgi_gpu_enum is only available on Windows")

        self.dll_path = _find_dll(dll_path)
        self._library = ctypes.WinDLL(str(self.dll_path))
        self._configure_functions()
        self._verify_abi()

    def _configure_functions(self) -> None:
        library = self._library

        library.DxgiGpuEnumGetAbiVersion.argtypes = []
        library.DxgiGpuEnumGetAbiVersion.restype = ctypes.c_uint32

        library.DxgiGpuEnumGetAdapterInfoSizeV1.argtypes = []
        library.DxgiGpuEnumGetAdapterInfoSizeV1.restype = ctypes.c_uint32

        library.DxgiGpuEnumDefaultOptionsV1.argtypes = [
            ctypes.POINTER(_DxgiGpuEnumOptionsV1)
        ]
        library.DxgiGpuEnumDefaultOptionsV1.restype = ctypes.c_int32

        library.DxgiGpuEnumEnumerateV1.argtypes = [
            ctypes.POINTER(_DxgiGpuEnumOptionsV1),
            ctypes.POINTER(_DxgiGpuAdapterInfoV1),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
        ]
        library.DxgiGpuEnumEnumerateV1.restype = ctypes.c_int32

        library.DxgiGpuEnumStatusMessage.argtypes = [ctypes.c_int32]
        library.DxgiGpuEnumStatusMessage.restype = ctypes.c_wchar_p

    def _verify_abi(self) -> None:
        native_version = self._library.DxgiGpuEnumGetAbiVersion()
        if native_version != ABI_VERSION:
            raise RuntimeError(
                f"Unsupported dxgi_gpu_enum ABI {native_version}; "
                f"Python expects {ABI_VERSION}"
            )

        native_size = self._library.DxgiGpuEnumGetAdapterInfoSizeV1()
        python_size = ctypes.sizeof(_DxgiGpuAdapterInfoV1)
        if native_size != python_size:
            raise RuntimeError(
                "DxgiGpuAdapterInfoV1 layout mismatch: "
                f"DLL={native_size}, Python={python_size}"
            )

    def _raise_for_status(self, status: int) -> None:
        if status == _STATUS_OK:
            return
        message = self._library.DxgiGpuEnumStatusMessage(status)
        raise DxgiGpuEnumError(status, message or "unknown error")

    @staticmethod
    def _options(
        preference: DxgiGpuPreference,
        include_software: bool,
        include_remote: bool,
    ) -> _DxgiGpuEnumOptionsV1:
        flags = 0
        if include_software:
            flags |= _OPTION_INCLUDE_SOFTWARE
        if include_remote:
            flags |= _OPTION_INCLUDE_REMOTE
        return _DxgiGpuEnumOptionsV1(
            struct_size=ctypes.sizeof(_DxgiGpuEnumOptionsV1),
            abi_version=ABI_VERSION,
            preference=int(preference),
            flags=flags,
        )

    def enumerate(
        self,
        *,
        preference: DxgiGpuPreference = DxgiGpuPreference.HIGH_PERFORMANCE,
        include_software: bool = False,
        include_remote: bool = False,
    ) -> list[DxgiGpuAdapter]:
        """Return adapters in the requested DXGI preference order.

        The native call is repeated if a display hot-plug changes the required
        capacity between the count and fill operations.
        """

        try:
            preference = DxgiGpuPreference(preference)
        except ValueError as error:
            raise ValueError(f"invalid GPU preference: {preference}") from error

        options = self._options(
            preference, include_software, include_remote
        )
        required = ctypes.c_uint32()
        status = self._library.DxgiGpuEnumEnumerateV1(
            ctypes.byref(options), None, 0, ctypes.byref(required)
        )
        self._raise_for_status(status)

        for _ in range(4):
            if required.value == 0:
                return []

            records = (_DxgiGpuAdapterInfoV1 * required.value)()
            capacity = required.value
            status = self._library.DxgiGpuEnumEnumerateV1(
                ctypes.byref(options),
                records,
                capacity,
                ctypes.byref(required),
            )
            if status == _STATUS_INSUFFICIENT_BUFFER:
                continue
            self._raise_for_status(status)
            if required.value > capacity:
                raise RuntimeError(
                    "dxgi_gpu_enum returned a count larger than the supplied buffer"
                )
            return [self._convert(records[index]) for index in range(required.value)]

        raise RuntimeError("GPU adapter list kept changing during enumeration")

    @staticmethod
    def _convert(record: _DxgiGpuAdapterInfoV1) -> DxgiGpuAdapter:
        if record.abi_version != ABI_VERSION:
            raise RuntimeError(
                f"Unexpected adapter record ABI {record.abi_version}"
            )
        if record.struct_size != ctypes.sizeof(_DxgiGpuAdapterInfoV1):
            raise RuntimeError(
                f"Unexpected adapter record size {record.struct_size}"
            )
        return DxgiGpuAdapter(
            name=record.name,
            enumeration_index=record.enumeration_index,
            vendor_id=record.vendor_id,
            device_id=record.device_id,
            subsystem_id=record.subsystem_id,
            revision=record.revision,
            flags=AdapterFlags(record.flags),
            dedicated_video_memory=record.dedicated_video_memory,
            dedicated_system_memory=record.dedicated_system_memory,
            shared_system_memory=record.shared_system_memory,
            luid_low=record.luid_low,
            luid_high=record.luid_high,
        )


def enumerate_gpus(
    *,
    preference: DxgiGpuPreference = DxgiGpuPreference.HIGH_PERFORMANCE,
    include_software: bool = False,
    include_remote: bool = False,
    dll_path: str | os.PathLike[str] | None = None,
) -> list[DxgiGpuAdapter]:
    """Convenience function for one-shot enumeration."""

    return DxgiGpuEnumerator(dll_path).enumerate(
        preference=preference,
        include_software=include_software,
        include_remote=include_remote,
    )


def _format_bytes(value: int) -> str:
    return f"{value / (1024**3):.2f} GiB"


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Enumerate Windows DXGI graphics adapters."
    )
    parser.add_argument(
        "--preference",
        choices=("high-performance", "minimum-power", "unspecified"),
        default="high-performance",
        help="DXGI adapter ordering (default: high-performance)",
    )
    parser.add_argument(
        "--include-software",
        action="store_true",
        help="include software adapters such as Microsoft Basic Render Driver",
    )
    parser.add_argument(
        "--include-remote",
        action="store_true",
        help="include remote display adapters",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--dll", type=Path, help="explicit DLL path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_argument_parser().parse_args(argv)
    preferences = {
        "high-performance": DxgiGpuPreference.HIGH_PERFORMANCE,
        "minimum-power": DxgiGpuPreference.MINIMUM_POWER,
        "unspecified": DxgiGpuPreference.UNSPECIFIED,
    }

    try:
        adapters = enumerate_gpus(
            preference=preferences[arguments.preference],
            include_software=arguments.include_software,
            include_remote=arguments.include_remote,
            dll_path=arguments.dll,
        )
    except (FileNotFoundError, OSError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if arguments.json:
        print(
            json.dumps(
                [adapter.to_dict() for adapter in adapters],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if not adapters:
        print("No matching GPU adapters found.")
        return 0

    for position, adapter in enumerate(adapters):
        kinds = []
        if adapter.is_software:
            kinds.append("software")
        if adapter.is_remote:
            kinds.append("remote")
        kind = ", ".join(kinds) if kinds else "hardware"
        print(f"GPU {position}: {adapter.name} [{kind}]")
        print(
            f"  Vendor/Device: {adapter.vendor_name} "
            f"{adapter.vendor_id:04X}:{adapter.device_id:04X}"
        )
        print(
            "  Memory: dedicated "
            f"{_format_bytes(adapter.dedicated_video_memory)}, "
            f"shared {_format_bytes(adapter.shared_system_memory)}"
        )
        print(f"  LUID: {adapter.luid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
