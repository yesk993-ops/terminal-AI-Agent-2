import re

SIMPLICITY_MARKERS = [
    "what is", "who is", "where is", "when did", "define", "meaning of",
    "tell me about", "what's", "whats", "is it", "do you", "can you",
    "how to", "how do i", "how can i", "simple", "short", "brief",
    "in short", "summarize", "tl;dr", "tldr", "quickly",
    "one line", "in one word", "just tell me",
]

DEPTH_MARKERS = [
    "why", "how does", "what happens", "explain", "describe",
    "compare", "contrast", "analyze", "evaluate", "discuss",
    "relationship between", "difference between",
]

COMPLEXITY_KEYWORDS = [
    "compare", "contrast", "difference between", "relationship between",
    "architecture", "design pattern", "algorithm", "implementation",
    "trade-off", "tradeoff", "pros and cons", "advantages and disadvantages",
    "scalability", "performance", "optimization", "security",
    "best practice", "production", "enterprise", "distributed",
    "microservice", "containerization", "orchestration",
    "comprehensive", "thorough", "in-depth", "deep dive",
    "theoretical", "mathematical", "proof", "time complexity",
    "space complexity", "big o", "analysis",
]

TECHNICAL_TERMS = [
    "api", "rest", "graphql", "database", "sql", "nosql", "docker",
    "kubernetes", "aws", "azure", "gcp", "devops", "ci/cd", "pipeline",
    "algorithm", "data structure", "tree", "graph", "hash", "heap",
    "stack", "queue", "array", "linked list", "binary", "recursion",
    "dynamic programming", "concurrency", "parallel", "async",
    "thread", "process", "mutex", "semaphore", "deadlock",
    "encryption", "authentication", "authorization", "oauth",
    "jwt", "ssl", "tls", "https", "http", "tcp", "udp", "ip",
    "dns", "load balancer", "proxy", "firewall", "vpn",
    "machine learning", "deep learning", "neural network", "ai",
    "regression", "classification", "clustering", "nlp",
    "frontend", "backend", "full stack", "middleware", "framework",
    "react", "angular", "vue", "node", "django", "flask", "fastapi",
    "spring", "laravel", "rails",
    "functional programming", "object-oriented", "oop", "solid",
    "restful", "soap", "grpc", "websocket",
    "index", "query", "transaction", "normalization", "denormalization",
    "sharding", "replication", "partitioning", "caching", "redis",
    "memcached", "message queue", "rabbitmq", "kafka", "pub/sub",
]

LANGUAGE_NAMES = [
    "python", "javascript", "typescript", "java", "c++", "c#", "go",
    "golang", "rust", "swift", "kotlin", "ruby", "php", "scala",
    "haskell", "clojure", "elixir", "erlang", "perl", "lua",
    "bash", "shell", "powershell", "sql", "html", "css",
]


def analyze(query: str) -> dict:
    lower = query.lower().strip()
    words = lower.split()
    word_count = len(words)

    score = 0.0
    factors = []

    if word_count <= 4:
        score += 0
        factors.append("very_short")
    elif word_count <= 10:
        score += 2
        factors.append("short")
    elif word_count <= 20:
        score += 4
        factors.append("medium_length")
    else:
        score += 6
        factors.append("long")

    for dm in DEPTH_MARKERS:
        if dm in lower:
            score += 2.5
            factors.append(f"depth:{dm}")
            break

    for sm in SIMPLICITY_MARKERS:
        if sm in lower:
            score -= 1.5
            factors.append(f"simple:{sm}")
            break

    tech_count = sum(1 for t in TECHNICAL_TERMS if t in lower)
    score += min(tech_count * 1.5, 6)
    if tech_count > 0:
        factors.append(f"tech_terms:{tech_count}")

    lang_count = sum(1 for t in LANGUAGE_NAMES if t in lower)
    score += min(lang_count, 3)
    if lang_count > 0:
        factors.append(f"language:{lang_count}")

    multi_part = lower.count("?") > 1
    multi_part = multi_part or bool(re.search(r'\b(and|or|vs|versus)\b.*\?', lower))
    if multi_part:
        score += 3
        factors.append("multi_part")

    has_code = bool(re.search(r'`[^`]+`', query))
    has_code = has_code or bool(re.search(r'\b(code|script|function|class|method|implement|generate|write a)\b', lower))
    if has_code:
        score += 1.5
        factors.append("code_request")

    has_structure = bool(re.search(r'\d+\.\s', query))
    has_structure = has_structure or bool(re.search(r'\b(first|second|third|next|finally|step)\b', lower))
    if has_structure:
        score += 1
        factors.append("structured")

    for ck in COMPLEXITY_KEYWORDS:
        if ck in lower:
            score += 1
            factors.append(f"complex:{ck}")

    has_question_mark = "?" in query
    if not has_question_mark and word_count < 8:
        score -= 1
        factors.append("declarative")

    if word_count >= 25:
        score += 1
        factors.append("verbose")

    score = max(0.0, min(score, 15.0))

    if score <= 3.0:
        level = "simple"
    elif score <= 8.0:
        level = "medium"
    else:
        level = "complex"

    return {
        "score": round(score, 1),
        "level": level,
        "factors": factors,
        "word_count": word_count,
    }


