$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

# 说明：保留旧产物再覆盖更安全，因此输出到 dist2；如需全新目录请手工删除 dist/dist2。
Write-Host "== 打包 exe =="
& $python -m PyInstaller mingpan.spec --noconfirm --workpath build2 --distpath dist2
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$exe = Get-ChildItem -Path .\dist2 -Filter *.exe | Select-Object -First 1
if (-not $exe) {
    Write-Error "没有找到生成的 exe"
}

$desktop = [Environment]::GetFolderPath("Desktop")
$target = Join-Path $desktop $exe.Name
Copy-Item $exe.FullName $target -Force

Write-Host "== 完成 =="
Write-Host "产物: $($exe.FullName)"
Write-Host "已复制到桌面: $target"
