param(
    [switch]$Connect,
    [switch]$ImportKey,
    [switch]$List,
    [switch]$AllGroups,
    [string[]]$Chat,
    [string]$Account,
    [string]$SelfId,
    [double]$Hours = 24,
    [int]$Timeout = 300
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw '未找到项目 Python 环境，请先运行 python scripts/bootstrap.py。'
}
if (($Connect -and $ImportKey) -or ($Chat -and $AllGroups)) { throw '连接模式或会话范围不能同时指定。' }
if ($List -and ($Connect -or $ImportKey -or $Chat -or $AllGroups)) { throw '-List 必须单独使用。' }
$taskArguments = @('-X', 'utf8', (Join-Path $PSScriptRoot 'local-reader.py'))
if ($Connect) { $taskArguments += @('--connect', '--timeout', [string]$Timeout) }
elseif ($ImportKey) { $taskArguments += '--import-key' }
elseif ($AllGroups) { $taskArguments += @('--all-groups', '--hours', [string]$Hours) }
elseif ($Chat) {
    foreach ($taskChatName in $Chat) { $taskArguments += @('--chat', $taskChatName) }
    $taskArguments += @('--hours', [string]$Hours)
} else { $taskArguments += '--list' }
if ($Account) { $taskArguments += @('--account', $Account) }
if ($SelfId) { $taskArguments += @('--self-id', $SelfId) }
Push-Location -LiteralPath $taskRoot
try {
    & $taskPython @taskArguments
    if ($LASTEXITCODE -ne 0) { throw '微信读取未完成，请根据上面的具体错误处理。' }
} finally { Pop-Location }
