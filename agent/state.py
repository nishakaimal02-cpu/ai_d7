from typing import TypedDict, List, Dict, Any

class IntelligenceState(TypedDict):
    
    # Which domain the user selected
    domain: str  # "ai_products" | "startup_funding" | "pm_jobs"
    
    # Raw data loaded from JSON
    dataset: List[Dict[str, Any]]
    
    # Top 3 gaps identified from dataset
    gaps: List[Dict[str, Any]]
    
    # Web search enrichment for each gap
    enriched_context: str
    
    # Severity classification
    severity: str  # "critical" | "moderate" | "healthy"
    
    # Human approval
    approved: bool
    
    # Final recommendation report
    recommendation: str
    
    # Run history from SQLite
    run_history: List[Dict[str, Any]]