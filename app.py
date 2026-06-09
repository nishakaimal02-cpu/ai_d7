# app.py

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from agent.database import init_database, load_history
from agent.nodes import (
    load_data, find_gaps, enrich_gaps,
    classify_severity, escalate, monitor,
    log_healthy, generate_recommendation,
    DOMAIN_LABELS, GAP_FIELD
)

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Market Intelligence Agent",
    page_icon="🧠",
    layout="wide"
)

# Initialise database
init_database()

# --- SESSION STATE DEFAULTS ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'idle'
if 'state' not in st.session_state:
    st.session_state.state = None
if 'log' not in st.session_state:
    st.session_state.log = []
if 'domain' not in st.session_state:
    st.session_state.domain = None

# --- HEADER ---
st.title("🧠 Market Intelligence Agent")
st.caption("LangGraph agent — finds gaps, enriches with web search, waits for your approval")

st.divider()

# --- DOMAIN SELECTOR ---
st.subheader("Select Intelligence Domain")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🤖 AI Product Intelligence", use_container_width=True):
        st.session_state.domain = "ai_products"
        st.session_state.stage = 'idle'
        st.session_state.log = []

with col2:
    if st.button("💰 Startup Funding Gaps", use_container_width=True):
        st.session_state.domain = "startup_funding"
        st.session_state.stage = 'idle'
        st.session_state.log = []

with col3:
    if st.button("💼 PM Job Market Intelligence", use_container_width=True):
        st.session_state.domain = "pm_jobs"
        st.session_state.stage = 'idle'
        st.session_state.log = []

# Show selected domain
if st.session_state.domain:
    st.success(f"Selected: {DOMAIN_LABELS[st.session_state.domain]}")
else:
    st.info("Select a domain to begin")

st.divider()

# --- SIDEBAR: RUN HISTORY ---
with st.sidebar:
    st.header("📋 Run History")
    
    if st.session_state.domain:
        history = load_history(st.session_state.domain)
        
        if history:
            for run in history:
                severity_color = "🔴" if run['severity'] == "CRITICAL" else "🟡" if run['severity'] == "MODERATE" else "🟢"
                with st.expander(f"{severity_color} {run['date'][:10]}"):
                    st.write(f"**Domain:** {DOMAIN_LABELS[run['domain']]}")
                    st.write(f"**Severity:** {run['severity']}")
                    st.write(f"**Approved:** {run['approved']}")
                    if run['recommendation']:
                        st.write("**Recommendation:**")
                        st.write(run['recommendation'][:300] + "...")
        else:
            st.info("No previous runs for this domain")
    else:
        st.info("Select a domain to see history")

# --- RUN BUTTON ---
run_button = st.button(
    "🚀 Run Intelligence Agent",
    type="primary",
    disabled=not st.session_state.domain
)

# --- AGENT EXECUTION ---
def add_log(message: str):
    st.session_state.log.append(message)

if run_button and st.session_state.domain:
    
    # Reset
    st.session_state.log = []
    st.session_state.stage = 'running'
    
    # Initial state
    current_state = {
        "domain": st.session_state.domain,
        "dataset": [],
        "gaps": [],
        "enriched_context": "",
        "severity": "",
        "approved": False,
        "recommendation": "",
        "run_history": []
    }
    
    # Run nodes up to approval point
    add_log("🟢 Agent started")
    
    add_log(f"[Node 1] Loading {DOMAIN_LABELS[st.session_state.domain]} dataset...")
    current_state = load_data(current_state)
    add_log(f"[Node 1] ✓ Loaded {len(current_state['dataset'])} records")
    
    if current_state['run_history']:
        add_log(f"[Node 1] ✓ Found {len(current_state['run_history'])} previous run(s)")
    
    add_log("[Node 2] Finding top 3 gaps...")
    current_state = find_gaps(current_state)
    add_log(f"[Node 2] ✓ Top 3 gaps identified")
    
    add_log("[Node 3] Enriching with web search — this may take 15-20 seconds...")
    current_state = enrich_gaps(current_state)
    add_log("[Node 3] ✓ Web enrichment complete")
    
    add_log("[Node 4] Classifying severity...")
    current_state = classify_severity(current_state)
    add_log(f"[Node 4] ✓ Severity: {current_state['severity']}")
    
    # Route by severity
    if current_state['severity'] == "CRITICAL":
        add_log("[Node 5a] 🔴 ESCALATING — critical gaps detected")
        current_state = escalate(current_state)
    elif current_state['severity'] == "MODERATE":
        add_log("[Node 5b] 🟡 MONITORING — moderate gaps flagged")
        current_state = monitor(current_state)
    else:
        add_log("[Node 5c] 🟢 LOGGING — market healthy")
        current_state = log_healthy(current_state)
    
    add_log("⏸️ Waiting for human approval...")
    
    st.session_state.state = current_state
    st.session_state.stage = 'awaiting_approval'

