"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Brain, Zap, Shield, BarChart3, CheckCircle, ArrowRight, Sparkles, Loader2, AlertCircle } from "lucide-react"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { apiClient, type PortfolioRecommendation, type AssessmentData, handleAPIError } from "@/lib/api"

// Interface matching the API response
interface PortfolioAllocation {
  name: string
  percentage: number
  amount: number
  color?: string
  rationale?: string
  [key: string]: any // Add index signature for chart compatibility
}

interface PortfolioRecommendationLocal {
  allocation: PortfolioAllocation[]
  expected_return: number
  volatility: number
  sharpe_ratio: number
  risk_score: number
  confidence: number
}

const aiProcessingSteps = [
  {
    id: 1,
    title: "Analyzing Risk Profile",
    description: "Processing risk tolerance and capacity data",
    duration: 2000,
  },
  { id: 2, title: "Market Data Integration", description: "Incorporating real-time market conditions", duration: 1500 },
  {
    id: 3,
    title: "Alternative Data Processing",
    description: "Analyzing sentiment and economic indicators",
    duration: 2500,
  },
  {
    id: 4,
    title: "Portfolio Optimization",
    description: "Running mean-variance optimization with AI enhancements",
    duration: 3000,
  },
  {
    id: 5,
    title: "Risk Management Calibration",
    description: "Applying stress testing and scenario analysis",
    duration: 2000,
  },
  {
    id: 6,
    title: "Final Validation",
    description: "Ensuring regulatory compliance and best practices",
    duration: 1000,
  },
]

