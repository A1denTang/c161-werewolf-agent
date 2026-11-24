# Install the SDK and the pinned local model on a Windows x64 machine.
$ErrorActionPreference = 'Stop'
$runtime = Join-Path $PSScriptRoot '.runtime'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null

function Get-VerifiedFile([string]$Url, [string]$File, [string]$Hash) {
    if ((Test-Path -LiteralPath $File) -and ((Get-FileHash -LiteralPath $File).Hash -eq $Hash)) {
        return
    }
    $partial = "$File.part"
    & curl.exe --fail --location --retry 2 --output $partial $Url
    if ($LASTEXITCODE -ne 0) { throw "Download failed for $File" }
    if ((Get-FileHash -LiteralPath $partial).Hash -ne $Hash) { throw "Checksum mismatch for $File" }
    Move-Item -Force -LiteralPath $partial -Destination $File
}

$archive = Join-Path $runtime 'llama-b12635.zip'
Get-VerifiedFile 'https://github.com/ggml-org/llama.cpp/releases/download/b12635/llama-b12635-bin-win-vulkan-x64.zip' $archive 'f2249334614c44e1222616754616a401c1d5ee460830868b1891166c455cb142'
Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $runtime 'llama-b12635') -Force
Get-VerifiedFile 'https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/7dabda4d13d513e3e842b20f0d435c732f172cbe/qwen2.5-3b-instruct-q4_k_m.gguf?download=true' (Join-Path $runtime 'qwen2.5-3b-q4.gguf') '626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d'

$agentPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $agentPython)) {
    & python -m venv (Join-Path $PSScriptRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 or newer is required.' }
}
Push-Location -LiteralPath $PSScriptRoot
try {
    & $agentPython -m pip install -e '.[dev]'
    if ($LASTEXITCODE -ne 0) { throw 'SDK installation failed.' }
} finally {
    Pop-Location
}
