param([switch]$Clean)

Set-Location $PSScriptRoot

$mains = @("MehrheitsVerhältniswahl", "ÄnderungenImVerfassungsgefüge")
$outDir = "dist"

if ($Clean) {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $outDir
    Write-Host "Cleaned."
    return
}

New-Item -ItemType Directory -Force $outDir | Out-Null
foreach ($main in $mains) {
    pdflatex -interaction=nonstopmode "-output-directory=$outDir" "$main.tex"
    pdflatex -interaction=nonstopmode "-output-directory=$outDir" "$main.tex"
}
