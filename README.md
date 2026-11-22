# Verifier-Supervised Look-Back

Code and results for *Verifier-Supervised Look-Back: Label-Free Screen Retrieval for Delayed
Information Needs in Mobile GUI Agents*.

A GUI agent often has to type text it saw many screens earlier. The question is which earlier
screen to re-read. Training a model to answer it normally needs human labels. This repository
shows that the automatic verifier used to *mine* such cases also *labels* every earlier screen
for free, and that training on those labels is what makes look-back work.

**Headline result (188 cross-validated cases):** the verifier's labels lift a full-history reader
from 54.8% to 65.4% localization and a per-screen scorer from 50.0% to 72.3%. The two trained
variants are statistically indistinguishable (p=0.086), so the supervision, not the architecture,
is the lever. On a fourth sample of trajectories held out from every design decision, they reach
76.3% and 79.6% against 59.1% for prompting.

---

## 1. What I wrote myself

Everything in `src/` is mine, written for this project. Nothing in `src/` is forked or adapted
from another repository. The external dependencies I call are:

| External | Role | Where called |
|---|---|---|
| EasyOCR | screenshot → OCR text | `ocr_shots.py`, `ocr_shard.py` |
| HuggingFace `transformers` | model loading, generation, logits | all `train_*`, `eval_*`, `read_*`, `score_*` |
| `peft` | the LoRA adapter | `train_scorer.py`, `train_fullhist.py` |
| Qwen2.5-3B/7B/14B-Instruct | the base models | same |
| GUI-Odyssey, AITZ | the trajectory corpora (annotations + screenshots) | `sample_*.py` |

The DPO loss in the writer experiment, the McNemar test, the BM25 scorer, and the trajectory-grouped
cross-validation splitter are all hand-written here rather than taken from a library; they are in
`gen_directory_r1.py`, `analyze_all.py`, `verify_and_bm25.py` and `build_scorer_data.py` respectively.

## 2. Repository layout

```
src/        every script; the pipeline below runs in this order
results/    every JSON this project produced (cases, labels, per-fold predictions, eval outputs)
figures/    the two report figures and the matplotlib scripts that draw them
report/     the NeurIPS-format PDF
```

## 3. Pipeline, in order

### 3.1 Build the dataset

| File | What it does |
|---|---|
| `sample_and_fetch.py` | First sample. Picks trajectories from GUI-Odyssey, applies rule A (any TYPE action whose argument is ≥3 chars and absent from the task description), downloads every screenshot up to the last candidate step. |
| `sample_long.py` | Second sample: trajectories of ≥20 steps with a candidate at step ≥16. `MINLEN`, `MINT`, `N` are environment variables. |
| `sample_holdout.py` | Third sample (seed 7), excluding every trajectory used by the first two. |
| `sample_more.py` | Fourth sample (seed 11), excluding all three earlier ones. This is the external test set. |
| `ocr_shots.py` | Runs EasyOCR over every new screenshot and appends `{img, elems:[{t,b,c}]}` to `parse_odyssey.jsonl`. Resumable: it skips images already in the file. |
| `ocr_shard.py` | Same, with `SHARD`/`NSHARD` so two GPUs can split the queue, and `OUT` to write a separate shard file. |

### 3.2 Verify the cases and produce the labels

| File | What it does |
|---|---|
| `verify_and_bm25.py` | **The verifier for the first sample**, plus the BM25 baselines. `norm()` lower-cases and strips whitespace and punctuation. `frame_text()` joins a screen's OCR elements. The `BM25` class implements Okapi BM25 from scratch (`score()` returns one score per earlier screen). Prints the mining funnel and the gap distribution. |
| `verify_long.py`, `verify_holdout.py`, `verify_more.py` | Same verifier for samples 2–4. Each writes `cases_*.json` (one record per need: `ep, t, src, ans, gap`) and `valid_screens_*.json` (**the label set**: for each case, every earlier screen whose OCR contains the answer). Two filters live here: a candidate is dropped if the answer is also on the current screen, and (in `verify_more.py`) if it appears in the task's step-by-step instruction field. |
| `build_scorer_data.py` | Turns cases + label sets into `scorer_cases.json` (188 cases with task text, current-screen text, fold id) and `scorer_pairs.json` (2,861 `(case, earlier screen, 0/1, fold)` items). **Assigns folds by trajectory**, so no trajectory is split across train and test. |
| `build_scorer_more.py` | The same for the external sample. |

### 3.3 Train

| File | What it does |
|---|---|
| `train_scorer.py` | **The per-screen scorer.** Builds a Yes/No prompt per (case, earlier screen) pair, takes the logits of `Yes`/`No` at the answer position, applies a two-way softmax and minimises weighted cross-entropy (`POSW`, default 3). LoRA rank 16 on q/k/v/o via `peft`. `FOLD=k` trains on the other four folds and scores fold *k*; `FOLD=ext` trains on all 188 and scores the external set. `TAG` names the output; `NODIST=1` removes the distance from the prompt (ablation); `MODEL` swaps the base model. Writes `scorer{TAG}_fold{FOLD}_probs.json` = `{case: {screen: P(Yes)}}`. |
| `train_fullhist.py` | **The full-history baseline, trained on the same labels.** Same folds, same LoRA, but one example per case: the prompt holds every earlier screen and the target is the screen number, with the loss on the number only. Writes predictions in the same format (`{pred: 1.0}`) so the evaluation code is shared. |
| `score_untrained.py` | The scorer's prompt on the same base model **without** the adapter. This is the ablation that isolates the labels from the prompt. |

