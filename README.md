# Verifier-Supervised Look-Back

When a phone agent reaches a text field, the value it needs may have disappeared from the screen. This project studies one step of that interaction. Given the task, the current screen's OCR and the preceding screens, can a model find a screen that contains the value and then type it? At training time, the trajectory records what the user typed. A normalized substring search uses that record to label earlier screens automatically.

[Final report (PDF)](doc/Final-Report.pdf) · [Presentation (PowerPoint)](doc/Slides.pptx) · [Presentation (PDF)](doc/Slides.pdf)

On 188 cases from 182 GUI-Odyssey trajectories, the same 7B per-screen scorer improved from 94/188 to 136/188 correct screen choices after verifier-supervised training (50.0% to 72.3%). With the same downstream reader and history, text recovery rose from 35.1% to 44.7%. On 93 cases from 90 additional trajectories in the same corpus, the trained scorer localized 74/93 and recovered the recorded text on 46/93. The report also compares a trained full-history selector, sensitivity to the definition of distance, readout controls and failure cases.

## Repository map and attribution

| Location | Contents |
| --- | --- |
| [doc/](doc/) | The three final files linked above. The existing `report-src/` and `slides-src/` directories preserve the earlier manuscript and deck generators. |
| [src/](src/) | The author's 54 Python programs and 33 shell drivers for sampling, OCR, verification, indexing, training, evaluation and analysis. A file and function index appears below. |
| [data/](data/) | Derived OCR text, generated screen-directory entries and a screenshot manifest. |
| [results/](results/) | 112 JSON files, including case lists, screen labels, train/test assignments, per-fold predictions, reader outcomes and earlier comparisons. |
| [EXPERIMENT-LOG.md](EXPERIMENT-LOG.md) | Chronological experiment record, including the current-screen leakage finding and retracted comparisons. |
| [configure.sh](configure.sh) | Points the original experiment programs at a local flat data directory and Python interpreters. It edits the copy of `src/` next to it. |

