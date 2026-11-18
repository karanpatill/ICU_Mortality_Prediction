@echo off
setlocal
echo ==============================================================================
echo [Typst Pipeline] Compiling ICU Mortality Prediction Research Manuscript...
echo ==============================================================================

typst compile main.typ output\research-paper.pdf

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Manuscript compiled successfully to:
    echo           research-paper\output\research-paper.pdf
    echo.
) else (
    echo.
    echo [ERROR] Typst compilation failed with exit code %ERRORLEVEL%.
    echo.
)
endlocal