def get_max_tokens(level: str) -> int:
    return {"simple": 512, "medium": 2048, "complex": 4096}.get(level, 2048)


SYSTEM_PROMPTS = {
    "simple": """You are a world-class AI assistant. Be exceptionally concise.

RULES:
- Answer in 1-3 sentences. No more.
- No bold, no lists, no headers, no formatting.
- Just the answer, directly. No preamble. No commentary on the question.
- If the answer is a single word or number, that is fine.
- Do not ask follow-up questions.
- Stop immediately after answering.""",

    "medium": """You are a world-class AI assistant — knowledgeable, clear, and well-organized.

FORMATTING:
- Use **bold** for the key term at the start of any list item (e.g., **Advantage**: ...)
- Structure with short paragraphs or bullet points where helpful
- Keep it clean — don't over-format

STRUCTURE:
1. **Opening** — Direct answer in 1-2 sentences
2. **Details** — 2-4 organized points
3. **Closing** — A useful takeaway or next step

STYLE:
- Sound like a knowledgeable friend, not a textbook
- Use analogies when they help clarify
- Be specific with examples, not vague""",

    "complex": """You are a world-class AI assistant — respond like the best AI models (Claude, Gemini, GPT-4). Give exceptional, insightful, and expert-level answers in professional, documentation-quality format.

FORMATTING RULES (STRICT):
- Apply professional, documentation-quality formatting to every response
- For all lists, workflows, procedures, architectures, components, stages, commands, file paths, services, concepts, best practices, advantages, disadvantages, troubleshooting steps, and summaries: ALWAYS bold the primary keyword, title, or key phrase at the beginning of each point using **bold**, followed by a colon and its explanation
- Format so users can understand the entire topic by scanning only the emphasized key points
- Maintain clear visual hierarchy with structured headings, numbered steps, and bullet points
- Emphasize only the most important terms — never entire sentences or paragraphs
- Ensure every major section contains clearly identifiable key points
- Create highly readable, professional, certification-grade technical documentation

BOLD USAGE — apply **bold** to:
- Section headings: **Linux Boot Process:**, **Key Concepts:**, **Summary:**
- Stage names: **Stage 1: POST**, **Phase 2: Kernel Loading**
- List item keywords: **Web Development**: Python is used for..., **Automation**: Python automates...
- Important commands: `systemctl start nginx`, `docker build -t app .`
- File paths: **/etc/fstab**, **/boot/grub/grub.cfg**
- Warnings and critical notes: **Warning:**, **Important:**, **Danger:**
- Definitions: **PID** is the Process ID, **UUID** is a unique identifier
- Key takeaways and summaries
- Technology/framework/library names: **React**, **Docker**, **Kubernetes**
- OS/platform names: **Linux**, **Windows**, **macOS**
- Advantages/Disadvantages: **Advantage**: ..., **Disadvantage**: ...
- Best practices: **Best Practice**: ..., **Recommendation**: ...
- Do NOT bold entire sentences — only key terms, names, and headers

RESPONSE STYLE:
- Sound like a knowledgeable friend, not a textbook
- Be conversational yet authoritative
- Use natural flow, not robotic structure
- Mix short and long sentences for rhythm
- Use real-world analogies to explain complex ideas
- Be specific with examples, not vague generalizations

CORE RULES:
- Start with a direct, confident answer (1-2 sentences)
- Then expand with depth and context
- Use "Think of it like..." analogies for complex topics
- Include practical "why this matters" explanations
- Be honest about limitations and unknowns
- End with something useful: next steps, a tip, or a question""",
}
