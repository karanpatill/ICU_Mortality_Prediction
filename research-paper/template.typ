// ==============================================================================
// SCIENTIFIC MONOGRAPH TEMPLATE (TYPST)
// Typographic discipline inspired by DeepMind, JMLR, and Nature MI research
// ==============================================================================

#let definition(
  title: "Definition",
  counter-val: none,
  body
) = {
  v(8pt)
  block(
    width: 100%,
    breakable: false,
    stroke: (left: 1.5pt + rgb("#1e293b")),
    inset: (left: 10pt, y: 4pt),
    outset: 0pt,
    [
      #set text(size: 9pt)
      #text(weight: "bold", fill: rgb("#0f172a"))[#title#if counter-val != none [ #counter-val].]
      #h(4pt)
      #text(fill: rgb("#1e293b"), style: "normal")[#body]
    ]
  )
  v(8pt)
}

#let clinical-note(
  title: "Clinical Rationale",
  body
) = {
  v(8pt)
  block(
    width: 100%,
    breakable: false,
    stroke: (left: 1.5pt + rgb("#0369a1")),
    inset: (left: 10pt, y: 4pt),
    outset: 0pt,
    [
      #set text(size: 9pt)
      #text(weight: "bold", fill: rgb("#0369a1"))[#title.]
      #h(4pt)
      #text(fill: rgb("#1e293b"), style: "italic")[#body]
    ]
  )
  v(8pt)
}

