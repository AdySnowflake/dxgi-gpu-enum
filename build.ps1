[CmdletBinding()]
param(
    [ValidateSet("Release", "Debug")]
    [string]$Configuration = "Release"
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$projectRoot = $PSScriptRoot
$sourceFile = Join-Path $projectRoot "native\dxgi_gpu_enum.cpp"
$outputDirectory = Join-Path $projectRoot "build\$Configuration"
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

$vswhere = Join-Path ${env:ProgramFiles(x86)} `
    "Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path $vswhere)) {
    throw "Visual Studio Installer (vswhere.exe) was not found."
}

$visualStudio = & $vswhere `
    -latest `
    -products * `
    -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
    -property installationPath
if (-not $visualStudio) {
    throw "Visual Studio C++ Build Tools were not found."
}

$developerCommand = Join-Path $visualStudio "Common7\Tools\VsDevCmd.bat"
if (-not (Test-Path $developerCommand)) {
    throw "VsDevCmd.bat was not found under $visualStudio."
}

$compilerArguments = @(
    "/nologo",
    "/LD",
    "/std:c++20",
    "/utf-8",
    "/permissive-",
    "/W4",
    "/WX",
    "/EHsc",
    "/Zc:wchar_t",
    "/Zc:__cplusplus",
    "/DUNICODE",
    "/D_UNICODE",
    "/DWIN32_LEAN_AND_MEAN",
    "/DNOMINMAX",
    "/DDXGI_GPU_ENUM_BUILD",
    "/guard:cf",
    "/Fo:$outputDirectory\dxgi_gpu_enum.obj",
    "/Fd:$outputDirectory\dxgi_gpu_enum.pdb",
    $sourceFile
)

$linkerArguments = @(
    "/link",
    "/NOLOGO",
    "/DLL",
    "/DYNAMICBASE",
    "/HIGHENTROPYVA",
    "/NXCOMPAT",
    "/guard:cf",
    "/OUT:$outputDirectory\dxgi_gpu_enum.dll",
    "/IMPLIB:$outputDirectory\dxgi_gpu_enum.lib",
    "/PDB:$outputDirectory\dxgi_gpu_enum.pdb",
    "dxgi.lib"
)

if ($Configuration -eq "Release") {
    $compilerArguments += @("/O2", "/Oi", "/GL", "/Gy", "/Gw", "/MT")
    $linkerArguments += @("/LTCG", "/OPT:REF", "/OPT:ICF", "/Brepro")
} else {
    $compilerArguments += @("/Od", "/Zi", "/MTd")
    $linkerArguments += @("/DEBUG")
}

function ConvertTo-CmdArgument {
    param([Parameter(Mandatory)][string]$Value)
    return '"' + $Value.Replace('"', '\"') + '"'
}

$allArguments = @($compilerArguments + $linkerArguments) |
    ForEach-Object { ConvertTo-CmdArgument $_ }
$command = "call `"$developerCommand`" -no_logo -arch=amd64 " +
    "-host_arch=amd64 && cl.exe " + ($allArguments -join " ")

& $env:ComSpec /d /s /c $command
if ($LASTEXITCODE -ne 0) {
    throw "MSVC build failed with exit code $LASTEXITCODE."
}

$dllPath = Join-Path $outputDirectory "dxgi_gpu_enum.dll"
if (-not (Test-Path $dllPath)) {
    throw "The compiler completed without producing $dllPath."
}

Write-Host "Built $dllPath"
