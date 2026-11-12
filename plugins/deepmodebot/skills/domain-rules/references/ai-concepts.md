# AI concepts

Read when a task involves LLM fundamentals, RAG or retrieval, fine-tuning, inference cost or hardware, local models, model choice, or explaining AI terms. How to design and review agents is in `agent-engineering.md`; this file is the vocabulary and mechanics. Model, price, and market facts are dated to the source video and go stale fast; verify before relying on them. Source keys are in this skill's `SKILL.md`.

## Model basics

- **LLM**: a network with billions of parameters, trained on huge text corpora to predict the next token. (LLM)
- **Token**: the unit a model reads. About 4 characters, or 3/4 of an English word; 100 words is about 130 tokens. (FORGETS)
- **Context window**: the token budget for one request. System prompt, history, retrieved docs, tool definitions, and the reply all share it. (FORGETS)
- **Lost in the middle**: recall is strong at the start and end of a long context and weak in the middle. (AI-COURSE)
- **Temperature**: scales the next-token distribution. Low is focused and repeatable, high is varied. Neither makes output true. (AI-101)
- **Hallucination**: fluent, plausible output that the facts or the given context do not support. (LLM)
- **Text watermarking**: during generation, nudge choices among equally good synonyms in a hidden statistical pattern that a detector can find over a few hundred words. (WATERMARK)

## Retrieval

- **Embedding**: a vector that encodes meaning, so related phrases sit close together even with different words. (RAG-ELI5)
- **Vector database** (Pinecone, Milvus, Chroma, Weaviate, pgvector): fast approximate nearest-neighbor search over embeddings. (VECTOR-DB)
- **Vector indexes**: HNSW builds a layered navigation graph; IVF clusters vectors. Both trade speed against recall. (AI-101)
- **RAG**: fetch relevant chunks at request time and put them in the prompt, grounding answers without retraining. (RAG-ELI5)
- **Hybrid search**: dense vectors plus BM25 keyword search, so exact IDs, product codes, and error strings still match. (AI-COURSE)
- **Reranking**: a cross-encoder scores the candidate chunks against the query, and only the top few enter the prompt. (AI-COURSE)
- **HyDE**: draft a hypothetical answer, embed it, and search with that. (AI-COURSE)
- **Corrective RAG**: a grader checks the retrieved passages and falls back to web or other search when the evidence is weak. (AI-COURSE)
- **GraphRAG**: entities as nodes and relations as edges, for multi-hop questions that text search misses. (AI-COURSE)
- **Agentic RAG**: retrieval becomes a tool the agent calls repeatedly until its stop condition holds. (AI-COURSE)
- **Treat the knowledge base like software**: each document has an owner, provenance is tracked, chunks are deleted when a document retires, and there is a shared glossary. (AI-COURSE)

## Changing model behavior

| Method | Changes | Use for |
|---|---|---|
| Prompting | Instructions in context | The task itself |
| RAG | Facts in context at runtime | Fresh or private knowledge |
| Fine-tuning (SFT) | Weights, from input/target pairs | Consistent voice, format, procedure |
| LoRA | Two small low-rank adapter matrices; base frozen | Cheap fine-tuning |
| QLoRA | LoRA on a 4-bit quantized base | Fine-tuning on consumer GPUs |
| Distillation | A small student copies a big teacher's output distribution and reasoning | Cheaper, faster deployment |
| RLHF | Reward model trained on human preference comparisons | Alignment |
| DPO | Weights optimized straight from preferred/rejected pairs, no reward model | Simpler alignment |

(AI-101, AI-COURSE)

- **Reward hacking and sycophancy**: training learns shortcuts that score well but hurt quality, such as padding answers or agreeing with the user. (AI-COURSE)

## Agent vocabulary

- **Chatbot vs agent**: a chatbot answers once; an agent loops (perceive, reason, act, observe) toward a goal. (AI-COURSE)
- **Tool calling**: the model emits JSON with a tool name and arguments; app code runs it and returns the result. (LAWS)
- **ReAct**: alternate reasoning, a tool action, and observing the result. (AI-COURSE)
- **Skills**: folders of procedure with a light header, loaded on demand. (AI-COURSE)
- **MCP**: Anthropic's open client-server protocol (November 2024) for discovering tools, resources, and prompts; solves N×M integration. (MCP)
- **WebMCP**: a W3C proposal letting pages expose tools through JS APIs and HTML annotations. (WEBMCP)
- **LangGraph**: agent workflows as stateful graphs of nodes (functions or agents), edges (routing), and checkpoints for human pauses. (LANGGRAPH)
- **LangSmith**: tracing, run-tree visualization, evals, latency and cost tracking. (LANGSMITH)
- **AI gateway**: middleware for multi-tenant LLM traffic: rate limits, cost accounting, model fallback, PII masking. (AI-COURSE)
- **Hermes Agent** (Nous Research, open source): persistent memory, scheduled background tasks, learned reusable skills. (HERMES)
- **Jev** (Typesafe AI): answers many typed questions (choice, score, yes/no) in parallel in 70–500 ms instead of generating text. (JEV)
- **REA (Reverse Engineer Anything)**: open source, 139 MCP tools in 12 families, wiring coding agents to Ghidra, Hopper, and IDA Pro to inspect, decompile, and reconstruct software. (REA)
- **Prompt injection**: direct (a user message overrides the system prompt) or indirect (instructions hidden in a document or web page the agent reads). (AI-COURSE)
- **Evals**: score outputs over a versioned golden dataset as pass rates, with an LLM judge using a rubric for groundedness, relevance, and tone. (AI-COURSE)

