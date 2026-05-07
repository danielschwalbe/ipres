param([switch]$Clean)

$main = "MehrheitsVerhältniswahl"

if ($Clean) {
    Remove-Item -ErrorAction SilentlyContinue *.aux, *.log, *.toc, *.out, *.synctex.gz
    Write-Host "Cleaned build artifacts."
    return
}

pdflatex -interaction=nonstopmode "$main.tex"
pdflatex -interaction=nonstopmode "$main.tex"
