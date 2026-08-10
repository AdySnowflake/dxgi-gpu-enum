#include <dxgi_gpu_enum.h>

#include <cstdint>
#include <iostream>
#include <vector>

namespace {

int ReportError(int32_t status) {
    std::wcerr << L"dxgi_gpu_enum failed: "
               << DxgiGpuEnumStatusMessage(status) << L'\n';
    return 1;
}

}  // namespace

int main() {
    DxgiGpuEnumOptionsV1 options{};
    int32_t status = DxgiGpuEnumDefaultOptionsV1(&options);
    if (status != DXGI_GPU_ENUM_STATUS_OK) {
        return ReportError(status);
    }

    uint32_t adapter_count = 0;
    status = DxgiGpuEnumEnumerateV1(&options, nullptr, 0, &adapter_count);
    if (status != DXGI_GPU_ENUM_STATUS_OK) {
        return ReportError(status);
    }

    std::vector<DxgiGpuAdapterInfoV1> adapters(adapter_count);
    if (adapter_count != 0) {
        status = DxgiGpuEnumEnumerateV1(
            &options, adapters.data(), adapter_count, &adapter_count);
        if (status != DXGI_GPU_ENUM_STATUS_OK) {
            return ReportError(status);
        }
    }

    for (uint32_t index = 0; index < adapter_count; ++index) {
        std::wcout << L"GPU " << index << L": " << adapters[index].name
                   << L'\n';
    }
    return 0;
}

