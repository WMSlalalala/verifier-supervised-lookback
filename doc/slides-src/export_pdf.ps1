param([string]$In, [string]$Out)
$ErrorActionPreference = 'Stop'
$ppt = New-Object -ComObject PowerPoint.Application
try {
    $pres = $ppt.Presentations.Open($In, $true, $false, $false)
    $pres.SaveAs($Out, 32)
    $pres.Close()
} finally {
    $ppt.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null
}
Write-Output "exported $Out"
