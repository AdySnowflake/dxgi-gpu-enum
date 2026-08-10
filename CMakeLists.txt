cmake_minimum_required(VERSION 3.25)

project(
    dxgi_gpu_enum
    VERSION 1.0.0
    DESCRIPTION "Safe DXGI graphics adapter enumeration for Windows"
    LANGUAGES CXX
)

if(NOT WIN32)
    message(FATAL_ERROR "dxgi_gpu_enum only supports Windows")
endif()

include(CTest)
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

add_library(dxgi_gpu_enum SHARED)
add_library(dxgi_gpu_enum::dxgi_gpu_enum ALIAS dxgi_gpu_enum)

target_sources(
    dxgi_gpu_enum
    PRIVATE
        native/dxgi_gpu_enum.cpp
    PUBLIC
        FILE_SET public_headers
        TYPE HEADERS
        BASE_DIRS native
        FILES native/dxgi_gpu_enum.h
)

target_compile_features(dxgi_gpu_enum PRIVATE cxx_std_20)
target_compile_definitions(
    dxgi_gpu_enum
    PRIVATE
        DXGI_GPU_ENUM_BUILD
        UNICODE
        _UNICODE
        WIN32_LEAN_AND_MEAN
        NOMINMAX
)
target_link_libraries(dxgi_gpu_enum PRIVATE dxgi)

set_target_properties(
    dxgi_gpu_enum
    PROPERTIES
        CXX_EXTENSIONS OFF
        RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
        ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
        LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
        MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>"
        INTERPROCEDURAL_OPTIMIZATION_RELEASE ON
)

if(MSVC)
    target_compile_options(
        dxgi_gpu_enum
        PRIVATE
            /W4
            /WX
            /utf-8
            /permissive-
            /guard:cf
            /Zc:wchar_t
            /Zc:__cplusplus
    )
    target_link_options(
        dxgi_gpu_enum
        PRIVATE
            /DYNAMICBASE
            /HIGHENTROPYVA
            /NXCOMPAT
            /guard:cf
            $<$<CONFIG:Release>:/Brepro>
    )
endif()

if(BUILD_TESTING)
    find_package(Python3 3.10 REQUIRED COMPONENTS Interpreter)

    add_test(
        NAME dxgi_gpu_enum.python
        COMMAND
            "${Python3_EXECUTABLE}"
            -m unittest discover
            -s "${CMAKE_CURRENT_SOURCE_DIR}/tests"
            -v
    )
    add_test(
        NAME dxgi_gpu_enum.cli
        COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/list_gpus.py"
    )
    set_tests_properties(
        dxgi_gpu_enum.python
        dxgi_gpu_enum.cli
        PROPERTIES
            WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
            ENVIRONMENT "DXGI_GPU_ENUM_DLL=$<TARGET_FILE:dxgi_gpu_enum>"
    )
endif()

set(dxgi_gpu_enum_cmake_directory
    "${CMAKE_INSTALL_LIBDIR}/cmake/dxgi_gpu_enum")

configure_package_config_file(
    cmake/dxgi_gpu_enumConfig.cmake.in
    "${CMAKE_CURRENT_BINARY_DIR}/dxgi_gpu_enumConfig.cmake"
    INSTALL_DESTINATION "${dxgi_gpu_enum_cmake_directory}"
)
write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/dxgi_gpu_enumConfigVersion.cmake"
    VERSION "${PROJECT_VERSION}"
    COMPATIBILITY SameMajorVersion
)

install(
    TARGETS dxgi_gpu_enum
    EXPORT dxgi_gpu_enumTargets
    RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}"
    LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}"
    ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}"
    FILE_SET public_headers DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}"
)
install(
    EXPORT dxgi_gpu_enumTargets
    FILE dxgi_gpu_enumTargets.cmake
    NAMESPACE dxgi_gpu_enum::
    DESTINATION "${dxgi_gpu_enum_cmake_directory}"
)
install(
    FILES
        "${CMAKE_CURRENT_BINARY_DIR}/dxgi_gpu_enumConfig.cmake"
        "${CMAKE_CURRENT_BINARY_DIR}/dxgi_gpu_enumConfigVersion.cmake"
    DESTINATION "${dxgi_gpu_enum_cmake_directory}"
)

