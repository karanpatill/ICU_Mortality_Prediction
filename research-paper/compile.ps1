# PowerShell compilation script for Typst research paper
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "[Typst Pipeline] Compiling ICU Mortality Prediction Research Manuscript..." -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan

$process = Start-Process typst -ArgumentList "compile main.typ output\research-paper.pdf" -NoNewWindow -PassThru -Wait

if ($process.ExitCode -eq 0) {
    Write-Host "`n[SUCCESS] Manuscript compiled successfully to research-paper\output\research-paper.pdf`n" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Typst compilation failed with exit code $($process.ExitCode)`n" -ForegroundColor Red
}
