# Website-generation context replay — September 20, 2026

**At the default cutoff, Dynamic Context Engine removed 34,104 generation-input tokens (14.8%), but estimated net input cost fell only 2.7% after paying for Jev.** Three of eight sites became slightly more expensive. All 80 pre-registered required-paragraph checks passed.

This is a replay of the eight newest completed generation archive records at capture, with their exact saved system prompts and user requests. All eight existing sites returned HTTP 200 and matching titles. The benchmark never regenerated, modified, deployed, or posted a website.

## Default selection results

| Existing generated site | Full input tokens | Dynamic input tokens | Tokens removed | Net USD saved | Required paragraphs |
| --- | ---: | ---: | ---: | ---: | ---: |
| [Bilateral Trade Negotiation Matrix & Bargaining Power Simulator](https://app.getsupers.com/sites/trade-negotiation-matrix-48/) | 28,716 | 24,795 | 3,921 (13.7%) | $0.000347 | 10/10 |
| [Human vs Machine Forecast Ensemble Lab — Calibration & Brier Score Analysis](https://app.getsupers.com/sites/forecast-ensemble-lab-48/) | 28,777 | 20,948 | 7,829 (27.2%) | $0.003257 | 10/10 |
| [Skincare Routine Auditor — Evidence-Based Barrier & Conflict Checker](https://app.getsupers.com/sites/skincare-routine-auditor-48/) | 28,994 | 23,294 | 5,700 (19.7%) | $0.001584 | 10/10 |
| [Command Deck Melder & Battle Simulator](https://app.getsupers.com/sites/command-deck-melder-88/) | 28,963 | 25,843 | 3,120 (10.8%) | $-0.000362 | 10/10 |
| [Documentary Release Risk & Distribution Modeler | DocuRisk](https://app.getsupers.com/sites/documentary-release-risk-modeler-72/) | 28,716 | 24,814 | 3,902 (13.6%) | $0.000338 | 10/10 |
| [Tribute Concert Setlist & Run of Show Planner](https://app.getsupers.com/sites/tribute-concert-setlist-planner-48/) | 28,484 | 25,825 | 2,659 (9.3%) | $-0.000526 | 10/10 |
| [Prosthetic Chair Optimizer — SFX Makeup Workflow & Call Sheet Planner](https://app.getsupers.com/sites/prosthetic-chair-optimizer-84/) | 28,799 | 25,232 | 3,567 (12.4%) | $0.000061 | 10/10 |
| [Vehicle Packaging & Chassis Dynamics Studio](https://app.getsupers.com/sites/vehicle-packaging-studio-72/) | 28,608 | 25,202 | 3,406 (11.9%) | $-0.000006 | 10/10 |
| **Total** | **230,057** | **195,953** | **34,104 (14.8%)** | **$0.004692** | **80/80** |

## Money accounting

- Full-prompt generation input: **$0.172543**.
- Reduced generation input: **$0.146965**.
- Jev selection: **497,275 provider-reported input tokens**, estimated **$0.020886**.
- Combined dynamic input cost: **$0.167850**.
- Net savings across eight sites: **$0.004692** (2.72%), or **$0.59 per 1,000 comparable requests** if this mix and price recur.
- Median selection latency: **1.083 seconds**; all eight immediate identical repeats hit the local cache with zero new Jev usage.

The removed generation tokens are not whole-pipeline token savings: the selector adds 497,275 Jev input tokens and 20,621 Jev output tokens (output is free at the cited rate). Jev and o200k_base counts use different tokenization, so they must not be presented as one homogeneous measured billing-token total.

Prices checked September 20, 2026: [Gemini 3.8 Flash standard input $0.75/M and cache reads $0.075/M](https://ai.google.dev/gemini-api/docs/pricing), consistent with the [OpenRouter public route](https://openrouter.ai/google/gemini-3.8-flash); [Jev input $0.042/M, output free](https://docs.typesafe.ai/models). Prices are explicit in the saved rates file. These are public-price estimates, not invoice reconciliations; a BYOK account may be billed differently.

## Prompt caching changes the answer

| Input-price scenario, default cutoff | Full prompt | Dynamic + cold Jev | Net saved |
| --- | ---: | ---: | ---: |
| Both generation prompts uncached | $0.172543 | $0.167850 | $0.004692 |
| Both system contexts receive cache-hit pricing | $0.024923 | $0.043251 | $-0.018328 |
| Full system context cached; dynamic system context uncached | $0.024923 | $0.167850 | $-0.142927 |

Cache-hit scenarios are counterfactuals, not verified cache receipts. User-request tokens remain uncached in both arms. Cache storage and creation fees are excluded. Immediate identical-query reuse also caches Jev locally, but that does not describe a fresh site request.

## Threshold sensitivity

All three cutoffs reuse the same raw judgments; they do not incur three sets of Jev calls. The 0.50 result is the pre-existing default. Sensitivity results are exploratory, not a tuned or held-out recommendation.

| Relevance cutoff | Generation input removed | Net input USD saved | Required paragraphs retained | Cases passing every check |
| --- | ---: | ---: | ---: | ---: |
| 0.35 | 6,963 (3.0%) | $-0.015663 | 80/80 | 8/8 |
| 0.50 | 34,104 (14.8%) | $0.004692 | 80/80 | 8/8 |
| 0.70 | 96,800 (42.1%) | $0.051714 | 69/80 | 1/8 |

**Do not promote 0.70 based on its larger savings.** It dropped 11 required-paragraph instances, including SEO/accessibility, safe DOM/runtime handling, and current visual direction. Seven of eight cases failed at least one pre-registered retention check. Exact omissions are in the JSON report.

## Why savings are limited

- The frozen system prompt has 78 blank-line paragraphs. One paragraph contains a 58,207-character block of 251 repair lessons. All eight default selections retained this whole block. Paragraph-level retrieval cannot remove irrelevant individual lessons inside it.
- Some headings and code-fence terminators are standalone paragraphs, while large multi-topic sections remain indivisible. The current import format therefore does not align every selection unit with a coherent rule or code example.
- Jev evaluates all paragraphs, repeats the complete user request across batches, and receives an independent question/policy per paragraph. This costs more selector tokens than the generation-input reduction.
- JSON provenance, separators, and the dynamic instruction wrapper count against the dynamic arm. They are not omitted to inflate savings.

## What the tests prove

The tested v0.2.0 engine used the unchanged 0.50 cutoff, 12-paragraph batches, three concurrent workers, and a 1,000,000-token budget. Baseline counts are the exact archived system plus unchanged user text. Dynamic counts are the exact emitted JSONL plus a fixed instruction wrapper and the same user text. Both are counted with o200k_base. Message-envelope overhead, native Gemini billing tokenization, output/thinking tokens, retries, and tool calls are not measured.

Ten required paragraphs were annotated before retrieval: complete output, canonical/social metadata, safe DOM handling, SEO/accessibility, footer attribution, latest functional-tool direction, latest art direction, actual computation, runtime loading, and public-slug guidance. Retaining those paragraphs is a necessary check, not proof that the generator follows them or that the resulting site is equally good. Full end-to-end savings require paired generations and output evaluation.

No relevance policy, production generation prompt, default cutoff, or production website was changed for this benchmark. The next experiment should use model-authored coherent retrieval units, preserve cross-site obligations, and compare equivalent generated outputs on a separate holdout set.

## Reproduce

Private prompts and requests are intentionally excluded from the public repository. The published result contains public site URLs, hashes, counts, price assumptions, and retention outcomes. Supply your own authorized archive fixture in the documented schema:

```sh
pip install -e .
python3 benchmarks/website_replay.py \
  --cases /private/cases.json \
  --rates benchmarks/rates-2026-09-20.json \
  --expectations benchmarks/website-expectations-2026-09-20.json \
  --output artifacts/website-replay
```

Each case needs `id`, `system`, `request`, `title`, `url`, `slug`, and optional public verification fields. The top-level object needs `selection_rule` and `cases`. Expectations are hash-bound to this frozen prompt; other corpora need their own pre-registered requirement positions. Provide TYPESAFE_API_KEY in the environment. Raw per-case outputs and the SQLite database are private artifacts. Delete or choose a new output directory to repeat a cold run.

- [Machine-readable results](results/website-replay-2026-09-20.json)
- [Replay harness](website_replay.py)
- [Pre-registered required paragraphs](website-expectations-2026-09-20.json)
- [Saved rates](rates-2026-09-20.json)
