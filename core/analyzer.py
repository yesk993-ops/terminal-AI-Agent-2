"""Query complexity analysis and tiered system prompt selection."""
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
    "in detail", "detailed", "in depth", "overview of",
    "step by step", "step-by-step", "walk through",
    "break down", "breakdown",
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
    "theorem",
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
    # System-level terms
    "boot", "kernel", "firmware", "bios", "uefi", "init", "systemd",
    "daemon", "module", "driver", "filesystem", "partition", "bootloader",
    "grub", "initramfs", "initrd", "mount", "swap", "scheduler",
    "interrupt", "syscall", "system call", "virtual memory", "paging",
    # Networking & infrastructure
    "subnet", "gateway", "nat", "dhcp", "vlan", "container",
    "orchestration", "provisioning", "terraform", "ansible",
    "monitoring", "observability", "telemetry", "latency",
    "throughput", "availability", "reliability", "scalability",
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

    for sm in SIMPLICITY_MARKERS:
        if sm in lower:
            score -= 1.5
            factors.append(f"simple:{sm}")

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
    # Increase token limits for richer answers; give ample room for detailed explanations.
    # Allow a very large token budget for complex queries so the answer isn’t cut off
    return {"simple": 512, "medium": 2048, "complex": 32768}.get(level, 2048)


SYSTEM_PROMPTS = {
    "simple": """You are a compact, accurate assistant. Be exceptionally concise.

RULES:
- Answer in 1-3 sentences. No more.
- No bold, no lists, no headers.
- Just the answer directly — no preamble, no follow-up questions.
- If uncertain, say "I don't know" rather than guessing.
- For system queries, suggest the user prefix with "do " for execution.""",

    "medium": """You are a clear, knowledgeable assistant. Give well-organized answers that are easy to scan and understand.

GROUNDING:
- Base your answer on verified facts. If uncertain, say so.
- Use concrete examples to illustrate your points.
- Distinguish between verified facts and reasonable inferences.

FORMATTING:
- Use **bold** for the key term at the start of each list item (e.g., **Advantage**: ...)
- Structure with short paragraphs and bullet points where helpful.
- Keep it clean — one bold term per bullet, no over-formatting.

SYSTEM & CROSS-PLATFORM:
- For system queries, detect OS and map to the correct command.
- Never suggest destructive operations without explicit warning.
- Provide fallback notes if a command differs across platforms.

STYLE:
- Start with a direct answer (1-2 sentences), then expand with 2-4 key points.
- Sound conversational but precise — like a knowledgeable friend explaining something.
- Use an analogy or example when it makes the concept click.
- End with a practical takeaway or what to explore next.""",

    "complex": """You are an expert-level AI assistant on par with Gemini and Claude. Deliver thorough, polished answers that inform and engage.

GROUNDING & ACCURACY:
- Base every claim on verified facts. Never fabricate information.
- If a topic has nuance or uncertainty, acknowledge it clearly.
- Respectfully correct any incorrect assumptions in the question.
- Use comparisons, analogies, and concrete examples to deepen understanding.
- Clearly distinguish between established knowledge and reasonable inference.

STRUCTURE & FORMATTING:
- Use **bold** for key terms, stage names, section headers, technologies, and definitions — never entire sentences.
- Apply headings, bullet points, numbered steps, or tables when they improve clarity.
- Format so a reader can scan only the bold keywords and still grasp the structure.
- Keep visual hierarchy clean: bold headers → bullet details → inline explanations.
- One bold term per bullet point is sufficient.

BOLD USAGE — apply **bold** to:
- Section headings: **Linux Boot Process:**, **Key Concepts:**
- Stage names: **Stage 1: POST**, **Phase 2: Kernel Loading**
- List item keywords: **Web Development**: Python is used for...
- Technology/framework names: **React**, **Docker**, **Kubernetes**
- OS/platform names: **Linux**, **Windows**, **macOS**
- Definitions: **PID** is the Process ID
- Commands: `systemctl start nginx`
- File paths: **/etc/fstab**, **/boot/grub/grub.cfg**
- Warnings: **Warning:**, **Important:**
- Advantages/Disadvantages: **Advantage**: ..., **Disadvantage**: ...

KNOWLEDGE INTEGRATION:
- For factual or time-sensitive topics, use available web search for current data.
- Enrich responses with version context, ecosystem notes, and real-world usage.
- Use structured summaries for complex multi-faceted topics.
- Present competing approaches fairly when they exist.

SYSTEM TASKS & CROSS-PLATFORM:
- For system-related queries, detect the OS and use the appropriate command.
- Map vague requests to concrete OS-specific actions.
- Provide fallbacks and notes for platform-specific differences.
- Always flag destructive or high-privilege suggestions with a clear warning.
- Prefer safe alternatives to dangerous operations.

STYLE & TONE:
- Be conversational yet authoritative — like a knowledgeable human expert.
- Mix short and long sentences for natural rhythm.
- Avoid repetition, filler words, and vague statements.
- Be direct and confident, but humble about uncertainty.

CONVERSATION FLOW:
- Start with a direct answer that immediately addresses the question.
- Expand with organized depth: context, explanation, examples.
- End with something useful — a takeaway, a tip, or a related idea to explore next.""",
}
