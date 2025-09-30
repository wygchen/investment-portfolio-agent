"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import {
  Brain,
  Shield,
  AlertTriangle,
  TrendingDown,
  Activity,
  BarChart3,
  Target,
  Zap,
  CheckCircle,
  XCircle,
  RefreshCw,
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
  ScatterChart,
  Scatter,
} from "recharts"

// Mock risk analytics data
const stressTestScenarios = [
  {
    scenario: "2008 Financial Crisis",
    portfolioLoss: -32.4,
    marketLoss: -37.8,
    duration: "18 months",
    recovery: "24 months",
    status: "outperformed",
  },
  {
    scenario: "COVID-19 Pandemic",
    portfolioLoss: -18.2,
    marketLoss: -34.0,
    duration: "3 months",
    recovery: "8 months",
    status: "outperformed",
  },
  {
    scenario: "Dot-com Bubble",
    portfolioLoss: -28.7,
    marketLoss: -49.1,
    duration: "30 months",
    recovery: "36 months",
    status: "outperformed",
  },
  {
    scenario: "Inflation Spike (1970s)",
    portfolioLoss: -15.3,
    marketLoss: -22.8,
    duration: "12 months",
    recovery: "18 months",
    status: "outperformed",
  },
]

const riskMetrics = [
  { metric: "Value at Risk (95%)", current: -12450, threshold: -15000, status: "good" },
  { metric: "Expected Shortfall", current: -18200, threshold: -22000, status: "good" },
  { metric: "Maximum Drawdown", current: -8.2, threshold: -12.0, status: "good" },
  { metric: "Beta", current: 0.92, threshold: 1.2, status: "good" },
  { metric: "Volatility", current: 12.3, threshold: 18.0, status: "good" },
  { metric: "Sharpe Ratio", current: 1.42, threshold: 1.0, status: "excellent" },
]

const correlationData = [
  { asset1: "US Equities", asset2: "Int'l Equities", correlation: 0.78, risk: "medium" },
  { asset1: "US Equities", asset2: "Bonds", correlation: -0.12, risk: "low" },
  { asset1: "US Equities", asset2: "REITs", correlation: 0.65, risk: "medium" },
  { asset1: "US Equities", asset2: "Commodities", correlation: 0.23, risk: "low" },
  { asset1: "Bonds", asset2: "REITs", correlation: 0.15, risk: "low" },
  { asset1: "Bonds", asset2: "Commodities", correlation: -0.08, risk: "low" },
]

const monteCarloResults = [
  { percentile: "5th", value: 285000, probability: 5 },
  { percentile: "25th", value: 420000, probability: 25 },
  { percentile: "50th", value: 580000, probability: 50 },
  { percentile: "75th", value: 780000, probability: 75 },
  { percentile: "95th", value: 1200000, probability: 95 },
]

const riskAlerts = [
  {
    type: "warning",
    title: "Increased Correlation Risk",
    description: "US and International equity correlation has increased to 0.85 during recent market stress.",
    severity: "Medium",
    recommendation: "Consider adding uncorrelated assets like commodities or alternative investments.",
  },
  {
    type: "info",
    title: "Volatility Regime Change",
    description: "AI detected potential shift to higher volatility environment based on options pricing.",
    severity: "Low",
    recommendation: "Monitor position sizing and consider defensive positioning.",
  },
  {
    type: "success",
    title: "Risk Budget Optimization",
    description: "Current portfolio is efficiently using 87% of available risk budget with optimal diversification.",
    severity: "Good",
    recommendation: "Maintain current allocation strategy.",
  },
]

