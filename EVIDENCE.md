# EVIDENCE.md

This file is the empirical grounding for the project. It exists so that every actionable recommendation we make about how to *use* Claude Code or any coding agent can be traced back to a published measurement rather than to intuition or marketing. Each bullet restates a verified claim and ends with an inline numbered citation `[n]`; the `## References` section maps each `[n]` to its title and URL. Where a source is rated below "high" confidence, that is noted inline. If a recommendation in this repository cannot point to a bullet here, treat it as an untested hypothesis, not a finding.

## Benchmarks & how success is measured

- SWE-bench comprises 2,294 task instances constructed from real merged GitHub issue–pull-request pairs across 12 popular Python repositories [1].
- A SWE-bench task is scored as "resolved" only if, after applying the model-generated patch, every `FAIL_TO_PASS` and `PASS_TO_PASS` unit test passes — grading is execution-based, not a textual match against the gold patch [2].
- In the original SWE-bench paper, the best system, Claude 2, resolved only 1.96% of issues in the realistic BM25-retrieval setting [1].
- SWE-bench's "oracle" retrieval setting hands the model exactly the files edited by the gold patch — a solution-localization hint that raised Claude 2's resolved rate to 4.8% versus 1.96% under realistic BM25 retrieval [2]. (Takeaway: *what the agent is given to look at* moves the score by more than 2x on the same tasks.)
- SWE-bench Verified is a 500-instance human-validated subset, produced after 93 professional Python developers screened 1,699 random test samples, with 68.3% of screened samples filtered out as problematic [3].
- OpenAI's human review flagged 38.3% of SWE-bench samples for underspecified problem statements and 61.1% for unit tests that may unfairly mark valid solutions as incorrect — the benchmark's two main documented pitfalls [3]. (Implication: a non-trivial share of "failures" on the original set are grader/spec artifacts, not agent errors.)
- WebArena is a reproducible web environment with fully functional sites across four domains (e-commerce, social forums, software development, content management); the best GPT-4-based agent achieved only a 14.41% end-to-end task success rate versus 78.24% for humans [4].
- GAIA is a 466-question benchmark for general AI assistants requiring reasoning, multimodality handling, web browsing, and tool use, on which human respondents scored 92% versus 15% for GPT-4 equipped with plugins [5].
- METR's "time horizon" methodology fits a logistic curve of a model's success probability against the human time-to-complete a task and reports the 50%-task-completion time horizon — the human task length at which the model succeeds 50% of the time [6].
- In METR's March 2025 study, Claude 3.7 Sonnet had a 50%-task-completion time horizon of about 50 minutes, and the frontier AI time horizon has roughly doubled every seven months since 2019 [6].
- Terminal-Bench evaluates AI agents on hand-crafted, human-verified tasks executed inside a real terminal shell, comprising 89 tasks spanning software engineering, machine learning, security, and system administration (confidence: medium) [7].
- On Terminal-Bench, frontier models and agents score less than 65%, indicating the tasks remain difficult for current systems (confidence: medium) [7].

## Claude Code usage (official guidance)

- Anthropic's official `CLAUDE.md` guidance is to target under 200 lines per file, because longer files consume more context and reduce instruction adherence [8].
- `CLAUDE.md` files can pull in other files with the `@path/to/import` syntax, and imports may recurse to a maximum depth of four hops [8].
- Auto memory requires Claude Code v2.1.59 or later, and only the first 200 lines (or first 25 KB, whichever comes first) of `MEMORY.md` are loaded into context at the start of every session [8].
- Anthropic recommends a four-phase workflow — explore, plan, implement, commit — using plan mode to separate research from execution, with `Ctrl+G` opening the generated plan in your text editor for editing before implementation [9].
- Custom subagents are defined as markdown files in the `.claude/agents/` directory with YAML frontmatter (`name`, `description`, `tools`, `model`) and run in their own separate context window with their own set of allowed tools [9].
- For unattended/batch runs, Anthropic recommends scoping permissions with the `--allowedTools` flag (e.g. `--allowedTools "Edit,Bash(git commit *)"`) and using `/permissions` to allowlist specific safe commands rather than approving each action manually [9].