The author implemented the candidate and leakage filters, grouped folds, verifier labels, retriever prompts and training loops, weighted binary objective, writer preference loss, screen-index variants, BM25 baselines, reader controls, metrics, paired tests and run drivers. EasyOCR provides character recognition, Hugging Face Transformers loads the Qwen2.5 models and computes logits/generations, PEFT supplies the LoRA adapters, and PyTorch handles tensor operations and optimization. Screens and human demonstrations come from [GUI-Odyssey](https://huggingface.co/datasets/OpenGVLab/GUI-Odyssey). AITZ supplies the short-task comparison. The original image collection, annotation directory, base models and trained writer adapter are external to this checkout.

## Recount the reported results on a CPU

From the repository root, run the following Python in an interpreter or save it as a script. It uses only the standard library and the committed predictions. `loc` counts any labeled source screen. `e2e` counts whether the normalized reader output contains the recorded text on that input step.

```python
import json
from pathlib import Path

results = Path("results")
for population, suffix in [("five held-out folds", ""), ("fourth sample", "_more")]:
    for retriever in ("scorer", "fullhist"):
        name = f"{retriever}_trained{suffix}_hist_e2e.json"
        rows = json.loads((results / name).read_text(encoding="utf-8"))
        located = sum(row["loc"] for row in rows)
        typed = sum(row["e2e"] for row in rows)
        print(population, retriever, len(rows), located, typed)
```

| Population | Retriever | Cases | Correct screen | Correct text |
| --- | --- | ---: | ---: | ---: |
| Five held-out folds | Per-screen | 188 | 136 | 84 |
| Five held-out folds | Full history | 188 | 123 | 80 |
| Fourth sample | Per-screen | 93 | 74 | 46 |
| Fourth sample | Full history | 93 | 71 | 48 |

`scorer_cases.json` contains the episode ID, step `t`, recorded value, fold and all valid earlier screen IDs for each development case. The logged `gap` equals `t - min(valid)`, the distance to the first occurrence. The shortest available look-back equals `t - max(valid)`. They differ on 111/188 development cases. The full-history training target uses `max(valid)`. External per-fold probability keys in the trained-model files start at 188.

## Rerun the experiments

The following Bash examples use a fresh clone on Linux. Run them from the repository root. Stage the published inputs and result files together because the original programs expect one flat data directory. Configure the paths once for that clone. The aggregate analysis reads the staged files and runs on a CPU.

```bash
mkdir -p run-data
cp data/*.json* results/*.json run-data/
bash configure.sh "$PWD/run-data" "$(command -v python3)"
python3 src/analyze_all.py
```

**Retrain from the published OCR and labels.** The GPU runs require CUDA-compatible PyTorch, Transformers with Qwen2.5 support, PEFT, Accelerate and access to the Qwen2.5-7B/14B-Instruct weights. The smaller ablation also uses Qwen2.5-3B-Instruct. The reported 7B training runs used a 48 GB GPU. New runs write to `run-data/`. Run the following commands after staging and configuration.

```bash
for fold in 0 1 2 3 4; do
  FOLD=$fold python3 src/train_scorer.py
  FOLD=$fold python3 src/train_fullhist.py
done
python3 src/score_untrained.py
SRC=untrained HIST=1 python3 src/read_scorer.py
SRC=trained HIST=1 python3 src/read_scorer.py
SRC=trained HIST=1 PREFIX=fullhist python3 src/read_scorer.py
python3 src/eval_scorer.py
```

**Ablations and reading controls.** Use the base scorer's five fold files from the preceding block. The 3B, no-distance and unit-positive-weight variants write separately named predictions.

```bash
for fold in 0 1 2 3 4; do
  FOLD=$fold TAG=_nodist NODIST=1 python3 src/train_scorer.py
  FOLD=$fold TAG=_posw1 POSW=1 python3 src/train_scorer.py
  FOLD=$fold TAG=_3B MODEL=Qwen/Qwen2.5-3B-Instruct python3 src/train_scorer.py
done
for mark in gold recent random top2; do
  SRC=trained HIST=1 MARK=$mark python3 src/read_scorer.py
done
SRC=trained HIST=0 python3 src/read_scorer.py
```

**Fourth sample.** Train on all 188 development cases and evaluate the disjoint sample. The published case and pair files already contain the task descriptions needed by these retrievers. The results table above uses the same 14B reader with the whole history and the selected screen marked for both trained models.

```bash
FOLD=ext python3 src/train_scorer.py
FOLD=ext python3 src/train_fullhist.py
SET=_more python3 src/score_untrained.py
SET=_more SRC=trained HIST=0 python3 src/read_scorer.py
SET=_more SRC=trained HIST=1 python3 src/read_scorer.py
SET=_more SRC=trained HIST=1 PREFIX=fullhist python3 src/read_scorer.py
python3 src/analyze_all.py
```

**Remine from the original corpus.** Place the source annotation JSON files under `run-data/annotations/` and install EasyOCR for fresh OCR. `sample_more.py` uses the three staged sample manifests to exclude previous trajectories, plus the staged screenshot index to fetch images. The OCR pass skips images with existing records. `verify_more.py` checks candidate text against the current screen, earlier screens and the instruction field. `build_scorer_more.py` then recreates the external task/candidate pairs. The prompted baselines read original annotations for task descriptions.

```bash
MINLEN=16 MINT=12 N=400 python3 src/sample_more.py
python3 src/ocr_shots.py
python3 src/verify_more.py
python3 src/build_scorer_more.py
CASES=more MODE=B python3 src/eval_long.py
CASES=more MODE=D python3 src/eval_long.py
```

The first three samples use `sample_and_fetch.py`, `sample_long.py` and `sample_holdout.py`. Their committed manifests fix the actual sample membership. The raw comparison scripts and historical shell drivers retain machine-specific settings used in those runs. Each reported training condition used a single run per fold. Paired tests measure disagreement on the same cases. The held-out trajectories share a corpus and OCR engine with the development data.

## Source code index

The tables link all 54 Python programs and 33 Bash drivers under `src/`. Each row names the functions and classes defined in those files. “Module body” and “Script body” mean the work runs directly from top-level statements. The index also covers the earlier screen-directory experiments recorded in the experiment log.

**Recurring Python helpers.** `norm` lowercases text and removes whitespace and the punctuation specified in that file. The mining routines remove commas, and several evaluation routines also remove periods. `toks` extracts lowercase alphanumeric tokens for BM25 or set overlap. `gen` generates and decodes a bounded model response. `pct` and `acc` express successful cases as a percentage. `mc` computes the paired net difference and the continuity-corrected asymptotic McNemar p-value. `L` reads a JSON artifact when it exists.

**Prompt helpers.** `prompt` constructs the task-specific model input. `prompt_for` formats a writer prompt for one screen. `score_prompt` formats the independent candidate-screen Yes/No question. `p_locate` requests a screen index. `p_read` requests the text to enter. The individual programs below specify the information each prompt can see.

### Sampling, verification and dataset construction

| Program | Purpose | Functions and classes |
| --- | --- | --- |
| [sample_and_fetch.py](src/sample_and_fetch.py) | Samples 300 eligible episodes and downloads indexed frames across each episode. `get` retrieves one image, skips an existing download and retries transfer failures. | `norm`, `get` |
| [sample_long.py](src/sample_long.py) | Samples long episodes outside the first sample. The minimum episode length, earliest eligible input step and sample size are configurable. `get` retrieves a frame through the last selected input. | `norm`, `get` |
| [sample_holdout.py](src/sample_holdout.py), [sample_more.py](src/sample_more.py) | Draws the third and fourth samples. The third excludes the previous two manifests and the fourth excludes all three. `get` downloads each required frame through the last selected input. | `norm`, `get` |
| [ocr_shots.py](src/ocr_shots.py) | Runs English EasyOCR on new PNGs. Appends text, bounding box and confidence for retained detections. | Module body |
| [ocr_shard.py](src/ocr_shard.py) | Splits the remaining ordered image list by shard number and appends each worker’s OCR results to its configured output. | Module body |
| [verify_and_bm25.py](src/verify_and_bm25.py) | Mines earliest OCR matches in the first sample before the final leakage filters. `frame_text` joins detected strings. `BM25.__init__` builds token statistics, `BM25.score` scores each earlier screen, and `evaluate` computes retrieval recall and rank for context and oracle queries. | `norm`, `toks`, `frame_text`, `BM25`, `BM25.__init__`, `BM25.score`, `evaluate` |
| [verify_long.py](src/verify_long.py), [verify_holdout.py](src/verify_holdout.py) | Requires current-screen OCR, excludes values visible there, and writes each case’s earliest source, distance and all matching earlier screen IDs for the second and third samples. | `norm` |
| [verify_more.py](src/verify_more.py) | Applies the fourth-sample verifier and also excludes values found in the step-by-step instruction field. | `norm` |
| [fix_metric.py](src/fix_metric.py) | Rebuilds the first sample’s full set of valid historical screen IDs from cleaned cases and OCR for any-valid localization scoring. | `norm` |
| [build_scorer_data.py](src/build_scorer_data.py) | Joins the three development lists with task and current OCR, groups by episode for five folds and emits a binary training pair for each readable earlier screen. | Module body |
| [build_scorer_more.py](src/build_scorer_more.py) | Produces the corresponding fourth-sample case and pair files. Training on the development pool holds these cases out for evaluation. | Module body |

### Verifier-supervised retrievers and readout

| Program | Purpose | Functions and classes |
| --- | --- | --- |
| [train_scorer.py](src/train_scorer.py) | Trains a LoRA-adapted Yes/No screen scorer with weighted cross-entropy. `enc` tokenizes the candidate prompt. Exports per-case candidate scores for held-out folds or external evaluation. | `prompt`, `enc` |
| [score_untrained.py](src/score_untrained.py) | Scores the same candidate task with the base model to provide the untrained comparison. | `prompt` |
| [train_fullhist.py](src/train_fullhist.py) | Fine-tunes a full-history locator on the latest verifier-positive screen index and saves its generated index for each evaluated case. | `prompt` |
| [read_scorer.py](src/read_scorer.py) | Takes retriever predictions, chooses the marked screen(s) for the configured control, prompts the 14B reader and saves per-case localization and text-recovery results. | `norm`, `gen` |
| [eval_scorer.py](src/eval_scorer.py) | Pools per-fold predictions and checks the top screen against each valid set. `report` summarizes a selected subset and compares paired outcomes with prompted baselines. | `pct`, `mc`, `report` |
| [analyze_all.py](src/analyze_all.py) | Aggregates available retriever, ablation, top-two and external artifacts. `load_probs` merges fold probability files and counts loaded folds. `loc_of` checks each highest-scoring candidate against the valid screen IDs. | `L`, `pct`, `mc`, `load_probs`, `loc_of` |

### Screen directories and earlier baselines

| Program | Purpose | Functions and classes |
| --- | --- | --- |
| [stage1_full.py](src/stage1_full.py) | Tests BM25 with three screen representations. `verbatim` joins OCR, `heuristic` combines app names with the first eight spatially sorted OCR items and `llmdir` reads a generated entry. `BM25.__init__` indexes tokens, `BM25.rank` returns scores and `run` summarizes recall for a representation and query type. | `norm`, `toks`, `verbatim`, `heuristic`, `llmdir`, `BM25`, `BM25.__init__`, `BM25.rank`, `run` |
| [fullhist_llm.py](src/fullhist_llm.py) | Compares text generation with current context, full history or a known source. `build` assembles the matching prompt. | `norm`, `build` |
| [fullhist_locate.py](src/fullhist_locate.py) | Separately measures source-index prediction from full OCR history and text generation given the recorded source. | `norm`, `p_locate`, `p_read`, `gen` |
| [full_matrix.py](src/full_matrix.py) | Runs current-only, full OCR, summary and directory conditions plus a known-source read. `hist_block` selects the history representation. The two prompt helpers construct the locator and readout inputs. | `norm`, `gen`, `hist_block`, `p_locate`, `p_read` |
| [hybrid_baseline.py](src/hybrid_baseline.py) | Compares BM25 shortlisting with an LLM reranker and rank fusion. `bm25_order` returns document indices in lexical relevance order. The local lambda `f` reports accuracy in a distance bin. | `toks`, `norm`, `bm25_order`, `gen`, `f` |
| [gen_directory.py](src/gen_directory.py), [gen_directory_long.py](src/gen_directory_long.py), [gen_directory_holdout.py](src/gen_directory_holdout.py), [gen_directory_more.py](src/gen_directory_more.py) | Writes short prompt-only OCR entries for the original, long, third and fourth samples respectively. All four append to the base directory file and skip entries already present. | `prompt_for` |
| [gen_directory_r1.py](src/gen_directory_r1.py) | Loads the trained writer adapter and regenerates directory entries. | Module body |
| [gen_directory_r2.py](src/gen_directory_r2.py) | Prompts for a two-part entry containing a screen’s subject and the types of values available. | `prompt_for` |
| [gen_directory_r3.py](src/gen_directory_r3.py) | Prompts for distinctive concrete values from the source OCR. | `prompt_for` |
| [gen_directory_rp.py](src/gen_directory_rp.py) | Applies the oracle experiment’s sampled writer prompt to every required screen and saves one entry per screen. | Module body |
| [gen_multiview.py](src/gen_multiview.py) | Samples several alternative descriptions of each screen for the multiview comparison. | `prompt_for` |
| [oracle_directory.py](src/oracle_directory.py), [oracle_fixed.py](src/oracle_fixed.py) | Substitutes sampled descriptions for the recorded source’s directory entry and checks whether any enables retrieval. `locate` runs the locator prompt and parses the predicted index. The second program also evaluates membership in the full valid set. | `norm`, `gen`, `p_locate`, `locate` |
| [train_writer.py](src/train_writer.py) | Trains the writer adapter on preferred and rejected descriptions. `encode` tokenizes prompt/response pairs and marks the response boundary. `seq_logp` sums response-token log probabilities under the policy or reference. `batch_loss` computes the direct preference optimization loss and pair accuracy. | `encode`, `seq_logp`, `batch_loss` |
| [cmp_r2.py](src/cmp_r2.py) | Compares r0, r1 and r2 directory quality. `load` reads image-to-entry mappings. `fieldrate` counts recognized right-field labels, `genrate` counts generic left descriptions, `intra` compares entries within episodes, and `discrim` finds each source’s most similar distractor by token-set overlap. The local lambda `fmt` formats the resulting table values. | `toks`, `load`, `fieldrate`, `genrate`, `intra`, `discrim`, `fmt` |

### Reader comparisons and analyses

| Program | Purpose | Functions and classes |
| --- | --- | --- |
| [eval_long.py](src/eval_long.py) | Evaluates prompted full-history or directory localization and text readout for a chosen case set. Saves per-case progress for resumption. | `norm`, `gen` |
| [eval_r1.py](src/eval_r1.py) | Evaluates a chosen directory using one index-selection call followed by a read of the selected screen. Its historical localization flag uses the recorded first source. | `norm`, `gen` |
| [eval_mv.py](src/eval_mv.py) | Changes how many sampled descriptions per screen the locator sees and reads the selected screen’s OCR. | `norm`, `gen` |
| [eval_seg.py](src/eval_seg.py) | Ablates the fields of a structured entry. `segof` extracts the left field, the right field or the full line. | `segof`, `norm`, `gen` |
| [eval_perscreen.py](src/eval_perscreen.py) | Scores directory entries one screen at a time with Yes/No logits, selects the strongest candidate and reads its OCR. | `norm`, `score_prompt`, `gen` |
| [eval_router.py](src/eval_router.py) | Adds screen-score confidence features to the per-screen directory reader’s output for offline routing experiments. | `norm`, `score_prompt`, `gen` |
| [eval_hybrid.py](src/eval_hybrid.py) | Uses full OCR for the most recent screens and short directory entries for older ones. Varies the recent window and optional recency prompt. | `norm`, `gen` |
| [eval_twopass.py](src/eval_twopass.py) | Searches the latest K OCR screens first. A first-pass abstention triggers a second search over older entries. | `norm`, `gen` |
| [eval_calib.py](src/eval_calib.py) | Records two candidate decisions for retrospective threshold selection. `pyes` computes a Yes/No probability for a recent candidate. | `norm`, `pyes`, `gen` |
| [eval_gate_e2e.py](src/eval_gate_e2e.py) | Uses recent-versus-older lexical overlap to choose a candidate, then reads its OCR and evaluates the predicted text. | `norm`, `toks`, `gen` |
| [analyze_long.py](src/analyze_long.py) | Compares the long-sample full-history and directory outcomes by need step and distance using paired tests. | `mc`, `pct` |
| [analyze_hybrid.py](src/analyze_hybrid.py) | Compares the hybrid history variants with full-history and directory baselines across the short and long samples. `load` reads one result file by tag. | `mc`, `pct`, `load` |
| [analyze_calib.py](src/analyze_calib.py) | Evaluates a confidence threshold using cross-validation. `route` selects the first- or second-pass result on each case. | `route`, `acc`, `mc` |
| [analyze_gate.py](src/analyze_gate.py) | Compares token overlap between the current screen and recent or older screens, then evaluates threshold routing against baseline results. | `toks`, `pct`, `mc` |
| [analyze_router.py](src/analyze_router.py) | Tests confidence-based routing. `sigval` orients each confidence feature. `route_acc` and `route3` count correct choices for two and three routes. `best_thr` and `best_thr3` fit one or two cutoffs using the training subset. | `sigval`, `route_acc`, `best_thr`, `route3`, `best_thr3` |
| [analyze_finish.py](src/analyze_finish.py) | Prints short, long and held-out comparisons across reader settings. `sig` flags a p-value below .05, `sub` selects case indices and `table` prints localization, text recovery and paired comparisons. | `L`, `mc`, `pct`, `sig`, `sub`, `table` |
| [fill_holdout.py](src/fill_holdout.py) | Computes historical held-out paired comparisons and edits the corresponding table row in a local draft LaTeX results file. | `pct`, `mc` |

**Shell helpers.** `pick` and `pick_gpu` wait for an eligible GPU and return its index. `free_of` estimates free memory for the specified card using the original machine’s configured capacity. `run` skips a completed output and retries the requested job. `run14` schedules the 14B model across two cards and `run1` runs a job on a single eligible card. The driver table lists only the helpers defined in each file.

### Bash experiment drivers

| Program | Purpose | Functions and classes |
| --- | --- | --- |
| [run_scorer.sh](src/run_scorer.sh) | Trains and scores the five development folds of the per-screen model. | Script body |
| [run_exp.sh](src/run_exp.sh) | Runs full-history training, the no-distance, unit-weight and 3B scorer ablations, and top-two readout on a selected GPU. | Script body |
| [run_exp2.sh](src/run_exp2.sh) | Runs the same comparison set with GPU selection, completed-output checks and retries. | `free_of`, `pick`, `run` |
| [run_read.sh](src/run_read.sh) | Runs single-screen readout for trained and untrained per-screen predictions. | Script body |
| [run_marks.sh](src/run_marks.sh) | Evaluates history readout with oracle, most recent and random screen marks. | Script body |
| [run_fhread.sh](src/run_fhread.sh) | Runs both marked-history and single-screen readout on the trained full-history locator’s development predictions. | `free_of`, `pick` |
| [run_ext.sh](src/run_ext.sh) | Waits for fourth-sample download completion, merges OCR, verifies cases, creates directory entries and pairs, and runs trained/untrained scorer, prompted baselines and readouts. | `free_of`, `pick` |
| [run_ext2.sh](src/run_ext2.sh) | Retries the external per-screen scorer’s marked-history readout. | `free_of`, `pick` |
| [run_fh_ext.sh](src/run_fh_ext.sh) | Trains the full-history locator on all development examples and localizes the fourth sample. | `free_of`, `pick` |
| [run_fill.sh](src/run_fill.sh) | Runs external marked-history readout for the full-history locator and development marked-history readout for the untrained scorer. | `free_of`, `pick`, `run` |
| [run_closeloop.sh](src/run_closeloop.sh) | Trains the preference-based writer, regenerates its directory and evaluates it. | Script body |
| [run_rest.sh](src/run_rest.sh) | Runs source-entry oracle substitution and the BM25/LLM hybrid baseline. | Script body |
| [run_r2.sh](src/run_r2.sh) | Waits for r2 entry generation and evaluates that directory. | Script body |
| [run_r3.sh](src/run_r3.sh), [run_r3b.sh](src/run_r3b.sh) | Generates and evaluates r3 entries. The second driver additionally runs the any-valid oracle evaluation. | Script body |
| [run_rp.sh](src/run_rp.sh) | Generates and evaluates the directory written with the oracle sampling prompt. | Script body |
| [run_seg.sh](src/run_seg.sh) | Waits for the r2 evaluation, then runs the left-only and right-only entry ablations. | Script body |
| [run_mv.sh](src/run_mv.sh) | Generates three descriptions per screen and evaluates access to one versus three. | Script body |
| [run_ps.sh](src/run_ps.sh) | Compares per-screen scoring on base entries and three-view entries. | Script body |
| [wait_and_run_ps.sh](src/wait_and_run_ps.sh) | Waits for GPU 0 to meet a memory threshold, then launches the per-screen comparison. | Script body |
| [run_router.sh](src/run_router.sh) | Runs multiview per-screen scoring with routing features recorded. | Script body |
| [run_long.sh](src/run_long.sh) | Waits for the long-sample download and runs OCR, verification, indexing and prompted evaluations. | Script body |
| [run_long2.sh](src/run_long2.sh) | Resumes the long-sample prompted full-history and directory runs with a GPU wait before each. | `pick_gpu` |
| [run_long3.sh](src/run_long3.sh), [run_long4.sh](src/run_long4.sh) | Retries long-sample prompted evaluations. The third driver runs full history first. The fourth starts with the directory and assigns condition-specific memory requirements. | `pick_gpu` |
| [run_long5.sh](src/run_long5.sh) | Retries only the long-sample full-history condition on one GPU. | `pick_gpu` |
| [run_long6.sh](src/run_long6.sh) | Runs the same full-history condition across two GPUs using dynamic memory caps. | `free_of` |
| [run_hybrid.sh](src/run_hybrid.sh) | Evaluates the recent-window hybrid with and without the recency prompt on short and long samples. | `pick` |
| [run_ksweep.sh](src/run_ksweep.sh) | Tests one- and three-screen recent windows on the long sample. | `pick` |
| [run_twopass.sh](src/run_twopass.sh) | Runs the recent-first two-pass reader with a two-screen recent window. | `pick` |
| [run_calib.sh](src/run_calib.sh), [run_calib_short.sh](src/run_calib_short.sh) | Runs the calibrated two-pass reader on the long and short samples respectively. | `pick` |
| [run_finish.sh](src/run_finish.sh) | Runs the lexical gate, 7B reader comparisons and third-sample OCR, verification, indexing and prompted evaluations. | `free_of`, `run14`, `run1` |
