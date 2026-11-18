@echo off
setlocal
echo ==============================================================================
echo [Typst Pipeline] Starting Live Watcher Mode...
echo ==============================================================================
echo Watching main.typ, template.typ, and references.bib...
echo Any change will automatically recompile output\research-paper.pdf in real time.
echo Press Ctrl+C to terminate watcher.
echo ==============================================================================

typst watch main.typ output\research-paper.pdf
endlocal