## Long-context behavior

These results explain *why* the Claude Code guidance above (keep `CLAUDE.md` short, scope context, isolate subagent context) is not stylistic but performance-relevant: more input is not free, and the wrong input can be actively harmful.

- In Liu et al.'s multi-document QA task with 20 documents, GPT-3.5-Turbo answered 75.8% correctly when the gold document was first but only 53.8% when it was in the middle — a ~22-point U-shaped drop (the last position recovered to 63.2%) [10].
- In the same study, accuracy with the relevant document buried in the middle (53.8%) fell *below* closed-book accuracy with no documents at all (56.1%): a badly-placed document was worse than no document [10].
- Levy et al. found reasoning accuracy averaged over five models (GPT-4, GPT-3.5, Gemini Pro, Mistral Medium, Mixtral 8x7B) fell from 0.92 to 0.68 (a 24-point drop) as total input length grew to about 3,000 tokens — with the relevant information held constant and the rest filled by padding — far below the models' technical context limits [11].
- Cuconasu et al. showed that adding a single related-but-non-answer "distractor" document to a RAG prompt sharply reduced answer accuracy (drops peaking around 25%), and multiple distractors compounded the loss [12].
- Counterintuitively, the same study found that inserting completely random/irrelevant noise documents near the query improved accuracy by up to roughly 35%, distinguishing topically-similar distractors (harmful) from unrelated noise (sometimes helpful) (confidence: medium) [12].
- Chroma's "Context Rot" report (2025) tested 18 LLMs across the Claude, GPT/o3, Gemini, and Qwen families and found that across all experiments performance consistently degraded as input length grew — including well below the models' maximum context windows. Adding distractors topically/semantically related to the target needle further reduced performance, amplified at longer inputs, though the report describes distractor impact as non-uniform rather than a strict semantic-similarity rule. Note: the 18 models include several legacy models (e.g. GPT-3.5 Turbo, GPT-4 Turbo, Claude Sonnet 3.5/3.7, Gemini 2.0), so not all are strictly "frontier" (confidence: medium) [13].

## Scaffolding & inference-time techniques

These are the candidate "usage choices" the project can test. Note that several of the strongest numbers below come from older models and non-coding benchmarks, so their transfer to a modern coding agent is itself an open question (see next section).

- Reflexion (verbal self-reflection stored in episodic memory across retries) reaches 91% pass@1 on HumanEval, versus 80% for the GPT-4 baseline reported in the same paper (+11 pp) [14].
- Self-consistency (sampling multiple chain-of-thought paths and taking the majority answer) raises GSM8K accuracy by +17.9 absolute points (56.5% → 74.4% with PaLM-540B) over single-path chain-of-thought; the paper also reports +11.0 on SVAMP and +12.2 on AQuA [15].
- ReAct (interleaving reasoning traces with tool/environment actions) outperforms imitation- and reinforcement-learning baselines by an absolute success-rate margin of 34% on ALFWorld and 10% on WebShop [16].
- Self-Debugging (the model inspects execution results and explains its own code to fix it) improves baseline code-generation accuracy by up to 12% on TransCoder and MBPP, and by 9% on the hardest-difficulty problems of the Spider text-to-SQL benchmark [17].
- Plan-and-Solve+ prompting (zero-shot: first devise a plan, then execute subtasks) reaches 59.3% on GSM8K versus 56.4% for zero-shot chain-of-thought ("Let's think step by step") using GPT-3 `text-davinci-003` (+2.9 pp) [18].
- Allocating test-time compute with a compute-optimal strategy improves scaling efficiency by more than 4x over a best-of-N baseline, and in a FLOPs-matched comparison lets a smaller model outperform a 14x larger model on problems where the small model already has non-trivial success [19].

## Open questions this project can test empirically

