# Project Context: Keep the Transcript (workshop paper)

## Identity

This paper shows that a retrievable per-screen index does not beat keeping the full OCR screen history in context for within-task recall in mobile GUI agents, and that two evaluation pitfalls, earliest-source scoring (worth up to 15 points of localization) and current-screen leakage (which reverses a 17-point result), each exceed every writer effect we measured.

Problem: a GUI agent must sometimes type text it saw many screens ago (a delayed information need). Who is affected: anyone building long-horizon mobile agents with memory modules; anyone evaluating them.

After 60 seconds a reader should remember: (1) full history wins on clean data (58.7 vs 44.2 localization, p=0.008); (2) training the index writer does not help because single-entry quality is capped and the oracle gain is redundancy; (3) filter cases where the answer is on the current screen, and score any valid source screen, or your numbers are wrong.

## Venue

- Target: ML/agents workshop (NeurIPS/ICLR-style), 4 pages + references
- Format: single column, no \smartparagraph; bold paragraph labels allowed
- Register: base/terse empirical (negative result + methodology)

## Term map (canonical names; use ONLY these)

- delayed information need: a step whose typed text appeared on an earlier screen and not on the current screen
- gap: steps between the source screen and the step that needs it
- full history (B): all earlier screens' OCR text in context
- screen index (E): one LLM-written line per screen; reader picks a screen, then reads its full text
- directory-only (D), summary (C), no-history (A), gold-screen read (F)
- writer: Qwen2.5-7B-Instruct that writes index lines; reader: Qwen2.5-14B-Instruct (second reader: 7B)
- localization: reader names a screen that contains the answer (any valid source screen)
- end-to-end: typed text matches the gold text
- earliest-source scoring (pitfall 1); current-screen leakage (pitfall 2)
- short set (t median 11, n=85 clean), long set (t>=16, n=53 clean), held-out set (t>=16, n=50 clean)

## Contributions (claims with evidence; all on clean subsets)

### Claim 1: delayed needs exist and benchmarks hide them (§2)
AITZ: 0 of 18,643 steps. GUI-Odyssey (300 sampled trajectories): 2.05% of steps, 31.1% of trajectories; gap median 5, max 27. Evidence: mining script verify_and_bm25.py + filter. STRONG.

### Claim 2: full history beats the screen index (§4.1, §4.3)
Short set n=85: localization 65.9 vs 49.4 (p=0.035), end-to-end 44.7 vs 21.2 (p=0.0005). Combined 138: 58.7 vs 44.2 (p=0.008), 34.1 vs 20.3 (p=0.002). Holds for a 7B reader. Long set (t>=16): both degrade, difference not significant (47.2 vs 35.8, n=53). STRONG; held-out: B 44.0 vs D 32.0 (p=0.26), e2e 24 vs 34 (p=0.18).

### Claim 3: training the writer cannot close the gap (§4.2)
DPO from reader feedback, forced two-field format, value-bearing entries, multi-view: 43.5–49.4 vs 49.4 baseline, all p>0.4. Oracle any-of-5 reaches 76.5 but each candidate hits 49–66 and the gain is redundancy (34/85 cases hit by all five, 20/85 by none). STRONG.

### Claim 4: two evaluation pitfalls (§4.4)
Earliest-source scoring: 47% of cases have >=2 valid source screens; fixing it raises index localization 34.1 -> 49.4, full history 54.1 -> 65.9. Current-screen leakage: 28% (short) / 58% (long) of mined cases; on leaked long cases a text-overlap gating method appeared to beat full history by 16 points (p=0.01) and loses by 12 points on clean cases (p=0.019). STRONG.

## Framing
- Paper type: measurement / negative result
- Closest works: ReadAgent (gist + lookup; our index is this design for GUI), GUI-Rise (summaries), PAL-UI (look-back), Mobile-Agent-E / AutoDroid (cross-task memory, different need), lost-in-the-middle / RULER (long-context evaluation)
- Positioning sentence: Unlike cross-task memory systems, we study within-task recall; unlike gist-and-lookup readers, we train the writer against the reader and show the ceiling is redundancy, not writing quality.

## Locked decisions
1. Report only clean subsets (leakage filtered). Contaminated numbers appear only in the pitfall section.
2. Localization = any valid source screen.
3. Paired McNemar tests, n stated everywhere.
4. No claim about token cost as a motivation (full history fits: median 1,088 tokens).

## Open questions
1. (resolved) held-out set done.
2. Whether to include the second-reader table or a sentence.

## Section architecture
| Section | Pages | Key claim | Tables |
|---|---|---|---|
| 1 Intro | 0.7 | all | — |
| 2 Delayed needs | 0.5 | Claim 1 | Tab 1 prevalence |
| 3 Setup | 0.5 | conditions, metrics | — |
| 4 Results | 1.7 | Claims 2–4 | Tab 2 main, Tab 3 writer/oracle, Tab 4 length, Tab 5 pitfalls |
| 5 Related work | 0.35 | positioning | — |
| 6 Lessons | 0.25 | synthesis | — |
