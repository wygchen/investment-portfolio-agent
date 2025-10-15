/**
 * API Client for PortfolioAI Backend
 * Handles all HTTP requests to the FastAPI backend
 */

// API Configuration  
const API_BASE_URL = 'http://127.0.0.1:8000';

// Types matching the backend Pydantic models
export interface AssessmentData {
  goals: Array<{
    goal_type: string;
    description: string;
    priority: number;
    target_date?: string;
  }>;
  timeHorizon: number;
  riskTolerance: string;
  annualIncome: number;
  monthlySavings: number;
  totalDebt: number;
  emergencyFundMonths: string;
  values: {
    esg_preferences?: {
      avoid_industries?: string[];
      prefer_industries?: string[];
      custom_constraints?: string;
      specific_assets?: string[];
    };
    investment_themes?: string[];
  };
  esgPrioritization: boolean;
  marketSelection: string[];
}

export interface PortfolioAllocation {
  name: string;
  percentage: number;
  amount: number;
  color?: string;
  rationale?: string;
}

export interface PortfolioRecommendation {
  allocation: PortfolioAllocation[];
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  risk_score: number;
  confidence: number;
}

export interface MarketOverview {
  market_indices: Array<{
    name: string;
    value: number;
    change: number;
    change_percent: number;
  }>;
  sector_performance: Array<{
    sector: string;
    change_percent: number;
  }>;
  economic_indicators: {
    vix: number;
    '10y_treasury': number;
    dollar_index: number;
    oil_price: number;
  };
  last_updated: string;
}

export interface DashboardOverview {
  portfolio_value: number;
  total_return: number;
  total_return_amount: number;
  performance_data: Array<{
    month: string;
    portfolio: number;
    benchmark: number;
    market: number;
  }>;
  allocation: PortfolioAllocation[];
  rebalancing_recommendations: Array<{
    asset: string;
    current: number;
    target: number;
    action: string;
  }>;
  recent_trades: Array<{
    date: string;
    action: string;
    asset: string;
    shares: number;
    price: number;
  }>;
}

export interface RiskMetrics {
  risk_metrics: {
    var_95: number;
    cvar_95: number;
    maximum_drawdown: number;
    beta: number;
    sharpe_ratio: number;
    sortino_ratio: number;
  };
  stress_test_scenarios: Array<{
    scenario: string;
    portfolio_loss: number;
    benchmark_loss: number;
  }>;
  monte_carlo_projections: Array<{
    percentile: string;
    value: number;
    probability: number;
  }>;
  risk_alerts: Array<{
    type: string;
    title: string;
    description: string;
    severity: string;
  }>;
}

// Streaming API interfaces
export interface StreamEvent {
  event: string;
  data: any;
  timestamp: string;
}

export interface StreamProgress {
  progress: number;
  message: string;
  [key: string]: any;
}

// Custom API Error class
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public statusText: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Generic API request function
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const config = { ...defaultOptions, ...options };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        response.statusText
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    
    // Network or other errors
    throw new APIError(
      error instanceof Error ? error.message : 'Network error occurred',
      0,
      'Network Error'
    );
  }
}