export default function GeneratePage() {
  const [currentStep, setCurrentStep] = useState(0)
  const [isGenerating, setIsGenerating] = useState(true)
  const [portfolio, setPortfolio] = useState<PortfolioRecommendationLocal | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [assessmentData, setAssessmentData] = useState<AssessmentData | null>(null)
  
  const router = useRouter()

  // Load assessment data on component mount
  useEffect(() => {
    const loadAssessmentData = () => {
      if (typeof window !== 'undefined') {
        const storedAssessment = localStorage.getItem('portfolioai_assessment')
        if (storedAssessment) {
          try {
            const parsedData = JSON.parse(storedAssessment)
            setAssessmentData(parsedData)
            return parsedData
          } catch (err) {
            console.error('Error parsing assessment data:', err)
            setError('Invalid assessment data. Please complete the assessment again.')
            return null
          }
        } else {
          setError('No assessment data found. Please complete the assessment first.')
          return null
        }
      }
      return null
    }

    const data = loadAssessmentData()
    if (!data) {
      // Redirect back to assessment if no data
      setTimeout(() => router.push('/assessment'), 2000)
    }
  }, [router])

  // Handle AI processing steps and API call
  useEffect(() => {
    if (!assessmentData || error) return

    if (isGenerating && currentStep < aiProcessingSteps.length) {
      const timer = setTimeout(() => {
        setCurrentStep(currentStep + 1)
      }, aiProcessingSteps[currentStep]?.duration || 1000)

      return () => clearTimeout(timer)
    } else if (currentStep >= aiProcessingSteps.length && assessmentData) {
      // Call the API to generate portfolio
      generatePortfolioFromAPI(assessmentData)
    }
  }, [currentStep, isGenerating, assessmentData, error])

  const generatePortfolioFromAPI = async (data: AssessmentData) => {
    try {
      console.log('Generating portfolio with assessment data:', data)
      const result = await apiClient.generatePortfolio(data)
      
      // Convert API response to local format
      const portfolioData: PortfolioRecommendationLocal = {
        allocation: result.allocation.map(item => ({
          ...item,
          color: item.color || getRandomColor()
        })),
        expected_return: result.expected_return,
        volatility: result.volatility,
        sharpe_ratio: result.sharpe_ratio,
        risk_score: result.risk_score,
        confidence: result.confidence
      }
      
      setPortfolio(portfolioData)
      setIsGenerating(false)
      
      // Save portfolio data for dashboard
      if (typeof window !== 'undefined') {
        localStorage.setItem('portfolioai_portfolio', JSON.stringify(portfolioData))
      }
      
    } catch (err) {
      console.error('Error generating portfolio:', err)
      setError(handleAPIError(err))
      setIsGenerating(false)
    }
  }

  const getRandomColor = () => {
    const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#F97316', '#06B6D4']
    return colors[Math.floor(Math.random() * colors.length)]
  }

  const totalAmount = 100000 // Mock initial investment

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm">
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
                <Sparkles className="w-4 h-4 mr-1" />
                AI Generation
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8 max-w-6xl">
        {error ? (
          <div className="text-center space-y-6">
            <div className="w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mx-auto">
              <AlertCircle className="w-8 h-8 text-destructive" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-destructive mb-2">Error</h1>
              <p className="text-muted-foreground max-w-md mx-auto">{error}</p>
            </div>
            <Link href="/assessment">
              <Button className="bg-primary hover:bg-primary/90">
                <ArrowRight className="w-4 h-4 mr-2" />
                Complete Assessment
              </Button>
            </Link>
          </div>
        ) : isGenerating ? (
          <div className="space-y-8">
            {/* AI Processing Header */}
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center mx-auto">
                <Brain className="w-8 h-8 text-accent animate-pulse" />
              </div>
              <h1 className="text-3xl font-bold">AI Portfolio Generation</h1>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Our advanced AI is analyzing your profile and market conditions to create your personalized investment
                portfolio.
              </p>
            </div>

            {/* Processing Steps */}
            <Card className="border-0 shadow-lg max-w-3xl mx-auto">
              <CardContent className="p-8">
                <div className="space-y-6">
                  {aiProcessingSteps.map((step, index) => {
                    const isActive = index === currentStep
                    const isCompleted = index < currentStep
                    const isUpcoming = index > currentStep

                    return (
                      <div key={step.id} className="flex items-center space-x-4">
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500 ${
                            isActive
                              ? "bg-accent border-accent text-accent-foreground animate-pulse"
                              : isCompleted
                                ? "bg-chart-4 border-chart-4 text-white"
                                : "border-border text-muted-foreground"
                          }`}
                        >
                          {isCompleted ? (
                            <CheckCircle className="w-5 h-5" />
                          ) : (
                            <span className="text-sm font-medium">{step.id}</span>
                          )}
                        </div>
                        <div className="flex-1">
                          <div
                            className={`font-medium transition-colors ${
                              isActive ? "text-accent" : isCompleted ? "text-chart-4" : "text-muted-foreground"
                            }`}
                          >
                            {step.title}
                          </div>
                          <div className="text-sm text-muted-foreground">{step.description}</div>
                          {isActive && <Progress value={75} className="mt-2 h-1" />}
                        </div>
                        {isActive && <Zap className="w-5 h-5 text-accent animate-pulse" />}
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            {/* AI Methodology Info */}
            <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              <Card className="border-0 shadow-lg bg-gradient-to-br from-accent/5 to-accent/10">
                <CardContent className="p-6 text-center space-y-3">
                  <div className="w-12 h-12 bg-accent/20 rounded-lg flex items-center justify-center mx-auto">
                    <Brain className="w-6 h-6 text-accent" />
                  </div>
                  <h3 className="font-semibold">Machine Learning</h3>
                  <p className="text-sm text-muted-foreground">
                    Advanced algorithms analyze your complete financial profile beyond traditional questionnaires.
                  </p>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg bg-gradient-to-br from-chart-2/5 to-chart-2/10">
                <CardContent className="p-6 text-center space-y-3">
                  <div className="w-12 h-12 bg-chart-2/20 rounded-lg flex items-center justify-center mx-auto">
                    <BarChart3 className="w-6 h-6 text-chart-2" />
                  </div>
                  <h3 className="font-semibold">Dynamic Optimization</h3>
                  <p className="text-sm text-muted-foreground">
                    Real-time market data integration with alternative data sources for superior insights.
                  </p>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg bg-gradient-to-br from-chart-4/5 to-chart-4/10">
                <CardContent className="p-6 text-center space-y-3">
                  <div className="w-12 h-12 bg-chart-4/20 rounded-lg flex items-center justify-center mx-auto">
                    <Shield className="w-6 h-6 text-chart-4" />
                  </div>
                  <h3 className="font-semibold">Risk Management</h3>
                  <p className="text-sm text-muted-foreground">
                    Comprehensive stress testing and scenario analysis for portfolio resilience.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Success Header */}
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-chart-4/10 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle className="w-8 h-8 text-chart-4" />
              </div>
              <h1 className="text-3xl font-bold">Your AI-Optimized Portfolio</h1>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Based on your risk profile and current market conditions, here's your personalized investment strategy.
              </p>
            </div>

            {/* Portfolio Summary */}
            <div className="grid md:grid-cols-4 gap-4 max-w-4xl mx-auto">
              <Card className="border-0 shadow-lg">
                <CardContent className="p-6 text-center">
                  <div className="text-2xl font-bold text-chart-4">{portfolio?.expected_return}%</div>
                  <div className="text-sm text-muted-foreground">Expected Return</div>
                </CardContent>
              </Card>
              <Card className="border-0 shadow-lg">
                <CardContent className="p-6 text-center">
                  <div className="text-2xl font-bold text-chart-2">{portfolio?.volatility}%</div>
                  <div className="text-sm text-muted-foreground">Volatility</div>
                </CardContent>
              </Card>
              <Card className="border-0 shadow-lg">
                <CardContent className="p-6 text-center">
                  <div className="text-2xl font-bold text-accent">{portfolio?.sharpe_ratio}</div>
                  <div className="text-sm text-muted-foreground">Sharpe Ratio</div>
                </CardContent>
              </Card>
              <Card className="border-0 shadow-lg">
                <CardContent className="p-6 text-center">
                  <div className="text-2xl font-bold text-primary">{portfolio?.confidence}%</div>
                  <div className="text-sm text-muted-foreground">AI Confidence</div>
                </CardContent>
              </Card>
            </div>

            {/* Portfolio Visualization */}
            <div className="grid lg:grid-cols-2 gap-8">
              {/* Allocation Chart */}
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <BarChart3 className="w-5 h-5 text-primary" />
                    <span>Asset Allocation</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={portfolio?.allocation}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={120}
                        paddingAngle={2}
                        dataKey="percentage"
                      >
                        {portfolio?.allocation.map((entry, index) => (
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
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Allocation Breakdown */}
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle>Portfolio Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {portfolio?.allocation.map((asset, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: asset.color }} />
                            <span className="font-medium">{asset.name}</span>
                          </div>
                          <div className="text-right">
                            <div className="font-medium">{asset.percentage}%</div>
                            <div className="text-sm text-muted-foreground">${asset.amount.toLocaleString()}</div>
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground ml-7">{asset.rationale}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* AI Rationale */}
            <Card className="border-0 shadow-lg bg-gradient-to-r from-accent/5 to-accent/10">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Brain className="w-5 h-5 text-accent" />
                  <span>AI Portfolio Rationale</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold mb-2">Risk-Return Optimization</h4>
                    <p className="text-sm text-muted-foreground">
                      Your portfolio is optimized for a {portfolio?.risk_score}/10 risk level, balancing growth potential
                      with downside protection. The {portfolio?.sharpe_ratio} Sharpe ratio indicates excellent
                      risk-adjusted returns.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Diversification Strategy</h4>
                    <p className="text-sm text-muted-foreground">
                      Geographic and asset class diversification reduces correlation risk. Alternative assets provide
                      inflation protection and uncorrelated returns during market stress.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Market Conditions</h4>
                    <p className="text-sm text-muted-foreground">
                      Current allocation reflects AI analysis of market sentiment, economic indicators, and alternative
                      data sources for optimal positioning.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Dynamic Rebalancing</h4>
                    <p className="text-sm text-muted-foreground">
                      Portfolio will be continuously monitored and rebalanced using reinforcement learning algorithms to
                      maintain optimal risk-return characteristics.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link href="/dashboard">
                <Button size="lg" className="bg-primary hover:bg-primary/90 text-lg px-8 py-6">
                  Accept & View Dashboard
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Button variant="outline" size="lg" className="text-lg px-8 py-6 bg-transparent">
                Customize Portfolio
              </Button>
              <Button variant="outline" size="lg" className="text-lg px-8 py-6 bg-transparent">
                Download Report
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
