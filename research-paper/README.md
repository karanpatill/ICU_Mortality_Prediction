# ICU Mortality Prediction — Scientific Research Paper Pipeline (Typst)

This directory provides an automated, publication-grade typesetting pipeline for the research paper:
> **Dynamic Mortality Risk Prediction in Mechanically Ventilated Intensive Care Patients via Targeted Laboratory Staleness: A Multi-Center Landmark Study on MIMIC-IV**

---

## 📁 Directory Architecture

```
research-paper/
├── template.typ        # Reusable scientific paper design system (DeepMind/Nature-grade)
├── main.typ            # Manuscript source file (structure, text, tables, figures)
├── references.bib      # Authenticated BibTeX bibliography (16+ clinical & ML citations)
├── figures/            # High-resolution vector and raster figures
│   ├── Figure1_Staleness_Performance_Curves.png
│   └── Figure2_MIMICIV_External_Validation.png
├── output/             # Compiled PDF and page preview exports
│   └── research-paper.pdf
├── compile.bat         # 1-click batch compilation script
├── watch.bat           # 1-click continuous recompilation watcher
├── compile.ps1         # PowerShell compilation script
├── watch.ps1           # PowerShell live watcher script
└── README.md           # Pipeline documentation
```

---

## ⚡ Quick Commands

### 1. Compile PDF
From terminal or command prompt:
```bash
typst compile main.typ output/research-paper.pdf
```
Or simply double-click `compile.bat` (or run `./compile.ps1` in PowerShell).

### 2. Live Recompilation (Watch Mode)
For real-time editing with instant preview:
```bash
typst watch main.typ output/research-paper.pdf
```
Or double-click `watch.bat` (or run `./watch.ps1`). Whenever you save changes in `main.typ`, `template.typ`, or `references.bib`, Typst instantly recompiles the PDF in milliseconds.

---

## 🎨 Template Design System Features

The `template.typ` module provides:
- **Clean Scientific Typography**: Uses `Libertinus Serif` with `Segoe UI` heading accents and `Consolas` code elements.
- **Top Full-Width Title & Metadata**: Includes running header/footers, author cards with institutional affiliations, contact emails, project metadata badge chips, and a bordered Abstract box with index keywords.
- **Two-Column Scientific Body**: Standard academic two-column grid with balanced leading and paragraph spacing.
- **Numbered Hierarchy**: Automatically numbered headings (`1.`, `1.1`, etc.).
- **Booktabs Tables**: Clean horizontal rules with support for spanning across both columns (`scope: "parent"`).
- **Clinical & Math Callout Boxes**: Custom `#callout(title: ..., type: "clinical" | "math" | "warning")` component for clinical insights and mathematical definitions.
- **Native Cross-Referencing**: Automatic equation numbering `(1)`, figure captions (`@fig:validation_curves`), table references (`@tab:mimic_results`), and BibTeX citation formatting via IEEE brackets `[1]`.
