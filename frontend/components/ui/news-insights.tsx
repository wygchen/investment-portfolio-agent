/**
 * News and Insights Component
 * 
 * This component displays daily and weekly news briefs for stocks in the user's portfolio,
 * with expandable key events and clickable news articles.
 */

"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Newspaper, 
  TrendingUp, 
  Calendar,
  Clock,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Activity,
  Globe,
  RefreshCw
} from "lucide-react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"

interface NewsArticle {
  timestamp: string
  heading: string
  source: string
  url?: string
}

interface KeyEvent {
  title: string
  description: string
  impact: "positive" | "negative" | "neutral"
  category: "earnings" | "analyst" | "regulatory" | "market" | "company"
}

interface StockBrief {
  ticker: string
  companyName: string
  keyEvent: KeyEvent
  eventSummary: string
  relatedNews: NewsArticle[]
  hotNewsSummary: string
  marketData?: {
    price: number
    change: number
    changePercent: number
  }
}

interface NewsInsightsData {
  daily: StockBrief[]
  weekly: StockBrief[]
}

// Portfolio tickers matching the dashboard holdings
const PORTFOLIO_TICKERS = [
  // Equity Holdings from dashboard
  { symbol: "VTI", name: "Vanguard Total Stock Market ETF" },
  { symbol: "MSFT", name: "Microsoft Corporation" },
  { symbol: "GOOGL", name: "Alphabet Inc Class A" },
  { symbol: "AAPL", name: "Apple Inc" },
  // Major ETF Holdings for additional news coverage
  { symbol: "BND", name: "Vanguard Total Bond Market ETF" },
  { symbol: "GLD", name: "SPDR Gold Shares ETF" }
]

