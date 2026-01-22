# HTML -> LaTeX Tag Mapping (WYSIWYG)

Date: 2026-01-22

## Purpose
This document summarizes how common WYSIWYG HTML tags are mapped to LaTeX by
HTML2LaTeX.

## Required Packages
- `graphicx` for images (`\includegraphics`).
- `hyperref` for links (`\href`, `\url`).

## Block-level tags

| HTML | LaTeX | Notes |
| --- | --- | --- |
| `p` | `... \par` | Paragraph terminator is explicit. |
| `div` | `... \par` | Treated as a block container. |
| `h1` | `\section{...}` | |
| `h2` | `\subsection{...}` | |
| `h3` | `\subsubsection{...}` | |
| `h4`–`h6` | content preserved | No heading commands emitted. |
| `ul` | `\begin{itemize} ... \end{itemize}` | `\item` for each `li`. |
| `ol` | `\begin{enumerate} ... \end{enumerate}` | `\item` for each `li`. |
| `dl` | `\begin{description} ... \end{description}` | `\item[term]` per `dt/dd`. |
| `blockquote` | `\begin{quote} ... \end{quote}` | |
| `pre` | `\begin{verbatim} ... \end{verbatim}` | Preserves whitespace. |
| `hr` | `\hrule` | |
| `table` | `tabular` | Column spec uses left alignment (`l`). |
| `thead`/`tbody`/`tfoot` | table grouping | Passed through to `tabular` generation. |
| `tr` | row with `\\` | |
| `th` | `\textbf{...}` | Column header. |
| `td` | cell contents | `colspan` mapped via `\multicolumn`. |
| `section`, `article`, `aside`, `header`, `footer`, `nav`, `main`, `figure`, `figcaption` | content preserved | Container tags; children are rendered. |

## Inline tags

| HTML | LaTeX | Notes |
| --- | --- | --- |
| `strong`, `b` | `\textbf{...}` | |
| `em`, `i` | `\textit{...}` | |
| `u` | `\underline{...}` | |
| `code` | `\texttt{...}` | |
| `sub` | `\textsubscript{...}` | |
| `sup` | `\textsuperscript{...}` | |
| `a` | `\href{url}{text}` or `\url{url}` | `hyperref` required. |
| `img` | `\includegraphics{src}` | `graphicx` required. |
| `span` (math) | `\( ... \)` or `\[ ... \]` | `class="math-tex"` or `data-latex`/`data-math`. |
| `span`, `mark`, `abbr`, `time`, `del`, `ins`, `s`, `strike`, `small`, `cite`, `dfn`, `kbd`, `samp`, `var` | content preserved | Inline semantic tags; children are rendered. |

## Notes
- Text content is LaTeX-escaped during serialization.
- Unlisted tags are flattened to their children.
- `rowspan` is currently ignored; `colspan` is supported.

## References
- Lists: https://www.overleaf.com/learn/latex/Lists
- Tables: https://www.overleaf.com/learn/latex/Tables
- Text formatting: https://www.overleaf.com/learn/latex/Bold%2C_italics_and_underlining
- Hyperlinks: https://www.overleaf.com/learn/latex/Hyperlinks
- Images: https://www.overleaf.com/learn/latex/Inserting_Images
