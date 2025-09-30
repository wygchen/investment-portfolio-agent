"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Activity,
  Globe,
  Satellite,
  MessageSquare,
  BarChart3,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
} from "lucide-react"
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart as RechartsBarChart,
  Bar,
} from "recharts"

// Mock real-time market data
const marketData = {
  indices: [
    { name: "S&P 500", value: 4756.5, change: 23.45, changePercent: 0.49, trend: "up" },
    { name: "NASDAQ", value: 14845.73, change: -12.34, changePercent: -0.08, trend: "down" },
    { name: "DOW", value: 37689.54, change: 156.78, changePercent: 0.42, trend: "up" },
    { name: "VIX", value: 13.45, change: -0.67, changePercent: -4.75, trend: "down" },
  ],
  sectors: [
    { name: "Technology", performance: 2.3, sentiment: 0.75, volume: "High" },
    { name: "Healthcare", performance: 1.8, sentiment: 0.62, volume: "Medium" },
    { name: "Financial", performance: -0.5, sentiment: 0.45, volume: "High" },
    { name: "Energy", performance: 3.2, sentiment: 0.82, volume: "Medium" },
    { name: "Consumer", performance: 1.1, sentiment: 0.58, volume: "Low" },
  ],
  alternativeData: [
    { source: "Social Sentiment", signal: "Bullish", confidence: 87, impact: "Medium" },
    { source: "Satellite Imagery", signal: "Economic Growth", confidence: 92, impact: "High" },
    { source: "Credit Card Spending", signal: "Consumer Strength", confidence: 78, impact: "Medium" },
    { source: "Supply Chain Data", signal: "Improving", confidence: 84, impact: "Low" },
  ],
}

const sentimentData = [
  { time: "9:00", bullish: 65, bearish: 35, neutral: 45 },
  { time: "10:00", bullish: 68, bearish: 32, neutral: 42 },
  { time: "11:00", bullish: 72, bearish: 28, neutral: 38 },
  { time: "12:00", bullish: 69, bearish: 31, neutral: 41 },
  { time: "13:00", bullish: 74, bearish: 26, neutral: 35 },
  { time: "14:00", bullish: 71, bearish: 29, neutral: 39 },
  { time: "15:00", bullish: 76, bearish: 24, neutral: 32 },
]

const volatilityData = [
  { asset: "US Equities", current: 12.3, historical: 15.2, percentile: 25 },
  { asset: "Int'l Equities", current: 14.8, historical: 17.1, percentile: 35 },
  { asset: "Bonds", current: 4.2, historical: 6.8, percentile: 15 },
  { asset: "REITs", current: 18.5, historical: 22.3, percentile: 40 },
  { asset: "Commodities", current: 22.1, historical: 28.4, percentile: 45 },
]

