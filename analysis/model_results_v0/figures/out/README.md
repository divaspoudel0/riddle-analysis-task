# Human-evaluation figures — how to read them

Provisional results from the **human evaluation** of the Multicultural Riddles
Benchmark, computed on the **17 of 44 cultures** with complete human coverage
(numbers will shift as coverage grows). Every value traces to Henry's
`model_riddle_results_flat.csv`; pending answers are dropped, never guessed.

Two scores appear throughout:

- **Heuristic (floor)** — the automatic judge: reference-based string matching
  (exact match after normalization). A conservative *lower bound*.
- **Human (ceiling)** — a native speaker's judgement on a 0–3 scale
  (0 hallucination, 1 admits not knowing, 2 partially correct, 3 correct).
  "Correct" here means the top score of 3 (strict).

Rerun everything after a newer flat file is dropped in:
`python analysis/model_results_v0/human_eval_figures.py`

---

## Heuristic floor vs human ceiling

![](human_floor_ceiling.png)

Per model, the grey dot is the automatic exact-match score and the blue dot is
the human score; the line between them is the lift from human judging. **How to
read:** the gap is what dumb string-matching misses — real correct answers a
person recognizes but the exact-match check rejects. The gap is largest for the
strongest models, so automatic scoring understates the best models the most.

---

## Model performance across cultures (box plot)

![](human_boxplot_cultures.png)

Each model was scored on 17 cultures, giving 17 accuracy numbers; the box shows
how they are spread. **How to read:** the box is the middle half of cultures,
the line inside is the median culture, whiskers are the typical range, grey dots
are outlier cultures, and the **red diamond is the model's lowest culture**. A
high box that is also tight = strong *and* consistent; a low diamond or a wide
box = uneven across cultures.

---

## How models rank per culture (heatmap)

![](human_culture_heatmap.png)

The same data as the box plot, but naming every culture. Rows are models (best
on top), columns are cultures (easiest on the left, hardest on the right), each
cell is that model's accuracy there. **How to read:** scan a row to see where a
model wins and collapses; scan a column to see which cultures are hard for
everyone. English/Italian are easy for all; the Indonesian regional languages
(Buginese, Mongondow) are near-zero for almost every model.

---

## Which cultures are hardest (community difficulty)

![](community_difficulty.png)

Mean accuracy across all models per culture, floor vs ceiling. **How to read:**
lower = harder for models in general. This is the column-averages of the
heatmap, sorted, so it isolates *culture* difficulty from model strength.

---

## How models fail (human error types)

![](human_error_types.png)

For each model, the breakdown of what its answers actually were when a person
judged them. **How to read:** green = correct, and the coloured segments are the
failure modes — **hallucinated** (made-up answer, red), **wrong entity** (right
category, wrong specific answer), **too broad** (generic answer), plus partially
correct and explicit uncertainty. The key pattern: hallucination dominates and
grows as models get weaker (≈7% for the best, ≈77% for the smallest), while
models almost never admit uncertainty (blue is barely visible) — they produce a
confident wrong answer instead.

---

## Correct answers missed by the exact-match heuristic

![](human_semantic_broadening.png)

Take only the answers a **human marked correct**, then ask what share the
automatic exact-match judge scored as *wrong*. **How to read:** higher = the
automatic judge throws away more genuinely-correct answers (synonyms,
translations, reworded answers). This is the concrete cost of automatic-only
scoring, per model.

---

## Does the auto-judge agree with humans? (Cohen's κ)

![](judge_human_kappa.png)

Cohen's κ measures how well the **automatic judge** agrees with the **human**,
per culture — corrected for chance agreement. **How to read:** 0 = no better
than random, 1 = perfect. Rough scale: <0.2 poor, 0.2–0.4 fair, 0.4–0.6
moderate, 0.6–0.8 substantial, >0.8 near-perfect. **Red bars (κ < 0.4)** are
cultures where string-matching is unreliable — mostly non-Latin scripts. The
dashed line is the overall κ (≈0.60).

**Formula.** Two raters (here: auto-judge and human) label the same items:

```
        p_o − p_e
κ  =  ─────────────
         1 − p_e
```

- `p_o` = observed agreement = share of items both rate the same way.
- `p_e` = agreement expected by chance = for correct/incorrect,
  `P(judge=correct)·P(human=correct) + P(judge=wrong)·P(human=wrong)`.

Worked example (our numbers, 31,965 doubly-labelled answers): both correct
3,760; judge-only 540; human-only 3,188; both wrong 24,477.
`p_o = (3,760+24,477)/31,965 = 0.883`;
`p_e = 0.134·0.217 + 0.866·0.783 = 0.707`;
`κ = (0.883−0.707)/(1−0.707) = 0.60`.

Note raw agreement is 88% but κ is only 0.60, because both raters usually say
"wrong," so much of that 88% is chance — which is exactly why we report κ.