## Inference and hardware

- **Transformer** (Vaswani et al., 2017): replaced sequential recurrence with parallel self-attention, where every token attends to every other token. (TRANSFORMERS)
- **Processors**: CPU for branchy sequential logic, GPU for massively parallel matrix math, TPU for tensor math (Google), NPU for low-power on-device inference. (PROCESSORS)
- **CUDA**: NVIDIA's platform and math libraries for general-purpose GPU programming. (AI-COURSE)
- **Prefill vs decode**: prefill reads the whole prompt in parallel and is compute-bound; decode emits tokens one at a time and is memory-bandwidth-bound. (AI-COURSE)
- **KV cache**: keeps past tokens' attention keys and values in GPU memory so each new token does not recompute them. (AI-COURSE)
- **Prompt caching**: reuse the processed state of an identical static prefix to skip its prefill. Put static content first. (AI-COURSE)
- **Quantization**: store weights in 8, 5, or 4 bits (Q8, Q4) instead of 16. Much less memory for a small quality loss. (LM-STUDIO)
- **Mixture of Experts**: routes each token to a few expert sub-networks, so only part of the parameters run per token (for example Qwen 3 Coder 480B). (OPEN-MODELS)
- **Local runtimes**: Ollama and LM Studio run quantized GGUF models on your own CPU or GPU with no data leaving the machine. (OLLAMA, LM-STUDIO)
- **Model routing**: easy tasks to small models, hard ones to big reasoning models. (AI-COURSE)
- **Research watch**: Next Concept Modeling (Stanford Hazy Research) generates text coarse to fine with residual VQ-VAE hierarchies, reported up to 31× faster than diffusion models. (NCM)

## Model and tool landscape (as of the video dates)

| Family | Positioned for |
|---|---|
| OpenAI GPT | General baseline for reasoning, code, structured output |
| Anthropic Claude (Haiku, Sonnet, Opus) | Hard coding, long documents, architecture writing |
| Claude Fable 5.2, Mythos 5.2 | Frontier reasoning; $8/M input, $40/M output; 49.1% on Frontier Code 2.0; long-horizon agent swarms (FABLE, 2026-11-10) |
| Google Gemini (Pro, Flash, Flash-Lite) | Native multimodal (text, audio, video, PDF), very large context |
| Meta Llama | Open weights for self-hosting, privacy, fine-tuning |
| xAI Grok | Real-time X and news context |
| Perplexity Sonar | Search-backed answers with live citations |
| Qwen, DeepSeek, Mistral and other open coders | Local agentic coding (Qwen 3 Coder, DeepSeek V4, Devstral Small), multimodal UI debugging (MiniMax M3) |

(PICK-MODEL, OPEN-MODELS)

- **Claude Code**: terminal agent that navigates a repo, runs commands, and makes multi-file edits behind permission checkpoints. (CLAUDE-WON)
- **Cursor Origin**: code hosting built around agents as first-class participants. (CURSOR-ORIGIN)
- **Abacus AI agent**: in a 15-minute test it built a news-curation app with a React front end, database tables (feeds, items, ingestion runs), hourly ingestion jobs, and an admin dashboard with filtering and duplicate detection. (APP-15MIN)
- **OpenClaw**: a local agent controlled remotely (for example over WhatsApp) that reads files, runs shell commands, and edits code. The risk shown is silent mistakes on a sensitive machine; sandbox it. (OPENCLAW)

## Industry and career signals (dated, verify before citing)

- **AGI**: hypothetical broad human-level competence with transfer, common sense, and continual learning. (AGI)
- **Bubble risk**: Gartner projects about $1 trillion of AI infrastructure spend in 2026, with over $3.5 trillion exposed to impairment by 2030 if profitable demand lags. Epoch AI: the cost to reach a given benchmark level fell about 47% per quarter since 2023. (BUBBLE)
- **Jobs**: WEF 2025 projects 170M jobs created and 92M displaced by 2030 (net +78M); 59 of every 100 workers need retraining. (CAREER-2030)
- **Early career**: Stanford found employment for ages 22–25 in AI-exposed roles 19% below expectations; PwC found entry-level postings requiring senior judgment up 35%. (AI-ERA)
- **Forward Deployed Engineer**: the hybrid role connecting models to legacy enterprise systems: requirements, RAG pipelines, evals, production deploys. (FDE)