### 3.4 Evaluate

| File | What it does |
|---|---|
| `eval_scorer.py` | Pools the five folds, scores localization against `valid_screens` (**any-valid scoring**: any screen containing the answer counts), and runs paired McNemar tests against full history and the index. `mc()` is the McNemar implementation; `PREFIX` selects which model's predictions to read. |
| `read_scorer.py` | **The read stage.** Takes a localization prediction, builds the 14B reader prompt, and scores end-to-end accuracy. `HIST=1` = read with history (full history plus the chosen screen repeated and marked); otherwise single-screen read. `MARK` picks which screen to mark (`scorer`, `gold`, `recent`, `random`, `top2`) — these are the read-stage controls in the report. `SET=_more` evaluates the external set. |
| `eval_long.py` | The prompted baselines (`MODE=B` full history, `MODE=D` screen index) on any case set via `CASES`. |
| `eval_calib.py` | The calibrated two-pass reader used in the earlier index experiments. |
| `analyze_all.py` | **The one script that reproduces every table in the report**: the main table, the by-gap table, the external table and the ablations, each with paired tests. |
| `analyze_gate.py`, `fill_holdout.py` | Analysis helpers kept for the record (the text-overlap gating rule reported as a pitfall, and the held-out back-fill). |

### 3.5 The screen-index route (reported as a negative result)

| File | What it does |
|---|---|
| `gen_directory_long.py` | The prompt-only writer: one ≤32-token index line per screen. |
| `gen_directory_r1/r2/r3.py` | Writer variants: DPO-trained (r1, with a hand-written DPO loss), forced two-field format (r2), values allowed in the line (r3). |
| `gen_directory_rp.py` | Rewrites every screen's line with the oracle's retrieval prompt and sampling — the realizable version of the oracle. |
| `oracle_directory.py` | The oracle: samples five candidate lines for the source screen and reports which cases any of them rescues. |
| `full_matrix.py` | The full baseline matrix (no history / full history / summary / directory / index / gold-screen read). |

### 3.6 Orchestration

`run_*.sh` are the driver scripts that ran the experiments on two shared GPUs. They all follow the
same pattern: `pick()` waits until a GPU has enough free memory before starting a job, every stage
skips itself if its output file already exists, and failures retry. `run_exp2.sh` runs the trained
full-history baseline and the three ablations; `run_ext.sh` runs the whole external-set pipeline;
`run_fill.sh` fills the two comparisons added after review.

## 4. Reproducing the results

```bash
# environment
conda create -n vsl python=3.11 && conda activate vsl
pip install torch transformers peft easyocr

export ROOT=/path/to/guiodyssey        # scripts read this path; edit the ROOT constant at the top of each file

# 1. data: sample trajectories, download screenshots, OCR them
MINLEN=16 MINT=12 N=400 python src/sample_more.py
python src/ocr_shots.py

# 2. verify and label
python src/verify_more.py              # -> cases_more.json, valid_screens_more.json
python src/build_scorer_data.py        # -> scorer_cases.json, scorer_pairs.json (188 cases, 2,861 pairs)

# 3. train (about 20 min per fold on one 48GB GPU)
for f in 0 1 2 3 4; do FOLD=$f python src/train_scorer.py; done
for f in 0 1 2 3 4; do FOLD=$f python src/train_fullhist.py; done
python src/score_untrained.py          # the no-adapter ablation

# 4. ablations
for f in 0 1 2 3 4; do FOLD=$f TAG=_nodist NODIST=1 python src/train_scorer.py; done
for f in 0 1 2 3 4; do FOLD=$f TAG=_posw1 POSW=1   python src/train_scorer.py; done
for f in 0 1 2 3 4; do FOLD=$f TAG=_3B MODEL=Qwen/Qwen2.5-3B-Instruct python src/train_scorer.py; done

# 5. read stage and its controls
SRC=trained HIST=1 python src/read_scorer.py                 # read with history
SRC=trained            python src/read_scorer.py             # single-screen read
for m in gold recent random top2; do SRC=trained HIST=1 MARK=$m python src/read_scorer.py; done

# 6. prompted baselines
CASES=long MODE=B python src/eval_long.py                    # full history
CASES=long MODE=D python src/eval_long.py                    # screen index

# 7. external set: train on all 188, evaluate once
FOLD=ext python src/train_scorer.py
FOLD=ext python src/train_fullhist.py
SRC=trained SET=_more HIST=1 python src/read_scorer.py

# 8. every table in the report
python src/analyze_all.py

# 9. the report figures
python figures/make_fig1.py && python figures/make_fig2.py
```

`results/` already holds the outputs of all of the above, so `python src/analyze_all.py` reproduces
every number in the report without a GPU.

## 5. Notes on honesty

- Every condition is a **single training run**; the paired tests account for case-level variance only.
- The three case sets used for cross-validation and the external set come from the same corpus
  (GUI-Odyssey) and one OCR engine (EasyOCR).
- The training labels and the localization metric are the same substring check, so training points
  the scorer at the metric it is scored on. A spot check of 20 cases is reported in the paper.
- Two earlier conclusions were **retracted** during this project after we found a data defect
  (cases whose answer was also on the current screen). The filter that removes them is in
  `verify_*.py`, and the retraction is reported in the paper as one of the two mandatory filters.
