# ADR 0001: Rewrite html2latex from scratch

## Status
Accepted

## Context
The current codebase has accumulated legacy behaviors, ad-hoc transformations, and domain-specific constraints that make it difficult to extend and reason about. We want a clean, generic HTML→LaTeX library with predictable output, strong typing, and high testability.

## Decision
We will rebuild the core from scratch with a small public API, typed ASTs, a dedicated LaTeX serializer, and a style system that separates data from presentation. Backward compatibility is explicitly not required. The implementation will be based on a JustHTML adapter (no lxml), strict LaTeX escaping, and deterministic output. Tectonic is required for integration tests.

## Consequences
- Existing call paths will be replaced by the new API and pipeline.
- The new architecture will prioritize maintainability, correctness, and test coverage over preserving legacy quirks.
- Documentation will describe current behavior only and omit historical caveats.