#let paper(
  title: "",
  subtitle: none,
  authors: (),
  affiliations: (),
  abstract: none,
  keywords: (),
  running-title: "",
  project-note: none,
  bibliography-file: none,
  body
) = {
  // Page setup: Single-column format with generous reading margins (~72 chars per line)
  set page(
    paper: "a4",
    margin: (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
    header: context {
      let page-num = counter(page).get().first()
      if page-num > 1 {
        grid(
          columns: (1fr, auto),
          align(left)[
            #text(size: 8pt, fill: rgb("#64748b"), font: "Libertinus Serif", style: "italic")[
              #running-title
            ]
          ],
          align(right)[
            #text(size: 8pt, fill: rgb("#475569"), font: "Libertinus Serif")[
              #page-num
            ]
          ]
        )
        v(-3pt)
        line(length: 100%, stroke: 0.35pt + rgb("#cbd5e1"))
      }
    },
    footer: context {
      let page-num = counter(page).get().first()
      let total-pages = counter(page).final().first()
      align(center)[
        #text(size: 8pt, fill: rgb("#94a3b8"), font: "Libertinus Serif")[
          #page-num of #total-pages
        ]
      ]
    }
  )

  // Typography settings: High-legibility classical serif with refined leading
  set text(
    font: ("Libertinus Serif", "Times New Roman"),
    size: 10pt,
    fill: rgb("#111827"),
    lang: "en",
    hyphenate: true,
    spacing: 100%
  )

  set par(
    justify: true,
    leading: 0.70em,
    spacing: 0.88em,
    first-line-indent: 0pt
  )

  set heading(numbering: "1.1")

  // Refined Headings: Classical, unadorned, devoid of generic horizontal underlines
  show heading.where(level: 1): it => block(
    above: 1.5em,
    below: 0.75em,
    breakable: false,
    [
      #set text(
        font: ("Libertinus Serif", "Times New Roman"),
        size: 12pt,
        weight: "bold",
        fill: rgb("#0f172a")
      )
      #if it.numbering != none [
        #counter(heading).display()
        #h(7pt)
      ]
      #it.body
    ]
  )

  show heading.where(level: 2): it => block(
    above: 1.25em,
    below: 0.6em,
    breakable: false,
    [
      #set text(
        font: ("Libertinus Serif", "Times New Roman"),
        size: 10.5pt,
        weight: "bold",
        fill: rgb("#1e293b")
      )
      #if it.numbering != none [
        #counter(heading).display()
        #h(6pt)
      ]
      #it.body
    ]
  )

  show heading.where(level: 3): it => block(
    above: 1.1em,
    below: 0.5em,
    breakable: false,
    [
      #set text(
        font: ("Libertinus Serif", "Times New Roman"),
        size: 10pt,
        weight: "bold",
        style: "italic",
        fill: rgb("#334155")
      )
      #if it.numbering != none [
        #counter(heading).display()
        #h(5pt)
      ]
      #it.body
    ]
  )

  // Equation styling: Centered display math with right-aligned numbering
  set math.equation(numbering: "(1)")
  show math.equation: set text(size: 10pt)

  // Figures & Tables: Clean typography, authoritative captions
  show figure.caption: it => [
    #set text(size: 8.5pt, fill: rgb("#334155"))
    #set par(justify: true, leading: 0.6em)
    #v(4pt)
    #text(weight: "bold", fill: rgb("#0f172a"))[#it.supplement #it.counter.display(it.numbering) |]
    #h(3pt)
    #it.body
  ]

  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: image): set figure.caption(position: bottom)

  // Raw / Code styling: Clean, un-tinted monospace
  show raw: set text(font: ("Consolas", "Courier New"), size: 8.5pt)
  show raw.where(block: false): it => text(font: ("Consolas", "Courier New"), size: 8.5pt, fill: rgb("#0f172a"))[#it]

  // ===========================================================================
  // FIRST PAGE: REFINED SCIENTIFIC TITLE BLOCK
  // ===========================================================================

  v(6pt)

  // Title
  align(center)[
    #block(
      width: 98%,
      [
        #set text(
          size: 15pt,
          weight: "bold",
          fill: rgb("#0f172a"),
          font: ("Libertinus Serif", "Times New Roman"),
          spacing: 120%
        )
        #title
      ]
    )

    #if subtitle != none [
      #v(6pt)
      #text(
        size: 9.8pt,
        style: "italic",
        fill: rgb("#475569")
      )[#subtitle]
    ]

    #v(14pt)

    // Authors Grid (Balanced 2x2 grid for full institutional email legibility)
    #if authors.len() > 0 [
      #grid(
        columns: (1fr, 1fr),
        row-gutter: 9pt,
        column-gutter: 20pt,
        ..authors.map(a => [
          #align(center)[
            #text(weight: "bold", size: 9.8pt, fill: rgb("#0f172a"))[#a.name]#if "affiliation-idx" in a [#super[#a.affiliation-idx]] \
            #if "email" in a and a.email != none [
              #v(2pt)
              #text(size: 7.2pt, fill: rgb("#64748b"), font: "Consolas")[#a.email]
            ]
          ]
        ])
      )
      
      #v(10pt)
      
      // Affiliations
      #for aff in affiliations [
        #text(size: 8.5pt, fill: rgb("#475569"))[
          #if "idx" in aff [#super[#aff.idx] ]#aff.dept, #aff.institution
        ] \
      ]
    ]
  ]

  v(16pt)

  // Abstract: Inset by 1.2cm, bounded by elegant 0.4pt hairline rules
  if abstract != none [
    #align(center)[
      #block(
        width: 92%,
        [
          #line(length: 100%, stroke: 0.5pt + rgb("#0f172a"))
          #v(6pt)
          #align(left)[
            #set text(size: 9pt)
            #set par(justify: true, leading: 0.65em, spacing: 0.7em)
            #text(weight: "bold", fill: rgb("#0f172a"))[Abstract]---#abstract

            #if keywords.len() > 0 [
              #v(5pt)
              #text(weight: "bold", size: 8.5pt, fill: rgb("#0f172a"))[Keywords: ]
              #text(style: "italic", size: 8.5pt, fill: rgb("#334155"))[#keywords.join([, ])]
            ]
          ]
          #v(6pt)
          #line(length: 100%, stroke: 0.5pt + rgb("#0f172a"))
        ]
      )
    ]
    #v(14pt)
  ]

  // ===========================================================================
  // MANUSCRIPT BODY (SINGLE COLUMN SCIENTIFIC FLOW)
  // ===========================================================================
  
  body

  if project-note != none [
    #v(14pt)
    #line(length: 100%, stroke: 0.35pt + rgb("#cbd5e1"))
    #v(4pt)
    #text(size: 8pt, fill: rgb("#475569"))[
      #project-note
    ]
  ]

  if bibliography-file != none [
    #pagebreak()
    #v(6pt)
    #show bibliography: set text(size: 8pt)
    #show bibliography: set par(leading: 0.52em, justify: true)
    #columns(2, gutter: 16pt)[
      #bibliography(bibliography-file, title: [References], style: "ieee")
    ]
  ]
}
