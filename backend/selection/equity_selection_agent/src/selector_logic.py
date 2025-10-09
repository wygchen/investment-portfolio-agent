"""
Screening and Selection Logic Module for Equity Selection Agent (ESA) V1.0

This module applies core investment rules through layered high-pass filters
to reduce the universe to a qualified shortlist based on multi-factor criteria.

Classes:
- EquityScreener: Applies layered quantitative and qualitative filters
- QualitativeAnalysisAgent: LangGraph-based LLM qualitative analysis (imported)
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
import json
from dataclasses import dataclass

from config import Config
from qualitative_agent import QualitativeAnalysisAgent

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ScreeningResults:
    """Results from each screening layer with exclusion tracking"""
    layer_name: str
    input_count: int
    output_count: int
    exclusion_count: int
    exclusion_reasons: List[str]  # Sample of exclusion reasons
    surviving_tickers: List[str]

class EquityScreener:
    """
    Primary screening engine that applies layered quantitative filters
    and integrates qualitative analysis for final candidate selection.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.qualitative_agent = QualitativeAnalysisAgent(config)
        self.screening_history: List[ScreeningResults] = []
        
    # Region and sector filters are intentionally removed; filtering now happens earlier in the workflow
    
    def apply_quality_screen(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, ScreeningResults]:
        """
        Apply Layer 1: Quality and Efficiency Screen.
        Filters for minimum ROE (simplified - no balance sheet data required).
        
        Args:
            data: DataFrame with fundamental metrics
            
        Returns:
            Tuple of (filtered_data, screening_results)
        """
        input_count = len(data)
        exclusion_reasons = []
        
        # Start with all data
        filtered_data = data.copy()
        
        # Filter: Minimum ROE threshold (only filter we can reliably apply)
        if 'roe' in filtered_data.columns:
            # Debug: Log ROE statistics
            roe_stats = filtered_data['roe'].describe()
            mean_val = roe_stats.get('mean', 'N/A')
            median_val = roe_stats.get('50%', 'N/A')
            min_val = roe_stats.get('min', 'N/A')
            max_val = roe_stats.get('max', 'N/A')
            
            # Format statistics safely
            mean_str = f"{mean_val:.3f}" if isinstance(mean_val, (int, float)) else str(mean_val)
            median_str = f"{median_val:.3f}" if isinstance(median_val, (int, float)) else str(median_val)
            min_str = f"{min_val:.3f}" if isinstance(min_val, (int, float)) else str(min_val)
            max_str = f"{max_val:.3f}" if isinstance(max_val, (int, float)) else str(max_val)
            
            logger.info(f"ROE statistics: mean={mean_str}, median={median_str}, min={min_str}, max={max_str}")
            logger.info(f"ROE threshold: {self.config.screening.min_roe}")
            
            # Count stocks with valid ROE data
            valid_roe_count = filtered_data['roe'].notna().sum()
            logger.info(f"Stocks with valid ROE data: {valid_roe_count}/{len(filtered_data)}")
            
            low_roe = filtered_data[
                (filtered_data['roe'].notna()) & 
                (filtered_data['roe'] < self.config.screening.min_roe)
            ]
            
            # Keep stocks with valid ROE above threshold OR missing ROE data (for now)
            filtered_data = filtered_data[
                (filtered_data['roe'].isna()) | 
                (filtered_data['roe'] >= self.config.screening.min_roe)
            ]
            
            logger.info(f"Stocks excluded due to low ROE: {len(low_roe)}")
            
            if len(low_roe) > 0:
                sample_exclusions = low_roe.head(3)
                for _, row in sample_exclusions.iterrows():
                    exclusion_reasons.append(
                        f"Ticker {row.get('ticker', 'Unknown')}: ROE {row['roe']:.3f} < {self.config.screening.min_roe}"
                    )
        else:
            logger.info("No ROE data available - skipping quality screen filtering")
        
        results = ScreeningResults(
            layer_name="Quality Screen",
            input_count=input_count,
            output_count=len(filtered_data),
            exclusion_count=input_count - len(filtered_data),
            exclusion_reasons=exclusion_reasons[:self.config.output.log_sample_exclusions],
            surviving_tickers=filtered_data['ticker'].tolist() if 'ticker' in filtered_data.columns else []
        )
        
        self.screening_history.append(results)
        logger.info(f"Quality screen: {input_count} -> {len(filtered_data)} stocks")
        
        return filtered_data, results
    
    def apply_risk_screen(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, ScreeningResults]:
        """
        Apply Layer 2: Risk and Leverage Screen.
        Filters for D/E ratios and Beta thresholds.
        
        Args:
            data: DataFrame with risk metrics
            
        Returns:
            Tuple of (filtered_data, screening_results)
        """
        input_count = len(data)
        exclusion_reasons = []
        filtered_data = data.copy()
        
        # Filter 1: Debt-to-Equity ratio (absolute threshold)
        if 'debt_to_equity' in filtered_data.columns:
            high_de = filtered_data[
                (filtered_data['debt_to_equity'].notna()) & 
                (filtered_data['debt_to_equity'] > self.config.screening.max_debt_equity_absolute)
            ]
            
            filtered_data = filtered_data[
                (filtered_data['debt_to_equity'].isna()) | 
                (filtered_data['debt_to_equity'] <= self.config.screening.max_debt_equity_absolute)
            ]
            
            if len(high_de) > 0:
                sample_exclusions = high_de.head(3)
                for _, row in sample_exclusions.iterrows():
                    sector_threshold = self.config.get_sector_specific_thresholds(
                        row.get('sector', 'Unknown')
                    ).get('max_debt_equity_absolute', self.config.screening.max_debt_equity_absolute)
                    
                    exclusion_reasons.append(
                        f"Ticker {row.get('ticker', 'Unknown')}: D/E {row['debt_to_equity']:.2f} > {sector_threshold}"
                    )
        
        # Filter 2: D/E Z-Score (peer-relative)
        if 'de_zscore' in filtered_data.columns:
            high_de_zscore = filtered_data[
                (filtered_data['de_zscore'].notna()) & 
                (filtered_data['de_zscore'] > self.config.screening.debt_equity_zscore_threshold)
            ]
            
            filtered_data = filtered_data[
                (filtered_data['de_zscore'].isna()) | 
                (filtered_data['de_zscore'] <= self.config.screening.debt_equity_zscore_threshold)
            ]
            
            if len(high_de_zscore) > 0:
                sample_exclusions = high_de_zscore.head(2)
                for _, row in sample_exclusions.iterrows():
                    exclusion_reasons.append(
                        f"Ticker {row.get('ticker', 'Unknown')}: D/E Z-score {row['de_zscore']:.2f} above sector average"
                    )
        
        # Filter 3: Beta threshold
        if 'beta' in filtered_data.columns:
            high_beta = filtered_data[
                (filtered_data['beta'].notna()) & 
                (filtered_data['beta'] > self.config.screening.max_beta)
            ]
            
            filtered_data = filtered_data[
                (filtered_data['beta'].isna()) | 
                (filtered_data['beta'] <= self.config.screening.max_beta)
            ]
            
            if len(high_beta) > 0:
                sample_exclusions = high_beta.head(2)
                for _, row in sample_exclusions.iterrows():
                    exclusion_reasons.append(
                        f"Ticker {row.get('ticker', 'Unknown')}: Beta {row['beta']:.2f} > {self.config.screening.max_beta}"
                    )
        
        results = ScreeningResults(
            layer_name="Risk Screen",
            input_count=input_count,
            output_count=len(filtered_data),
            exclusion_count=input_count - len(filtered_data),
            exclusion_reasons=exclusion_reasons[:self.config.output.log_sample_exclusions],
            surviving_tickers=filtered_data['ticker'].tolist() if 'ticker' in filtered_data.columns else []
        )
        
        self.screening_history.append(results)
        logger.info(f"Risk screen: {input_count} -> {len(filtered_data)} stocks")
        
        return filtered_data, results
    
    def apply_valuation_screen(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, ScreeningResults]:
        """
        Apply Layer 3: Valuation Screen.
        Filters for attractive P/E ratios relative to sector peers.
        
        Args:
            data: DataFrame with valuation metrics
            
        Returns:
            Tuple of (filtered_data, screening_results)
        """
        input_count = len(data)
        exclusion_reasons = []
        filtered_data = data.copy()
        
        # Filter 1: P/E Z-Score (must be cheaper than sector average)
        if 'pe_zscore' in filtered_data.columns:
            expensive_pe = filtered_data[
                (filtered_data['pe_zscore'].notna()) & 
                (filtered_data['pe_zscore'] > self.config.screening.pe_zscore_threshold)
            ]
            
            filtered_data = filtered_data[
                (filtered_data['pe_zscore'].isna()) | 
                (filtered_data['pe_zscore'] <= self.config.screening.pe_zscore_threshold)
            ]
            
            if len(expensive_pe) > 0:
                sample_exclusions = expensive_pe.head(3)
                for _, row in sample_exclusions.iterrows():
                    exclusion_reasons.append(
                        f"Ticker {row.get('ticker', 'Unknown')}: P/E Z-score {row['pe_zscore']:.2f} above sector average"
                    )
        
        # Filter 2: Absolute P/E cap (avoid extreme outliers)
        if 'pe_ratio' in filtered_data.columns:
            extreme_pe = filtered_data[
                (filtered_data['pe_ratio'].notna()) & 
                (filtered_data['pe_ratio'] > self.config.screening.max_pe_absolute)
            ]
            
            filtered_data = filtered_data[
                (filtered_data['pe_ratio'].isna()) | 
                (filtered_data['pe_ratio'] <= self.config.screening.max_pe_absolute)
            ]
            
            if len(extreme_pe) > 0:
                sample_exclusions = extreme_pe.head(2)
                for _, row in sample_exclusions.iterrows():
                    sector_threshold = self.config.get_sector_specific_thresholds(
                        row.get('sector', 'Unknown')
                    ).get('max_pe_absolute', self.config.screening.max_pe_absolute)
                    
                    exclusion_reasons.append(
                        f"Ticker {row.get('ticker', 'Unknown')}: P/E {row['pe_ratio']:.1f} > {sector_threshold}"
                    )
        
        results = ScreeningResults(
            layer_name="Valuation Screen",
            input_count=input_count,
            output_count=len(filtered_data),
            exclusion_count=input_count - len(filtered_data),
            exclusion_reasons=exclusion_reasons[:self.config.output.log_sample_exclusions],
            surviving_tickers=filtered_data['ticker'].tolist() if 'ticker' in filtered_data.columns else []
        )
        
        self.screening_history.append(results)
        logger.info(f"Valuation screen: {input_count} -> {len(filtered_data)} stocks")
        
        return filtered_data, results
    
    def apply_technical_screen(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, ScreeningResults]:
        """
        Apply Technical Filter: Confirm positive trend and avoid overbought conditions.
        
        Args:
            data: DataFrame with technical indicators
            
        Returns:
            Tuple of (filtered_data, screening_results)
        """
        input_count = len(data)
        exclusion_reasons = []
        filtered_data = data.copy()
        
        # Filter 1: Positive trend requirement
        if self.config.screening.require_positive_trend and 'positive_trend' in filtered_data.columns:
            negative_trend = filtered_data[
                (filtered_data['positive_trend'].notna()) & 
                (~filtered_data['positive_trend'])
            ]
            
            filtered_data = filtered_data[
                (filtered_data['positive_trend'].isna()) | 
                (filtered_data['positive_trend'])
            ]
            
            if len(negative_trend) > 0:
                sample_exclusions = negative_trend.head(3)
                for _, row in sample_exclusions.iterrows():
                    exclusion_reasons.append(
                        f"Ticker {row.get('ticker', 'Unknown')}: No positive trend (Price below SMA50 and MACD bearish)"
                    )
        
        # Filter 2: RSI overbought filter
        if 'rsi_overbought' in filtered_data.columns:
            overbought = filtered_data[
                (filtered_data['rsi_overbought'].notna()) & 
                (filtered_data['rsi_overbought'])
            ]
            
            filtered_data = filtered_data[
                (filtered_data['rsi_overbought'].isna()) | 
                (~filtered_data['rsi_overbought'])
            ]
            
            if len(overbought) > 0:
                sample_exclusions = overbought.head(2)
                for _, row in sample_exclusions.iterrows():
                    exclusion_reasons.append(
                        f"Ticker {row.get('ticker', 'Unknown')}: RSI overbought (>{self.config.screening.max_rsi_overbought})"
                    )
        
        results = ScreeningResults(
            layer_name="Technical Screen",
            input_count=input_count,
            output_count=len(filtered_data),
            exclusion_count=input_count - len(filtered_data),
            exclusion_reasons=exclusion_reasons[:self.config.output.log_sample_exclusions],
            surviving_tickers=filtered_data['ticker'].tolist() if 'ticker' in filtered_data.columns else []
        )
        
        self.screening_history.append(results)
        logger.info(f"Technical screen: {input_count} -> {len(filtered_data)} stocks")
        
        return filtered_data, results
    
    def apply_full_screening_pipeline(self, 
                                    data: pd.DataFrame) -> pd.DataFrame:
        """
        Apply the complete screening pipeline in sequence.
        
        Args:
            data: Input DataFrame with all features
            allowed_regions: List of allowed regions (None for all)
            allowed_sectors: List of allowed sectors (None for all)
            
        Returns:
            Filtered DataFrame with surviving candidates
        """
        logger.info(f"Starting full screening pipeline with {len(data)} stocks")
        
        # Reset screening history
        self.screening_history = []
        
        current_data = data.copy()
        
        # Step 1: Quality screen
        current_data, _ = self.apply_quality_screen(current_data)
        
        # Step 2: Risk screen
        current_data, _ = self.apply_risk_screen(current_data)
        
        # Step 3: Valuation screen
        current_data, _ = self.apply_valuation_screen(current_data)
        
        # Step 4: Technical screen
        current_data, _ = self.apply_technical_screen(current_data)
        
        logger.info(f"Completed screening pipeline: {len(data)} -> {len(current_data)} stocks")
        
        return current_data
    
    def get_screening_summary(self) -> Dict[str, Any]:
        """
        Get summary of screening results for reporting.
        
        Returns:
            Dictionary with screening statistics
        """
        if not self.screening_history:
            return {}
        
        summary = {
            'total_layers': len(self.screening_history),
            'initial_count': self.screening_history[0].input_count if self.screening_history else 0,
            'final_count': self.screening_history[-1].output_count if self.screening_history else 0,
            'total_exclusions': sum(r.exclusion_count for r in self.screening_history),
            'layers': []
        }
        
        for result in self.screening_history:
            layer_summary = {
                'name': result.layer_name,
                'input_count': result.input_count,
                'output_count': result.output_count,
                'exclusion_count': result.exclusion_count,
                'exclusion_rate': result.exclusion_count / result.input_count if result.input_count > 0 else 0,
                'sample_exclusions': result.exclusion_reasons
            }
            summary['layers'].append(layer_summary)
        
        return summary
    
    def enable_qualitative_analysis(self, enable: bool = True):
        """Enable qualitative analysis integration"""
        self.qualitative_agent.enable_qualitative_analysis(enable)
    
    def add_qualitative_scores(self, data: pd.DataFrame, 
                             fundamental_data: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """
        Add qualitative scores to the screened data.
        
        Args:
            data: Screened DataFrame
            fundamental_data: Original fundamental data with business summaries
            
        Returns:
            DataFrame with qualitative scores added
        """
        logger.info(f"Starting qualitative analysis for {len(data)} stocks")
        logger.info(f"Qualitative agent enabled: {self.qualitative_agent.enabled}")
        logger.info(f"LLM available: {self.qualitative_agent.llm is not None}")
        
        if not self.qualitative_agent.enabled or data.empty:
            logger.info("Qualitative analysis disabled or no data - using placeholder scores")
            # Add placeholder qualitative score
            data = data.copy()
            data['qual_score'] = self.config.weights.w_qualitative * 0  # Zero weight if disabled
            return data
        
        # Prepare data for qualitative analysis
        companies_for_analysis = {}
        for _, row in data.iterrows():
            ticker = row['ticker']
            if ticker in fundamental_data:
                companies_for_analysis[ticker] = {
                    'news': fundamental_data[ticker].get('business_summary', ''),  # Changed from 'business_summary' to 'news'
                    'roe': row.get('roe'),
                    'debt_to_equity': row.get('debt_to_equity'),
                    'pe_ratio': row.get('pe_ratio')
                }
        
        logger.info(f"Prepared {len(companies_for_analysis)} companies for qualitative analysis")
        
        # Get qualitative scores
        logger.info("Starting batch qualitative analysis...")
        qual_scores = self.qualitative_agent.batch_analyze(companies_for_analysis)
        logger.info(f"Completed qualitative analysis for {len(qual_scores)} companies")
        
        # Add scores to DataFrame
        data = data.copy()
        data['qual_score'] = 5.0  # Default neutral score
        data['qual_confidence'] = 0.5
        data['qual_assessment'] = 'Not analyzed'
        
        for ticker, qual_result in qual_scores.items():
            mask = data['ticker'] == ticker
            data.loc[mask, 'qual_score'] = qual_result.qual_score
            data.loc[mask, 'qual_confidence'] = qual_result.confidence or 0.5
            data.loc[mask, 'qual_assessment'] = qual_result.overall_assessment or 'Analyzed'
        
        logger.info(f"Added qualitative scores for {len(qual_scores)} stocks")
        return data