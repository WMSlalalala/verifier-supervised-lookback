# Project Context: Verifier-Supervised Look-Back (6-page, final)

## Identity
This paper shows that the verifier that mines delayed information needs in GUI-agent trajectories also supplies free training labels for look-back, and that this label-free supervision, not the retrieval architecture, is what makes look-back work: it lifts a full-history reader by 10.6 points and a per-screen scorer by 22.3 points over their prompted versions, and the per-screen scorer's remaining advantage is confined to gaps of 8-12 screens (78% vs 56%, p=0.003).

## Headline numbers (all clean, any-valid scoring, paired McNemar)
In-fold, n=188, five folds grouped by trajectory, localization:
- full history prompted 54.8 | screen index prompted 41.0 | per-screen scorer prompted (untrained) 50.0
- full history SFT on verifier labels 65.4 (+10.6 over prompted, p=0.019)
- per-screen scorer SFT on verifier labels 72.3 (+22.3 over prompted; vs full-history SFT p=0.086)
By gap (scorer vs full-history SFT): 1-2 29/29; 3-4 76/82; 5-7 81/81; 8-12 78/56 (p=0.003); 13+ 52/42 (both below prompted 65)
External set (fourth sample, 93 cases, train on all 188, evaluate once):
- scorer 79.6 | full-history SFT 76.3 (p=0.63) | full history prompted 59.1 (p=0.003) | index 37.6 | untrained scorer 41.9
- end-to-end read with history: scorer 49.5 vs prompted full history 23.7 (p<0.001); single-screen read 37.6 (p=0.016)
End-to-end in-fold (read with history): scorer 44.7 vs prompted full history 31.4 (p<0.001); t>=16 42.5 vs 20.4
Read-stage controls (in-fold, e2e): gold-marked 45.2 | scorer-marked 44.7 | most-recent 38.8 | random 36.7 | top-2 45.2
Ablations (localization, n=188): no distance feature 70.7 | positive weight 1 72.3 | 3B scorer 68.1 (t>=20: 48.1, best)
Index route: writer DPO 45.9, format 47.1, values 49.4, three lines 43.5, retrieval prompt 44.7; oracle single line 58.8-65.9, best-of-5 76.5

## Claim structure (what the paper argues)
1. Problem + verifier (free labels). 2. Supervision, not architecture, is the lever (both arch improve). 3. Decomposition helps where one call must weigh many candidates (gaps 8-12). 4. External validation. 5. Honest limits: gaps 13+ both trained variants fall below prompted full history; t>=20 small n; one dataset.

## Venue / format
ML-agents workshop, 6 pages + references, single column, base terse register.

## Locked
- Report both instantiations side by side; never claim the architecture alone is the contribution.
- Any-valid scoring; current-screen leakage filter; folds grouped by trajectory; untrained ablation mandatory.
- External set = fourth sample, trained on all 188, evaluated once.
