/**
 * Data Transformers
 * 
 * Transform data between frontend and backend formats
 */

/**
 * Transform frontend assessment data to backend format
 */
export function transformAssessmentToBackend(data: any) {
  return {
    goals: data.goals || [],
    timeHorizon: data.time_horizon || data.timeHorizon || 10,
    riskTolerance: data.risk_tolerance || data.riskTolerance || "moderate",
    annualIncome: data.income || data.annualIncome || 0,
    monthlySavings: data.monthly_contribution || data.monthlySavings || 0,
    totalDebt: data.total_debt || data.totalDebt || 0,
    emergencyFundMonths: data.emergency_fund || data.emergencyFundMonths || "6 months",
    values: {
      avoidIndustries: data.avoid_industries || [],
      preferIndustries: data.prefer_industries || [],
      specificAssets: data.specific_assets || "",
      customConstraints: data.special_circumstances || data.customConstraints || ""
    },
    esgPrioritization: data.esg_preferences || data.esgPrioritization || false,
    marketSelection: data.market_selection || data.marketSelection || ["US"]
  };
}

/**
 * Transform backend report to frontend portfolio format
 */
export function transformReportToPortfolio(report: any) {
  const getRandomColor = () => {
    const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#F97316', '#06B6D4'];
    return colors[Math.floor(Math.random() * colors.length)];
  };

  // Handle different backend response formats
  const holdings = report.individual_holdings || report.weights_map || {};
  const tickers = report.portfolio_tickers || Object.keys(holdings);
  const weights = report.portfolio_weights || Object.values(holdings);
  const totalValue = report.total_portfolio_value || 100000;
  
  // Convert holdings to allocation array for pie chart
  const allocation = tickers.map((ticker: string, index: number) => {
    const weight = typeof holdings === 'object' ? holdings[ticker] : weights[index];
    const percentage = (weight || 0) * 100;  // Convert 0.3 → 30%
    
    return {
      name: ticker,
      symbol: ticker,
      percentage: percentage,
      amount: (percentage / 100) * totalValue,  // Calculate dollar amount
      color: getRandomColor(),
      rationale: `${ticker}: ${percentage.toFixed(1)}% allocation based on your risk profile and market analysis.`
    };
  }).filter((a: any) => a.percentage > 0);  // Remove zero allocations

  return {
    allocation: allocation,
    expected_return: report.expected_return || 7.6,
    volatility: report.volatility || 12.3,
    sharpe_ratio: report.sharpe_ratio || 1.42,
    risk_score: report.risk_score || 6.8,
    confidence: report.confidence || 85
  };
}

/**
 * Transform backend report to dashboard format
 */
export function transformReportToDashboard(report: any) {
  return {
    portfolio_value: report.total_portfolio_value || 125000,
    total_return: report.total_return_percent || 5.06,
    total_return_amount: report.total_return_amount || 23450,
    allocation: transformReportToPortfolio(report).allocation,
    risk_score: report.risk_score || 6.8,
    sharpe_ratio: report.sharpe_ratio || 1.42
  };
}
