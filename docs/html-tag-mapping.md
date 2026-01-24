# HTML -> LaTeX Tag Mapping (WYSIWYG)

Date: 2026-01-24

## Purpose
This document summarizes how common WYSIWYG HTML tags are mapped to LaTeX by
HTML2LaTeX.

## Required Packages
- `graphicx` for images (`\includegraphics`).
- `hyperref` for links (`\href`, `\url`).
- `xcolor` for highlighted text (`\colorbox`).
- `ulem` (with normalem option) for strikethrough (`\sout`).
- `multirow` for table cells spanning multiple rows (`\multirow`).

## Block-level tags

| HTML | LaTeX | Notes |
| --- | --- | --- |
| `p` | `... \par` | Paragraph terminator is explicit. With `text-align` style maps to `center`/`flushleft`/`flushright` environments. |
| `div` | `... \par` | Treated as a block container. Supports `text-align` style like `p`. |
| `h1` | `\section{...}` | |
| `h2` | `\subsection{...}` | |
| `h3` | `\subsubsection{...}` | |
| `h4` | `\paragraph{...}` | |
| `h5` | `\subparagraph{...}` | |
| `h6` | content preserved | No heading command emitted. |
| `center` | `\begin{center} ... \end{center}` | Deprecated HTML tag, still supported. |
| `ul` | `\begin{itemize} ... \end{itemize}` | `\item` for each `li`. |
| `ol` | `\begin{enumerate} ... \end{enumerate}` | `\item` for each `li`; `start` uses `\setcounter{enumi}{start-1}` (nested uses `enumii`, `enumiii`, ...); `li value` uses `\setcounter` before the item; `type` uses `\renewcommand{\label...}{...}`; `reversed` decrements the counter per item. |
| `dl` | `\begin{description} ... \end{description}` | `\item[term]` per `dt/dd`. |
| `blockquote` | `\begin{quote} ... \end{quote}` | |
| `pre` | `\begin{verbatim} ... \end{verbatim}` | Preserves whitespace. |
| `hr` | `\hrule` | |
| `table` | `tabular` | Column spec uses detected alignment (`l`/`c`/`r`); wrapped in `table` environment when a `caption` is present. |
| `caption` | `\caption{...}` | Only when nested in a `table`. |
| `thead`/`tbody`/`tfoot` | table grouping | Passed through to `tabular` generation. |
| `tr` | row with `\\` | |
| `th` | `\textbf{...}` | Column header, bold by default. |
| `td` | cell contents | See table features below. |
| `figure` | `\begin{figure} ... \end{figure}` | With `\centering`. |
| `figcaption` | `\caption{...}` | When inside `figure`. |
| `section`, `article`, `aside`, `header`, `footer`, `nav`, `main` | content preserved | Semantic container tags; children are rendered. |

### Table features

| Feature | HTML | LaTeX | Notes |
| --- | --- | --- | --- |
| Column span | `colspan="N"` | `\multicolumn{N}{align}{...}` | |
| Row span | `rowspan="N"` | `\multirow{N}{*}{...}` | Requires `multirow` package. |
| Cell alignment | `align="left\|center\|right"` | Column spec `l`/`c`/`r` | Detected per-column from dominant alignment. |
| Cell alignment (CSS) | `style="text-align: ..."` | Column spec `l`/`c`/`r` | Same as `align` attribute. |
| Combined colspan+alignment | `colspan` + `align` | `\multicolumn{N}{c}{...}` | Uses cell's alignment in multicolumn. |
| Combined rowspan+colspan | Both attributes | Nested `\multicolumn` and `\multirow` | |

## Inline tags

| HTML | LaTeX | Notes |
| --- | --- | --- |
| `strong`, `b` | `\textbf{...}` | |
| `em`, `i` | `\textit{...}` | |
| `u`, `ins` | `\underline{...}` | |
| `code` | `\texttt{...}` | |
| `sub` | `\textsubscript{...}` | |
| `sup` | `\textsuperscript{...}` | |
| `a` | `\href{url}{text}` or `\url{url}` | `hyperref` required. |
| `img` | `\includegraphics[width=Wpx,height=Hpx]{src}` | `graphicx` required. Supports `width`/`height` attributes. |
| `span` (math) | `\( ... \)` or `\[ ... \]` | `class="math-tex"` or `data-latex`/`data-math`. |
| `mark` | `\colorbox{yellow}{...}` | `xcolor` required. |
| `del`, `s`, `strike` | `\sout{...}` | `ulem` required (normalem option). |
| `small` | `{\small ...}` | Font size switch. |
| `big` | `{\large ...}` | Font size switch (deprecated HTML tag). |
| `q` | ``` ``...'' ``` or `` `...' `` | Inline quote. Outer quotes use double backticks/apostrophes; nested quotes alternate to single. |
| `kbd`, `samp` | `\texttt{...}` | Keyboard input / sample output. |
| `var`, `cite` | `\textit{...}` | Variable / citation. |
| `br` | `\newline` | Line break. |
| `span`, `abbr`, `time`, `dfn` | content preserved | Inline semantic tags; children are rendered. |

## Notes
- Text content is LaTeX-escaped during serialization.
- Unlisted tags are flattened to their children.
- Math content preserves delimiters (`$...$`, `\(...\)`, `\[...\]`, `$$...$$`).

## References
- Lists: https://www.overleaf.com/learn/latex/Lists
- Tables: https://www.overleaf.com/learn/latex/Tables
- Text formatting: https://www.overleaf.com/learn/latex/Bold%2C_italics_and_underlining
- Hyperlinks: https://www.overleaf.com/learn/latex/Hyperlinks
- Images: https://www.overleaf.com/learn/latex/Inserting_Images
