# PowerShell continuous live watcher script for Typst research paper
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "[Typst Pipeline] Starting Live Watcher Mode..." -ForegroundColor Cyan
Write-Host "Watching main.typ, template.typ, and references.bib..." -ForegroundColor Yellow
Write-Host "Any saved change will automatically recompile output\research-paper.pdf." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to terminate watcher." -ForegroundColor Yellow
Write-Host "==============================================================================" -ForegroundColor Cyan

typst watch main.typ output\research-paper.pdf