Each hypothesis below is derived from the evidence above and is framed so that it can be confirmed *or falsified* on a held-out task suite with execution-based grading (in the spirit of SWE-bench's pass/fail criterion [2]). Default to falsification: design each test to give the technique a fair chance to *fail*.

1. **Does a `CLAUDE.md` actually raise pass-rate, and does length hurt?** Run a suite with no `CLAUDE.md`, with a concise (<200-line) one, and with a deliberately bloated one. The official guidance predicts the concise version helps and the bloated one regresses [8]; the long-context literature predicts the same direction for a mechanistic reason — added tokens degrade reasoning even below the context limit [10][11][13]. Hypothesis is falsified if the bloated file matches or beats the concise file.

2. **Is "context placement" measurable inside a real agent run?** Lost-in-the-Middle and Context Rot show ordering and burial matter in QA [10][13]. Test whether putting the most relevant files/instructions early vs. buried mid-context changes resolved-rate on the same tasks. A null result would be evidence that agent scaffolding masks the positional effect seen in isolated QA.

3. **Distractors vs. noise: which kind of extra context hurts an agent?** Cuconasu et al. found topically-similar distractors harmful but random noise sometimes helpful (the latter at medium confidence) [12]. Test whether feeding the agent plausibly-related-but-wrong files lowers pass-rate more than feeding it unrelated files. This directly informs retrieval/`@import` policy.

4. **Does oracle-style file localization explain most of the gain?** The 4.8% vs 1.96% oracle/BM25 gap [2] suggests *telling the agent where to edit* is a large lever. Test giving the agent the gold-edited file paths vs. making it locate them, holding the model fixed, to quantify how much of success is localization rather than reasoning.

5. **Do self-reflection / self-debugging / planning transfer to a modern coding agent?** Reflexion, Self-Debugging, and Plan-and-Solve+ report gains on older models and partly non-coding benchmarks [14][17][18]. Test each as a togglable scaffold on the same suite to see whether the gains replicate, shrink, or vanish on a current agent. The honest prior is that some will not transfer.

6. **Does spending more inference-time compute beat a single pass, and where is the knee?** Self-consistency and compute-optimal scaling report large gains from extra sampling/search [15][19]. Test best-of-N and retry-with-reflection against single-shot on the suite, reporting cost per resolved task — the relevant metric is pass-rate *per unit compute*, not pass-rate alone.

## References

1. SWE-bench: Can Language Models Resolve Real-World GitHub Issues? (Jimenez et al., arXiv:2310.06770) — https://arxiv.org/abs/2310.06770
2. SWE-bench paper, Section A.4 (ar5iv HTML of arXiv:2310.06770) — https://ar5iv.labs.arxiv.org/html/2310.06770
3. Introducing SWE-bench Verified | OpenAI — https://openai.com/index/introducing-swe-bench-verified/
4. WebArena: A Realistic Web Environment for Building Autonomous Agents (arXiv:2307.13854) — https://arxiv.org/abs/2307.13854
5. GAIA: a benchmark for General AI Assistants (arXiv:2311.12983) — https://arxiv.org/abs/2311.12983
6. Measuring AI Ability to Complete Long Tasks (arXiv:2503.14499 / METR) — https://arxiv.org/abs/2503.14499
7. Terminal-Bench: Benchmarking Agents on Hard, Realistic Tasks in Command Line Interfaces (arXiv:2601.11868) — https://arxiv.org/abs/2601.11868
8. How Claude remembers your project — Claude Code Docs — https://code.claude.com/docs/en/memory
9. Best practices for Claude Code — https://code.claude.com/docs/en/best-practices
10. Lost in the Middle: How Language Models Use Long Contexts (Liu et al. 2023) — https://arxiv.org/abs/2307.03172
11. Same Task, More Tokens: the Impact of Input Length on the Reasoning Performance of LLMs (Levy et al. 2024) — https://arxiv.org/abs/2402.14848
12. The Power of Noise: Redefining Retrieval for RAG Systems (Cuconasu et al. 2024) — https://arxiv.org/abs/2401.14887
13. Context Rot: How Increasing Input Tokens Impacts LLM Performance (Chroma 2025) — https://www.trychroma.com/research/context-rot
14. Reflexion: Language Agents with Verbal Reinforcement Learning (arXiv:2303.11366) — https://arxiv.org/abs/2303.11366
15. Self-Consistency Improves Chain of Thought Reasoning in Language Models (arXiv:2203.11171) — https://arxiv.org/abs/2203.11171
16. ReAct: Synergizing Reasoning and Acting in Language Models (arXiv:2210.03629) — https://arxiv.org/abs/2210.03629
17. Teaching Large Language Models to Self-Debug (arXiv:2304.05128) — https://arxiv.org/abs/2304.05128
18. Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning (arXiv:2305.04091) — https://ar5iv.labs.arxiv.org/html/2305.04091
19. Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters (arXiv:2408.03314) — https://arxiv.org/abs/2408.03314

## International & Chinese-origin evidence

The following sources corroborate and extend the Western references cited above, drawing on benchmarks, code LLMs, and agent research from Chinese institutions (Tsinghua/THUDM, DeepSeek, Alibaba/Qwen, Tencent, Fudan, USTC) and other non-Western groups. Citations are numbered from [100] to avoid clashing with the main reference list.

### Agent & tool-use benchmarks

- AgentBench (THUDM/Tsinghua, Liu et al. 2023) evaluates LLMs as agents across 8 distinct interactive environments — Operating System, Database, Knowledge Graph, Digital Card Game, Lateral Thinking Puzzles, House-Holding (ALFWorld), Web Shopping (WebShop), and Web Browsing (Mind2Web) — in a multi-turn, open-ended setting. [100]
- AgentBench tested 29 API-based and open-source LLMs (per the current arXiv v3 abstract; the original 2023 v1 abstract reported 25, not 27) and found a significant gap between top commercial LLMs and open-source competitors no larger than 70B, attributing the gap mainly to weaker long-term reasoning, decision-making, and instruction-following. [100]
- ToolLLM/ToolBench (Tsinghua, Qin et al. 2023) builds its instruction-tuning dataset from 16,464 real-world RESTful APIs across 49 categories collected from RapidAPI Hub, with instructions and solution paths generated automatically using ChatGPT. [101]
- ToolLLM introduces a depth-first search-based decision tree (DFSDT) for reasoning and an automatic evaluator (ToolEval); the resulting ToolLLaMA executes complex instructions, generalizes to unseen APIs, and shows performance qualitatively comparable to ChatGPT. [101]
- CodeAct (Wang et al. 2024) uses executable Python code as a unified action space for LLM agents, achieving up to a 20% higher success rate than Text- and JSON-formatted actions across 17 LLMs on API-Bank and the newly curated M3ToolEval benchmark. [102]
- CodeAct releases CodeActInstruct, an instruction-tuning dataset of 7k multi-turn interactions; the derived CodeActAgent is fine-tuned from Llama2 and Mistral with an integrated Python interpreter for multi-turn self-debugging. [102]
- Reflexion, which adds verbal self-reflection stored in episodic memory, reaches 91% pass@1 on HumanEval versus an 80% GPT-4 baseline — evidence that self-reflection empirically improves coding success. [103]
- Teaching LLMs to Self-Debug, using code-execution results and self-generated explanations, improves baseline accuracy by up to 12% on TransCoder and MBPP (and +9% on the hardest Spider problems), indicating that execution feedback raises code-generation success. [104]
- SWE-agent (GPT-4 Turbo) with a purpose-built agent-computer interface resolves 12.47% of the 2,294 SWE-bench test tasks versus a previous best of 3.8%, showing that tooling/interface design materially improves autonomous issue resolution. [105]
- A non-Western survey (Fudan University et al.) of LLM-based agents for software engineering systematically categorizes 124 papers, identifying perception and use of external tools/resources as a core capability extending LLM coding effectiveness. [106]
- A non-Western survey on LLM-agent planning (USTC / Huawei Noah's Ark) organizes methods into a five-category taxonomy: task decomposition, plan selection, external module, reflection, and memory. [107]
- A 2025 survey of AI agentic programming (University of Leeds) frames coding agents around autonomous planning, tool integration, and feedback-based execution monitoring, while flagging limited long-context handling and lack of persistent cross-task memory as key open challenges to reliability (qualitative taxonomy; confidence: medium). [108]

### Code LLMs & coding benchmarks

- DeepSeek-Coder-Base 33B scores 56.1% pass@1 on HumanEval (Python) and 66.0% on MBPP, with a 50.3% average HumanEval across 8 programming languages. [109]
- DeepSeek-Coder-V2-Instruct reaches 90.2% on HumanEval and 76.2% on MBPP+, and is reported as the first open-source model to surpass 10% on SWE-bench (12.7%). [110]
- DeepSeek-Coder-V2-Instruct scores 43.4% overall on LiveCodeBench (across 226 questions) per its technical report. [110]
- Qwen2.5-Coder-32B-Instruct scores 92.7% on HumanEval, 90.2% on MBPP, and 31.4% on LiveCodeBench in its technical report. [111]
- Qwen2.5-Coder-7B-Instruct scores 88.4% on HumanEval, 83.5% on MBPP, and 18.2% on LiveCodeBench in its technical report. [111]
- CodeGeeX is a 13B-parameter model trained on 850 billion tokens across 23 programming languages, reporting 22.89% pass@1 on HumanEval (Python). [112]

Note: HumanEval/MBPP numbers above are self-reported in each model's own technical report and use differing harnesses; treat cross-model comparisons with caution. The contemporaneous SWE-bench and LiveCodeBench figures are the more informative agentic/contamination-resistant signals.

### Reasoning / test-time compute

- DeepSeek-R1-Zero, trained with pure reinforcement learning and no supervised fine-tuning, improved AIME 2024 pass@1 from 15.6% to 71.0% over RL training, reaching 86.7% with majority voting (cons@64). [113]
- DeepSeek-R1 scores 79.8% pass@1 on AIME 2024 (slightly surpassing OpenAI-o1-1217) and 97.3% on MATH-500. [113]
- DeepSeek-R1 reaches a 2,029 Elo rating on Codeforces, outperforming 96.3% of human competition participants. [113]
- Distilling DeepSeek-R1 into a Qwen 32B base yields 72.6% on AIME 2024 versus 47.0% for large-scale RL applied directly to the same base (DeepSeek-R1-Zero-Qwen-32B) — distillation beats direct RL for small models. [113]
- s1-32B (Qwen2.5-32B-Instruct supervised-fine-tuned on just 1,000 reasoning examples plus a "budget forcing" test-time technique) scales AIME24 from 50% to 57% by adding test-time compute and exceeds OpenAI o1-preview on competition math by up to 27%. [114]
- OpenAI o1 averaged 74% (11.1/15) on AIME 2024 with a single sample versus GPT-4o's ~12% (1.8/15), and ranks in the 89th percentile on Codeforces — included as the Western reference point these RL/test-time-scaling results are measured against. [115]

### Long-context & retrieval

- LongBench, the first bilingual (English/Chinese) multitask long-context benchmark (Tsinghua University and the Institute of Automation, Chinese Academy of Sciences), comprises 21 datasets across 6 task categories totaling 4,750 test instances, averaging 6,711 English words and 13,386 Chinese characters. [116]
- LongBench v2 (Tsinghua, ACL 2025) contains 503 challenging multiple-choice questions with contexts from 8k to 2M words; human experts scored only 53.7% under a 15-minute limit, the best model answering directly reached 50.1%, and o1-preview with extended reasoning reached 57.7%. [117]
- Counting-Stars (Tencent Hunyuan), a multi-evidence needle-in-a-haystack variant, inserts M=32 "stars" into contexts up to 128K tokens; Gemini 1.5 Pro scored best at 0.775 (P@32) on Chinese multi-evidence searching and 0.833 on English. [118]
- In "Long Context vs. RAG for LLMs" (Fudan University and Nanyang Technological University), long context (LC) generally outperforms retrieval-augmented generation (RAG) on QA benchmarks — especially Wikipedia-based questions — while summarization-based retrieval performs comparably to LC and chunk-based retrieval lags. [119]
- LaRA (Alibaba-NLP) benchmarks RAG against long-context LLMs on 2,326 test cases spanning four QA task categories and three long-text types across 11 models (7 open-source, 4 proprietary), concluding there is no silver bullet: the optimal RAG-vs-LC choice depends on model size, context length, and task type. [120]
- LongBench Pro is a bilingual (English/Chinese) long-context benchmark of 1,500 naturally occurring samples spanning 11 primary and 25 secondary tasks with inputs from 8k to 256k tokens, built via a Human-Model Collaborative Construction pipeline (confidence: medium). [121]

### References (international)

- [100] AgentBench: Evaluating LLMs as Agents (arXiv:2308.03688) — https://arxiv.org/abs/2308.03688
- [101] ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs (arXiv:2307.16789) — https://arxiv.org/abs/2307.16789
- [102] Executable Code Actions Elicit Better LLM Agents (arXiv:2402.01030) — https://arxiv.org/abs/2402.01030
- [103] Reflexion: Language Agents with Verbal Reinforcement Learning (arXiv:2303.11366) — https://arxiv.org/abs/2303.11366
- [104] Teaching Large Language Models to Self-Debug (arXiv:2304.05128) — https://arxiv.org/abs/2304.05128
- [105] SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering (arXiv:2405.15793, NeurIPS 2024) — https://arxiv.org/abs/2405.15793
- [106] Large Language Model-Based Agents for Software Engineering: A Survey (arXiv:2409.02977) — https://arxiv.org/abs/2409.02977
- [107] Understanding the planning of LLM agents: A survey (arXiv:2402.02716) — https://arxiv.org/abs/2402.02716
- [108] AI Agentic Programming: A Survey of Techniques, Challenges, and Opportunities (arXiv:2508.11126) — https://arxiv.org/abs/2508.11126
- [109] DeepSeek-Coder: When the Large Language Model Meets Programming — The Rise of Code Intelligence (arXiv:2401.14196) — https://arxiv.org/html/2401.14196v1
- [110] DeepSeek-Coder-V2: Breaking the Barrier of Closed-Source Models in Code Intelligence (arXiv:2406.11931) — https://arxiv.org/html/2406.11931v1
- [111] Qwen2.5-Coder Technical Report (arXiv:2409.12186) — https://arxiv.org/html/2409.12186v3
- [112] CodeGeeX: A Pre-Trained Model for Code Generation with Multilingual Benchmarking on HumanEval-X (arXiv:2303.17568) — https://arxiv.org/html/2303.17568v2
- [113] DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning (arXiv:2501.12948) — https://arxiv.org/abs/2501.12948
- [114] s1: Simple test-time scaling (arXiv:2501.19393) — https://arxiv.org/abs/2501.19393
- [115] Learning to reason with LLMs (OpenAI) — https://openai.com/index/learning-to-reason-with-llms/
- [116] LongBench: A Bilingual, Multitask Benchmark for Long Context Understanding (arXiv:2308.14508) — https://arxiv.org/abs/2308.14508
- [117] LongBench v2: Towards Deeper Understanding and Reasoning on Realistic Long-context Multitasks (arXiv:2412.15204) — https://arxiv.org/abs/2412.15204
- [118] Counting-Stars: A Multi-evidence, Position-aware, and Scalable Benchmark for Evaluating Long-Context LLMs (arXiv:2403.11802) — https://arxiv.org/abs/2403.11802
- [119] Long Context vs. RAG for LLMs: An Evaluation and Revisits (arXiv:2501.01880) — https://arxiv.org/abs/2501.01880
- [120] LaRA: Benchmarking Retrieval-Augmented Generation and Long-Context LLMs — No Silver Bullet for LC or RAG Routing (arXiv:2502.09977) — https://arxiv.org/abs/2502.09977
- [121] LongBench Pro: A More Realistic and Comprehensive Bilingual Long-Context Evaluation Benchmark (arXiv:2601.02872) — https://arxiv.org/abs/2601.02872
