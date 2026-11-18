# Run AURA-ICU Dashboard (PowerShell alternative)
# D. Y. Patil School of Engineering and Management, Kolhapur

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "  ====================================================" -ForegroundColor Cyan
Write-Host "   AURA-ICU: Clinical Decision Support System" -ForegroundColor Cyan
Write-Host "   D. Y. Patil School of Engineering and Management" -ForegroundColor Cyan
Write-Host "   (Deemed-to-be-University), Kolhapur" -ForegroundColor Cyan
Write-Host "  ====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Starting dashboard on http://localhost:8501" -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

Set-Location -Path "D:\ICU_Mortality_Prediction"

streamlit run dashboard\app.py `
    --server.port 8501 `
    --server.headless false `
    --server.fileWatcherType none `
    --browser.gatherUsageStats false
