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
  DollarSign,
  Shield,
  BarChart3,
  LucidePieChart,
  Activity,
  AlertTriangle,
  CheckCircle,
  Settings,
  RefreshCw,
  Target,
  Home,
  GraduationCap,
  Heart,
  Plane,
  Sparkles,
  FileText,
  MessageSquare,
} from "lucide-react"
import { MarketDataWidget } from "@/components/market-data-widget"
import { InvestmentReportComponent } from "@/components/ui/investment report"
import { AINewsInsightsComponent } from "@/components/ui/ai-news-insights"
import {
  LineChart,
  AreaChart,
  Area,
  PieChart as RechartsPieChart,
  Cell,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Pie,
  Line,
} from "recharts"
import Link from "next/link"

// Goal options with consistent icons
const GOAL_OPTIONS = [
  { id: "retirement", label: "Retirement Planning", icon: Target },
  { id: "house", label: "Buy a Home", icon: Home },
  { id: "education", label: "Education Funding", icon: GraduationCap },
  { id: "wealth", label: "Wealth Growth", icon: TrendingUp },
  { id: "legacy", label: "Legacy & Estate", icon: Heart },
  { id: "travel", label: "Travel & Lifestyle", icon: Plane },
]

export default function DashboardPage() {
  const [selectedTab, setSelectedTab] = useState("overview")
  const [portfolioData, setPortfolioData] = useState<any>(null)
  const [reportData, setReportData] = useState<any>(null)
  const [fullResult, setFullResult] = useState<any>(null)
  
  // Default values
  const portfolioValue = portfolioData?.totalValue || 100000
  const changeAmount = 0
  const changePercentage = 0

  // Load portfolio data from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedPortfolio = localStorage.getItem('portfolioai_portfolio')
      const savedReport = localStorage.getItem('portfolioai_report')
      const savedFullResult = localStorage.getItem('portfolioai_full_result')
      
      if (savedPortfolio) {
        console.log('📊 Loading portfolio data...')
        setPortfolioData(JSON.parse(savedPortfolio))
      }
      
      if (savedReport) {
        console.log('📄 Loading report data...')
        setReportData(JSON.parse(savedReport))
      }
      
      if (savedFullResult) {
        console.log('🔍 Loading full result data...')
        setFullResult(JSON.parse(savedFullResult))
      }
    }
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
              <Badge className="px-3 py-1 bg-gray-100 text-gray-700">
                AI Dashboard
              </Badge>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/market-data">
                <Button variant="outline" size="sm" className="bg-transparent">
                  <Activity className="w-4 h-4 mr-2" />
                  Market Data
                </Button>
              </Link>
              <Link href="/risk-analytics">
                <Button variant="outline" size="sm" className="bg-transparent">
                  <Shield className="w-4 h-4 mr-2" />
                  Risk Analytics
                </Button>
              </Link>
              <Button variant="outline" size="sm" className="bg-transparent">
                <RefreshCw className="w-4 h-4 mr-2" />
                Sync Data
              </Button>
              <Button variant="outline" size="sm" className="bg-transparent">
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8 max-w-7xl">
        {/* AI Communication Agent Announcement Banner */}
        <div className="mb-8">
          <Card className="border-2 border-primary/20 bg-gradient-to-r from-primary/5 via-accent/5 to-primary/5 shadow-lg">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-primary to-accent rounded-full">
                    <Brain className="w-6 h-6 text-white animate-pulse" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-lg font-semibold text-foreground">🆕 AI Communication Agent Now Available!</h3>
                      <Badge className="animate-bounce bg-red-500 text-white">NEW</Badge>
                    </div>
                    <p className="text-muted-foreground">
                      Generate professional investment reports and get AI-powered explanations about your portfolio decisions
                    </p>
                  </div>
                </div>
                <Button
                  onClick={() => setSelectedTab("communication")}
                  className="bg-gradient-to-r from-primary to-accent hover:from-primary/90 hover:to-accent/90 text-white shadow-lg"
                >
                  <Brain className="w-4 h-4 mr-2" />
                  Try AI Reports
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Portfolio Summary */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Portfolio Dashboard</h1>
              <p className="text-muted-foreground">AI-optimized investment portfolio</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-foreground">${portfolioValue.toLocaleString()}</div>
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-chart-4" />
                <span className="text-chart-4 font-medium">
                  +${changeAmount.toLocaleString()} ({changePercentage.toFixed(2)}%)
                </span>
              </div>
            </div>
          </div>

          {/* Key Metrics Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <Card className="border-0 shadow-lg">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Expected Return</p>
                    <div className="flex items-center space-x-1">
                      <span className="text-2xl font-bold text-chart-4">
                        {reportData?.expected_return 
                          ? `${Number(reportData.expected_return).toFixed(2)}%` 
                          : 'N/A'}
                      </span>
                      <TrendingUp className="w-4 h-4 text-chart-4" />
                    </div>
                    <p className="text-sm text-chart-4">Annual</p>
                  </div>
                  <div className="w-12 h-12 bg-chart-4/10 rounded-lg flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-chart-4" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Risk Score</p>
                    <div className="text-2xl font-bold text-foreground">
                      {reportData?.risk_score 
                        ? `${Number(reportData.risk_score).toFixed(1)}/100` 
                        : 'N/A'}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {reportData?.risk_score 
                        ? Number(reportData.risk_score) < 40 ? 'Low Risk' 
                          : Number(reportData.risk_score) < 70 ? 'Moderate Risk' 
                          : 'High Risk'
                        : 'Unknown'}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-chart-2/10 rounded-lg flex items-center justify-center">
                    <Shield className="w-6 h-6 text-chart-2" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
                    <div className="text-2xl font-bold text-foreground">
                      {reportData?.sharpe_ratio 
                        ? Number(reportData.sharpe_ratio).toFixed(2) 
                        : 'N/A'}
                    </div>
                    <p className="text-sm text-chart-4">
                      {reportData?.sharpe_ratio 
                        ? Number(reportData.sharpe_ratio) > 2 ? 'Excellent' 
                          : Number(reportData.sharpe_ratio) > 1 ? 'Good' 
                          : 'Fair'
                        : 'Unknown'}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center">
                    <BarChart3 className="w-6 h-6 text-accent" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Volatility</p>
                    <div className="text-2xl font-bold text-foreground">
                      {reportData?.volatility 
                        ? `${Number(reportData.volatility).toFixed(1)}%` 
                        : 'N/A'}
                    </div>
                    <p className="text-sm text-muted-foreground">Annual</p>
                  </div>
                  <div className="w-12 h-12 bg-chart-5/10 rounded-lg flex items-center justify-center">
                    <Activity className="w-6 h-6 text-chart-5" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Main Dashboard Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 bg-muted/50">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="allocation">Allocation</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="communication" className="relative">
              <span className="flex items-center gap-2">
                <Brain className="w-4 h-4" />
                AI Reports
                <Badge className="text-xs px-1 py-0 h-4 bg-red-500 text-white">NEW</Badge>
              </span>
            </TabsTrigger>
            <TabsTrigger value="ai-insights">AI Insights</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* User Goals Section */}
            {fullResult?.profile?.goals && fullResult.profile.goals.length > 0 && (
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Target className="w-5 h-5 text-primary" />
                    <span>Your Investment Goals</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {fullResult.profile.goals.slice(0, 6).map((goal: any, index: number) => {
                      const goalOption = GOAL_OPTIONS.find(opt => opt.id === goal.goal_type)
                      if (!goalOption) return null
                      const Icon = goalOption.icon
                      return (
                        <div
                          key={goal.goal_type || index}
                          className="flex items-center gap-3 p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                        >
                          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                            <Icon className="w-5 h-5 text-primary" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-sm truncate">{goalOption.label}</h4>
                            <p className="text-xs text-muted-foreground">Priority #{goal.priority}</p>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="grid lg:grid-cols-3 gap-6">
              {/* Portfolio Performance Chart */}
              <Card className="lg:col-span-2 border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <TrendingUp className="w-5 h-5 text-primary" />
                    <span>Portfolio Performance</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart
                      data={[
                        { month: "Jan", portfolio: 4.2, benchmark: 3.1, market: 2.8 },
                        { month: "Feb", portfolio: 2.8, benchmark: 1.9, market: 2.1 },
                        { month: "Mar", portfolio: 6.1, benchmark: 4.3, market: 4.8 },
                        { month: "Apr", portfolio: 3.4, benchmark: 2.7, market: 3.2 },
                        { month: "May", portfolio: 5.8, benchmark: 4.1, market: 4.5 },
                        { month: "Jun", portfolio: 4.9, benchmark: 3.6, market: 3.9 },
                        { month: "Jul", portfolio: 7.2, benchmark: 5.4, market: 5.8 },
                        { month: "Aug", portfolio: 2.1, benchmark: 1.8, market: 2.3 },
                        { month: "Sep", portfolio: 4.6, benchmark: 3.2, market: 3.7 },
                        { month: "Oct", portfolio: 6.3, benchmark: 4.8, market: 5.1 },
                        { month: "Nov", portfolio: 3.9, benchmark: 2.9, market: 3.4 },
                        { month: "Dec", portfolio: 5.2, benchmark: 4.0, market: 4.3 },
                      ]}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" />
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
                        dataKey="portfolio"
                        stackId="1"
                        stroke="hsl(var(--chart-1))"
                        fill="hsl(var(--chart-1))"
                        fillOpacity={0.3}
                        name="Your Portfolio"
                      />
                      <Area
                        type="monotone"
                        dataKey="benchmark"
                        stackId="2"
                        stroke="hsl(var(--chart-2))"
                        fill="hsl(var(--chart-2))"
                        fillOpacity={0.2}
                        name="Benchmark"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Market Data Widget */}
              <MarketDataWidget />
            </div>

            {/* Asset Allocation */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <LucidePieChart className="w-5 h-5 text-primary" />
                  <span>Asset Allocation</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {portfolioData?.allocation && portfolioData.allocation.length > 0 ? (
                  <div className="grid lg:grid-cols-2 gap-6">
                    <ResponsiveContainer width="100%" height={250}>
                      <RechartsPieChart>
                        <Pie
                          data={portfolioData.allocation}
                          cx="50%"
                          cy="50%"
                          innerRadius={60} 
                          outerRadius={100}
                          paddingAngle={2}
                          dataKey="percentage"
                        >
                          {portfolioData.allocation.map((entry: any, index: number) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(value: any) => [`${value}%`, "Allocation"]}
                          contentStyle={{
                            backgroundColor: "hsl(var(--card))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "8px",
                          }}
                        />
                      </RechartsPieChart>
                    </ResponsiveContainer>
                    <div className="space-y-3">
                      {portfolioData.allocation.map((item: any) => (
                        <div key={item.name} className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                            <span className="text-sm font-medium">{item.name}</span>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-semibold">{item.percentage}%</div>
                            <div className="text-xs text-muted-foreground">
                              ${((portfolioValue * item.percentage) / 100).toLocaleString(undefined, {maximumFractionDigits: 0})}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-muted-foreground">No portfolio data available. Please generate a portfolio first.</p>
                )}
              </CardContent>
            </Card>

            {/* Risk Metrics */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Shield className="w-5 h-5 text-primary" />
                  <span>Risk Metrics</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-4 gap-6">
                  {[
                    { metric: "Value at Risk (95%)", value: "-$12,450", status: "normal" },
                    { metric: "Beta", value: "0.92", status: "good" },
                    { metric: "Correlation to S&P 500", value: "0.78", status: "normal" },
                    { metric: "Downside Deviation", value: "8.7%", status: "good" },
                  ].map((metric) => (
                    <div key={metric.metric} className="space-y-2">
                      <div className="flex items-center space-x-2">
                        {metric.status === "good" ? (
                          <CheckCircle className="w-4 h-4 text-chart-4" />
                        ) : metric.status === "risk" ? (
                          <AlertTriangle className="w-4 h-4 text-destructive" />
                        ) : (
                          <div className="w-4 h-4 rounded-full bg-chart-2" />
                        )}
                        <span className="text-sm text-muted-foreground">{metric.metric}</span>
                      </div>
                      <div className="text-xl font-bold">{metric.value}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="allocation" className="space-y-6">
            <div className="grid lg:grid-cols-2 gap-6">
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle>Asset Class Allocation</CardTitle>
                </CardHeader>
                <CardContent>
                  {reportData?.asset_class_allocations ? (
                    <div className="space-y-4">
                      {Object.entries(reportData.asset_class_allocations).map(([assetClass, percentage]: [string, any]) => {
                        const percent = typeof percentage === 'number' ? percentage * 100 : 0
                        if (percent === 0) return null
                        
                        // Format asset class name
                        const formattedName = assetClass
                          .split('_')
                          .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
                          .join(' ')
                        
                        return (
                          <div key={assetClass} className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span>{formattedName}</span>
                              <span>{percent.toFixed(1)}%</span>
                            </div>
                            <Progress value={percent} className="flex-1" />
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No allocation data available</p>
                  )}
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle>Individual Holdings</CardTitle>
                </CardHeader>
                <CardContent>
                  {reportData?.individual_holdings ? (
                    <div className="space-y-3">
                      {Object.entries(reportData.individual_holdings).map(([ticker, weight]: [string, any]) => {
                        const percentage = typeof weight === 'number' ? weight * 100 : 0
                        if (percentage === 0) return null
                        
                        const amount = (portfolioValue * percentage) / 100
                        
                        return (
                          <div key={ticker} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                            <div className="flex items-center space-x-3">
                              <div>
                                <div className="font-medium">{ticker}</div>
                                <div className="text-sm text-muted-foreground">{percentage.toFixed(2)}% allocation</div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="font-medium">${amount.toLocaleString(undefined, {maximumFractionDigits: 0})}</div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No holdings data available</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="performance" className="space-y-6">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Performance Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart
                    data={[
                      { month: "Jan", portfolio: 4.2, benchmark: 3.1, market: 2.8 },
                      { month: "Feb", portfolio: 2.8, benchmark: 1.9, market: 2.1 },
                      { month: "Mar", portfolio: 6.1, benchmark: 4.3, market: 4.8 },
                      { month: "Apr", portfolio: 3.4, benchmark: 2.7, market: 3.2 },
                      { month: "May", portfolio: 5.8, benchmark: 4.1, market: 4.5 },
                      { month: "Jun", portfolio: 4.9, benchmark: 3.6, market: 3.9 },
                      { month: "Jul", portfolio: 7.2, benchmark: 5.4, market: 5.8 },
                      { month: "Aug", portfolio: 2.1, benchmark: 1.8, market: 2.3 },
                      { month: "Sep", portfolio: 4.6, benchmark: 3.2, market: 3.7 },
                      { month: "Oct", portfolio: 6.3, benchmark: 4.8, market: 5.1 },
                      { month: "Nov", portfolio: 3.9, benchmark: 2.9, market: 3.4 },
                      { month: "Dec", portfolio: 5.2, benchmark: 4.0, market: 4.3 },
                    ]}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" />
                    <YAxis stroke="hsl(var(--muted-foreground))" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="portfolio"
                      stroke="hsl(var(--chart-1))"
                      strokeWidth={3}
                      name="Your Portfolio"
                    />
                    <Line
                      type="monotone"
                      dataKey="benchmark"
                      stroke="hsl(var(--chart-2))"
                      strokeWidth={2}
                      name="Benchmark"
                    />
                    <Line
                      type="monotone"
                      dataKey="market"
                      stroke="hsl(var(--chart-3))"
                      strokeWidth={2}
                      name="Market Average"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="communication" className="space-y-6">
            {/* Communication Agent Section with Prominent Header */}
            <div className="text-center space-y-4 mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary/20 to-accent/20 rounded-full">
                <Brain className="w-8 h-8 text-primary animate-pulse" />
              </div>
              <div>
                <h2 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                  AI Communication Agent
                </h2>
                <p className="text-muted-foreground text-lg mt-2">
                  Generate professional investment reports and get detailed explanations about your portfolio decisions
                </p>
              </div>
              <div className="flex items-center justify-center gap-2">
                <Badge className="bg-gradient-to-r from-primary to-accent text-white">
                  🤖 Powered by AI
                </Badge>
                <Badge className="border border-primary text-primary bg-transparent">
                  Professional Reports
                </Badge>
                <Badge className="border border-accent text-accent bg-transparent">
                  Q&A Available
                </Badge>
              </div>
            </div>

            {/* Investment Report Component */}
            <div className="bg-gradient-to-br from-card/50 via-background to-accent/5 p-6 rounded-lg border border-border/50 shadow-lg">
              <InvestmentReportComponent />
            </div>
          </TabsContent>

          <TabsContent value="ai-insights" className="space-y-6">
            <AINewsInsightsComponent />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
