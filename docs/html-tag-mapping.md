# HTML → LaTeX Tag Mapping (WYSIWYG)

Date: 2026-01-21

## Purpose
This document defines the target mapping for common HTML5/WYSIWYG tags and inline styles to LaTeX constructs. It is the source of truth for tag coverage and package requirements.

## Package policy
Required:
- `graphicx` for images (`\includegraphics`).
- `hyperref` for links (`\href`, `\url`).

Optional (feature-gated):
- `xcolor` for text/background color.
- `ulem` for strikethrough (`\sout`).
- `tabularx` for flexible-width tables.

## Block-level tags

| HTML | LaTeX | Notes |
| --- | --- | --- |
| `p` | `\noindent ... \par` | Paragraphs are explicit to avoid implicit indentation. |
| `div` | `\par ... \par` | Treated as a block container. |
| `h1` | `\section{...}` | Headings map to standard sectioning. |
| `h2` | `\subsection{...}` |  |
| `h3` | `\subsubsection{...}` |  |
| `h4` | `\paragraph{...}` |  |
| `h5` | `\subparagraph{...}` |  |
| `h6` | `\subparagraph{...}` |  |
| `ul` | `\begin{itemize} ... \end{itemize}` | `\item` for each `li`. |
| `ol` | `\begin{enumerate} ... \end{enumerate}` | `\item` for each `li`. |
| `li` | `\item ...` |  |
| `blockquote` | `\begin{quote} ... \end{quote}` |  |
| `pre` | `\begin{verbatim} ... \end{verbatim}` | Preserve whitespace. |
| `code` | `\texttt{...}` or `verbatim` | Inline by default; block when wrapped by `pre`. |
| `hr` | `\hrule` | May be wrapped in `\vspace` as needed. |
| `table` | `tabular`/`tabularx` | No screenshot-based rendering. |
| `thead`/`tbody`/`tfoot` | table grouping | Passed through to `tabular` generation. |
| `tr` | row with `\\` |  |
| `th` | `\textbf{...}` | Column header. |
| `td` | cell contents | colspan/rowspan supported where possible. |
| `figure` | `\begin{figure} ... \end{figure}` |  |
| `figcaption` | `\caption{...}` |  |

## Inline tags

| HTML | LaTeX | Notes |
| --- | --- | --- |
| `strong`, `b` | `\textbf{...}` |  |
| `em`, `i` | `\textit{...}` or `\emph{...}` | `\emph` preferred for nested emphasis. |
| `u` | `\underline{...}` |  |
| `s`, `strike`, `del` | `\sout{...}` | Requires `ulem`. |
| `sub` | `\textsubscript{...}` or math subscript |  |
| `sup` | `\textsuperscript{...}` or math superscript |  |
| `a` | `\href{url}{text}` or `\url{url}` | Requires `hyperref`. |
| `img` | `\includegraphics` | Requires `graphicx`. |
| `span` | style-driven | Use inline style mapping. |

## Inline style mapping

Supported CSS (subset):
- `text-align`: maps to `\centering`, `\raggedright`, `\raggedleft`.
- `font-weight: bold`: `\textbf{...}`.
- `font-style: italic`: `\textit{...}`.
- `text-decoration: underline`: `\underline{...}`; `line-through` → `\sout{...}`.
- `color`: `\textcolor{...}{...}` (requires `xcolor`).
- `background-color`: `\colorbox{...}{...}` (requires `xcolor`).

## Notes
- HTML entities must be unescaped before LaTeX escaping.
- LaTeX escaping must avoid double-escaping and preserve math spans.
- If a tag is unknown, default to rendering its text content.

## References
- Lists: https://www.overleaf.com/learn/latex/Lists
- Tables: https://www.overleaf.com/learn/latex/Tables
- Text formatting: https://www.overleaf.com/learn/latex/Bold%2C_italics_and_underlining
- Hyperlinks: https://www.overleaf.com/learn/latex/Hyperlinks
- Images: https://www.overleaf.com/learn/latex/Inserting_Images
- Alignment: https://www.overleaf.com/learn/latex/Text_alignment
