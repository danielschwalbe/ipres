param([switch]$Clean)

# Windows PowerShell 5.1 uses the OEM code page for native exe arguments.
# Switching to the ANSI code page (Windows-1252 on Western EU) makes pdflatex
# receive the ä as 0xE4, which matches what NTFS returns for the file lookup.
$OutputEncoding = [System.Text.Encoding]::GetEncoding(1252)
[Console]::OutputEncoding = [System.Text.Encoding]::GetEncoding(1252)

$main = "MehrheitsVerhältniswahl"

if ($Clean) {
    Remove-Item -ErrorAction SilentlyContinue *.aux, *.log, *.toc, *.out, *.synctex.gz
    Write-Host "Cleaned build artifacts."
    return
}

pdflatex -interaction=nonstopmode "$main.tex"
pdflatex -interaction=nonstopmode "$main.tex"
