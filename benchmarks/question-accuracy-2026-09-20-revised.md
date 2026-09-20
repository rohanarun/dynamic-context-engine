# Revised question-answer accuracy and context savings — September 20, 2026

Revised 29-question benchmark. Excluded after the original run: `tribute-multi`, `prosthetic-multi`, `vehicle-multi`. Fresh Jev selections and fresh answers in all three arms; no further questions were removed. This post-selected subset is not evidence of improved accuracy on the original workload. [Original 32-question run](question-accuracy-2026-09-20.md).

**Full context: 29/29 (100.0%). Dynamic context: 29/29 (100.0%). No context: 9/29 (31.0%). Dynamic selection removed 96.1% of answer-model input tokens.**

This is a separate workload from the 14.8% website-generation-prompt replay: it answers questions about frozen public text from the same eight generated sites plus Orbit's fictional sample memory. It does not rerun the private website-generation prompt or regenerate websites. The source corpus contains 71 coherent paragraphs across 11 documents. Do not extrapolate its compression rate to website generation.

Dynamic accuracy on answerable questions alone was **20/20 (100.0%)**; all nine deliberately unanswerable questions were correctly answered with null in every arm.

![Accuracy and average answer-model input for full, dynamic, and no-context arms.](../demo/static/benchmark-accuracy.png)

## Results

| Arm | Correct answers | Reference input tokens | Provider input tokens | Provider output tokens |
| --- | ---: | ---: | ---: | ---: |
| Full context | 29/29 (100.0%) | 252,143 | 272,352 | 6,822 |
| Dynamic context | 29/29 (100.0%) | 9,748 | 10,402 | 9,622 |
| No-context control | 9/29 (31.0%) | 4,367 | 4,566 | 4,073 |

- Input tokens removed: **242,395**, including the same question and answer instructions in both arms.
- Context payload alone: **247,863 → 5,441 tokens (97.8% removed)**. Both arms use the engine's identical JSONL provenance format. The full raw-text corpus without provenance is 5,757 tokens per question; the full JSONL corpus is 8,547. No repeated filler was added.
- Accuracy change: **+0.000 percentage points**. Paired counts: {"both_correct":29,"full_only_correct":0,"dynamic_only_correct":0,"both_wrong":0}.
- Correct dynamic answers on answerable questions: **20/20**. The no-context control failed all 20 answerable questions and passed all nine abstention cases.
- Gold evidence retained: **25/26 paragraph instances**; every required paragraph retained on 19/20 answerable questions. Unanswerable questions have no gold evidence and are excluded from this denominator.
- Jev processing overhead: **746,435 input and 67,512 output tokens**. These are additional provider-native tokens, excluded from the answer-model reduction. Token savings are not cost savings.
- Zero answer-call infrastructure errors in the measured run. The rerun used the direct OpenRouter endpoint with the same frozen answer model in every arm. No Super API preflight calls were made for this rerun.

## Accuracy by question type

| Type | Full | Dynamic | No context | Input reduction |
| --- | ---: | ---: | ---: | ---: |
| calculation | 3/3 (100.0%) | 3/3 (100.0%) | 0/3 (0.0%) | 97.0% |
| lookup | 9/9 (100.0%) | 9/9 (100.0%) | 0/9 (0.0%) | 94.8% |
| multi_paragraph | 6/6 (100.0%) | 6/6 (100.0%) | 0/6 (0.0%) | 95.0% |
| policy_exception | 2/2 (100.0%) | 2/2 (100.0%) | 0/2 (0.0%) | 94.7% |
| unanswerable | 9/9 (100.0%) | 9/9 (100.0%) | 9/9 (100.0%) | 98.3% |

## Failures and omitted evidence

No dynamic answer failed the frozen exact scorer. This does not establish universal equivalence.

## Frozen protocol and limits