export function NewsInsightsComponent() {
  const [newsData, setNewsData] = useState<NewsInsightsData>({ daily: [], weekly: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<"daily" | "weekly">("daily")
  const [expandedStocks, setExpandedStocks] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadNewsData()
  }, [])

  const loadNewsData = async () => {
    setLoading(true)
    setError(null)

    try {
      // Get portfolio tickers
      const tickers = PORTFOLIO_TICKERS.map(stock => stock.symbol)
      
      // Fetch daily and weekly briefs from backend
      const [dailyResponse, weeklyResponse] = await Promise.all([
        fetch('http://localhost:8000/api/get-portfolio-news-mock', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            tickers: tickers,
            period: 'daily'
          })
        }),
        fetch('http://localhost:8000/api/get-portfolio-news-mock', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            tickers: tickers,
            period: 'weekly'
          })
        })
      ])

      if (!dailyResponse.ok || !weeklyResponse.ok) {
        throw new Error('Failed to fetch news data')
      }

      const dailyData = await dailyResponse.json()
      const weeklyData = await weeklyResponse.json()
      
      setNewsData({
        daily: dailyData.portfolio_news || [],
        weekly: weeklyData.portfolio_news || []
      })
    } catch (err) {
      setError("Failed to load news data")
      console.error("News loading error:", err)
      
      // Fallback to mock data if API fails
      const dailyBriefs = await generateMockBriefs("daily")
      const weeklyBriefs = await generateMockBriefs("weekly")
      
      setNewsData({
        daily: dailyBriefs,
        weekly: weeklyBriefs
      })
    } finally {
      setLoading(false)
    }
  }

  const generateMockBriefs = async (period: "daily" | "weekly"): Promise<StockBrief[]> => {
    return PORTFOLIO_TICKERS.map(stock => {
      // Generate realistic mock data based on the stock
      const keyEvents: { [key: string]: KeyEvent } = {
        "MSFT": {
          title: "Microsoft Reports Strong Q4 Cloud Revenue Growth",
          description: "Azure revenue increased by 31% year-over-year, beating analyst expectations as enterprise cloud adoption continues to accelerate.",
          impact: "positive",
          category: "earnings"
        },
        "GOOGL": {
          title: "Alphabet Announces AI Infrastructure Investment",
          description: "Google parent company commits $2.3 billion to expand data center capacity for AI workloads, signaling confidence in AI market growth.",
          impact: "positive",
          category: "company"
        },
        "AAPL": {
          title: "Apple iPhone 15 Pre-Orders Exceed Expectations",
          description: "Strong consumer demand for new iPhone models with USB-C and improved camera systems drives positive analyst sentiment.",
          impact: "positive",
          category: "market"
        },
        "NVDA": {
          title: "NVIDIA Partnership with Major Cloud Providers",
          description: "New strategic partnerships announced with AWS, Azure, and Google Cloud to accelerate AI chip deployment in enterprise environments.",
          impact: "positive",
          category: "company"
        },
        "NEE": {
          title: "NextEra Energy Secures $4.2B Solar Development Deal",
          description: "Major utility-scale solar project approvals in Florida and Texas position company for continued renewable energy expansion.",
          impact: "positive",
          category: "regulatory"
        },
        "TSLA": {
          title: "Tesla Cybertruck Production Update",
          description: "Company confirms limited production ramp beginning Q4 2024, with full-scale manufacturing targeted for mid-2025.",
          impact: "neutral",
          category: "company"
        }
      }

      const mockNews: NewsArticle[] = [
        {
          timestamp: "2024-10-15T09:30:00Z",
          heading: `${stock.name} sees increased institutional buying activity`,
          source: "Reuters",
          url: "https://reuters.com"
        },
        {
          timestamp: "2024-10-15T08:15:00Z",
          heading: `Analysts raise price targets for ${stock.symbol} following strong quarter`,
          source: "Bloomberg",
          url: "https://bloomberg.com"
        },
        {
          timestamp: "2024-10-14T16:45:00Z",
          heading: `${stock.name} announces strategic partnership expansion`,
          source: "MarketWatch",
          url: "https://marketwatch.com"
        }
      ]

      return {
        ticker: stock.symbol,
        companyName: stock.name,
        keyEvent: keyEvents[stock.symbol],
        eventSummary: `Recent developments for ${stock.name} indicate continued strength in core business segments. ${keyEvents[stock.symbol].description} This positions the company favorably for upcoming quarters.`,
        relatedNews: mockNews,
        hotNewsSummary: `${stock.name} continues to demonstrate strong market performance with positive analyst sentiment and increased institutional interest. Recent ${period === "daily" ? "daily" : "weekly"} trading shows healthy volume and price stability.`,
        marketData: {
          price: Math.random() * 200 + 50,
          change: (Math.random() - 0.5) * 10,
          changePercent: (Math.random() - 0.5) * 5
        }
      }
    })
  }

  const toggleStockExpansion = (ticker: string) => {
    setExpandedStocks(prev => {
      const newSet = new Set(prev)
      if (newSet.has(ticker)) {
        newSet.delete(ticker)
      } else {
        newSet.add(ticker)
      }
      return newSet
    })
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case "positive": return "text-green-600 bg-green-50"
      case "negative": return "text-red-600 bg-red-50"
      default: return "text-blue-600 bg-blue-50"
    }
  }

  const getImpactIcon = (impact: string) => {
    switch (impact) {
      case "positive": return <TrendingUp className="w-4 h-4" />
      case "negative": return <TrendingUp className="w-4 h-4 rotate-180" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="flex items-center space-x-2">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span>Loading news and insights...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <CardContent className="pt-6">
          <div className="flex items-center space-x-2 text-red-600">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
          <Button onClick={loadNewsData} variant="outline" className="mt-4">
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
        <div className="flex items-center space-x-2">
          <Newspaper className="w-6 h-6 text-primary" />
          <h3 className="text-2xl font-semibold">Portfolio News & Insights</h3>
        </div>
        <Button onClick={loadNewsData} variant="outline" size="sm" className="flex items-center space-x-1">
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </Button>
      </div>

      {/* Period Tabs */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "daily" | "weekly")}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="daily" className="flex items-center space-x-2">
            <Calendar className="w-4 h-4" />
            <span>Daily Brief</span>
          </TabsTrigger>
          <TabsTrigger value="weekly" className="flex items-center space-x-2">
            <Activity className="w-4 h-4" />
            <span>Weekly Brief</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="daily" className="space-y-4">
          {newsData.daily.map((stock) => (
            <StockBriefCard
              key={stock.ticker}
              stock={stock}
              expanded={expandedStocks.has(stock.ticker)}
              onToggle={() => toggleStockExpansion(stock.ticker)}
              formatTimestamp={formatTimestamp}
              getImpactColor={getImpactColor}
              getImpactIcon={getImpactIcon}
            />
          ))}
        </TabsContent>

        <TabsContent value="weekly" className="space-y-4">
          {newsData.weekly.map((stock) => (
            <StockBriefCard
              key={stock.ticker}
              stock={stock}
              expanded={expandedStocks.has(`weekly-${stock.ticker}`)}
              onToggle={() => toggleStockExpansion(`weekly-${stock.ticker}`)}
              formatTimestamp={formatTimestamp}
              getImpactColor={getImpactColor}
              getImpactIcon={getImpactIcon}
            />
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}

interface StockBriefCardProps {
  stock: StockBrief
  expanded: boolean
  onToggle: () => void
  formatTimestamp: (timestamp: string) => string
  getImpactColor: (impact: string) => string
  getImpactIcon: (impact: string) => JSX.Element
}

function StockBriefCard({ 
  stock, 
  expanded, 
  onToggle, 
  formatTimestamp, 
  getImpactColor, 
  getImpactIcon 
}: StockBriefCardProps) {
  return (
    <Card className="border-l-4 border-l-primary">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Badge variant="outline" className="font-mono font-medium">
              {stock.ticker}
            </Badge>
            <h4 className="font-semibold">{stock.companyName}</h4>
            {stock.marketData && (
              <div className="flex items-center space-x-2 text-sm">
                <span className="font-medium">${stock.marketData.price.toFixed(2)}</span>
                <span className={`flex items-center ${stock.marketData.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {stock.marketData.change >= 0 ? '+' : ''}{stock.marketData.change.toFixed(2)} 
                  ({stock.marketData.changePercent.toFixed(2)}%)
                </span>
              </div>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Key Event */}
        <Collapsible>
          <CollapsibleTrigger
            onClick={onToggle}
            className="flex items-center justify-between w-full p-3 bg-muted/50 rounded-lg hover:bg-muted/80 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-full ${getImpactColor(stock.keyEvent.impact)}`}>
                {getImpactIcon(stock.keyEvent.impact)}
              </div>
              <div className="text-left">
                <h5 className="font-medium text-sm">{stock.keyEvent.title}</h5>
                <Badge variant="secondary" className="mt-1 text-xs">
                  {stock.keyEvent.category}
                </Badge>
              </div>
            </div>
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </CollapsibleTrigger>

          <CollapsibleContent className="pt-4">
            <div className="space-y-4 pl-4 border-l-2 border-muted">
              {/* Event Summary */}
              <div className="space-y-2">
                <h6 className="font-medium text-sm flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4" />
                  <span>Event Summary</span>
                </h6>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {stock.eventSummary}
                </p>
              </div>

              {/* Related News */}
              <div className="space-y-2">
                <h6 className="font-medium text-sm flex items-center space-x-2">
                  <Newspaper className="w-4 h-4" />
                  <span>Related News</span>
                </h6>
                <div className="space-y-2">
                  {stock.relatedNews.map((article, index) => (
                    <div 
                      key={index} 
                      className="flex items-start justify-between p-3 bg-background rounded border hover:border-primary/50 transition-colors"
                    >
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground leading-snug">
                          {article.heading}
                        </p>
                        <div className="flex items-center space-x-2 mt-2 text-xs text-muted-foreground">
                          <span>{article.source}</span>
                          <span>•</span>
                          <span className="flex items-center space-x-1">
                            <Clock className="w-3 h-3" />
                            <span>{formatTimestamp(article.timestamp)}</span>
                          </span>
                        </div>
                      </div>
                      {article.url && (
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="ml-3 h-8 w-8 p-0"
                          onClick={() => window.open(article.url, '_blank')}
                        >
                          <ExternalLink className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Hot News Summary */}
              <div className="space-y-2">
                <h6 className="font-medium text-sm flex items-center space-x-2">
                  <Globe className="w-4 h-4" />
                  <span>Market Sentiment</span>
                </h6>
                <div className="p-3 bg-primary/5 rounded-lg border border-primary/20">
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {stock.hotNewsSummary}
                  </p>
                </div>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  )
}