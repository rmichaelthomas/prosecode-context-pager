# CLAUDE.md - Behavioral Contract for prosecode-heap-pager

## Project Purpose
prosecode-heap-pager is a token-conscious context lifecycle manager for LLM prompt streams. It profiles historical conversation blocks, scores their contextual relevance against active Intent IR verbs, and applies deterministic paging operations (retain, page, evict) to update an active Liminate (.limn) session contract.

## Architecture Guidelines
- Strict Zero-Dependency Rule: Use only native Python 3 standard library utilities. Do not add external tokenizers or machine learning frameworks.
- Algorithmic Focus: Implement the retention score formula using native string parsing, keyword weight intersection (as a proxy for vector similarity), and distance tracking.
- Output Discipline: Keep files clean, documentation declarative, and console logging structured.

## Validation & Verification Commands
- Run verification benchmark: `python3 scripts/benchmark-pager.py --verbose`
- Verify skill compliance: `python3 scripts/validate-skill.py`

## Development Directives
1. State your structural assumptions clearly before creating files.
2. Maintain minimum code footprints (simplicity first). Do not write speculative error handling.
3. Keep the target .limn modifications bounded precisely to Liminate's 35-word vocabulary.