- Gold questions, expected JSON objects, and supporting source quotes were authored and frozen before model calls. Neither gold answers nor evidence annotations are sent to Jev or the answer model. The three exclusions were chosen after observing the original failures. Remaining question text, gold answers, source documents, policy, and threshold are unchanged. Fresh results are all retained, including any new failures.
- Answer model: `google/gemini-3.8-flash` via OpenRouter, temperature 0, 4,096 maximum completion tokens, provider-default reasoning. All response model names, finish reasons, token receipts, and answers are published in the JSON. No tools, web search, external knowledge, or previous turns are supplied. Each arm is an independent completion.
- Jev: existing relevance policy v1, cutoff 0.50, 12-paragraph batches, three workers, 1,000,000-token budget, cold queries. The returned actual Jev version is retained per question.
- All 87 answer calls were fresh, shuffled with seed 20260920 and run with four workers; 29 fresh cold Jev queries preceded them. Local answer receipts and Jev cache were not reused from the original run. The harness checkpoints results for resumption without rerunning successful answers. No best-of selection or failed-answer retries.
- Primary score is all-fields-correct per question. Numeric tolerance is 0.000001 after requested rounding; strings ignore case and repeated whitespace; booleans require booleans; missing facts require explicit JSON null. Missing, extra, malformed, or incorrect fields fail. There is no subjective AI judge. This tests structured source-grounded answers, not free-form prose quality.
- The no-context control measures what the same model can answer or abstain from without sources. Unanswerable cases are deliberately included; abstention gets credit there but fails answerable questions.
- Counts use o200k_base for exact message content, including instructions, question, JSONL provenance, and separators. Chat-envelope overhead is excluded from reference counts; provider-native token receipts are reported separately. Output/reasoning and Jev tokens are not hidden inside the reported input reduction.
- The public pages are test documents, not verified medical, legal, financial, technical, or historical authority. Questions test faithful reading of their frozen initial HTML text. They do not validate the correctness of the sites or their interactive computations. Static snapshots may contain stale or internally inconsistent display values.
- This is one small, hand-authored run on one answer model. The questions share documents, so observations are correlated. The Wilson intervals below are descriptive single-proportion intervals, not a paired non-inferiority test or proof of deployment-wide equivalence. No held-out validation or repeated-run stability study was performed.
- Full descriptive 95% Wilson accuracy interval: 88.3%–100.0%.
- Dynamic descriptive 95% Wilson accuracy interval: 88.3%–100.0%.
- No context descriptive 95% Wilson accuracy interval: 17.3%–49.2%.

## Reproduce

Install the engine, set `TYPESAFE_API_KEY`, and set `ANSWER_API_KEY` plus `ANSWER_API_BASE_URL=https://openrouter.ai/api/v1`. An OpenAI-compatible endpoint is required; the fixture is public. Without answer-specific variables the harness uses the installed Super API configuration. Provider routes can change: verify the returned model. Credentials never belong in fixtures or commits.

```sh
python3 benchmarks/question_accuracy.py \
  --fixture benchmarks/fixtures/question-answering-2026-09-20-revised.json \
  --model google/gemini-3.8-flash \
  --output artifacts/qa-reproduction-revised
python3 scripts/render_accuracy_report.py \
  --results artifacts/qa-reproduction-revised/report.json --revision-fixture benchmarks/fixtures/question-answering-2026-09-20-revised.json
```

The renderer requires matplotlib and writes report/demo artifacts. Keep a reproduction separate until its results are reviewed. Use a fresh output directory for a new independent run; rerunning the same directory resumes saved responses.

- [Frozen source corpus, questions, gold answers, and evidence](fixtures/question-answering-2026-09-20-revised.json)
- [Full measured results, raw answers, usage, and relevance scores](results/question-accuracy-2026-09-20-revised.json)
- [Benchmark harness](question_accuracy.py)
- [Existing website-generation input replay](website-replay-2026-09-20.md)

## Every question

| Question ID | Full | Dynamic | No context | Full input | Dynamic input | Removed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| trade-fact | Pass | Pass | Fail | 8,682 | 419 | 95.2% |
| trade-multi | Pass | Pass | Fail | 8,703 | 440 | 94.9% |
| trade-unknown | Pass | Pass | Pass | 8,693 | 149 | 98.3% |
| forecast-fact | Pass | Pass | Fail | 8,677 | 634 | 92.7% |
| forecast-multi | Pass | Pass | Fail | 8,706 | 337 | 96.1% |
| forecast-unknown | Pass | Pass | Pass | 8,693 | 149 | 98.3% |
| skin-fact | Pass | Pass | Fail | 8,683 | 423 | 95.1% |
| skin-multi | Pass | Pass | Fail | 8,719 | 772 | 91.1% |
| skin-unknown | Pass | Pass | Pass | 8,690 | 146 | 98.3% |
| deck-fact | Pass | Pass | Fail | 8,676 | 384 | 95.6% |
| deck-multi | Pass | Pass | Fail | 8,696 | 387 | 95.5% |
| deck-unknown | Pass | Pass | Pass | 8,704 | 160 | 98.2% |
| doc-fact | Pass | Pass | Fail | 8,683 | 481 | 94.5% |
| doc-multi | Pass | Pass | Fail | 8,698 | 359 | 95.9% |
| doc-unknown | Pass | Pass | Pass | 8,697 | 153 | 98.2% |
| tribute-fact | Pass | Pass | Fail | 8,683 | 389 | 95.5% |
| tribute-unknown | Pass | Pass | Pass | 8,686 | 142 | 98.4% |
| prosthetic-fact | Pass | Pass | Fail | 8,682 | 694 | 92.0% |
| prosthetic-unknown | Pass | Pass | Pass | 8,694 | 150 | 98.3% |
| vehicle-fact | Pass | Pass | Fail | 8,679 | 362 | 95.8% |
| vehicle-unknown | Pass | Pass | Pass | 8,686 | 142 | 98.4% |
| orbit-refund | Pass | Pass | Fail | 8,714 | 429 | 95.1% |
| orbit-renewal | Pass | Pass | Fail | 8,700 | 491 | 94.4% |
| orbit-price | Pass | Pass | Fail | 8,708 | 222 | 97.5% |
| orbit-theme | Pass | Pass | Fail | 8,712 | 304 | 96.5% |
| orbit-rollback | Pass | Pass | Fail | 8,714 | 352 | 96.0% |
| orbit-offsite | Pass | Pass | Fail | 8,701 | 218 | 97.5% |
| orbit-digest | Pass | Pass | Fail | 8,692 | 312 | 96.4% |
| orbit-unknown | Pass | Pass | Pass | 8,692 | 148 | 98.3% |

