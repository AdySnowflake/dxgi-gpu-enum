#include "dxgi_gpu_enum.h"

#include <cstddef>
#include <cstring>

#include <dxgi1_6.h>
#include <wrl/client.h>

#pragma comment(lib, "dxgi.lib")

using Microsoft::WRL::ComPtr;

namespace {

constexpr uint32_t kKnownOptionFlags =
    DXGI_GPU_ENUM_OPTION_INCLUDE_SOFTWARE | DXGI_GPU_ENUM_OPTION_INCLUDE_REMOTE;

bool IsValidPreference(uint32_t preference) noexcept {
    return preference == DXGI_GPU_ENUM_PREFERENCE_UNSPECIFIED ||
           preference == DXGI_GPU_ENUM_PREFERENCE_MINIMUM_POWER ||
           preference == DXGI_GPU_ENUM_PREFERENCE_HIGH_PERFORMANCE;
}

DXGI_GPU_PREFERENCE ToDxgiPreference(uint32_t preference) noexcept {
    switch (preference) {
        case DXGI_GPU_ENUM_PREFERENCE_MINIMUM_POWER:
            return DXGI_GPU_PREFERENCE_MINIMUM_POWER;
        case DXGI_GPU_ENUM_PREFERENCE_HIGH_PERFORMANCE:
            return DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE;
        default:
            return DXGI_GPU_PREFERENCE_UNSPECIFIED;
    }
}

bool ShouldInclude(const DXGI_ADAPTER_DESC1& description,
                   uint32_t option_flags) noexcept {
    const auto flags = static_cast<uint32_t>(description.Flags);
    const bool is_software = (flags & DXGI_ADAPTER_FLAG_SOFTWARE) != 0;
    const bool is_remote = (flags & DXGI_ADAPTER_FLAG_REMOTE) != 0;

    if (is_software &&
        (option_flags & DXGI_GPU_ENUM_OPTION_INCLUDE_SOFTWARE) == 0) {
        return false;
    }
    if (is_remote && (option_flags & DXGI_GPU_ENUM_OPTION_INCLUDE_REMOTE) == 0) {
        return false;
    }
    return true;
}

void FillAdapterInfo(const DXGI_ADAPTER_DESC1& description,
                     uint32_t enumeration_index,
                     DxgiGpuAdapterInfoV1* output) noexcept {
    DxgiGpuAdapterInfoV1 info{};
    info.struct_size = sizeof(info);
    info.abi_version = DXGI_GPU_ENUM_ABI_VERSION;
    wcsncpy_s(info.name, description.Description, _TRUNCATE);

    info.enumeration_index = enumeration_index;
    info.vendor_id = description.VendorId;
    info.device_id = description.DeviceId;
    info.subsystem_id = description.SubSysId;
    info.revision = description.Revision;

    const auto dxgi_flags = static_cast<uint32_t>(description.Flags);
    if ((dxgi_flags & DXGI_ADAPTER_FLAG_SOFTWARE) != 0) {
        info.flags |= DXGI_GPU_ENUM_ADAPTER_SOFTWARE;
    }
    if ((dxgi_flags & DXGI_ADAPTER_FLAG_REMOTE) != 0) {
        info.flags |= DXGI_GPU_ENUM_ADAPTER_REMOTE;
    }

    info.dedicated_video_memory =
        static_cast<uint64_t>(description.DedicatedVideoMemory);
    info.dedicated_system_memory =
        static_cast<uint64_t>(description.DedicatedSystemMemory);
    info.shared_system_memory =
        static_cast<uint64_t>(description.SharedSystemMemory);
    info.luid_low = description.AdapterLuid.LowPart;
    info.luid_high = description.AdapterLuid.HighPart;

    std::memcpy(output, &info, sizeof(info));
}

HRESULT GetAdapter(IDXGIFactory1* factory,
                   IDXGIFactory6* factory6,
                   uint32_t preference,
                   uint32_t index,
                   IDXGIAdapter1** adapter) noexcept {
    if (factory6 != nullptr &&
        preference != DXGI_GPU_ENUM_PREFERENCE_UNSPECIFIED) {
        return factory6->EnumAdapterByGpuPreference(
            index,
            ToDxgiPreference(preference),
            IID_PPV_ARGS(adapter));
    }
    return factory->EnumAdapters1(index, adapter);
}

}  // namespace

static_assert(sizeof(wchar_t) == 2,
              "The public ABI requires Windows 16-bit wchar_t.");
static_assert(sizeof(DxgiGpuEnumOptionsV1) == 16);
static_assert(offsetof(DxgiGpuAdapterInfoV1, name) == 8);
static_assert(offsetof(DxgiGpuAdapterInfoV1, dedicated_video_memory) == 288);
static_assert(sizeof(DxgiGpuAdapterInfoV1) == 352);

uint32_t DXGI_GPU_ENUM_CALL DxgiGpuEnumGetAbiVersion(void) {
    return DXGI_GPU_ENUM_ABI_VERSION;
}

