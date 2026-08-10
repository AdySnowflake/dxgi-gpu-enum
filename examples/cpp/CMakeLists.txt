cmake_minimum_required(VERSION 3.25)

project(dxgi_gpu_enum_example LANGUAGES CXX)

find_package(dxgi_gpu_enum 1 CONFIG REQUIRED)

add_executable(dxgi_gpu_enum_example main.cpp)
target_compile_features(dxgi_gpu_enum_example PRIVATE cxx_std_20)
target_link_libraries(
    dxgi_gpu_enum_example
    PRIVATE dxgi_gpu_enum::dxgi_gpu_enum
)

add_custom_command(
    TARGET dxgi_gpu_enum_example
    POST_BUILD
    COMMAND
        "${CMAKE_COMMAND}" -E copy_if_different
        "$<TARGET_FILE:dxgi_gpu_enum::dxgi_gpu_enum>"
        "$<TARGET_FILE_DIR:dxgi_gpu_enum_example>"
    VERBATIM
)

