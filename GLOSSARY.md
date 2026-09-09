# Glossary

Every term and acronym introduced in the course, with the lesson that teaches it. Terms are added as
each module is written.

Jump to: [A](#a) · [B](#b) · [C](#c) · [D](#d) · [E](#e) · [F](#f) · [G](#g) · [H](#h) · [I](#i) · [K](#k) · [L](#l) · [M](#m) · [N](#n) · [O](#o) · [P](#p) · [Q](#q) · [R](#r) · [S](#s) · [T](#t) · [U](#u) · [V](#v) · [W](#w)

---

<a id="a"></a>
## A

**Activation function** — a non-linearity applied between layers. Without one, any depth collapses to a single linear layer. — M3-L10

**Adam** — Adaptive Moment Estimation — momentum plus per-parameter scaling by a running mean of squared gradients. Stores 2 extra parameter copies. — M3-L12

**Agent (reinforcement learning)** — the entity taking actions in an environment. Related to but
distinct from an *AI agent*. — M1-L07

**AI effect** — the tendency to stop calling a technique "AI" once it works reliably and is
understood. — M1-L01

**Aleatoric uncertainty** — uncertainty inherent in the process, not reducible by more data. — M1-L10

**Algorithm** — a procedure for producing a model from data. Distinct from the model itself. — M1-L04

**ALiBi** — Attention with Linear Biases — a distance penalty added to attention scores, with a different slope per head. Extrapolates well and costs no parameters. — M4-L09

**Anisotropy** — the tendency of embeddings to occupy a narrow cone, inflating cosine similarity between unrelated items. — M4-L04

**Anomaly detection** — identifying items unlike the rest of a dataset. — M1-L03

**Artificial Intelligence (AI)** — the engineering field of building systems that perform tasks we
call intelligent when people do them. A field, not a technique. — M1-L01

**AUC** — Area Under a Curve. **ROC-AUC** = P(random positive outranks random negative); **PR-AUC** (average precision) = area under the precision-recall curve. — M3-L14

**Auditability** — the ability to explain after the fact exactly why a specific decision was made.
— M1-L02

**Autoregressive** — generating one token at a time, each conditioned on all previous ones. — M4-L05

**Availability test** — asking whether a feature's value would be known at the moment of prediction.
The master leakage diagnostic. — M1-L09

**Axis** — the dimension a NumPy reduction collapses. `axis=0` collapses rows, leaving one value per column. — M3-L01


<a id="b"></a>
## B

**Backpropagation** — the algorithm for computing how each parameter should change. — M3-L11

**Base model** — the output of pretraining — a text continuer, not an assistant. — M4-L12

**Base rate** — the natural frequency of the positive class. The random baseline for a PR curve, and the dominant term in Bayes' theorem. — M3-L04, M3-L14

**Baseline** — the simplest reasonable alternative, used for comparison. A model that cannot beat its
baseline has not been shown to work. — M1-L11, M3-L14

**Bayes' theorem** — `P(A|B) = P(B|A)·P(A)/P(B)`. Converts one conditional probability into the other. — M3-L04

**Beam search** — keeping several candidate sequences and expanding the best. Largely abandoned for open-ended generation. — M4-L14

**Benchmark contamination** — a pretrained model having seen evaluation data during pretraining, so
its score measures recall rather than capability. — M1-L09

**Bias correction** — adam's `/(1−β^t)` terms, which fix the zero-initialised moment estimates. Without it the first step is 3.16× too large. — M3-L12

**Bias (fairness)** — unfair treatment of groups. — M10-L08

**Bias (model internals)** — the learned constant added after multiplication, the `b` in `wx + b`.
— M1-L05

**Bias (parameter)** — the additive constant in `Wx + b`. Shifts the output independently of the input. Not penalised by weight decay. — M3-L10

**Bias (statistical error)** — error from a model being too simple to capture the real pattern; leads
to underfitting. — M1-L08

**Binary classification** — classification with exactly two possible labels. — M1-L03

**BPE** — Byte Pair Encoding — repeatedly merge the most frequent adjacent pair. The dominant subword algorithm. — M4-L03

**Bradley–Terry** — the model turning pairwise comparisons into scalar scores: `P(A ≻ B) = σ(r(A) − r(B))`. — M4-L13

**Brittleness** — failing completely rather than degrading gracefully on inputs slightly outside what
was anticipated. — M1-L02

**Broadcasting** — numPy's rule for operating on mismatched shapes, aligning from the right. — M3-L01


<a id="c"></a>
## C

**Calibration** — the property that among predictions made with confidence *p*, about *p* of them are
correct. — M1-L10

**Capability** — what a model can do at least sometimes under favourable conditions. Distinct from
reliability. — M1-L11

**Capacity** — how complex a relationship a model can represent. — M1-L08

**Cardinality** — how many distinct values a feature takes. — M1-L04

**Catastrophic forgetting** — losing earlier capabilities while fine-tuning on a narrow distribution. — M4-L12

**Causal mask** — a mask preventing a position from attending to later positions. Applied to scores, before softmax. — M4-L05

**Chain rule** — `dy/dx = (dy/du)(du/dx)` — rates multiply along a path. The whole of backpropagation. — M3-L06

**Chat template** — the exact formatting marking system, user and assistant turns. A format **and** a trust boundary. — M4-L12

**Chinchilla** — the compute-optimal scaling result: roughly 20 training tokens per parameter. — M4-L12

**Class weight** — a per-class multiplier on the loss, raising a rare class's influence without duplicating data. — M3-L13

**Classification** — a task whose output is one label from a fixed, finite set defined in advance.
— M1-L03

**Clustering** — a task whose output is a grouping where the groups were not defined in advance.
— M1-L03

**Compound error** — the multiplication of per-step success rates across a pipeline. `p^n`. — M1-L11

**Confidence** — the probability a model assigns to its own output. Not the same as accuracy. — M1-L10

**Confusion matrix** — the 2×2 table of TP, FP, FN, TN from which every classification metric is derived. — M3-L14

**Context window** — the maximum tokens a model can attend over at once. Shared by input **and** output. — M4-L06

**Continuous batching** — adding and removing requests from a serving batch as they arrive and finish. — M4-L17

**Cosine similarity** — `(a·b)/(‖a‖‖b‖)`. Compares direction, not magnitude. Range −1 to 1. — M3-L02

**Coverage** — the proportion of real-world inputs a rule set actually handles. — M1-L02

**Credit assignment** — in reinforcement learning, determining which of many actions caused an
outcome. — M1-L07

**Cross-attention** — attention where queries come from one sequence and keys and values from another. — M4-L07

**Cross-entropy** — `−log(p)` assigned to the true class. The training objective of every language model. — M3-L05

**Cross-validation** — rotating which part of the data is held out so every example is tested once.
— M1-L06


<a id="d"></a>
## D

**Data augmentation** — creating extra training examples by transforming existing ones. — M1-L08

**Data leakage** — information reaching the model that will not be available at prediction time, or
that comes from evaluation data. — M1-L09

**Data poisoning** — influencing model behaviour by inserting crafted data into a training corpus.
— M1-L07, M10-L05

**Dataset** — a collection of examples used to train or evaluate a model. — M1-L04

**Dead ReLU** — a unit whose pre-activation is negative for every example, so it outputs 0, receives zero gradient, and never changes. — M3-L10, M3-L11

**Decode** — the generation phase — one token at a time, memory-bandwidth-bound. — M4-L05

**Deep learning (DL)** — machine learning using neural networks with many stacked layers. — M1-L01

**Demo gap** — the distance between an impressive demonstration and a dependable product. — M1-L11

**Derivative** — the local rate of change of a function's output with respect to its input. — M3-L06

**Determinism** — the property that the same input always produces the same output. — M1-L02, M1-L10

**Diffusion model** — a generative model producing images by iteratively removing noise. Not next-token prediction. — M4-L02

**Dimensionality reduction** — compressing many features into fewer while preserving structure.
— M1-L07

**Distribution shift** — live data ceasing to resemble training data. — M1-L06

**Dot product** — `Σ aᵢbᵢ`. A scalar measuring alignment, scaled by both magnitudes. — M3-L02

**Double descent** — the phenomenon where validation error falls, rises, then falls again as capacity
grows past the interpolation point. — M1-L08

**DPO** — Direct Preference Optimization — preference training without a separate reward model or RL loop. — M4-L13

**Dropout** — randomly disabling units during training so the model cannot rely on any single one.
— M1-L08

**Duplicate leakage** — near-identical examples appearing in more than one split. — M1-L09


<a id="e"></a>
## E

**Early stopping** — halting training when validation performance stops improving. — M1-L06, M1-L08

**ECE** — Expected Calibration Error — the support-weighted mean gap between predicted probability and observed frequency across bins. — M3-L14

**Effective context** — the range over which a model actually uses information well, as opposed to what it accepts. — M4-L06

**EOS token** — the end-of-sequence token a model emits when it considers a response complete. — M4-L15

**Epistemic uncertainty** — uncertainty from lack of knowledge. Reducible with more data or
retrieval. — M1-L10

**Epoch** — one complete pass through the training data. — M1-L05, M1-L06

**Example** — one item in a dataset: one email, one customer, one image. Also *row*, *sample*,
*instance*, *observation*. — M1-L04

**Expected Calibration Error (ECE)** — the average gap between stated confidence and observed
accuracy, weighted by bucket size. — M1-L10

**Expert system** — a large rule-based system encoding specialist knowledge as `if/then` rules.
— M1-L02

**Exposure bias** — generation conditions on the model's own output, a distribution never seen in teacher-forced training. — M4-L05

**Extrapolation** — predicting outside the range of the training data. A linear model does it confidently and without warning. — M3-L08


<a id="f"></a>
## F

**F1 / Fβ** — harmonic mean of precision and recall; β>1 favours recall. F1 ignores true negatives. — M3-L14

**Feature** — one measurable property of an example, used as input. — M1-L04

**Feature engineering** — deriving new, more useful features from raw data by hand. — M1-L04

**Feature matrix (`X`)** — all examples' feature vectors stacked; shape `(n, d)`. — M1-L04

**Few-shot prompting** — including worked examples in a prompt. — M5-L03

**finish_reason** — the field reporting why generation stopped. The only reliable truncation signal. — M4-L15

**Forward chaining** — time-series cross-validation where training data always precedes the validation period. — M3-L13

**Foundation model** — a large model trained broadly once, then adapted to many tasks. — M1-L01,
M4-L01


<a id="g"></a>
## G

**Generalization** — performing well on data not seen during training. The actual goal. — M1-L08

**Generalization gap** — training performance minus validation performance. — M1-L08

**Generation** — a task whose output is newly constructed content from an open-ended space. — M1-L03

**Generative AI** — AI whose output is newly produced content rather than a label, number or group.
A statement about output shape, not method. — M1-L01

**GQA** — Grouped-Query Attention — fewer key/value heads than query heads, shrinking the KV cache 4–8×. — M4-L17

**Graceful degradation** — producing a somewhat-worse answer on unfamiliar input rather than failing
completely. — M1-L02

**Gradient** — the vector of partial derivatives of a loss with respect to every parameter. Points toward steepest increase. — M3-L06

**Gradient checking** — comparing an analytic gradient to a central-difference numerical one. Relative error <1e-7 is correct. — M3-L11

**Gradient clipping** — scaling the gradient down when its global norm exceeds a cap. Preserves direction, bounds magnitude. — M3-L12

**Greedy decoding** — always choosing the highest-probability next token. Deterministic. — M1-L10,
M4-L14

**Grid search** — trying every combination from a fixed list of candidate hyperparameter values.
— M1-L05

**Ground truth** — the correct answer for an example, from a trustworthy process. — M1-L02

**Groundedness** — the property that every claim is supported by provided evidence. — M1-L10, M7-L19

**Group leakage** — related examples from one entity split across train and test. — M1-L09

**Grouped split** — a split keeping all rows sharing an entity on the same side. — M3-L13


<a id="h"></a>
## H

**Hallucination** — fluent, confident output unsupported by any source and often false. — M1-L10

**Happy path** — the inputs and conditions a system was designed and demonstrated on. — M1-L11

**Hyperparameter** — a value you set before training that controls how training happens or how the
model is shaped. Your prompt is one. — M1-L05

<a id="i"></a>
## I

**In-context learning** — adapting behaviour from examples in the prompt, without weight changes. A capability that emerges at scale. — M4-L16

**Inference** — using a trained model on new input. Also *serving*. No learning occurs. — M1-L06

**Inter-annotator agreement** — how often two human labellers agree. Sets your realistic accuracy
ceiling. — M1-L04


<a id="k"></a>
## K

**k-fold** — cross-validation with `k` equal parts. — M1-L06

**Knowledge cutoff** — the date after which training data was not collected. — M4-L16

**KV cache** — stored attention keys and values so prefill work is not repeated per token. Grows with tokens × concurrency. — M4-L06


<a id="l"></a>
## L

**Label** — the correct answer for an example. Also *target*, *ground truth*, `y`. — M1-L04

**Label noise** — errors in the labels themselves. A model cannot be more correct than its labels.
— M1-L04

**Laplace smoothing** — adding a constant to every count so no probability is zero. — M1-L02

**Large Language Model (LLM)** — a deep-learning model trained on large text corpora to produce text.
— M1-L01

**Leakage (target encoding)** — a feature computed from the label — e.g. a per-entity mean of the target over all rows. No split prevents it. — M3-L13, Project 3

**Learning rate** — a hyperparameter controlling the size of each training update. — M1-L05, M3-L12

**Logit** — a raw pre-activation score before sigmoid or softmax. Unbounded. — M3-L09

**Logits** — raw unnormalised scores over the vocabulary, before softmax. — M4-L05

**Log-odds** — `log(p/(1−p))`. Logistic regression is linear in log-odds, not in probability. — M3-L09

**Long tail** — the large set of rare, varied inputs that collectively make up much of real traffic.
— M1-L11

**Loss function** — a single number measuring how wrong a prediction is, which training minimises. — M3-L07

**Lost in the middle** — degraded use of information placed mid-context. — M4-L06


<a id="m"></a>
## M

**Machine learning (ML)** — techniques where decision logic is fitted from data rather than written
by a person. — M1-L01

**Macro / micro average** — macro = unweighted mean of per-class metrics (every class equal). Micro = pooled counts (overall correctness). — M3-L14

**MAE / MSE / RMSE** — Mean Absolute / mean squared / root mean squared error. RMSE/MAE is a read-out of error skew. — M3-L14

**Masked prediction** — a self-supervised pretext task predicting hidden tokens using context on both
sides. Suits encoding/embeddings. — M1-L07

**Memorization** — the extreme of overfitting: storing training examples rather than learning a rule.
Carries a privacy risk. — M1-L08

**min-p** — a sampling truncation keeping tokens above a fraction of the top token's probability. — M4-L14

**Model** — the artefact produced by training: learned numbers plus the structure that uses them.
— M1-L04

**Momentum** — an exponentially decayed running average of past gradients; damps oscillation, accelerates consistent descent. — M3-L12

**Multi-class classification** — one label chosen from three or more mutually exclusive options.
— M1-L03

**Multicollinearity** — near-duplicate features producing unstable coefficients while predictions stay fine. — M3-L08

**Multi-label classification** — zero or more labels applied simultaneously. — M1-L03


<a id="n"></a>
## N

**Naive Bayes** — a simple learned classifier combining independent per-feature evidence. — M1-L02

**Neural network** — a function built from layers of simple numeric operations controlled by learned
weights. — M1-L01, M3-L10

**Next-token prediction** — a self-supervised pretext task predicting the following token from
left context. Suits generation. — M1-L07

**Norm** — `‖a‖ = √(Σaᵢ²)`. A vector's length. — M3-L02

**Nucleus sampling** — see top-p. — M4-L14


<a id="o"></a>
## O

**One-hot encoding** — representing a category as one 0/1 column per possible value. — M1-L04

**Open weights** — model parameters downloadable, often under a restrictive custom licence. **Not** open source. — M4-L01

**Optimistic bias** — the inflation of a reported score caused by selecting the best of several noisy
measurements. — M1-L05

**Ordinal** — categories with a meaningful order but no meaningful arithmetic. — M1-L03

**Overconfident** — stated confidence exceeding actual accuracy. — M1-L10

**Overfitting** — learning patterns specific to the training data, including its noise, that do not
generalise. — M1-L08


<a id="p"></a>
## P

**Parameter** — a number inside a model learned from data. — M1-L05

**Parametric knowledge** — information encoded in the weights during training. — M4-L16

**Patch** — a small square of an image treated as one unit — the image equivalent of a token. — M4-L02

**Perfect separation** — when a logistic model can separate the classes exactly, so the unregularised optimum has infinite weights. — M3-L09

**Perplexity** — `exp(cross-entropy)`. The effective number of options the model is choosing among. Comparable only across the same tokenizer and data. — M3-L05

**Point-in-time reconstruction** — rebuilding a feature's value as of the prediction moment rather
than reading its current value. — M1-L09

**Policy (RL)** — the strategy mapping situations to actions. — M1-L07

**PPO** — Proximal Policy Optimization — the reinforcement-learning algorithm usually used in RLHF. — M4-L13

**PR curve** — precision against recall across thresholds. Its random baseline is the base rate. — M3-L14

**Precision** — `TP/(TP+FP)`. Of what we flagged, how much was right. Measures false alarms. — M3-L14

**Prefill** — processing the prompt — all positions in parallel, compute-bound. Sets time to first token. — M4-L05

**Preprocessing leakage** — computing statistics over the whole dataset before splitting. — M1-L09

**Pretext task** — an artificial task invented purely to create a training signal. — M1-L07

**Pretraining** — the first, large, usually self-supervised training phase. — M1-L07

**Prior** — `P(A)` — the base rate before evidence. — M3-L04

**Provenance** — a record of where each piece of data came from. — M1-L09, M10-L05

**Proxy variable** — a feature that indirectly encodes something else, including a protected
attribute or the label. — M1-L09


<a id="q"></a>
## Q

**Quantization** — storing weights or activations at lower numerical precision. Speeds up decode more than the arithmetic saving suggests. — M4-L17


<a id="r"></a>
## R

**R²** — fraction of variance explained. Can be negative; always rises with more features; meaningless on tiny samples. — M3-L08

**Random search** — sampling hyperparameter combinations at random. Usually beats grid search at
equal budget. — M1-L05

**Ranking** — a task whose output is an ordering of items by relevance. RAG retrieval is ranking.
— M1-L03

**Recall (sensitivity, TPR)** — `TP/(TP+FN)`. Of what exists, how much we found. Measures misses. — M3-L14

**Regression** — a task whose output is a continuous number on a scale. — M1-L03

**Regularization** — any technique constraining a model to reduce overfitting. — M1-L08

**Reinforcement learning (RL)** — learning from rewards received by taking actions. — M1-L07

**Reliability** — how often a complete system produces an acceptable result under real conditions.
— M1-L11

**Reliability diagram** — a plot of stated confidence against observed accuracy. — M1-L10

**ReLU** — `max(0, z)`. Derivative 1 for positive inputs, 0 otherwise — passes or blocks gradients. — M3-L10

**Residual connection** — an added identity path, giving the gradient a second route with local derivative 1. — M3-L11

**Reward hacking** — an optimiser satisfying the stated reward in a way that defeats the intent.
— M1-L07

**RLHF** — reinforcement Learning from Human Feedback. — M1-L07, M4-L13

**RoPE** — Rotary Position Embedding — rotates queries and keys so their dot product depends only on relative distance. — M4-L09

**Rule-based system** — software whose decision logic is conditions a human wrote. — M1-L02


<a id="s"></a>
## S

**Sampling** — choosing an outcome at random according to a probability distribution. — M1-L10

**Schedule** — a rule changing the learning rate over training. Warmup + cosine is the transformer default. — M3-L12

**Schema** — the definition of what fields exist and their types. — M1-L04

**Self-supervised learning** — learning where the target is derived automatically from the data, such
as predicting a hidden token. The reason LLMs exist. — M1-L07

**Semi-supervised learning** — using a small labelled set plus a large unlabelled set. — M1-L07

**SFT** — Supervised Fine-Tuning on curated instruction-response pairs. — M4-L12

**Sigmoid** — `1/(1+e^−z)`. Maps any real number to (0,1). `σ(0)=0.5`. — M3-L09

**Softmax** — turns a vector of logits into a probability distribution. Shift-invariant; temperature reshapes it. — M3-L09

**Specificity (TNR)** — `TN/(TN+FP)`. — M3-L14

**Speculative decoding** — a small model drafts tokens which the large model verifies in parallel. Output is identical to normal sampling. — M4-L17

**Spurious correlation** — a pattern that holds in the sample but carries no generalisable signal.
— M1-L02, M1-L09

**Standard error** — `σ/√n` for a mean; `√(p(1−p)/n)` for a proportion. Halving it needs 4× the data. — M3-L03

**Stochastic** — involving randomness; repeated runs may differ. — M1-L10

**Stop sequence** — a string that halts generation when produced. Usually excluded from the returned text. — M4-L15

**Stratified split** — a split preserving class proportions in each part. — M1-L06

**Supervised learning** — learning from examples paired with human-provided correct answers. — M1-L07

**Sycophancy** — agreeing with the user because agreement is rated well in preference data. — M4-L13


<a id="t"></a>
## T

**Target leakage** — a feature that is a consequence of, or contains, the label. — M1-L09

**Task shape** — the structural form of a task's output: classification, regression, clustering,
ranking or generation. — M1-L03

**Teacher forcing** — training on the true previous tokens rather than the model's own predictions. — M4-L05

**Temperature** — a setting flattening or sharpening the next-token distribution before sampling.
— M1-L10, M4-L14

**Temporal leakage** — using future information to predict the past. — M1-L09

**Temporal split** — training on the past, evaluating on the future, with a gap if features use rolling windows. — M3-L13

**Test set** — held-out data used **once** to estimate real-world performance. — M1-L06

**Threshold (decision)** — the probability above which the positive class is predicted. A product decision, chosen on validation. — M3-L14

**Top-k** — keeping only the k highest-probability tokens before sampling. A fixed count. — M4-L14

**Top-p** — keeping the smallest set of tokens whose probability sums to p. Adapts to the distribution. — M4-L14

**TPOT** — time per output token — set by memory bandwidth. — M4-L17

**Training** — the phase where an algorithm adjusts parameters using the training set. — M1-L06

**Training signal** — the information telling an algorithm whether it is doing well. — M1-L07

**Training/serving skew** — features computed differently in training than in serving. — M1-L04

**Train–test contamination** — test examples, or information derived from them, present in training.
— M1-L09

**TTFT** — time to first token — set by prefill, and what a streaming user perceives as speed. — M4-L17


<a id="u"></a>
## U

**Underfitting** — failing to learn patterns that are present, usually from too little capacity or
training. — M1-L08

**Universal approximation** — the theorem that a wide enough hidden layer can approximate any continuous function. Says nothing about learnability or width. — M3-L10

**Unsupervised learning** — learning structure from data with no answers provided. — M1-L07


<a id="v"></a>
## V

**Validation set** — held-out data used to compare hyperparameter choices. Also *dev set*. — M1-L06

**Vanishing / exploding gradients** — gradients shrinking or growing multiplicatively through depth. Diagnosed by per-layer gradient norms. — M3-L10, M3-L11

**Variance (statistical)** — mean squared deviation from the mean. `ddof=0` (population) vs `ddof=1` (sample) differ between NumPy and pandas. — M3-L03

**Variance (statistical error)** — error from a model being overly sensitive to the particular
training sample; leads to overfitting. — M1-L08


<a id="w"></a>
## W

**Weight** — the most common kind of parameter: a multiplier applied to an input. — M1-L05

**Weight decay** — L2 regularisation applied to weights (never the bias). AdamW applies it to the parameter directly. — M3-L12