// API Client object with all endpoint methods
export const apiClient = {
  // Health and status endpoints
  async getHealth(): Promise<{ status: string; timestamp: string }> {
    return apiRequest('/health');
  },

  async getStatus(): Promise<{ message: string; status: string; version: string }> {
    return apiRequest('/');
  },

  // Assessment endpoints
  async submitAssessment(data: AssessmentData): Promise<{
    user_id: string;
    status: string;
    message: string;
    assessment_id: string;
  }> {
    return apiRequest('/api/assessment', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getAssessment(userId: string): Promise<AssessmentData> {
    return apiRequest(`/api/assessment/${userId}`);
  },

  // Portfolio endpoints
  async generatePortfolio(assessmentData: AssessmentData): Promise<PortfolioRecommendation> {
    return apiRequest('/api/portfolio/generate', {
      method: 'POST',
      body: JSON.stringify(assessmentData),
    });
  },

  // Streaming portfolio generation with real-time updates
  async generatePortfolioStream(
    assessmentData: any,
    onProgress: (event: StreamEvent) => void,
    onComplete: (finalReport: any) => void,
    onError: (error: string) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/generate-report/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(assessmentData),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep the last incomplete line

        for (const line of lines) {
          if (line.trim().startsWith('data: ')) {
            try {
              const eventData = JSON.parse(line.slice(6)); // Remove 'data: ' prefix
              const streamEvent: StreamEvent = {
                event: eventData.event,
                data: eventData.data,
                timestamp: eventData.timestamp,
              };

              onProgress(streamEvent);

              // Handle completion
              if (eventData.event === 'final_report_complete') {
                onComplete(eventData.data);
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE event:', line, parseError);
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Streaming error occurred');
    }
  },

  async getPortfolio(userId: string): Promise<PortfolioRecommendation> {
    return apiRequest(`/api/portfolio/${userId}`);
  },

  // Market data endpoints
  async getMarketOverview(): Promise<MarketOverview> {
    return apiRequest('/api/market-data/overview');
  },

  async getAssetPerformance(assetClass: string): Promise<{
    asset_class: string;
    current_price: number;
    change_24h: number;
    change_percent_24h: number;
    historical_data: Array<{
      date: string;
      price: number;
      volume: number;
    }>;
    volatility: number;
  }> {
    return apiRequest(`/api/market-data/assets/${assetClass}`);
  },

  // Risk analytics endpoints
  async getPortfolioRiskMetrics(userId: string): Promise<RiskMetrics> {
    return apiRequest(`/api/risk-analytics/portfolio/${userId}`);
  },

  async getMarketRiskConditions(): Promise<{
    volatility_regime: string;
    market_stress_level: number;
    correlation_environment: string;
    liquidity_conditions: string;
    risk_indicators: {
      vix_level: number;
      credit_spreads: number;
      currency_volatility: number;
      commodity_volatility: number;
    };
    regime_probabilities: {
      low_volatility: number;
      normal_volatility: number;
      high_volatility: number;
    };
  }> {
    return apiRequest('/api/risk-analytics/market-conditions');
  },

  // Dashboard endpoints
  async getDashboardOverview(userId: string): Promise<DashboardOverview> {
    return apiRequest(`/api/dashboard/overview/${userId}`);
  },

  async getPerformanceAnalytics(userId: string, period: string = '1y'): Promise<{
    period: string;
    total_return: number;
    annualized_return: number;
    volatility: number;
    sharpe_ratio: number;
    max_drawdown: number;
    benchmark_comparison: {
      portfolio_return: number;
      benchmark_return: number;
      alpha: number;
      beta: number;
      tracking_error: number;
    };
    attribution_analysis: Array<{
      factor: string;
      contribution: number;
    }>;
  }> {
    return apiRequest(`/api/dashboard/performance/${userId}?period=${period}`);
  },

  // Chatbot endpoints
  async sendChatMessage(userId: string, message: string, sessionId?: string): Promise<{
    status: string;
    response: {
      answer: string;
      reasoning_trace: Array<{
        step: number;
        action: string;
        result: string;
        success: boolean;
      }>;
      sources_used: Array<{
        title?: string;
        url?: string;
        snippet?: string;
        source_type?: string;
      }>;
      tools_called: string[];
      metadata: {
        user_id: string;
        session_id?: string;
        timestamp: string;
        reasoning_steps: number;
        context_retrieved: boolean;
        web_searched: boolean;
      };
    };
    timestamp: string;
  }> {
    return apiRequest('/api/chat/message', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        message: message,
        session_id: sessionId
      })
    });
  },

  async getChatHistory(userId: string, limit?: number): Promise<{
    status: string;
    user_id: string;
    conversation: Array<{
      type: string;
      content: string;
      timestamp: string;
    }>;
    total_messages: number;
    timestamp: string;
  }> {
    const url = limit 
      ? `/api/chat/history/${userId}?limit=${limit}`
      : `/api/chat/history/${userId}`;
    return apiRequest(url);
  },

  async clearChatHistory(userId: string): Promise<{
    status: string;
    message: string;
    timestamp: string;
  }> {
    return apiRequest(`/api/chat/history/${userId}`, {
      method: 'DELETE'
    });
  },

  // Report generation endpoints
  async generatePdfReport(userId: string, reportData?: any): Promise<{
    status: string;
    pdf_filename: string;
    download_url: string;
    message: string;
  }> {
    return apiRequest('/api/report/generate-pdf', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        report_data: reportData
      })
    });
  },

  async getMarkdownReport(userId: string): Promise<{
    status: string;
    user_id: string;
    markdown_content: string;
    timestamp: string;
  }> {
    return apiRequest(`/api/report/markdown/${userId}`);
  },

  async storeReportInVectorDb(userId: string, reportId: string, markdownContent: string, metadata?: any): Promise<{
    status: string;
    message: string;
    timestamp: string;
  }> {
    return apiRequest('/api/report/store-in-vector-db', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        report_id: reportId,
        markdown_content: markdownContent,
        metadata: metadata
      })
    });
  },
};

// Helper functions for error handling
export function isAPIError(error: unknown): error is APIError {
  return error instanceof APIError;
}

export function handleAPIError(error: unknown): string {
  if (isAPIError(error)) {
    if (error.status === 404) {
      return 'Data not found. Please try again.';
    } else if (error.status === 422) {
      return 'Invalid data provided. Please check your inputs.';
    } else if (error.status === 500) {
      return 'Server error. Please try again later.';
    } else if (error.status === 0) {
      return 'Unable to connect to server. Please check your connection.';
    }
    return error.message;
  }
  
  return 'An unexpected error occurred. Please try again.';
}

export default apiClient;