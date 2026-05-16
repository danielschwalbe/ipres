param([switch]$Clean)

Set-Location $PSScriptRoot

$main = "MehrheitsVerhältniswahl"
$outDir = "dist"

if ($Clean) {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $outDir
    Write-Host "Cleaned."
    return
}

New-Item -ItemType Directory -Force $outDir | Out-Null
pdflatex -interaction=nonstopmode "-output-directory=$outDir" "$main.tex"
pdflatex -interaction=nonstopmode "-output-directory=$outDir" "$main.tex"
