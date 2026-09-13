# EMCテストレポート作成資料アプリ を Windows 用 exe としてビルドするスクリプト。
#
# 使い方:
#   .\build_exe.ps1
#
# 出力先: dist\EmcReportTool\EmcReportTool.exe
# 配布時はこの dist\EmcReportTool フォルダごとコピーする（exe単体では動かない）。

$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
Set-Location $root

Write-Host "既存のビルド成果物を削除します..."
Remove-Item -Recurse -Force "$root\build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$root\dist" -ErrorAction SilentlyContinue

Write-Host "PyInstallerでビルドします..."
& "$root\.venv\Scripts\pyinstaller.exe" "$root\emc_report_tool.spec" --noconfirm
if ($LASTEXITCODE -ne 0) {
    throw "PyInstallerのビルドに失敗しました。"
}

Write-Host "Wordテンプレートフォルダをコピーします..."
Copy-Item -Recurse -Force "$root\テンプレート" "$root\dist\EmcReportTool\テンプレート"

Write-Host ""
Write-Host "ビルド完了: $root\dist\EmcReportTool\EmcReportTool.exe"
Write-Host "配布する場合は dist\EmcReportTool フォルダ全体をコピーしてください。"