uint32_t DXGI_GPU_ENUM_CALL DxgiGpuEnumGetAdapterInfoSizeV1(void) {
    return sizeof(DxgiGpuAdapterInfoV1);
}

int32_t DXGI_GPU_ENUM_CALL DxgiGpuEnumDefaultOptionsV1(
    DxgiGpuEnumOptionsV1* options) {
    if (options == nullptr) {
        return DXGI_GPU_ENUM_STATUS_INVALID_ARGUMENT;
    }

    DxgiGpuEnumOptionsV1 defaults{};
    defaults.struct_size = sizeof(defaults);
    defaults.abi_version = DXGI_GPU_ENUM_ABI_VERSION;
    defaults.preference = DXGI_GPU_ENUM_PREFERENCE_HIGH_PERFORMANCE;
    defaults.flags = 0;
    std::memcpy(options, &defaults, sizeof(defaults));
    return DXGI_GPU_ENUM_STATUS_OK;
}

int32_t DXGI_GPU_ENUM_CALL DxgiGpuEnumEnumerateV1(
    const DxgiGpuEnumOptionsV1* options,
    DxgiGpuAdapterInfoV1* adapters,
    uint32_t capacity,
    uint32_t* adapter_count) {
    if (adapter_count == nullptr ||
        (adapters == nullptr && capacity != 0)) {
        return DXGI_GPU_ENUM_STATUS_INVALID_ARGUMENT;
    }
    *adapter_count = 0;

    DxgiGpuEnumOptionsV1 resolved_options{};
    DxgiGpuEnumDefaultOptionsV1(&resolved_options);
    if (options != nullptr) {
        if (options->struct_size < sizeof(DxgiGpuEnumOptionsV1) ||
            options->abi_version != DXGI_GPU_ENUM_ABI_VERSION ||
            !IsValidPreference(options->preference) ||
            (options->flags & ~kKnownOptionFlags) != 0) {
            return DXGI_GPU_ENUM_STATUS_INVALID_ARGUMENT;
        }
        std::memcpy(&resolved_options, options, sizeof(resolved_options));
    }

    ComPtr<IDXGIFactory1> factory;
    HRESULT result = CreateDXGIFactory1(IID_PPV_ARGS(factory.GetAddressOf()));
    if (FAILED(result)) {
        return DXGI_GPU_ENUM_STATUS_FACTORY_CREATION_FAILED;
    }

    ComPtr<IDXGIFactory6> factory6;
    if (resolved_options.preference != DXGI_GPU_ENUM_PREFERENCE_UNSPECIFIED) {
        // DXGI 1.6 is optional at runtime. Older systems safely fall back to
        // IDXGIFactory1 enumeration order.
        factory.As(&factory6);
    }

    uint32_t matched_count = 0;
    for (uint32_t enumeration_index = 0;; ++enumeration_index) {
        ComPtr<IDXGIAdapter1> adapter;
        result = GetAdapter(factory.Get(),
                            factory6.Get(),
                            resolved_options.preference,
                            enumeration_index,
                            adapter.GetAddressOf());
        if (result == DXGI_ERROR_NOT_FOUND) {
            break;
        }
        if (FAILED(result)) {
            return DXGI_GPU_ENUM_STATUS_ENUMERATION_FAILED;
        }

        DXGI_ADAPTER_DESC1 description{};
        result = adapter->GetDesc1(&description);
        if (FAILED(result)) {
            return DXGI_GPU_ENUM_STATUS_ADAPTER_QUERY_FAILED;
        }
        if (!ShouldInclude(description, resolved_options.flags)) {
            continue;
        }

        if (adapters != nullptr && matched_count < capacity) {
            FillAdapterInfo(description,
                            enumeration_index,
                            &adapters[matched_count]);
        }
        ++matched_count;
    }

    *adapter_count = matched_count;
    if (adapters != nullptr && matched_count > capacity) {
        return DXGI_GPU_ENUM_STATUS_INSUFFICIENT_BUFFER;
    }
    return DXGI_GPU_ENUM_STATUS_OK;
}

const wchar_t* DXGI_GPU_ENUM_CALL DxgiGpuEnumStatusMessage(int32_t status) {
    switch (status) {
        case DXGI_GPU_ENUM_STATUS_OK:
            return L"success";
        case DXGI_GPU_ENUM_STATUS_INSUFFICIENT_BUFFER:
            return L"the output buffer is too small";
        case DXGI_GPU_ENUM_STATUS_INVALID_ARGUMENT:
            return L"an argument or ABI version is invalid";
        case DXGI_GPU_ENUM_STATUS_FACTORY_CREATION_FAILED:
            return L"DXGI factory creation failed";
        case DXGI_GPU_ENUM_STATUS_ENUMERATION_FAILED:
            return L"DXGI adapter enumeration failed";
        case DXGI_GPU_ENUM_STATUS_ADAPTER_QUERY_FAILED:
            return L"DXGI adapter information query failed";
        case DXGI_GPU_ENUM_STATUS_INTERNAL_ERROR:
            return L"an internal error occurred";
        default:
            return L"unknown dxgi_gpu_enum status";
    }
}
