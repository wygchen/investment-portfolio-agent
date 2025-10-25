/**
 * AI News Insights Component
 * 
 * Displays stock cards with price data, news articles, and market summaries
 * for each stock in the portfolio using Finnhub news data and WatsonX AI analysis
 */

"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  TrendingUp,
  TrendingDown,
  ExternalLink,
  RefreshCw,
  DollarSign,
  Newspaper,
  BarChart3
} from "lucide-react"

interface NewsArticle {
  title: string
  summary: string
  publisher: string
  published_date: string
  url: string
  source: string
}

interface StockInsight {
  symbol: string
  priceData: {
    price: number
    change: number
    changePercent: number
  }
  newsArticles: NewsArticle[]
  newsUrls: string[]
  marketSummary: string
  timestamp: string
}

export function AINewsInsightsComponent() {
  const [insights, setInsights] = useState<StockInsight[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [portfolioStocks, setPortfolioStocks] = useState<Array<{symbol: string, name: string}>>([])
  
  // Load actual portfolio tickers from localStorage on mount
  useEffect(() => {
    try {
      const savedPortfolio = localStorage.getItem('portfolioai_portfolio')
      if (savedPortfolio) {
        const portfolio = JSON.parse(savedPortfolio)
        const stocks: Array<{symbol: string, name: string}> = []
        
        // Extract tickers from portfolio allocation array
        if (portfolio.allocation && Array.isArray(portfolio.allocation)) {
          portfolio.allocation.forEach((holding: any) => {
            if (holding.symbol) {
              stocks.push({
                symbol: holding.symbol,
                name: holding.name || holding.symbol
              })
            }
          })
        }
        
        console.log('📊 Loaded portfolio stocks from localStorage:', stocks)
        setPortfolioStocks(stocks)
      } else {
        console.log('⚠️ No portfolio found in localStorage, using empty list')
        setPortfolioStocks([])
      }
    } catch (e) {
      console.error('❌ Error loading portfolio:', e)
      setPortfolioStocks([])
    }
  }, [])

  // Test function to load comprehensive mock data
  const loadTestData = () => {
    console.log("🧪 Loading comprehensive test data...")
    const testData: StockInsight[] = [
      {
        symbol: "VTI",
        priceData: { price: 284.75, change: 2.15, changePercent: 0.76 },
        newsArticles: [
          {
            title: "Vanguard Total Stock Market ETF Sees Record Inflows",
            summary: "VTI attracted $2.3 billion in new investments as investors seek broad market exposure amid economic uncertainty.",
            publisher: "MarketWatch",
            published_date: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            url: "https://marketwatch.com/vti-record-inflows",
            source: "finnhub"
          },
          {
            title: "Broad Market ETFs Outperform Active Funds in 2024",
            summary: "Total market index funds like VTI continue to demonstrate superior risk-adjusted returns compared to actively managed alternatives.",
            publisher: "Financial Times",
            published_date: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
            url: "https://ft.com/etf-performance-2024",
            source: "finnhub"
          }
        ],
        newsUrls: ["https://marketwatch.com/vti-record-inflows", "https://ft.com/etf-performance-2024"],
        marketSummary: "VTI shows strong institutional confidence with record inflows. Maintain long-term position for diversified market exposure.",
        timestamp: new Date().toISOString()
      },
      {
        symbol: "MSFT",
        priceData: { price: 428.90, change: -3.25, changePercent: -0.75 },
        newsArticles: [
          {
            title: "Microsoft Azure Revenue Grows 29% in Latest Quarter",
            summary: "Cloud computing division continues robust growth despite economic headwinds, with AI services driving new customer acquisitions.",
            publisher: "Bloomberg",
            published_date: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
            url: "https://bloomberg.com/msft-azure-growth",
            source: "finnhub"
          },
          {
            title: "Microsoft Announces Major AI Partnership with OpenAI",
            summary: "Strategic expansion of AI capabilities across Office 365 and Azure platforms expected to drive significant revenue growth.",
            publisher: "TechCrunch",
            published_date: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
            url: "https://techcrunch.com/msft-openai-partnership",
            source: "finnhub"
          },
          {
            title: "Enterprise Software Demand Remains Strong for Microsoft",
            summary: "Corporate customers continue digital transformation initiatives, benefiting Microsoft's productivity and cloud offerings.",
            publisher: "Wall Street Journal",
            published_date: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
            url: "https://wsj.com/msft-enterprise-demand",
            source: "finnhub"
          }
        ],
        newsUrls: ["https://bloomberg.com/msft-azure-growth", "https://techcrunch.com/msft-openai-partnership", "https://wsj.com/msft-enterprise-demand"],
        marketSummary: "Microsoft demonstrates strong AI leadership and cloud growth. Minor pullback presents attractive buying opportunity for long-term investors.",
        timestamp: new Date().toISOString()
      },
      {
        symbol: "GOOGL",
        priceData: { price: 175.32, change: 4.87, changePercent: 2.86 },
        newsArticles: [
          {
            title: "Google's Gemini AI Shows Superior Performance in Latest Tests",
            summary: "Alphabet's advanced AI model outperforms competitors in reasoning and multimodal tasks, strengthening position in AI race.",
            publisher: "Reuters",
            published_date: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
            url: "https://reuters.com/googl-gemini-performance",
            source: "finnhub"
          },
          {
            title: "YouTube Ad Revenue Exceeds Expectations Despite Economic Concerns",
            summary: "Strong advertiser demand and improved targeting capabilities drive 12% year-over-year growth in YouTube advertising revenue.",
            publisher: "CNBC",
            published_date: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
            url: "https://cnbc.com/youtube-ad-revenue-growth",
            source: "finnhub"
          }
        ],
        newsUrls: ["https://reuters.com/googl-gemini-performance", "https://cnbc.com/youtube-ad-revenue-growth"],
        marketSummary: "Google's AI advancements and strong YouTube performance signal robust growth trajectory. Consider increasing position on positive momentum.",
        timestamp: new Date().toISOString()
      },
      {
        symbol: "AAPL",
        priceData: { price: 251.42, change: 1.60, changePercent: 0.64 },
        newsArticles: [
          {
            title: "Apple iPhone 16 Sales Exceed Analyst Expectations",
            summary: "Strong consumer demand for new AI-powered features drives higher than anticipated iPhone 16 sales in key markets.",
            publisher: "Apple Insider",
            published_date: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
            url: "https://appleinsider.com/iphone16-sales-strong",
            source: "finnhub"
          },
          {
            title: "Apple Services Revenue Hits New Record High",
            summary: "App Store, iCloud, and subscription services generate $24.2 billion in quarterly revenue, up 16% year-over-year.",
            publisher: "9to5Mac",
            published_date: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            url: "https://9to5mac.com/apple-services-record",
            source: "finnhub"
          },
          {
            title: "Apple Expands Manufacturing in India and Vietnam",
            summary: "Supply chain diversification strategy reduces China dependency while maintaining production quality and cost efficiency.",
            publisher: "Nikkei Asia",
            published_date: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
            url: "https://nikkei.com/apple-manufacturing-expansion",
            source: "finnhub"
          }
        ],
        newsUrls: ["https://appleinsider.com/iphone16-sales-strong", "https://9to5mac.com/apple-services-record", "https://nikkei.com/apple-manufacturing-expansion"],
        marketSummary: "Apple shows strong product demand and services growth. Supply chain diversification reduces risks. Maintain strong buy rating.",
        timestamp: new Date().toISOString()
      },
      {
        symbol: "BND",
        priceData: { price: 72.85, change: -0.12, changePercent: -0.16 },
        newsArticles: [
          {
            title: "Bond ETFs See Increased Demand Amid Market Volatility",
            summary: "Investors rotate into fixed income securities as hedge against equity market uncertainty and inflation concerns.",
            publisher: "Bond Buyer",
            published_date: new Date(Date.now() - 1.5 * 60 * 60 * 1000).toISOString(),
            url: "https://bondbuyer.com/etf-demand-volatility",
            source: "finnhub"
          },
          {
            title: "Federal Reserve Signals Potential Rate Cuts in 2024",
            summary: "Fed officials indicate possible monetary policy easing could benefit long-term bond performance and ETF valuations.",
            publisher: "Federal Reserve News",
            published_date: new Date(Date.now() - 7 * 60 * 60 * 1000).toISOString(),
            url: "https://federalreserve.gov/rate-cut-signals",
            source: "finnhub"
          }
        ],
        newsUrls: ["https://bondbuyer.com/etf-demand-volatility", "https://federalreserve.gov/rate-cut-signals"],
        marketSummary: "Bond market positioning for potential rate cuts. BND provides stable income and portfolio diversification. Hold current allocation.",
        timestamp: new Date().toISOString()
      },
      {
        symbol: "GLD",
        priceData: { price: 234.67, change: 5.23, changePercent: 2.28 },
        newsArticles: [
          {
            title: "Gold Prices Surge on Geopolitical Tensions and Inflation Fears",
            summary: "Precious metals rally as investors seek safe-haven assets amid global economic uncertainty and currency debasement concerns.",
            publisher: "Kitco News",
            published_date: new Date(Date.now() - 20 * 60 * 1000).toISOString(),
            url: "https://kitco.com/gold-surge-geopolitical",
            source: "finnhub"
          },
          {
            title: "Central Banks Continue Gold Accumulation in Q4",
            summary: "Global central banks add 387 tons of gold reserves, supporting long-term price stability and ETF demand.",
            publisher: "Gold Mining News",
            published_date: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
            url: "https://goldminingnews.com/central-bank-buying",
            source: "finnhub"
          }
        ],
        newsUrls: ["https://kitco.com/gold-surge-geopolitical", "https://goldminingnews.com/central-bank-buying"],
        marketSummary: "Gold strengthens on safe-haven demand and central bank buying. GLD provides effective portfolio hedge. Consider maintaining position.",
        timestamp: new Date().toISOString()
      }
    ]
    setInsights(testData)
    console.log("✅ Comprehensive test data loaded:", testData)
  }

  const loadInsights = async () => {
    setLoading(true)
    setError(null)

    try {
      console.log("🚀 Loading AI news insights...")
      console.log("📊 Portfolio stocks:", portfolioStocks)
      
      if (portfolioStocks.length === 0) {
        setError("No portfolio stocks found. Please generate a portfolio first.")
        return
      }

      const insightPromises = portfolioStocks.map(async (stock: {symbol: string, name: string}) => {
        try {
          console.log(`🔄 Analyzing ${stock.symbol}...`)

          const response = await fetch('http://127.0.0.1:8000/api/news-insights', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              symbol: stock.symbol
            })
          })

          console.log(`📡 Response status for ${stock.symbol}:`, response.status)

          if (!response.ok) {
            const errorText = await response.text()
            console.error(`❌ Response error for ${stock.symbol}:`, errorText)
            throw new Error(`Failed to get insights for ${stock.symbol}: ${response.status}`)
          }

          const result = await response.json()
          console.log(`✅ ${stock.symbol} insights loaded:`, result)

          return result.data
        } catch (error) {
          console.error(`❌ Error loading ${stock.symbol}:`, error)
          // Return fallback data
          return {
            symbol: stock.symbol,
            priceData: { price: 0, change: 0, changePercent: 0 },
            newsArticles: [],
            newsUrls: [],
            marketSummary: `Analysis unavailable for ${stock.symbol}`,
            timestamp: new Date().toISOString()
          }
        }
      })

      const results = await Promise.all(insightPromises)
      console.log("✅ All insights loaded:", results)
      console.log("📈 Setting insights state with", results.length, "items")

      setInsights(results)
    } catch (err) {
      setError("Failed to load AI news insights")
      console.error("❌ Insights error:", err)
    } finally {
      setLoading(false)
    }
  }

  const getPriceChangeColor = (change: number) => {
    if (change > 0) return "text-green-600"
    if (change < 0) return "text-red-600"
    return "text-gray-600"
  }

  const getPriceChangeIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="w-4 h-4" />
    if (change < 0) return <TrendingDown className="w-4 h-4" />
    return <BarChart3 className="w-4 h-4" />
  }

  const getStockName = (symbol: string) => {
    return portfolioStocks.find((stock: {symbol: string, name: string}) => stock.symbol === symbol)?.name || `${symbol} Inc`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="flex items-center space-x-2">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span>Loading AI news insights...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <CardContent className="pt-6">
          <div className="flex items-center space-x-2 text-red-600">
            <BarChart3 className="w-5 h-5" />
            <span>{error}</span>
          </div>
          <Button onClick={loadInsights} variant="outline" className="mt-4">
            Try Again
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-br from-primary/10 to-blue-100 rounded-lg">
            <Newspaper className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h3 className="text-2xl font-semibold bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
              AI News & Insights
            </h3>
            <p className="text-sm text-gray-600">
              Real-time news from Finnhub • AI analysis by WatsonX • Live prices from Yahoo Finance
            </p>
          </div>
        </div>
        <div className="flex space-x-2">
          <Button onClick={loadTestData} variant="secondary" size="sm">
            🧪 Test Data
          </Button>
          <Button onClick={loadInsights} variant="outline" size="sm" disabled={loading}>
            <RefreshCw className="w-4 h-4 mr-2" />
            {insights.length > 0 ? 'Refresh' : 'Load Insights'}
          </Button>
        </div>
      </div>

      {/* Stock Cards */}
      <div className="space-y-4">
        {insights.length > 0 ? (
          insights.map((stock) => (
            <Card key={stock.symbol} className="border-l-4 border-l-primary">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  {/* Ticker Symbol - Top Left */}
                  <div className="flex items-center space-x-3">
                    <Badge variant="outline" className="font-mono font-bold text-lg px-3 py-1">
                      {stock.symbol}
                    </Badge>
                    <span className="text-sm text-gray-600">{getStockName(stock.symbol)}</span>
                  </div>
                  
                  {/* Price Data - Top Right */}
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-1">
                      <DollarSign className="w-4 h-4 text-gray-500" />
                      <span className="font-bold text-xl">${stock.priceData.price.toFixed(2)}</span>
                    </div>
                    <div className={`flex items-center space-x-1 ${getPriceChangeColor(stock.priceData.change)}`}>
                      {getPriceChangeIcon(stock.priceData.change)}
                      <span className="font-medium">
                        {stock.priceData.change >= 0 ? '+' : ''}{stock.priceData.changePercent.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* News Articles Card */}
                <Card className="bg-gray-50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center space-x-2">
                      <Newspaper className="w-4 h-4" />
                      <span>Recent News</span>
                      <Badge className="text-xs">{stock.newsArticles.length} articles</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {stock.newsArticles.length > 0 ? (
                      stock.newsArticles.map((article, index) => (
                        <div key={index} className="p-3 bg-white rounded-lg border border-gray-200 hover:border-primary/50 hover:shadow-sm transition-all">
                          <div className="space-y-2">
                            {/* Clickable News Title */}
                            <a 
                              href={article.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="block text-sm font-semibold text-primary hover:text-primary/80 hover:underline cursor-pointer leading-tight"
                            >
                              {article.title}
                              <ExternalLink className="inline w-3 h-3 ml-1 mb-1" />
                            </a>
                            
                            {/* Article Summary */}
                            {article.summary && (
                              <p className="text-xs text-gray-600 leading-relaxed line-clamp-2">
                                {article.summary}
                              </p>
                            )}
                            
                            {/* Article Metadata */}
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2 text-xs text-gray-500">
                                <span className="font-medium">{article.publisher}</span>
                                <span>•</span>
                                <span>{new Date(article.published_date).toLocaleDateString()}</span>
                              </div>
                              <Badge className="text-xs px-2 py-0.5 bg-green-100 text-green-700">
                                Finnhub
                              </Badge>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-6">
                        <Newspaper className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-500">No recent news available</p>
                        <p className="text-xs text-gray-400 mt-1">Check back later for updates</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Market Summary */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="font-medium text-sm flex items-center space-x-2">
                      <BarChart3 className="w-4 h-4 text-blue-600" />
                      <span>AI Market Analysis</span>
                      <Badge className="text-xs bg-blue-100 text-blue-700">WatsonX AI</Badge>
                    </h5>
                    <span className="text-xs text-gray-500">
                      {new Date(stock.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                    <p className="text-sm text-gray-800 leading-relaxed font-medium">
                      {stock.marketSummary}
                    </p>
                    
                    {/* News URLs Summary */}
                    {stock.newsUrls.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-blue-200">
                        <p className="text-xs text-blue-600 mb-2">
                          Analysis based on {stock.newsUrls.length} news source{stock.newsUrls.length !== 1 ? 's' : ''}
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {stock.newsUrls.slice(0, 3).map((url, index) => (
                            <a
                              key={index}
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                            >
                              Source {index + 1}
                              <ExternalLink className="inline w-2 h-2 ml-1" />
                            </a>
                          ))}
                          {stock.newsUrls.length > 3 && (
                            <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                              +{stock.newsUrls.length - 3} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="pt-6">
              <div className="text-center">
                <Newspaper className="w-12 h-12 text-blue-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-blue-800 mb-2">
                  Ready for AI News Analysis
                </h3>
                <p className="text-blue-700 mb-4">
                  Click below to load news insights and market analysis for your portfolio stocks
                </p>
                <Button onClick={loadInsights} className="bg-blue-600 hover:bg-blue-700 text-white">
                  <Newspaper className="w-4 h-4 mr-2" />
                  Load News Insights
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}