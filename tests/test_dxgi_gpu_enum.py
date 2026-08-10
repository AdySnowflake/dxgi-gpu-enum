from __future__ import annotations

import ctypes
import unittest

import dxgi_gpu_enum


class DxgiGpuEnumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.enumerator = dxgi_gpu_enum.DxgiGpuEnumerator()

    def test_abi_layout_matches_native_library(self) -> None:
        self.assertEqual(ctypes.sizeof(dxgi_gpu_enum._DxgiGpuEnumOptionsV1), 16)
        self.assertEqual(ctypes.sizeof(dxgi_gpu_enum._DxgiGpuAdapterInfoV1), 352)
        self.assertEqual(
            self.enumerator._library.DxgiGpuEnumGetAbiVersion(),
            dxgi_gpu_enum.ABI_VERSION,
        )
        self.assertEqual(
            self.enumerator._library.DxgiGpuEnumGetAdapterInfoSizeV1(),
            ctypes.sizeof(dxgi_gpu_enum._DxgiGpuAdapterInfoV1),
        )

    def test_default_enumeration_returns_only_local_hardware(self) -> None:
        adapters = self.enumerator.enumerate()
        self.assertGreater(len(adapters), 0)
        self.assertTrue(all(adapter.name for adapter in adapters))
        self.assertTrue(all(adapter.is_hardware for adapter in adapters))

    def test_software_opt_in_is_a_superset(self) -> None:
        hardware = self.enumerator.enumerate()
        all_local = self.enumerator.enumerate(include_software=True)
        hardware_luids = {adapter.luid for adapter in hardware}
        all_luids = {adapter.luid for adapter in all_local}
        self.assertLessEqual(hardware_luids, all_luids)

    def test_invalid_abi_is_rejected(self) -> None:
        options = dxgi_gpu_enum._DxgiGpuEnumOptionsV1(
            struct_size=ctypes.sizeof(dxgi_gpu_enum._DxgiGpuEnumOptionsV1),
            abi_version=999,
            preference=int(dxgi_gpu_enum.DxgiGpuPreference.HIGH_PERFORMANCE),
            flags=0,
        )
        count = ctypes.c_uint32()
        status = self.enumerator._library.DxgiGpuEnumEnumerateV1(
            ctypes.byref(options), None, 0, ctypes.byref(count)
        )
        self.assertEqual(status, -1)

    def test_capacity_is_honored_without_overwriting_next_record(self) -> None:
        options = self.enumerator._options(
            dxgi_gpu_enum.DxgiGpuPreference.HIGH_PERFORMANCE,
            include_software=True,
            include_remote=True,
        )
        records = (dxgi_gpu_enum._DxgiGpuAdapterInfoV1 * 2)()
        record_size = ctypes.sizeof(dxgi_gpu_enum._DxgiGpuAdapterInfoV1)
        ctypes.memset(ctypes.byref(records[1]), 0xA5, record_size)
        canary_before = ctypes.string_at(ctypes.byref(records[1]), record_size)

        count = ctypes.c_uint32()
        status = self.enumerator._library.DxgiGpuEnumEnumerateV1(
            ctypes.byref(options), records, 1, ctypes.byref(count)
        )

        canary_after = ctypes.string_at(ctypes.byref(records[1]), record_size)
        self.assertEqual(canary_before, canary_after)
        self.assertGreaterEqual(count.value, 1)
        if count.value > 1:
            self.assertEqual(status, dxgi_gpu_enum._STATUS_INSUFFICIENT_BUFFER)
        else:
            self.assertEqual(status, dxgi_gpu_enum._STATUS_OK)


if __name__ == "__main__":
    unittest.main()
