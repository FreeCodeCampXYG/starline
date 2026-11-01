#requires -Version 7.0
param()

$ErrorActionPreference = "Stop"
$panelRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$distRoot = Join-Path $panelRoot "dist"
$outputRoot = [IO.Path]::GetFullPath((Join-Path $panelRoot "..\outputs\story-companion-panel"))
New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
$zipPath = Join-Path $outputRoot "故事搭子_PID11910_播放器与3D展示_v4.zip"

foreach ($required in @("index.html", "MainPage.html", "app.json")) {
    if (-not (Test-Path -LiteralPath (Join-Path $distRoot $required))) {
        throw "缺少构建文件 $required，请先运行 npm run build。"
    }
}

# 仅封装 Vite 产物；根目录直接放入口，不混入固件、源码、环境配置或 node_modules。
$files = @(Get-ChildItem -LiteralPath $distRoot -Recurse -File)
if ($files | Where-Object { $_.Name -match "^\.env|\.map$|\.(bin|elf)$" -or $_.FullName -match "[\\/]node_modules[\\/]" }) {
    throw "dist 中出现不应发布的文件。"
}

$temporaryZip = Join-Path $outputRoot ("panel-" + [Guid]::NewGuid().ToString("N") + ".zip")
[IO.Compression.ZipFile]::CreateFromDirectory($distRoot, $temporaryZip, [IO.Compression.CompressionLevel]::Optimal, $false)
if ((Get-Item -LiteralPath $temporaryZip).Length -gt 15MB) {
    throw "压缩包超过平台 15 MB 限制：$temporaryZip"
}

$archive = [IO.Compression.ZipFile]::OpenRead($temporaryZip)
try {
    foreach ($required in @("index.html", "MainPage.html", "app.json")) {
        if (-not $archive.GetEntry($required)) { throw "ZIP 顶层缺少 $required" }
    }
    # .NET 解压读取校验每个条目的压缩数据；SHA-256 留给用户核对交付文件。
    foreach ($entry in $archive.Entries) {
        $stream = $entry.Open()
        try { $stream.CopyTo([IO.Stream]::Null) } finally { $stream.Dispose() }
    }
} finally { $archive.Dispose() }
Move-Item -LiteralPath $temporaryZip -Destination $zipPath -Force
$hash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash
[IO.File]::WriteAllText((Join-Path $outputRoot "SHA256-v4.txt"), "$hash  $([IO.Path]::GetFileName($zipPath))`n", [Text.UTF8Encoding]::new($false))
[pscustomobject]@{ Path = $zipPath; Bytes = (Get-Item -LiteralPath $zipPath).Length; Files = $files.Count; SHA256 = $hash } | ConvertTo-Json
