# Project Context: Verifier-Supervised Look-Back (workshop paper, method version)

## Identity
This paper shows that a GUI agent can learn to look back at the right earlier screen without human labels, by training a per-screen relevance scorer on labels produced by an automatic verifier, and that this scorer localizes the needed screen in 72.3% of 188 verified cases against 54.8% for full-history context (p<0.001), with the largest gain on late needs (t>=16: 67.3 vs 46.0, p=0.001).

Problem: delayed information needs (text seen screens ago must be typed now). Full history and gist-and-lookup indexes both degrade with history length because one call must pick among all screens. Key abstraction: **verifier-supervised look-back** (the verifier that mines the cases also labels the training pairs; no human in the loop).

After 60 s: (1) delayed needs are real and absent from short benchmarks; (2) scoring each earlier screen independently, trained from free verifier labels, beats reading the whole history, especially late in a task; (3) the prompted index route is a dead end (ceiling = full history), and two evaluation filters are required.

## Venue
ML/agents workshop, 4 pages + refs, single column; base register.

## Term map
- delayed information need; source screen; gap; need step index t
- full history (B); screen index (E); directory-only (D); summary (C); no-history (A); gold-screen read (F); BM25
- look-back scorer (ours): Qwen2.5-7B-Instruct + LoRA, input (task, current screen, one earlier screen, distance), output P(Yes); untrained scorer = same prompt, no LoRA
- verifier: answer string appears in OCR of an earlier screen and not on the current screen (current-screen leakage filter); any-valid scoring
- short set n=85, long set n=53, held-out set n=50 (all clean); five folds grouped by trajectory
- localization; end-to-end; reader for the read stage = Qwen2.5-14B-Instruct

## Claims (clean cases)
1. Problem (§2): AITZ 0/18,643; GUI-Odyssey 2.05% of steps, 31.1% of sampled trajectories; gap median 5. STRONG.
2. Method result (§4.1): scorer 72.3 vs B 54.8 vs index 41.0 vs untrained 50.0 (n=188, p<0.001 each); t>=16 67.3 vs 46.0 (p=0.001); held-out fold 74.0 vs 44.0 (p=0.001). STRONG. End-to-end (read with history): 44.7 vs 31.4 (p<0.001); t>=16 42.5 vs 20.4; t<=15 48.0 = 48.0; held-out 48.0 vs 24.0. Single-screen read: 35.1 overall, 33.6 on t>=16, below B on t<=15 (37.3 vs 48.0).
3. Why the index route fails (§4.2, compressed from the negative-result draft): E 49.4 vs B 65.9 on short set; writer training rounds 43.5–49.4; source-line rewrite ceiling 59–66 = full history; rp 44.7. STRONG.
4. Limits and pitfalls (§4.3): t>=20 (n=27) scorer 37.0 = B; gap 13+ 51.6 vs 64.5 (p=0.39); earliest-source scoring and current-screen leakage effect sizes. STRONG.
5. Confidence (optional, one sentence): pmax AUC 0.768 for localization correctness; fallback to B below 0.5 gives 75.0.

## Locked decisions
- Clean subsets only; any-valid scoring; paired McNemar; folds by trajectory; untrained scorer is the mandatory ablation.
- Scorer cost: t forward passes per step, no generation; state it.
- Honest: CV on one dataset; held-out set is one fold, not an external set.

## Section plan
| Section | Pages | Claim | Tables |
|---|---|---|---|
| 1 Intro | 0.8 | all | |
| 2 Delayed needs + verifier | 0.5 | 1 | Tab 1 |
| 3 Method: verifier-supervised look-back | 0.5 | design | (pipeline sketch optional) |
| 4.1 Main result | 0.8 | 2 | Tab 2 main (by set, by t) |
| 4.2 Index route ceiling | 0.5 | 3 | Tab 3 |
| 4.3 Limits + pitfalls | 0.5 | 4 | Tab 4 |
| 5 Related, 6 Conclusion | 0.4 | | |