### trade-fact

In the frozen Trade Negotiation Matrix snapshot, what percentage leverage is displayed for China? Return {"china_leverage_percent": number}.

Gold: `{"china_leverage_percent":54}`

- full: `{"china_leverage_percent":54}`
- dynamic: `{"china_leverage_percent":54}`
- no_context: `{"china_leverage_percent":null}`

### trade-multi

In the Trade Negotiation Matrix snapshot, subtract the United States displayed leverage percentage from China’s displayed leverage percentage. Use the two delegation profiles, not the separate net-advantage metric. Return {"leverage_gap_percentage_points": number}.

Gold: `{"leverage_gap_percentage_points":8}`

- full: `{"leverage_gap_percentage_points":8}`
- dynamic: `{"leverage_gap_percentage_points":8}`
- no_context: `{"leverage_gap_percentage_points":null}`

### trade-unknown

What exact calendar date did the modeled bilateral trade agreement get signed? Return {"signed_date": "YYYY-MM-DD"}, or null for the field if the frozen sources do not state it.

Gold: `{"signed_date":null}`

- full: `{"signed_date":null}`
- dynamic: `{"signed_date":null}`
- no_context: `{"signed_date":null}`

### forecast-fact

How many resolved items are listed in the frozen Forecast Ensemble Lab benchmark? Return {"resolved_items": number}.

Gold: `{"resolved_items":12}`

- full: `{"resolved_items":12}`
- dynamic: `{"resolved_items":12}`
- no_context: `{"resolved_items":null}`

### forecast-multi

In the Forecast Ensemble Lab snapshot, subtract the hybrid Brier score from the human Brier score. Does the source say a lower Brier score is better? Return {"absolute_brier_improvement": number, "lower_is_better": boolean}.

Gold: `{"absolute_brier_improvement":0.03,"lower_is_better":true}`

- full: `{"absolute_brier_improvement":0.03,"lower_is_better":true}`
- dynamic: `{"absolute_brier_improvement":0.03,"lower_is_better":true}`
- no_context: `{"absolute_brier_improvement":null,"lower_is_better":null}`

### forecast-unknown

What is the first and last name of the highest-scoring individual human forecaster in the frozen Forecast Ensemble Lab benchmark? Return {"person_name": string}, or null if unstated.

Gold: `{"person_name":null}`

- full: `{"person_name":null}`
- dynamic: `{"person_name":null}`
- no_context: `{"person_name":null}`

### skin-fact

How many dermatological rules does the frozen Skincare Routine Auditor status explicitly say it evaluated? Return {"rules_evaluated": number}.

Gold: `{"rules_evaluated":6}`

- full: `{"rules_evaluated":6}`
- dynamic: `{"rules_evaluated":6}`
- no_context: `{"rules_evaluated":null}`

### skin-multi

According to the frozen Skincare Routine Auditor, is SPF last in its AM flow sequence, and does it treat relying on SPF makeup alone as sufficient protection? Answer only about the page text, not medical advice. Return {"spf_last_in_am": boolean, "makeup_spf_alone_sufficient": boolean}.

Gold: `{"spf_last_in_am":true,"makeup_spf_alone_sufficient":false}`

- full: `{"spf_last_in_am":true,"makeup_spf_alone_sufficient":false}`
- dynamic: `{"spf_last_in_am":true,"makeup_spf_alone_sufficient":false}`
- no_context: `{"spf_last_in_am":null,"makeup_spf_alone_sufficient":null}`

