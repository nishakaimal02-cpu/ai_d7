# agent/nodes.py

import json
import os
from langchain_openai import ChatOpenAI
from agent.database import load_history, save_run
from agent.state import IntelligenceState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Domain labels for display
DOMAIN_LABELS = {
    "ai_products": "AI Product Intelligence",
    "startup_funding": "Startup Funding Gaps",
    "pm_jobs": "PM Job Market Intelligence"
}

# Score field per domain — what we sort by to find gaps
GAP_FIELD = {
    "ai_products": "coverage_score",
    "startup_funding": "funding_gap_score",
    "pm_jobs": "gap_score"
}

# For ai_products and startup_funding, LOW score = gap
# For pm_jobs, HIGH gap_score = gap
SORT_ASCENDING = {
    "ai_products": True,   # lowest coverage = biggest gap
    "startup_funding": True,  # lowest funding = biggest gap
    "pm_jobs": False       # highest gap score = biggest gap
}


def load_data(state: IntelligenceState) -> IntelligenceState:
    """
    Node 1 — loads dataset for selected domain + run history
    """
    print(f"\n[Node 1] Loading data for domain: {state['domain']}")
    
    # Load the right JSON file based on domain
    domain_files = {
        "ai_products": "data/ai_products.json",
        "startup_funding": "data/startup_funding.json",
        "pm_jobs": "data/pm_jobs.json"
    }
    
    filepath = domain_files[state['domain']]
    
    with open(filepath, 'r') as f:
        state['dataset'] = json.load(f)
    
    print(f"[Node 1] Loaded {len(state['dataset'])} records")
    
    # Load previous runs for this domain
    state['run_history'] = load_history(state['domain'])
    
    if state['run_history']:
        print(f"[Node 1] Found {len(state['run_history'])} previous run(s)")
    else:
        print(f"[Node 1] No previous runs for this domain")
    
    return state


def find_gaps(state: IntelligenceState) -> IntelligenceState:
    """
    Node 2 — finds top 3 gaps from dataset by sorting on gap field
    """
    print(f"\n[Node 2] Finding gaps in dataset")
    
    domain = state['domain']
    gap_field = GAP_FIELD[domain]
    ascending = SORT_ASCENDING[domain]
    
    # Sort dataset by gap field to find biggest gaps
    sorted_data = sorted(
        state['dataset'],
        key=lambda x: x[gap_field],
        reverse=not ascending  # ascending=True means lowest first
    )
    
    # Take top 3
    state['gaps'] = sorted_data[:3]
    
    for i, gap in enumerate(state['gaps'], 1):
        # Get the name field — different per domain
        name = gap.get('category') or gap.get('problem_space') or gap.get('skill')
        print(f"[Node 2] Gap {i}: {name} — score: {gap[gap_field]}")
    
    return state


def enrich_gaps(state: IntelligenceState) -> IntelligenceState:
    """
    Node 3 — enriches each gap with web search context
    Uses OpenAI's built-in web search tool
    """
    print(f"\n[Node 3] Enriching gaps with web search")
    
    enriched = []
    
    for gap in state['gaps']:
        # Get name field
        name = gap.get('category') or gap.get('problem_space') or gap.get('skill')
        
        # Build a targeted search query per domain
        if state['domain'] == 'ai_products':
            query = f"{name} AI market startups funding news 2026"
        elif state['domain'] == 'startup_funding':
            query = f"{name} startups investment funding news 2026"
        else:
            query = f"{name} product manager jobs demand salary 2026"
        
        print(f"[Node 3] Searching: {query}")
        
        # Use LLM with web search tool
        from openai import OpenAI
        search_client = OpenAI()
        
        response = search_client.chat.completions.create(
            model="gpt-4o-mini-search-preview",
            messages=[
                {
                    "role": "user",
                    "content": f"Find current market context for: {query}. Summarise in 2-3 sentences focusing on recent developments, new entrants, or funding news."
                }
            ]
        )
        
        enriched.append({
            "name": name,
            "gap_data": gap,
            "web_context": response.choices[0].message.content
        })
    
    # Store enriched context as formatted string for LLM consumption
    context_parts = []
    for item in enriched:
        context_parts.append(
            f"**{item['name']}**\n"
            f"Data: {json.dumps(item['gap_data'])}\n"
            f"Current context: {item['web_context']}"
        )
    
    state['enriched_context'] = "\n\n".join(context_parts)
    print(f"[Node 3] Enrichment complete")
    
    return state


def classify_severity(state: IntelligenceState) -> IntelligenceState:
    """
    Node 4 — classifies overall severity based on gaps + enriched context
    """
    print(f"\n[Node 4] Classifying severity")
    
    response = llm.invoke(
        f"""You are an intelligence analyst reviewing market gaps.
        
        Domain: {DOMAIN_LABELS[state['domain']]}
        
        Top gaps identified:
        {state['enriched_context']}
        
        Classify the overall severity as exactly one of:
        - CRITICAL: gaps represent urgent opportunities or risks requiring immediate action
        - MODERATE: gaps worth monitoring and planning around
        - HEALTHY: market is well served, no significant gaps
        
        Respond with ONLY the word: CRITICAL, MODERATE, or HEALTHY"""
    )
    
    state['severity'] = response.content.strip().upper()
    print(f"[Node 4] Severity: {state['severity']}")
    
    return state


def escalate(state: IntelligenceState) -> IntelligenceState:
    """
    Node 5a — runs when severity is CRITICAL
    """
    print(f"\n[Node 5a: ESCALATE] Critical gaps — flagging for urgent review")
    return state


def monitor(state: IntelligenceState) -> IntelligenceState:
    """
    Node 5b — runs when severity is MODERATE
    """
    print(f"\n[Node 5b: MONITOR] Moderate gaps — flagging for monitoring")
    return state


def log_healthy(state: IntelligenceState) -> IntelligenceState:
    """
    Node 5c — runs when severity is HEALTHY
    """
    print(f"\n[Node 5c: LOG] Market healthy — logging for records")
    return state


def generate_recommendation(state: IntelligenceState) -> IntelligenceState:
    """
    Node 6 — generates final recommendation report if approved
    Saves run to SQLite regardless of approval
    """
    print(f"\n[Node 6] Generating recommendation")
    
    if not state['approved']:
        state['recommendation'] = "⛔ Recommendation cancelled by user."
        save_run(state)
        return state
    
    response = llm.invoke(
        f"""You are a strategic intelligence analyst.
        
        Domain: {DOMAIN_LABELS[state['domain']]}
        Severity: {state['severity']}
        
        Gap analysis:
        {state['enriched_context']}
        
        Write a strategic recommendation report with:
        1. Executive summary (2 sentences)
        2. Top 3 gaps with why each matters
        3. Recommended actions (3 bullet points)
        4. Risk if ignored
        
        Be specific and actionable. Use the web context to make recommendations current."""
    )
    
    state['recommendation'] = response.content
    save_run(state)
    
    return state


def route_by_severity(state: IntelligenceState) -> str:
    """
    Conditional edge function — reads severity, returns next node name
    """
    severity = state['severity']
    if severity == "CRITICAL":
        return "escalate"
    elif severity == "MODERATE":
        return "monitor"
    else:
        return "log_healthy"