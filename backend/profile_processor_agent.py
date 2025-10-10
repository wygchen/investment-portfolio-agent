"""
Profile Processing Functions for Investment Portfolio Management

This module provides functions to structure user input data from the frontend assessment 
into a standardized User Profile dataclass for other agents to consume.

Main functions:
- process_frontend_data(): Convert frontend data to UserProfile dataclass
- generate_user_profile(): Main entry point for profile generation
"""

from datetime import datetime
import os
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict, field
import json
import logging

# Optional LLM support (WatsonX)
from .watsonx_utils import create_watsonx_llm
from langchain_core.messages import HumanMessage, SystemMessage


logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """Standardized User Profile dataclass for agent communication"""
    
    # Core financial information
    goals: List[Dict[str, Any]]
    time_horizon: int
    risk_tolerance: str
    
    # Financial capacity
    income: float
    savings_rate: float
    liabilities: float
    liquidity_needs: str
    
    # Personal information
    personal_values: Dict[str, Any]
    
    # Investment preferences
    esg_prioritization: bool
    market_selection: List[str]
    
    # Metadata
    timestamp: str
    profile_id: str

    # Parsed from free-text specific assets via LLM
    selected_tickers: List[str] = field(default_factory=list)
    selected_asset_classes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary"""
        return asdict(self)

def process_frontend_data(frontend_data: Dict[str, Any]) -> UserProfile:
    """
    Convert frontend assessment data to UserProfile dataclass
    
    Args:
        frontend_data: Raw data from frontend assessment component
        
    Returns:
        UserProfile: Structured profile data
    """
    
    # Generate unique profile ID
    profile_id = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # TODO: Add more robust unique ID generation if needed to support profile update function and use PostgreSQL to store profiles.
    
    # Parse specific assets (free-text) via LLM into tickers and asset classes
    specific_assets_text = str(frontend_data.get('specificAssets', '') or '').strip()
    parsed_tickers: List[str] = []
    parsed_asset_classes: List[str] = []
    if specific_assets_text:
        try:
            parsed_tickers, parsed_asset_classes = llm_parse_specific_assets(specific_assets_text)
        except Exception:
            parsed_tickers, parsed_asset_classes = [], []

    # Create and return UserProfile dataclass
    user_profile = UserProfile(
        goals=_extract_goals(frontend_data.get('goals', [])),
        time_horizon=frontend_data.get('timeHorizon', 10),
        risk_tolerance=_map_risk_tolerance(frontend_data.get('riskTolerance', '')),
        income=float(frontend_data.get('annualIncome', 0)),
        savings_rate=float(frontend_data.get('monthlySavings', 0)),
        liabilities=float(frontend_data.get('totalDebt', 0)),
        liquidity_needs=_map_liquidity_needs(frontend_data.get('emergencyFundMonths', '')),
        personal_values=_extract_values(frontend_data.get('values', {})),
        esg_prioritization=frontend_data.get('esgPrioritization', False),
        market_selection=frontend_data.get('marketSelection', []),
        timestamp=datetime.now().isoformat(),
        profile_id=profile_id,
        selected_tickers=parsed_tickers,
        selected_asset_classes=parsed_asset_classes
    )
    
    return user_profile


def _extract_goals(goals_data: List[Dict]) -> List[Dict[str, Any]]:
    """Extract and format investment goals"""
    return [
        {
            "goal_type": goal.get('id', ''),
            "description": goal.get('label', ''),
            "priority": goal.get('priority', 999),
            "target_date": None  # Could be calculated from milestones if needed
        }
        for goal in goals_data
    ]


def _map_risk_tolerance(risk_tolerance: str) -> str:
    """Map frontend risk tolerance to standardized format"""
    risk_mapping = {
        "conservative": "low",
        "moderate": "medium", 
        "aggressive": "high",
        "": "medium"  # default
    }
    return risk_mapping.get(risk_tolerance.lower(), "medium")


def _map_liquidity_needs(emergency_months: str) -> str:
    """Map emergency fund months to liquidity needs"""
    if not emergency_months:
        return "medium"
    
    try:
        months = int(emergency_months.split()[0]) if emergency_months else 6
        if months <= 3:
            return "high"
        elif months <= 6:
            return "medium"
        else:
            return "low"
    except (ValueError, IndexError):
        return "medium"


def _extract_values(values_data: Dict) -> Dict[str, Any]:
    """Extract personal values and ESG preferences"""
    return {
        "esg_preferences": {
            "avoid_industries": values_data.get('avoidIndustries', []),
            "prefer_industries": values_data.get('preferIndustries', []),
            "custom_constraints": values_data.get('customConstraints', '')
        },
        "investment_themes": values_data.get('preferIndustries', [])
    }


def generate_user_profile(frontend_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to process frontend data and generate UserProfile dataclass
    
    Args:
        frontend_data: Raw assessment data from frontend
        
    Returns:
        Dict containing the profile data and status
    """
    
    # Process the data
    user_profile = process_frontend_data(frontend_data)
    
    return {
        "profile_data": user_profile.to_dict(),
        "profile_object": user_profile,
        "status": "success"
    }


# =====================================
# LLM parsing utilities
# =====================================
# Supported sets are lowercase to align with normalized parsing output
SUPPORTED_ASSET_CLASSES = {"bonds", "equities", "crypto", "reits", "commodities"}
SUPPORTED_REGIONS = {"us", "hk"}