export default function RiskAnalyticsPage() {
  const [selectedTab, setSelectedTab] = useState("overview")

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
                <Shield className="w-4 h-4 mr-1" />
                Risk Analytics
              </Badge>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="outline" size="sm" className="bg-transparent">
                <RefreshCw className="w-4 h-4 mr-2" />
                Run Analysis
              </Button>
              <Button variant="outline" size="sm" className="bg-transparent">
                Export Report
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8 max-w-7xl">
        {/* Risk Overview */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Risk Management & Analytics</h1>
              <p className="text-muted-foreground">AI-powered risk assessment and portfolio stress testing</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-chart-4">Low Risk</div>
              <div className="text-sm text-muted-foreground">Overall Portfolio Risk Level</div>
            </div>
          </div>

          {/* Risk Alerts */}
          <div className="grid gap-4 mb-8">
            {riskAlerts.map((alert, index) => (
              <Card
                key={index}
                className={`border-0 shadow-lg ${
                  alert.type === "warning"
                    ? "bg-destructive/5 border-destructive/20"
                    : alert.type === "info"
                      ? "bg-chart-2/5 border-chart-2/20"
                      : "bg-chart-4/5 border-chart-4/20"
                }`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start space-x-4">
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        alert.type === "warning"
                          ? "bg-destructive/10"
                          : alert.type === "info"
                            ? "bg-chart-2/10"
                            : "bg-chart-4/10"
                      }`}
                    >
                      {alert.type === "warning" ? (
                        <AlertTriangle className="w-5 h-5 text-destructive" />
                      ) : alert.type === "info" ? (
                        <Activity className="w-5 h-5 text-chart-2" />
                      ) : (
                        <CheckCircle className="w-5 h-5 text-chart-4" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold">{alert.title}</h3>
                        <Badge
                          variant={
                            alert.severity === "Medium"
                              ? "destructive"
                              : alert.severity === "Low"
                                ? "default"
                                : "secondary"
                          }
                        >
                          {alert.severity}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">{alert.description}</p>
                      <p className="text-sm font-medium">{alert.recommendation}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Risk Analytics Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 bg-muted/50">
            <TabsTrigger value="overview">Risk Overview</TabsTrigger>
            <TabsTrigger value="stress-testing">Stress Testing</TabsTrigger>
            <TabsTrigger value="correlations">Correlations</TabsTrigger>
            <TabsTrigger value="monte-carlo">Monte Carlo</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* Risk Metrics Grid */}
            <div className="grid md:grid-cols-3 gap-6">
              {riskMetrics.map((metric, index) => (
                <Card key={index} className="border-0 shadow-lg">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold text-sm">{metric.metric}</h3>
                      {metric.status === "excellent" ? (
                        <CheckCircle className="w-5 h-5 text-chart-4" />
                      ) : metric.status === "good" ? (
                        <CheckCircle className="w-5 h-5 text-chart-2" />
                      ) : (
                        <XCircle className="w-5 h-5 text-destructive" />
                      )}
                    </div>
                    <div className="space-y-2">
                      <div className="text-2xl font-bold">
                        {typeof metric.current === "number" && metric.current < 0
                          ? `${metric.current < -1000 ? "$" : ""}${metric.current.toLocaleString()}${metric.current > -1000 ? "%" : ""}`
                          : metric.current}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Threshold:{" "}
                        {typeof metric.threshold === "number" && metric.threshold < 0
                          ? `${metric.threshold < -1000 ? "$" : ""}${metric.threshold.toLocaleString()}${metric.threshold > -1000 ? "%" : ""}`
                          : metric.threshold}
                      </div>
                      <Progress value={(Math.abs(metric.current) / Math.abs(metric.threshold)) * 100} className="h-2" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Risk Decomposition */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="w-5 h-5 text-primary" />
                  <span>Risk Contribution by Asset Class</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsBarChart
                    data={[
                      { asset: "US Equities", riskContribution: 42.3, allocation: 35 },
                      { asset: "Int'l Equities", riskContribution: 28.7, allocation: 25 },
                      { asset: "Bonds", riskContribution: 8.2, allocation: 20 },
                      { asset: "REITs", riskContribution: 15.4, allocation: 10 },
                      { asset: "Commodities", riskContribution: 4.8, allocation: 7 },
                      { asset: "Crypto", riskContribution: 0.6, allocation: 3 },
                    ]}
                  >
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
                    <Bar dataKey="riskContribution" fill="hsl(var(--chart-1))" name="Risk Contribution %" />
                    <Bar dataKey="allocation" fill="hsl(var(--chart-2))" name="Allocation %" />
                  </RechartsBarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="stress-testing" className="space-y-6">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <TrendingDown className="w-5 h-5 text-primary" />
                  <span>Historical Stress Test Results</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {stressTestScenarios.map((scenario, index) => (
                    <div key={index} className="p-6 rounded-lg bg-muted/30 space-y-4">
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold">{scenario.scenario}</h3>
                        <Badge variant={scenario.status === "outperformed" ? "secondary" : "destructive"}>
                          {scenario.status === "outperformed" ? "Outperformed Market" : "Underperformed Market"}
                        </Badge>
                      </div>

                      <div className="grid md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-destructive">{scenario.portfolioLoss}%</div>
                          <div className="text-sm text-muted-foreground">Portfolio Loss</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-muted-foreground">{scenario.marketLoss}%</div>
                          <div className="text-sm text-muted-foreground">Market Loss</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold">{scenario.duration}</div>
                          <div className="text-sm text-muted-foreground">Crisis Duration</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-chart-4">{scenario.recovery}</div>
                          <div className="text-sm text-muted-foreground">Recovery Time</div>
                        </div>
                      </div>

                      <div className="flex space-x-4">
                        <div className="flex-1">
                          <div className="text-sm text-muted-foreground mb-1">Portfolio Performance</div>
                          <Progress value={Math.abs(scenario.portfolioLoss)} className="h-2" />
                        </div>
                        <div className="flex-1">
                          <div className="text-sm text-muted-foreground mb-1">Market Performance</div>
                          <Progress value={Math.abs(scenario.marketLoss)} className="h-2" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* AI Stress Testing Insights */}
            <Card className="border-0 shadow-lg bg-gradient-to-r from-accent/5 to-accent/10">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Brain className="w-5 h-5 text-accent" />
                  <span>AI Stress Testing Analysis</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold mb-2">Portfolio Resilience</h4>
                    <p className="text-sm text-muted-foreground">
                      Your portfolio has consistently outperformed market benchmarks during major stress events, with an
                      average outperformance of 12.3% during crisis periods.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Recovery Characteristics</h4>
                    <p className="text-sm text-muted-foreground">
                      AI analysis shows your portfolio recovers 35% faster than market averages due to diversification
                      across uncorrelated asset classes and defensive positioning.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Tail Risk Protection</h4>
                    <p className="text-sm text-muted-foreground">
                      Bond and commodity allocations provide effective tail risk hedging, reducing maximum drawdown by
                      an estimated 8-12% during extreme market events.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Dynamic Adjustments</h4>
                    <p className="text-sm text-muted-foreground">
                      AI monitoring enables proactive risk management, with automatic rebalancing triggers activated
                      when correlation patterns indicate increased systemic risk.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="correlations" className="space-y-6">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Asset Correlation Matrix</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {correlationData.map((corr, index) => (
                    <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-muted/30">
                      <div className="flex items-center space-x-4">
                        <div className="text-sm font-medium">
                          {corr.asset1} × {corr.asset2}
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <div
                            className={`text-lg font-bold ${
                              Math.abs(corr.correlation) > 0.7
                                ? "text-destructive"
                                : Math.abs(corr.correlation) > 0.3
                                  ? "text-accent"
                                  : "text-chart-4"
                            }`}
                          >
                            {corr.correlation > 0 ? "+" : ""}
                            {corr.correlation.toFixed(2)}
                          </div>
                          <div className="text-xs text-muted-foreground">Correlation</div>
                        </div>
                        <Badge
                          variant={
                            corr.risk === "high" ? "destructive" : corr.risk === "medium" ? "default" : "secondary"
                          }
                        >
                          {corr.risk} risk
                        </Badge>
                        <Progress value={Math.abs(corr.correlation) * 100} className="w-20 h-2" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Correlation Heatmap Visualization</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <ScatterChart
                    data={correlationData.map((d) => ({
                      x: Math.random() * 100,
                      y: Math.random() * 100,
                      correlation: d.correlation,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="x" stroke="hsl(var(--muted-foreground))" />
                    <YAxis dataKey="y" stroke="hsl(var(--muted-foreground))" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Scatter dataKey="correlation" fill="hsl(var(--chart-1))" />
                  </ScatterChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="monte-carlo" className="space-y-6">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Target className="w-5 h-5 text-primary" />
                  <span>Monte Carlo Simulation Results</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="text-center space-y-2">
                    <div className="text-3xl font-bold text-foreground">$580,000</div>
                    <div className="text-muted-foreground">Expected Portfolio Value (10 Years)</div>
                    <div className="text-sm text-muted-foreground">Based on 10,000 simulations</div>
                  </div>

                  <div className="grid md:grid-cols-5 gap-4">
                    {monteCarloResults.map((result, index) => (
                      <Card key={index} className="border border-border">
                        <CardContent className="p-4 text-center">
                          <div className="text-lg font-bold">${result.value.toLocaleString()}</div>
                          <div className="text-sm text-muted-foreground">{result.percentile} Percentile</div>
                          <div className="text-xs text-muted-foreground">{result.probability}% Probability</div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart
                      data={[
                        { year: 1, p5: 95000, p25: 105000, p50: 115000, p75: 125000, p95: 140000 },
                        { year: 2, p5: 110000, p25: 125000, p50: 140000, p75: 160000, p95: 185000 },
                        { year: 3, p5: 125000, p25: 150000, p50: 175000, p75: 205000, p95: 245000 },
                        { year: 4, p5: 140000, p25: 175000, p50: 215000, p75: 260000, p95: 320000 },
                        { year: 5, p5: 155000, p25: 205000, p50: 265000, p75: 330000, p95: 420000 },
                        { year: 6, p5: 170000, p25: 235000, p50: 320000, p75: 415000, p95: 550000 },
                        { year: 7, p5: 185000, p25: 270000, p50: 385000, p75: 520000, p95: 720000 },
                        { year: 8, p5: 200000, p25: 310000, p50: 460000, p75: 650000, p95: 940000 },
                        { year: 9, p5: 220000, p25: 355000, p50: 550000, p75: 810000, p95: 1220000 },
                        { year: 10, p5: 240000, p25: 405000, p50: 650000, p75: 1010000, p95: 1580000 },
                      ]}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="year" stroke="hsl(var(--muted-foreground))" />
                      <YAxis stroke="hsl(var(--muted-foreground))" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "hsl(var(--card))",
                          border: "1px solid hsl(var(--border))",
                          borderRadius: "8px",
                        }}
                        formatter={(value: any) => [`$${value.toLocaleString()}`, ""]}
                      />
                      <Legend />
                      <Area
                        type="monotone"
                        dataKey="p95"
                        stackId="1"
                        stroke="hsl(var(--chart-4))"
                        fill="hsl(var(--chart-4))"
                        fillOpacity={0.1}
                        name="95th Percentile"
                      />
                      <Area
                        type="monotone"
                        dataKey="p75"
                        stackId="1"
                        stroke="hsl(var(--chart-3))"
                        fill="hsl(var(--chart-3))"
                        fillOpacity={0.2}
                        name="75th Percentile"
                      />
                      <Area
                        type="monotone"
                        dataKey="p50"
                        stackId="1"
                        stroke="hsl(var(--chart-1))"
                        fill="hsl(var(--chart-1))"
                        fillOpacity={0.4}
                        name="Median"
                      />
                      <Area
                        type="monotone"
                        dataKey="p25"
                        stackId="1"
                        stroke="hsl(var(--chart-2))"
                        fill="hsl(var(--chart-2))"
                        fillOpacity={0.2}
                        name="25th Percentile"
                      />
                      <Area
                        type="monotone"
                        dataKey="p5"
                        stackId="1"
                        stroke="hsl(var(--destructive))"
                        fill="hsl(var(--destructive))"
                        fillOpacity={0.1}
                        name="5th Percentile"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg bg-gradient-to-r from-chart-4/5 to-chart-4/10">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="w-5 h-5 text-chart-4" />
                  <span>Simulation Insights</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-3 gap-6">
                  <div>
                    <h4 className="font-semibold mb-2">Success Probability</h4>
                    <p className="text-sm text-muted-foreground">
                      87% probability of achieving your target portfolio value of $1M within 10 years based on current
                      allocation and contribution strategy.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Downside Protection</h4>
                    <p className="text-sm text-muted-foreground">
                      Only 5% chance of portfolio value falling below $240K, demonstrating strong downside protection
                      from diversification.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Upside Potential</h4>
                    <p className="text-sm text-muted-foreground">
                      25% probability of exceeding $1M portfolio value, with potential upside reaching $1.58M in
                      favorable scenarios.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