### skin-unknown

What named patient has a recorded confirmed allergy diagnosis in the frozen Skincare Routine Auditor sources? Return {"patient_name": string}, or null if no such patient is documented.

Gold: `{"patient_name":null}`

- full: `{"patient_name":null}`
- dynamic: `{"patient_name":null}`
- no_context: `{"patient_name":null}`

### deck-fact

How many slots does the Command Deck Melder action deck support? Return {"deck_slots": number}.

Gold: `{"deck_slots":8}`

- full: `{"deck_slots":8}`
- dynamic: `{"deck_slots":8}`
- no_context: `{"deck_slots":null}`

### deck-multi

Using the Command Deck Melder snapshot, report Firaga’s described recharge time and the simulation dummy’s maximum HP. Return {"firaga_recharge_seconds": number, "dummy_max_hp": number}.

Gold: `{"firaga_recharge_seconds":12,"dummy_max_hp":2400}`

- full: `{"firaga_recharge_seconds":12,"dummy_max_hp":2400}`
- dynamic: `{"firaga_recharge_seconds":12,"dummy_max_hp":2400}`
- no_context: `{"firaga_recharge_seconds":null,"dummy_max_hp":null}`

### deck-unknown

What exact damage number did the user’s most recent manual Firaga cast inflict? Use only the frozen Command Deck Melder source, not game knowledge. Return {"last_cast_damage": number}, or null if no cast result is recorded.

Gold: `{"last_cast_damage":null}`

- full: `{"last_cast_damage":null}`
- dynamic: `{"last_cast_damage":null}`
- no_context: `{"last_cast_damage":null}`

### doc-fact

In the frozen Documentary Release Modeler, how long is the Formal Right of Reply response window? Return {"reply_window_days": number}.

Gold: `{"reply_window_days":30}`

- full: `{"reply_window_days":30}`
- dynamic: `{"reply_window_days":30}`
- no_context: `{"reply_window_days":null}`

### doc-multi

In the Documentary Release Modeler snapshot, how many viability points does Boutique Division / Indie Re-licensing have above Full Theatrical & Day-and-Date Streaming? Return {"viability_point_gap": number}.

Gold: `{"viability_point_gap":28}`

- full: `{"viability_point_gap":28}`
- dynamic: `{"viability_point_gap":28}`
- no_context: `{"viability_point_gap":null}`

### doc-unknown

What verified actual box-office gross did the modeled documentary earn after release? Do not substitute a projected pathway yield. Return {"actual_gross_usd": number}, or null if no actual gross is recorded.

Gold: `{"actual_gross_usd":null}`

- full: `{"actual_gross_usd":null}`
- dynamic: `{"actual_gross_usd":null}`
- no_context: `{"actual_gross_usd":null}`

### tribute-fact

What total running time in minutes appears for the initial tribute revue in the frozen Tribute Concert Planner? Return {"running_time_minutes": number}.

Gold: `{"running_time_minutes":48.5}`

- full: `{"running_time_minutes":48.5}`
- dynamic: `{"running_time_minutes":48.5}`
- no_context: `{"running_time_minutes":null}`

### tribute-unknown

How many tickets were actually sold for the tribute revue? Return {"tickets_sold": number}, or null if the frozen source does not document sales.

Gold: `{"tickets_sold":null}`

- full: `{"tickets_sold":null}`
- dynamic: `{"tickets_sold":null}`
- no_context: `{"tickets_sold":null}`

### prosthetic-fact

How many lead SFX makeup artists are configured in the frozen Prosthetic Chair Optimizer? Return {"lead_artists": number}.

Gold: `{"lead_artists":3}`

- full: `{"lead_artists":3}`
- dynamic: `{"lead_artists":3}`
- no_context: `{"lead_artists":null}`

### prosthetic-unknown

What is the full name of the lead makeup artist assigned to the optimizer’s current crew? Return {"lead_artist_name": string}, or null if the frozen source gives only counts or roles.

Gold: `{"lead_artist_name":null}`

- full: `{"lead_artist_name":null}`
- dynamic: `{"lead_artist_name":null}`
- no_context: `{"lead_artist_name":null}`

### vehicle-fact

What track width in millimeters is displayed in the frozen Vehicle Packaging Studio? Return {"track_width_mm": number}.

Gold: `{"track_width_mm":1730}`

- full: `{"track_width_mm":1730}`
- dynamic: `{"track_width_mm":1730}`
- no_context: `{"track_width_mm":null}`

### vehicle-unknown

