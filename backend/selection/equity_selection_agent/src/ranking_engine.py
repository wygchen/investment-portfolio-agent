"""
Agent Output and Reporting Module for Equity Selection Agent (ESA) V1.0

This module synthesizes surviving candidates' features into actionable metrics
and formats the output for state passing to other agents.

Classes:
- RankingEngine: Calculates final composite scores and ranks candidates
- OutputProcessor: Processes data into structured format for state passing
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from .config import Config

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class StockSelection:
    """Structure for individual stock selection with all metrics"""
    ticker: str
    final_score: float
    sector: str
    current_price: Optional[float]
    market_cap: Optional[float]
    
    # Raw fundamental metrics
    pe_ratio: Optional[float]
    roe: Optional[float]
    debt_to_equity: Optional[float]
    price_to_book: Optional[float]
    beta: Optional[float]
    
    # Normalized scores (Z-scores)
    pe_zscore: Optional[float]
    de_zscore: Optional[float]
    
    # Factor scores
    value_score: float
    quality_score: float
    risk_score: float
    momentum_score: float
    qualitative_score: float
    
    # Technical indicators
    rsi: Optional[float]
    positive_trend: Optional[bool]
    price_above_sma50: Optional[bool]
    
    # Qualitative assessment
    qual_assessment: Optional[str]
    qual_confidence: Optional[float]
    
    # Rankings
    overall_rank: int
    sector_rank: Optional[int]


@dataclass
class SelectionSummary:
    """Summary statistics for the selection process"""
    timestamp: str
    total_universe_size: int
    final_selection_count: int
    screening_layers_applied: int
    total_exclusions: int
    
    # Score distribution
    avg_final_score: float
    median_final_score: float
    score_std: float
    
    # Sector distribution
    sector_distribution: Dict[str, int]
    
    # Factor contributions
    avg_value_contribution: float
    avg_quality_contribution: float
    avg_risk_contribution: float
    avg_momentum_contribution: float
    avg_qualitative_contribution: float


class RankingEngine:
    """
    Calculates final composite scores and ranks all surviving candidates.
    Implements the weighted scoring methodology from the system design.
    """
    
    def __init__(self, config: Config):
        self.config = config
    
    def calculate_value_score(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate value factor score based on P/E and P/B Z-scores.
        Lower P/E and P/B ratios (negative Z-scores) indicate better value.
        
        Args:
            data: DataFrame with P/E and P/B metrics
            
        Returns:
            Series with value scores (0-10 scale)
        """
        value_scores = pd.Series(5.0, index=data.index)  # Default neutral score
        
        # P/E Z-score component (negative is better for value)
        if 'pe_zscore' in data.columns:
            pe_component = data['pe_zscore'].fillna(0)
            # Convert Z-score to 0-10 scale (negative Z-score = higher value score)
            pe_scores = 5 - (pe_component * 2)  # Each std dev = 2 points
            pe_scores = pd.Series(np.clip(pe_scores, 0, 10), index=data.index)
        else:
            pe_scores = pd.Series(5.0, index=data.index)
        
        # P/B component (if available)
        if 'price_to_book' in data.columns:
            pb_values = data['price_to_book'].fillna(data['price_to_book'].median())
            # Simple ranking approach for P/B
            pb_ranks = pb_values.rank(ascending=True, pct=True)  # Lower P/B = higher rank
            pb_scores = pb_ranks * 10
        else:
            pb_scores = pd.Series(5.0, index=data.index)
        
        # Combine P/E (70%) and P/B (30%) for value score
        value_scores = (pe_scores * 0.7) + (pb_scores * 0.3)
        value_scores = pd.Series(np.clip(value_scores, 0, 10), index=data.index)
        
        return value_scores
    
    def calculate_quality_score(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate quality factor score based primarily on ROE.
        
        Args:
            data: DataFrame with ROE metrics
            
        Returns:
            Series with quality scores (0-10 scale)
        """
        quality_scores = pd.Series(5.0, index=data.index)
        
        if 'roe' in data.columns:
            roe_values = data['roe'].fillna(0)
            
            # Convert ROE to 0-10 scale
            # ROE of 15% = 5.0, 30% = 10.0, 0% = 0.0
            quality_scores = pd.Series(np.clip(roe_values * 33.33, 0, 10), index=data.index)  # 33.33 = 10/0.3
        
        return quality_scores
    
    def calculate_risk_score(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate risk factor score (inverse of risk - higher score = lower risk).
        Based on Beta and D/E ratio.
        
        Args:
            data: DataFrame with Beta and D/E metrics
            
        Returns:
            Series with risk scores (0-10 scale, higher = safer)
        """
        risk_scores = pd.Series(5.0, index=data.index)
        
        # Beta component (lower Beta = higher score)
        if 'beta' in data.columns:
            beta_values = data['beta'].fillna(1.0)
            # Beta of 1.0 = 5.0, Beta of 0.5 = 7.5, Beta of 1.5 = 2.5
            beta_scores = 10 - (beta_values * 5)
            beta_scores = pd.Series(np.clip(beta_scores, 0, 10), index=data.index)
        else:
            beta_scores = pd.Series(5.0, index=data.index)
        
        # D/E Z-score component (lower D/E = higher score)
        if 'de_zscore' in data.columns:
            de_component = data['de_zscore'].fillna(0)
            # Negative Z-score (lower than sector average) = higher risk score
            de_scores = 5 - (de_component * 2)
            de_scores = pd.Series(np.clip(de_scores, 0, 10), index=data.index)
        else:
            de_scores = pd.Series(5.0, index=data.index)
        
        # Combine Beta (60%) and D/E (40%)
        risk_scores = (beta_scores * 0.6) + (de_scores * 0.4)
        risk_scores = pd.Series(np.clip(risk_scores, 0, 10), index=data.index)
        
        return risk_scores
    
    def calculate_momentum_score(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate momentum factor score based on technical indicators.
        
        Args:
            data: DataFrame with technical indicators
            
        Returns:
            Series with momentum scores (0-10 scale)
        """
        momentum_scores = pd.Series(5.0, index=data.index)
        
        # RSI component (50-70 range is optimal)
        if 'rsi' in data.columns:
            rsi_values = data['rsi'].fillna(50)
            # Optimal RSI around 60, penalty for extreme values
            rsi_scores = 10 - np.abs(rsi_values - 60) / 10
            rsi_scores = pd.Series(np.clip(rsi_scores, 0, 10), index=data.index)
        else:
            rsi_scores = pd.Series(5.0, index=data.index)
        
        # Trend component
        trend_scores = pd.Series(5.0, index=data.index)
        if 'positive_trend' in data.columns:
            trend_scores = data['positive_trend'].fillna(False).astype(int) * 3 + 4
            # True = 7, False = 4
        
        # Price above SMA50 component
        sma_scores = pd.Series(5.0, index=data.index)
        if 'price_above_sma50' in data.columns:
            sma_scores = data['price_above_sma50'].fillna(False).astype(int) * 2 + 4
            # True = 6, False = 4
        
        # Combine components
        momentum_scores = (rsi_scores * 0.4) + (trend_scores * 0.4) + (sma_scores * 0.2)
        momentum_scores = pd.Series(np.clip(momentum_scores, 0, 10), index=data.index)
        
        return momentum_scores
    
    def calculate_composite_score(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the final composite score using configured weights.
        
        Args:
            data: DataFrame with all calculated metrics
            
        Returns:
            DataFrame with factor scores and final composite score
        """
        if data.empty:
            return data
        
        # Calculate individual factor scores
        value_scores = self.calculate_value_score(data)
        quality_scores = self.calculate_quality_score(data)
        risk_scores = self.calculate_risk_score(data)
        momentum_scores = self.calculate_momentum_score(data)
        
        # Qualitative scores (already on 0-10 scale or default to 5.0)
        qual_scores = data.get('qual_score', pd.Series(5.0, index=data.index))
        
        # Calculate weighted composite score
        composite_scores = (
            (value_scores * self.config.weights.w_value) +
            (quality_scores * self.config.weights.w_quality) +
            (risk_scores * self.config.weights.w_risk) +
            (momentum_scores * self.config.weights.w_momentum) +
            (qual_scores * self.config.weights.w_qualitative)
        )
        
        # Add factor scores to DataFrame
        result_data = data.copy()
        result_data['value_score'] = value_scores
        result_data['quality_score'] = quality_scores
        result_data['risk_score'] = risk_scores
        result_data['momentum_score'] = momentum_scores
        result_data['qualitative_score'] = qual_scores
        result_data['final_score'] = composite_scores
        
        return result_data
    
    def rank_candidates(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Rank candidates by final score and add ranking information.
        
        Args:
            data: DataFrame with calculated scores
            
        Returns:
            DataFrame sorted by final score with ranking columns
        """
        if data.empty:
            return data
        
        # Sort by final score (descending)
        ranked_data = data.sort_values('final_score', ascending=False).copy()
        
        # Add overall ranking
        ranked_data['overall_rank'] = range(1, len(ranked_data) + 1)
        
        # Add sector ranking
        if 'sector' in ranked_data.columns:
            ranked_data['sector_rank'] = ranked_data.groupby('sector')['final_score'].rank(
                ascending=False, method='dense'
            ).astype(int)
        
        return ranked_data
    
    def select_top_candidates(self, ranked_data: pd.DataFrame) -> pd.DataFrame:
        """
        Select top N candidates according to configuration.
        
        Args:
            ranked_data: DataFrame with ranked candidates
            
        Returns:
            DataFrame with top N candidates
        """
        n = self.config.output.target_stock_count
        return ranked_data.head(n).copy()


class OutputProcessor:
    """
    Processes final selection data into structured format for state passing.
    Focused on data transformation rather than file generation.
    """
    
    def __init__(self, config: Config):
        self.config = config
    
    def create_stock_selections(self, data: pd.DataFrame) -> List[StockSelection]:
        """
        Convert DataFrame to structured StockSelection objects.
        
        Args:
            data: DataFrame with ranked stock data
            
        Returns:
            List of StockSelection objects
        """
        selections = []
        
        for _, row in data.iterrows():
            selection = StockSelection(
                ticker=row.get('ticker', 'Unknown'),
                final_score=row.get('final_score', 0.0),
                sector=row.get('sector', 'Unknown'),
                current_price=row.get('current_price'),
                market_cap=row.get('market_cap'),
                
                # Raw metrics
                pe_ratio=row.get('pe_ratio'),
                roe=row.get('roe'),
                debt_to_equity=row.get('debt_to_equity'),
                price_to_book=row.get('price_to_book'),
                beta=row.get('beta'),
                
                # Z-scores
                pe_zscore=row.get('pe_zscore'),
                de_zscore=row.get('de_zscore'),
                
                # Factor scores
                value_score=row.get('value_score', 0.0),
                quality_score=row.get('quality_score', 0.0),
                risk_score=row.get('risk_score', 0.0),
                momentum_score=row.get('momentum_score', 0.0),
                qualitative_score=row.get('qualitative_score', 0.0),
                
                # Technical indicators
                rsi=row.get('rsi'),
                positive_trend=row.get('positive_trend'),
                price_above_sma50=row.get('price_above_sma50'),
                
                # Qualitative
                qual_assessment=row.get('qual_assessment'),
                qual_confidence=row.get('qual_confidence'),
                
                # Rankings
                overall_rank=row.get('overall_rank', 0),
                sector_rank=row.get('sector_rank')
            )
            selections.append(selection)
        
        return selections
    
    def create_selection_summary(self, 
                               initial_universe_size: int,
                               final_data: pd.DataFrame,
                               screening_summary: Dict[str, Any]) -> SelectionSummary:
        """
        Create summary statistics for the selection process.
        
        Args:
            initial_universe_size: Size of initial universe
            final_data: Final selected candidates
            screening_summary: Summary from screening process
            
        Returns:
            SelectionSummary object
        """
        if final_data.empty:
            return SelectionSummary(
                timestamp=datetime.now().isoformat(),
                total_universe_size=initial_universe_size,
                final_selection_count=0,
                screening_layers_applied=screening_summary.get('total_layers', 0),
                total_exclusions=initial_universe_size,
                avg_final_score=0.0,
                median_final_score=0.0,
                score_std=0.0,
                sector_distribution={},
                avg_value_contribution=0.0,
                avg_quality_contribution=0.0,
                avg_risk_contribution=0.0,
                avg_momentum_contribution=0.0,
                avg_qualitative_contribution=0.0
            )
        
        # Score statistics
        final_scores = final_data['final_score']
        
        # Sector distribution
        sector_dist = final_data['sector'].value_counts().to_dict()
        
        # Factor contributions (weighted scores)
        weights = self.config.weights
        
        summary = SelectionSummary(
            timestamp=datetime.now().isoformat(),
            total_universe_size=initial_universe_size,
            final_selection_count=len(final_data),
            screening_layers_applied=screening_summary.get('total_layers', 0),
            total_exclusions=screening_summary.get('total_exclusions', 0),
            
            avg_final_score=float(final_scores.mean()),
            median_final_score=float(final_scores.median()),
            score_std=float(final_scores.std()),
            
            sector_distribution=sector_dist,
            
            avg_value_contribution=float(final_data.get('value_score', pd.Series([0])).mean() * weights.w_value),
            avg_quality_contribution=float(final_data.get('quality_score', pd.Series([0])).mean() * weights.w_quality),
            avg_risk_contribution=float(final_data.get('risk_score', pd.Series([0])).mean() * weights.w_risk),
            avg_momentum_contribution=float(final_data.get('momentum_score', pd.Series([0])).mean() * weights.w_momentum),
            avg_qualitative_contribution=float(final_data.get('qualitative_score', pd.Series([0])).mean() * weights.w_qualitative)
        )
        
        return summary
    
    def process_final_output(self, 
                           final_data: pd.DataFrame,
                           initial_universe_size: int,
                           screening_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process final selection data into structured output for state passing.
        
        Args:
            final_data: Final ranked selection data
            initial_universe_size: Size of initial universe
            screening_summary: Screening process summary
            
        Returns:
            Structured output dictionary ready for state passing
        """
        # Create structured objects
        selections = self.create_stock_selections(final_data)
        summary = self.create_selection_summary(
            initial_universe_size, final_data, screening_summary
        )
        
        # Generate structured output for state passing
        output = {
            'meta': {
                'timestamp': summary.timestamp,
                'agent_version': '1.0.0',
                'configuration': self.config.to_dict()
            },
            'summary': asdict(summary),
            'screening_details': screening_summary,
            'selections': [asdict(selection) for selection in selections],
            'top_picks': {
                'top_5_by_score': [asdict(s) for s in selections[:5]],
                'top_value_pick': None,
                'top_quality_pick': None,
                'top_momentum_pick': None
            }
        }
        
        # Find top picks by factor
        if selections:
            # Top value pick (highest value score)
            top_value = max(selections, key=lambda x: x.value_score)
            output['top_picks']['top_value_pick'] = asdict(top_value)
            
            # Top quality pick (highest quality score)
            top_quality = max(selections, key=lambda x: x.quality_score)
            output['top_picks']['top_quality_pick'] = asdict(top_quality)
            
            # Top momentum pick (highest momentum score)
            top_momentum = max(selections, key=lambda x: x.momentum_score)
            output['top_picks']['top_momentum_pick'] = asdict(top_momentum)
        
        return output