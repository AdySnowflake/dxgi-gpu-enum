#pragma once

#include <stdint.h>
#include <wchar.h>

#if !defined(_WIN32)
#error dxgi_gpu_enum is only supported on Windows.
#endif

#ifdef __cplusplus
#define DXGI_GPU_ENUM_EXTERN_C extern "C"
#else
#define DXGI_GPU_ENUM_EXTERN_C extern
#endif

#if defined(DXGI_GPU_ENUM_BUILD)
#define DXGI_GPU_ENUM_API DXGI_GPU_ENUM_EXTERN_C __declspec(dllexport)
#else
#define DXGI_GPU_ENUM_API DXGI_GPU_ENUM_EXTERN_C __declspec(dllimport)
#endif

#define DXGI_GPU_ENUM_CALL __cdecl

#define DXGI_GPU_ENUM_ABI_VERSION 1u
#define DXGI_GPU_ENUM_ADAPTER_NAME_LENGTH 128u

typedef enum DxgiGpuEnumStatus {
    DXGI_GPU_ENUM_STATUS_OK = 0,
    DXGI_GPU_ENUM_STATUS_INSUFFICIENT_BUFFER = 1,
    DXGI_GPU_ENUM_STATUS_INVALID_ARGUMENT = -1,
    DXGI_GPU_ENUM_STATUS_FACTORY_CREATION_FAILED = -2,
    DXGI_GPU_ENUM_STATUS_ENUMERATION_FAILED = -3,
    DXGI_GPU_ENUM_STATUS_ADAPTER_QUERY_FAILED = -4,
    DXGI_GPU_ENUM_STATUS_INTERNAL_ERROR = -5
} DxgiGpuEnumStatus;

typedef enum DxgiGpuEnumPreference {
    DXGI_GPU_ENUM_PREFERENCE_UNSPECIFIED = 0,
    DXGI_GPU_ENUM_PREFERENCE_MINIMUM_POWER = 1,
    DXGI_GPU_ENUM_PREFERENCE_HIGH_PERFORMANCE = 2
} DxgiGpuEnumPreference;

typedef enum DxgiGpuEnumOptionFlags {
    DXGI_GPU_ENUM_OPTION_INCLUDE_SOFTWARE = 1u << 0,
    DXGI_GPU_ENUM_OPTION_INCLUDE_REMOTE = 1u << 1
} DxgiGpuEnumOptionFlags;

typedef enum DxgiGpuEnumAdapterFlags {
    DXGI_GPU_ENUM_ADAPTER_SOFTWARE = 1u << 0,
    DXGI_GPU_ENUM_ADAPTER_REMOTE = 1u << 1
} DxgiGpuEnumAdapterFlags;

typedef struct DxgiGpuEnumOptionsV1 {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t preference;
    uint32_t flags;
} DxgiGpuEnumOptionsV1;

typedef struct DxgiGpuAdapterInfoV1 {
    uint32_t struct_size;
    uint32_t abi_version;
    wchar_t name[DXGI_GPU_ENUM_ADAPTER_NAME_LENGTH];

    uint32_t enumeration_index;
    uint32_t vendor_id;
    uint32_t device_id;
    uint32_t subsystem_id;
    uint32_t revision;
    uint32_t flags;

    uint64_t dedicated_video_memory;
    uint64_t dedicated_system_memory;
    uint64_t shared_system_memory;

    uint32_t luid_low;
    int32_t luid_high;

    uint64_t reserved[4];
} DxgiGpuAdapterInfoV1;

DXGI_GPU_ENUM_API uint32_t DXGI_GPU_ENUM_CALL DxgiGpuEnumGetAbiVersion(void);
DXGI_GPU_ENUM_API uint32_t DXGI_GPU_ENUM_CALL DxgiGpuEnumGetAdapterInfoSizeV1(void);
DXGI_GPU_ENUM_API int32_t DXGI_GPU_ENUM_CALL DxgiGpuEnumDefaultOptionsV1(
    DxgiGpuEnumOptionsV1* options);
DXGI_GPU_ENUM_API int32_t DXGI_GPU_ENUM_CALL DxgiGpuEnumEnumerateV1(
    const DxgiGpuEnumOptionsV1* options,
    DxgiGpuAdapterInfoV1* adapters,
    uint32_t capacity,
    uint32_t* adapter_count);
DXGI_GPU_ENUM_API const wchar_t* DXGI_GPU_ENUM_CALL DxgiGpuEnumStatusMessage(
    int32_t status);