export default function MarketDataPage() {
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [isLive, setIsLive] = useState(true)

  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdate(new Date())
    }, 5000) // Update every 5 seconds

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <Brain className="w-5 h-5 text-primary-foreground" />
                </div>
                <span className="text-xl font-semibold text-foreground">PortfolioAI</span>
              </div>
              <Badge variant="secondary" className="px-3 py-1">
                <Activity className="w-4 h-4 mr-1" />
                Market Intelligence
              </Badge>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div
                  className={`w-2 h-2 rounded-full ${isLive ? "bg-chart-4 animate-pulse" : "bg-muted-foreground"}`}
                />
                <span className="text-sm text-muted-foreground">Last update: {lastUpdate.toLocaleTimeString()}</span>
              </div>
              <Button variant="outline" size="sm" className="bg-transparent">
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8 max-w-7xl">
        {/* Market Overview */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Real-time Market Intelligence</h1>
              <p className="text-muted-foreground">AI-powered market analysis and alternative data integration</p>
            </div>
          </div>

          {/* Market Indices */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {marketData.indices.map((index) => (
              <Card key={index.name} className="border-0 shadow-lg">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-muted-foreground">{index.name}</span>
                    {index.trend === "up" ? (
                      <TrendingUp className="w-4 h-4 text-chart-4" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-destructive" />
                    )}
                  </div>
                  <div className="text-2xl font-bold">{index.value.toLocaleString()}</div>
                  <div className={`text-sm ${index.trend === "up" ? "text-chart-4" : "text-destructive"}`}>
                    {index.change > 0 ? "+" : ""}
                    {index.change} ({index.changePercent > 0 ? "+" : ""}
                    {index.changePercent}%)
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Main Data Tabs */}
        <Tabs defaultValue="sentiment" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 bg-muted/50">
            <TabsTrigger value="sentiment">Market Sentiment</TabsTrigger>
            <TabsTrigger value="alternative">Alternative Data</TabsTrigger>
            <TabsTrigger value="sectors">Sector Analysis</TabsTrigger>
            <TabsTrigger value="volatility">Risk Metrics</TabsTrigger>
          </TabsList>

          <TabsContent value="sentiment" className="space-y-6">
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Sentiment Chart */}
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <MessageSquare className="w-5 h-5 text-primary" />
                    <span>Real-time Sentiment Analysis</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={sentimentData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" />
                      <YAxis stroke="hsl(var(--muted-foreground))" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "hsl(var(--card))",
                          border: "1px solid hsl(var(--border))",
                          borderRadius: "8px",
                        }}
                      />
                      <Legend />
                      <Area
                        type="monotone"
                        dataKey="bullish"
                        stackId="1"
                        stroke="hsl(var(--chart-4))"
                        fill="hsl(var(--chart-4))"
                        fillOpacity={0.6}
                        name="Bullish"
                      />
                      <Area
                        type="monotone"
                        dataKey="bearish"
                        stackId="1"
                        stroke="hsl(var(--destructive))"
                        fill="hsl(var(--destructive))"
                        fillOpacity={0.6}
                        name="Bearish"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Sentiment Sources */}
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle>Sentiment Data Sources</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 rounded-lg bg-muted/30">
                      <div className="flex items-center space-x-3">
                        <MessageSquare className="w-5 h-5 text-chart-2" />
                        <div>
                          <div className="font-medium">Social Media</div>
                          <div className="text-sm text-muted-foreground">Twitter, Reddit, Discord</div>
                        </div>
                      </div>
                      <Badge variant="secondary">76% Bullish</Badge>
                    </div>

                    <div className="flex items-center justify-between p-4 rounded-lg bg-muted/30">
                      <div className="flex items-center space-x-3">
                        <Globe className="w-5 h-5 text-chart-3" />
                        <div>
                          <div className="font-medium">News Analysis</div>
                          <div className="text-sm text-muted-foreground">Financial news, earnings calls</div>
                        </div>
                      </div>
                      <Badge variant="secondary">68% Positive</Badge>
                    </div>

                    <div className="flex items-center justify-between p-4 rounded-lg bg-muted/30">
                      <div className="flex items-center space-x-3">
                        <BarChart3 className="w-5 h-5 text-accent" />
                        <div>
                          <div className="font-medium">Options Flow</div>
                          <div className="text-sm text-muted-foreground">Put/call ratios, unusual activity</div>
                        </div>
                      </div>
                      <Badge variant="secondary">Neutral</Badge>
                    </div>

                    <div className="flex items-center justify-between p-4 rounded-lg bg-muted/30">
                      <div className="flex items-center space-x-3">
                        <Activity className="w-5 h-5 text-chart-5" />
                        <div>
                          <div className="font-medium">Insider Trading</div>
                          <div className="text-sm text-muted-foreground">Corporate insider activity</div>
                        </div>
                      </div>
                      <Badge variant="secondary">Slightly Bullish</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="alternative" className="space-y-6">
            <div className="grid gap-6">
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Satellite className="w-5 h-5 text-primary" />
                    <span>Alternative Data Signals</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-6">
                    {marketData.alternativeData.map((data, index) => (
                      <div key={index} className="space-y-4 p-6 rounded-lg bg-muted/30">
                        <div className="flex items-center justify-between">
                          <h3 className="font-semibold">{data.source}</h3>
                          <Badge
                            variant={
                              data.impact === "High"
                                ? "destructive"
                                : data.impact === "Medium"
                                  ? "default"
                                  : "secondary"
                            }
                          >
                            {data.impact} Impact
                          </Badge>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="flex-1">
                            <div className="text-lg font-medium text-chart-4">{data.signal}</div>
                            <div className="text-sm text-muted-foreground">Confidence: {data.confidence}%</div>
                          </div>
                          <div className="w-16 h-16 rounded-full bg-chart-4/10 flex items-center justify-center">
                            <CheckCircle className="w-8 h-8 text-chart-4" />
                          </div>
                        </div>
                        <Progress value={data.confidence} className="h-2" />
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Alternative Data Explanation */}
              <Card className="border-0 shadow-lg bg-gradient-to-r from-accent/5 to-accent/10">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Brain className="w-5 h-5 text-accent" />
                    <span>How We Use Alternative Data</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid md:grid-cols-3 gap-6">
                    <div>
                      <h4 className="font-semibold mb-2">Satellite Imagery</h4>
                      <p className="text-sm text-muted-foreground">
                        Monitor economic activity through parking lots, shipping ports, and construction sites to
                        predict earnings before official reports.
                      </p>
                    </div>
                    <div>
                      <h4 className="font-semibold mb-2">Credit Card Data</h4>
                      <p className="text-sm text-muted-foreground">
                        Track consumer spending patterns in real-time to identify sector trends and economic shifts
                        ahead of traditional indicators.
                      </p>
                    </div>
                    <div>
                      <h4 className="font-semibold mb-2">Supply Chain Analytics</h4>
                      <p className="text-sm text-muted-foreground">
                        Analyze shipping data, inventory levels, and logistics patterns to predict supply chain
                        disruptions and opportunities.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="sectors" className="space-y-6">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Sector Performance & Sentiment</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {marketData.sectors.map((sector, index) => (
                    <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-muted/30">
                      <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                          <BarChart3 className="w-6 h-6 text-primary" />
                        </div>
                        <div>
                          <div className="font-medium">{sector.name}</div>
                          <div className="text-sm text-muted-foreground">Volume: {sector.volume}</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-6">
                        <div className="text-right">
                          <div
                            className={`text-lg font-bold ${sector.performance >= 0 ? "text-chart-4" : "text-destructive"}`}
                          >
                            {sector.performance >= 0 ? "+" : ""}
                            {sector.performance}%
                          </div>
                          <div className="text-sm text-muted-foreground">Performance</div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold">{Math.round(sector.sentiment * 100)}%</div>
                          <div className="text-sm text-muted-foreground">Sentiment</div>
                        </div>
                        <Progress value={sector.sentiment * 100} className="w-20 h-2" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="volatility" className="space-y-6">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="w-5 h-5 text-primary" />
                  <span>Volatility Analysis</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <RechartsBarChart data={volatilityData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="asset" stroke="hsl(var(--muted-foreground))" />
                    <YAxis stroke="hsl(var(--muted-foreground))" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Legend />
                    <Bar dataKey="current" fill="hsl(var(--chart-1))" name="Current Volatility" />
                    <Bar dataKey="historical" fill="hsl(var(--chart-2))" name="Historical Average" />
                  </RechartsBarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <div className="grid md:grid-cols-3 gap-6">
              <Card className="border-0 shadow-lg">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 bg-chart-4/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <TrendingDown className="w-6 h-6 text-chart-4" />
                  </div>
                  <div className="text-2xl font-bold text-chart-4">Low</div>
                  <div className="text-sm text-muted-foreground">Overall Market Volatility</div>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <AlertTriangle className="w-6 h-6 text-accent" />
                  </div>
                  <div className="text-2xl font-bold">13.2</div>
                  <div className="text-sm text-muted-foreground">VIX Level</div>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 bg-chart-2/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <CheckCircle className="w-6 h-6 text-chart-2" />
                  </div>
                  <div className="text-2xl font-bold">Stable</div>
                  <div className="text-sm text-muted-foreground">Market Regime</div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