# --- DISPLAY LOG AND GAPS ---
if st.session_state.log:
    
    left_col, right_col = st.columns([1, 1])
    
    with left_col:
        st.subheader("📡 Agent Log")
        for log_line in st.session_state.log:
            st.text(log_line)
    
    with right_col:
        if st.session_state.state and st.session_state.state['gaps']:
            st.subheader("🔍 Top 3 Gaps Found")
            
            domain = st.session_state.state['domain']
            gap_field = GAP_FIELD[domain]
            
            for i, gap in enumerate(st.session_state.state['gaps'], 1):
                name = gap.get('category') or gap.get('problem_space') or gap.get('skill')
                score = gap[gap_field]
                market = gap.get('market_size_usd_bn', 'N/A')
                
                with st.expander(f"Gap {i}: {name}"):
                    st.metric("Gap Score", score)
                    if market != 'N/A':
                        st.metric("Market Size", f"${market}B")
                    
                    # Show domain-specific fields
                    if domain == 'ai_products':
                        st.write(f"**Competitors:** {gap.get('num_competitors')}")
                        st.write(f"**Pain points:** {gap.get('top_pain_points')}")
                    elif domain == 'startup_funding':
                        st.write(f"**Funded startups:** {gap.get('num_funded_startups')}")
                        st.write(f"**Investor interest:** {gap.get('investor_interest')}")
                    else:
                        st.write(f"**Demand score:** {gap.get('demand_score')}")
                        st.write(f"**Supply score:** {gap.get('supply_score')}")
                        st.write(f"**Top companies:** {gap.get('top_hiring_companies')}")

# --- APPROVAL SECTION ---
if st.session_state.stage == 'awaiting_approval':
    
    current_state = st.session_state.state
    
    st.divider()
    st.subheader("⚠️ Human Approval Required")
    
    severity = current_state['severity']
    if severity == "CRITICAL":
        st.error(f"🔴 Severity: CRITICAL — Immediate action recommended")
    elif severity == "MODERATE":
        st.warning(f"🟡 Severity: MODERATE — Monitor and plan")
    else:
        st.success(f"🟢 Severity: HEALTHY — No urgent action needed")
    
    st.write("**Web-enriched gap analysis:**")
    st.write(current_state['enriched_context'])
    
    st.write("**Generate full strategic recommendation report?**")
    
    yes_col, no_col = st.columns([1, 5])
    
    with yes_col:
        if st.button("✅ Yes, generate", type="primary"):
            st.session_state.state['approved'] = True
            st.session_state.stage = 'complete'
            st.rerun()
    
    with no_col:
        if st.button("❌ No, cancel"):
            st.session_state.state['approved'] = False
            st.session_state.stage = 'complete'
            st.rerun()

# --- RECOMMENDATION OUTPUT ---
if st.session_state.stage == 'complete':
    
    current_state = st.session_state.state
    
    add_log("[Node 6] Generating recommendation...")
    current_state = generate_recommendation(current_state)
    add_log("✅ Run complete — saved to history")
    
    st.divider()
    st.subheader("📄 Strategic Recommendation Report")
    
    if current_state['approved']:
        st.success("Report generated and saved to history")
        st.markdown(current_state['recommendation'])
    else:
        st.error("⛔ Report generation cancelled")
    
    st.session_state.stage = 'idle'