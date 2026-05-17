# prosecode-heap-pager

`prosecode-heap-pager` is a token-conscious context lifecycle manager and garbage collector for LLM prompt streams. Operating as the memory management unit (MMU) alongside `prosecode-intent-compiler` and `session-contracts`, it profiles active conversation history, scores block-level relevance against current intent vectors, and dynamically executes context eviction or compression.

By maintaining a lean, un-diluted context window, it preserves global attention sharpness, reduces token cost, and prevents semantic drift in long-running agent sessions.

## The Core Paging Operations

The pager profiles history against three strict structural directives:

| Directive | Action Taken | Target Material |
| --- | --- | --- |
| retain | Keep 100% intact in active memory. | Current Intent IR slots, open questions, active targets. |
| page | Compress block into a dense, low-token summary stub. | Resolved sub-tasks, historical code iterations, closed arguments. |
| evict | Completely purge block from the stream. | Corrected syntax errors, typos, raw logs successfully compiled. |

## The Retention Formula

The engine evaluates the retention priority ($R$) of any given conversation block using a zero-dependency decay formula:

$$R = \alpha \cdot \text{sim}(V_{\text{block}}, V_{\text{intent}}) + \beta \cdot \left(\frac{1}{1 + \ln(\Delta t)}\right)$$

Where `sim` is a native token-intersection proxy for vector similarity, and $\Delta t$ represents the distance in tokens from the current generation head.

## Repository Structure

prosecode-heap-pager/
├── SKILL.md                 # Agent installation frontmatter and execution protocol
├── README.md                # This user and developer guide
├── references/
│   ├── paging-directives.md # Formal specs for retain/page/evict boundaries
│   └── retention-math.md    # Deep-dive on algorithmic tuning coefficients
├── assets/
│   ├── test-history.json    # Synthetic multi-turn noisy conversation logs
│   └── profiles.json        # Pre-calibrated alpha/beta tuning profiles
└── scripts/
├── pager.py             # Core analytical and text-patching engine
├── run-pager.py         # CLI wrapper for piping active contexts
└── benchmark-pager.py   # Regression and recall validation script

## Usage and Integration

### 1. Manual CLI Execution

You can pass an active conversation log and an intent directly to the pager to see what should be evicted or summarized:

python3 scripts/run-pager.py --history assets/test-history.json --intent fix --output-patch patch.limn

### 2. Automated Pipeline Integration

In a live agent runtime, the pager intercepts the pipeline directly between prompt compilation and state logging:

[Raw Prompt] -> (intent-compiler) -> [Intent IR] -> (heap-pager) -> (session-contracts) -> [Updated Contract]

If the pager calculates that historical blocks have fallen below the retention threshold, it directly generates and appends Liminate (.limn) statements to your active session contract:

add "page-block-0x04" to paged-blocks
show "GC: compressed historical analysis of module_x"

## Benchmarking

To verify the deterministic scoring engine and check for regression across configuration models, run the benchmark suite:

python3 scripts/benchmark-pager.py --verbose

## License

MIT