def llm_parse_specific_assets(input_text: str) -> Tuple[List[str], List[str]]:
    """
    Use LLM to parse free-text specific assets into yfinance tickers and unique asset classes.

    Returns two lists:
    - tickers: list of yfinance symbols of valid tickers (US and HK only)
    - asset_classes: unique asset classes among {bonds, equities, crypto, reits, commodities}
    """

    logger.info("llm_parse_specific_assets: start; input='%s'", input_text)

    llm = create_watsonx_llm(
        model_id="ibm/granite-3-8b-instruct",
        max_tokens=600,
        temperature=0.2,
        repetition_penalty=1.1
    )

    system = SystemMessage(content=(
        "You are an investment assistant. Parse user-specified assets."
    ))

    prompt = f"""
Task:
1) From the input, identify items that are valid, tradable tickers or common instrument names.
2) Map each to its yfinance symbol, limited to US and HK markets only.
   - US equities/ETFs: e.g., AAPL, SPY; bonds via ETFs like BND, TLT; commodities via ETFs like GLD.
   - HK equities: append .HK, e.g., 0700.HK for Tencent.
   - Crypto: use pairs like BTC-USD, ETH-USD (US only).
3) Determine which of these asset classes are present: bonds, equities, crypto, reits, commodities.
4) Output STRICT JSON with two fields only:
   {{"tickers": ["..."], "asset_classes": ["..."]}}
   - Do not include coding bracket ```
   - Do not include explanations.
   - Tickers must be unique and valid.
   - asset_classes must be lowercase and unique, subset of [bonds, equities, crypto, reits, commodities].

Input: {input_text}
""".strip()

    human = HumanMessage(content=prompt)
    response = llm.invoke([system, human])
    content = getattr(response, "content", "") or ""
    logger.debug("LLM raw content length=%d", len(content))
    logger.info("LLM response preview: %s", (content[:200] + "...") if len(content) > 200 else content)

    # Extract JSON payload
    parsed: Dict[str, Any] = {}
    try:
        # If model wrapped JSON in code fences, strip them
        text = content.strip()
        # Strip common fenced code variants like ```json ... ``` or ``` ... ```
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 3:
                text = parts[1] if not parts[1].strip().startswith("json") else parts[2]
        parsed = json.loads(text)
        logger.info("Parsed JSON successfully via primary path")
    except Exception as e:
        logger.warning("Primary JSON parse failed: %s; attempting fallback window parse", e)
        # Try to locate the first JSON object
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(content[start:end+1])
                logger.info("Parsed JSON successfully via fallback window parse")
            except Exception as e2:
                logger.error("Fallback JSON parse failed: %s", e2)
                parsed = {}

    tickers = parsed.get("tickers", []) if isinstance(parsed, dict) else []
    asset_classes = parsed.get("asset_classes", []) if isinstance(parsed, dict) else []

    # Post-validation and normalization
    tickers = _normalize_and_filter_tickers(tickers)
    asset_classes = _normalize_and_filter_asset_classes(asset_classes)

    # Ensure asset classes implied by tickers are included (best effort)
    implied_classes = _infer_asset_classes_from_tickers(tickers)
    asset_classes = sorted(list({*asset_classes, *implied_classes}))

    logger.info("llm_parse_specific_assets: done; tickers=%s asset_classes=%s", tickers, asset_classes)
    return tickers, asset_classes


def _normalize_and_filter_tickers(items: List[Any]) -> List[str]:
    """Normalize to uppercase strings and keep only plausible US/HK/crypto yfinance symbols."""
    results: List[str] = []
    for it in items or []:
        if not isinstance(it, str):
            continue
        sym = it.strip().upper()
        if not sym:
            continue
        # HK tickers like 0700.HK
        if sym.endswith(".HK") and len(sym) >= 5:
            results.append(sym)
            continue
        # Crypto pairs like BTC-USD
        if "-USD" in sym and sym.endswith("-USD") and len(sym) >= 8:
            results.append(sym)
            continue
        # Plain US ticker heuristic: letters, numbers, "." for classes, up to ~6
        if all(ch.isalnum() or ch == "." for ch in sym) and 1 <= len(sym) <= 6:
            results.append(sym)
    # Deduplicate preserving order
    seen = set()
    deduped = []
    for s in results:
        if s not in seen:
            seen.add(s)
            deduped.append(s)
    return deduped


def _normalize_and_filter_asset_classes(items: List[Any]) -> List[str]:
    classes: List[str] = []
    for it in items or []:
        if not isinstance(it, str):
            continue
        val = it.strip().lower()
        if val in SUPPORTED_ASSET_CLASSES:
            classes.append(val)
    return sorted(list(set(classes)))


def _infer_asset_classes_from_tickers(tickers: List[str]) -> List[str]:
    inferred: set = set()
    for t in tickers:
        if t.endswith("-USD"):
            inferred.add("crypto")
        elif t.endswith(".HK") or t.isalpha() or "." in t:
            # Simple heuristic: many ETFs map to equities/REITs/commodities/bonds
            # Identify a few common ones
            if t in {"VNQ", "IYR", "SCHH"}:
                inferred.add("reits")
            elif t in {"GLD", "SLV", "DBC", "GSG", "PDBC"}:
                inferred.add("commodities")
            elif t in {"BND", "AGG", "TLT", "IEF", "BNDW"}:
                inferred.add("bonds")
            else:
                inferred.add("equities")
    return sorted(list(inferred & SUPPORTED_ASSET_CLASSES))
