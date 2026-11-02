# Shared tool-path contract: environment variables contain real paths, not ${VAR} strings.
function Resolve-GameToolPath {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [string]$Path = '',
        [string]$Leaf = '',
        [string[]]$Fallback = @()
    )
    $configured = if ($Path) { $Path } else { [Environment]::GetEnvironmentVariable($Name, 'Process') }
    $candidates = if ($configured) { @($configured) } else { $Fallback }
    foreach ($candidate in $candidates) {
        if (-not $candidate) { continue }
        $resolved = [Environment]::ExpandEnvironmentVariables($candidate)
        if ($Leaf -and (Test-Path -LiteralPath $resolved -PathType Container)) {
            $resolved = Join-Path $resolved $Leaf
        }
        if (Test-Path -LiteralPath $resolved) {
            return (Resolve-Path -LiteralPath $resolved).Path
        }
    }
    throw "Tool path $Name is unavailable. Set `$env:$Name to its real path or pass the script's explicit path parameter; .env is not loaded automatically."
}