What is the VIN of the physical car measured for the Vehicle Packaging Studio preset? Return {"vin": string}, or null if no VIN is documented.

Gold: `{"vin":null}`

- full: `{"vin":null}`
- dynamic: `{"vin":null}`
- no_context: `{"vin":null}`

### orbit-refund

Orbit customer: first paid subscription purchased 12 days ago, first refund, and no permission to cancel yet. Under the stored policy, are they within the refund window, and may support cancel without their confirmation? Return {"within_refund_window": boolean, "cancel_without_confirmation": boolean}.

Gold: `{"within_refund_window":true,"cancel_without_confirmation":false}`

- full: `{"within_refund_window":true,"cancel_without_confirmation":false}`
- dynamic: `{"within_refund_window":true,"cancel_without_confirmation":false}`
- no_context: `{"within_refund_window":null,"cancel_without_confirmation":null}`

### orbit-renewal

An Orbit customer requests a refund of an annual renewal from two days ago. Can support promise automatic approval, and is support review required? Return {"promise_automatic_approval": boolean, "support_review_required": boolean}.

Gold: `{"promise_automatic_approval":false,"support_review_required":true}`

- full: `{"promise_automatic_approval":false,"support_review_required":true}`
- dynamic: `{"promise_automatic_approval":false,"support_review_required":true}`
- no_context: `{"promise_automatic_approval":null,"support_review_required":null}`

### orbit-price

An Orbit workspace has seven paid Team collaborators. What is its monthly cost under the stored per-collaborator rate, and how many collaborators does the free plan support? Return {"team_monthly_usd": number, "free_collaborators": number}.

Gold: `{"team_monthly_usd":84,"free_collaborators":3}`

- full: `{"team_monthly_usd":84,"free_collaborators":3}`
- dynamic: `{"team_monthly_usd":84,"free_collaborators":3}`
- no_context: `{"team_monthly_usd":null,"free_collaborators":null}`

### orbit-theme

For an Orbit theme toggle, should an explicit choice persist in localStorage, should it follow prefers-color-scheme without an explicit choice, and must the toggle work by keyboard? Return {"persist_local_storage": boolean, "fallback_system_theme": boolean, "keyboard_required": boolean}.

Gold: `{"persist_local_storage":true,"fallback_system_theme":true,"keyboard_required":true}`

- full: `{"persist_local_storage":true,"fallback_system_theme":true,"keyboard_required":true}`
- dynamic: `{"persist_local_storage":true,"fallback_system_theme":true,"keyboard_required":true}`
- no_context: `{"persist_local_storage":null,"fallback_system_theme":null,"keyboard_required":null}`

### orbit-rollback

Orbit error rates rise after a deployment involving a database change. Should the team restore the previous versioned image and verify the health endpoint? May they reverse the database migration without an explicit recovery plan? Return {"restore_image_and_check_health": boolean, "reverse_migration_without_plan": boolean}.

Gold: `{"restore_image_and_check_health":true,"reverse_migration_without_plan":false}`

- full: `{"restore_image_and_check_health":true,"reverse_migration_without_plan":false}`
- dynamic: `{"restore_image_and_check_health":true,"reverse_migration_without_plan":false}`
- no_context: `{"restore_image_and_check_health":null,"reverse_migration_without_plan":null}`

### orbit-offsite

The Orbit offsite is in October and dietary requirements are due one month before departure. What city hosts it and what numbered month is the dietary deadline? Return {"city": string, "dietary_deadline_month": number}.

Gold: `{"city":"Lisbon","dietary_deadline_month":9}`

- full: `{"city":"Lisbon","dietary_deadline_month":9}`
- dynamic: `{"city":"Lisbon","dietary_deadline_month":9}`
- no_context: `{"city":null,"dietary_deadline_month":null}`

### orbit-digest

At what local workspace time does Orbit send its daily digest, and can users opt out? Return {"workspace_local_time": "HH:MM", "can_opt_out": boolean}.

Gold: `{"workspace_local_time":"09:00","can_opt_out":true}`

- full: `{"workspace_local_time":"09:00","can_opt_out":true}`
- dynamic: `{"workspace_local_time":"09:00","can_opt_out":true}`
- no_context: `{"workspace_local_time":null,"can_opt_out":null}`

### orbit-unknown

What exact monthly USD price has Orbit negotiated for Acme Corporation’s Enterprise contract? Return {"enterprise_monthly_usd": number}, or null if no account-specific quote is stored.

Gold: `{"enterprise_monthly_usd":null}`

- full: `{"enterprise_monthly_usd":null}`
- dynamic: `{"enterprise_monthly_usd":null}`
- no_context: `{"enterprise_monthly_usd":null}`
