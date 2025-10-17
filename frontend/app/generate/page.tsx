"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Brain, Zap, Shield, BarChart3, CheckCircle, ArrowRight, Sparkles, Loader2, AlertCircle, FileText, Download } from "lucide-react"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { apiClient, type PortfolioRecommendation, type AssessmentData, type StreamEvent, handleAPIError } from "@/lib/api"

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
  const [streamProgress, setStreamProgress] = useState<number>(0)
  const [streamMessage, setStreamMessage] = useState<string>("")
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([])
  const [currentPhase, setCurrentPhase] = useState<string>("")
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false)
  const [pdfDownloadUrl, setPdfDownloadUrl] = useState<string | null>(null)
  const [userId, setUserId] = useState<string>("demo_user")
  const [riskBlueprint, setRiskBlueprint] = useState<any>(null)
  const [portfolioAllocation, setPortfolioAllocation] = useState<any>(null)
  const [securitySelections, setSecuritySelections] = useState<any>(null)
  
  const router = useRouter()

  // PDF generation function
  const generatePdfReport = async () => {
    if (!portfolio || !assessmentData) {
      setError("No portfolio data available for PDF generation")
      return
    }

    setIsGeneratingPdf(true)
    try {
      const response = await apiClient.generatePdfReport(userId, {
        report_title: `Investment Portfolio Analysis - ${userId.slice(0, 8)}`,
        generated_date: new Date().toLocaleDateString(),
        client_id: userId,
        executive_summary: "AI-generated portfolio analysis based on your investment profile and risk tolerance.",
        allocation_rationale: "Portfolio allocation optimized using advanced AI algorithms considering your risk profile and market conditions.",
        selection_rationale: "Individual investments selected based on fundamental analysis, market sentiment, and risk-return optimization.",
        risk_commentary: "Risk management through diversification and appropriate asset allocation tailored to your risk tolerance.",
        key_recommendations: [
          "Review portfolio performance quarterly",
          "Maintain target allocation through rebalancing",
          "Consider tax-loss harvesting opportunities"
        ],
        next_steps: [
          "Set up automatic monthly investments",
          "Monitor portfolio performance regularly",
          "Review and adjust strategy annually"
        ],
        portfolio_allocation: portfolio.allocation.reduce((acc, item) => {
          acc[item.name] = item.percentage
          return acc
        }, {} as Record<string, number>),
        individual_holdings: portfolio.allocation.map(item => ({
          name: item.name,
          symbol: item.name.replace(/\s+/g, '').toUpperCase(),
          allocation_percent: item.percentage,
          value: item.amount
        }))
      })

      if (response.status === "success") {
        setPdfDownloadUrl(response.download_url)
      } else {
        throw new Error("Failed to generate PDF")
      }
    } catch (error) {
      console.error("Error generating PDF:", error)
      setError("Failed to generate PDF report. Please try again.")
    } finally {
      setIsGeneratingPdf(false)
    }
  }

  // Load assessment data on component mount
  useEffect(() => {
    const loadAssessmentData = () => {
      if (typeof window !== 'undefined') {
        const storedAssessment = localStorage.getItem('portfolioai_assessment')
        if (storedAssessment) {
          try {
            const parsedData = JSON.parse(storedAssessment)
            setAssessmentData(parsedData)
            // Extract user ID from stored profile ID
            const storedProfileId = localStorage.getItem('profileId')
            if (storedProfileId) {
              setUserId(storedProfileId)
            }
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

  // Handle streaming portfolio generation
  useEffect(() => {
    if (!assessmentData || error) return

    if (isGenerating) {
      generatePortfolioWithStreaming(assessmentData)
    }
  }, [assessmentData, error])

  const generatePortfolioWithStreaming = async (data: AssessmentData) => {
    try {
      console.log('Starting streaming portfolio generation with data:', data)
      
      await apiClient.generatePortfolioStream(
        data,
        // onProgress callback
        (event: StreamEvent) => {
          console.log('Stream event received:', event)
          setStreamEvents(prev => [...prev, event])
          
          // Update progress and message based on event type
          if (event.data.progress) {
            setStreamProgress(event.data.progress)
          }
          if (event.data.message) {
            setStreamMessage(event.data.message)
          }
          
          // Update current phase and capture intermediate data
          switch (event.event) {
            case 'profile_generation_started':
              setCurrentPhase('Profile Generation')
              break
            case 'risk_analysis_started':
              setCurrentPhase('Risk Analysis')
              break
            case 'risk_analysis_complete':
              setCurrentPhase('Risk Analysis Complete')
              setRiskBlueprint(event.data.risk_blueprint)
              break
            case 'portfolio_construction_started':
              setCurrentPhase('Portfolio Optimization')
              break
            case 'portfolio_construction_complete':
              setCurrentPhase('Portfolio Optimization Complete')
              setPortfolioAllocation(event.data.portfolio_allocation)
              break
            case 'selection_started':
              setCurrentPhase('Security Selection')
              break
            case 'selection_complete':
              setCurrentPhase('Security Selection Complete')
              setSecuritySelections(event.data.security_selections)
              break
            case 'communication_started':
              setCurrentPhase('Report Generation')
              break
            default:
              break
          }
        },
        // onComplete callback
        (finalReport: any) => {
          console.log('Portfolio generation completed:', finalReport)
          
          // Convert final report to portfolio format
          if (finalReport.final_report && finalReport.final_report.portfolio_details) {
            const portfolioData: PortfolioRecommendationLocal = {
              allocation: Object.entries(finalReport.final_report.portfolio_details.allocation_summary?.sectors || {})
                .map(([name, percentage]) => ({
                  name: name.charAt(0).toUpperCase() + name.slice(1),
                  percentage: Number(percentage) * 100,
                  amount: Number(percentage) * 100000, // Mock amount
                  color: getRandomColor()
                })),
              expected_return: finalReport.final_report.executive_summary?.expected_annual_return ? 
                parseFloat(finalReport.final_report.executive_summary.expected_annual_return.replace('%', '')) / 100 : 0.087,
              volatility: 0.142, // Mock volatility
              sharpe_ratio: 0.61, // Mock Sharpe ratio
              risk_score: 65, // Mock risk score
              confidence: 0.85 // Mock confidence
            }
            
            setPortfolio(portfolioData)
            
            // Save portfolio data for dashboard
            if (typeof window !== 'undefined') {
              localStorage.setItem('portfolioai_portfolio', JSON.stringify(portfolioData))
              localStorage.setItem('portfolioai_final_report', JSON.stringify(finalReport.final_report))
            }
          }
          
          setIsGenerating(false)
          setStreamProgress(100)
          setStreamMessage('Portfolio generation completed successfully!')
        },
        // onError callback
        (errorMessage: string) => {
          console.error('Streaming error:', errorMessage)
          setError(`Portfolio generation failed: ${errorMessage}`)
          setIsGenerating(false)
        }
      )
      
    } catch (err) {
      console.error('Error starting streaming generation:', err)
      setError(err instanceof Error ? err.message : 'Failed to start portfolio generation')
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

            {/* Real-time Progress */}
            <Card className="border-0 shadow-lg max-w-3xl mx-auto">
              <CardContent className="p-8">
                <div className="space-y-6">
                  {/* Current Phase */}
                  <div className="text-center space-y-3">
                    <div className="text-lg font-semibold text-accent">{currentPhase || 'Initializing...'}</div>
                    <div className="text-sm text-muted-foreground">{streamMessage || 'Starting AI analysis...'}</div>
                    <Progress value={streamProgress} className="h-2" />
                    <div className="text-xs text-muted-foreground">{streamProgress}% Complete</div>
                  </div>

                  {/* Live Activity Stream */}
                  {streamEvents.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-medium text-sm">Live Activity Stream:</h4>
                      <div className="max-h-48 overflow-y-auto space-y-2 bg-muted/20 rounded-lg p-4">
                        {streamEvents.slice(-5).map((event, index) => (
                          <div key={index} className="flex items-center space-x-3 text-sm">
                            <div className="w-2 h-2 bg-accent rounded-full animate-pulse"></div>
                            <div className="flex-1">
                              <span className="font-medium">{event.data.message}</span>
                              <span className="text-muted-foreground ml-2">
                                ({new Date(event.timestamp).toLocaleTimeString()})
                              </span>
                            </div>
                            {event.data.progress && (
                              <Badge variant="secondary" className="text-xs">
                                {event.data.progress}%
                              </Badge>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Real-time Data Preview */}
                  {streamEvents.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-medium text-sm">Analysis Results:</h4>
                      <div className="grid md:grid-cols-2 gap-4">
                        {streamEvents.find(e => e.event === 'risk_analysis_complete') && (
                          <div className="p-4 bg-muted/10 rounded-lg">
                            <div className="flex items-center space-x-2 mb-2">
                              <CheckCircle className="w-4 h-4 text-green-500" />
                              <span className="text-sm font-medium">Risk Analysis</span>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Risk profile assessed and validated
                            </div>
                          </div>
                        )}
                        {streamEvents.find(e => e.event === 'portfolio_construction_complete') && (
                          <div className="p-4 bg-muted/10 rounded-lg">
                            <div className="flex items-center space-x-2 mb-2">
                              <CheckCircle className="w-4 h-4 text-green-500" />
                              <span className="text-sm font-medium">Portfolio Optimization</span>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Optimal allocation calculated
                            </div>
                          </div>
                        )}
                        {streamEvents.find(e => e.event === 'selection_complete') && (
                          <div className="p-4 bg-muted/10 rounded-lg">
                            <div className="flex items-center space-x-2 mb-2">
                              <CheckCircle className="w-4 h-4 text-green-500" />
                              <span className="text-sm font-medium">Security Selection</span>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Investment securities chosen
                            </div>
                          </div>
                        )}
                        {streamEvents.find(e => e.event === 'final_report_complete') && (
                          <div className="p-4 bg-muted/10 rounded-lg">
                            <div className="flex items-center space-x-2 mb-2">
                              <CheckCircle className="w-4 h-4 text-green-500" />
                              <span className="text-sm font-medium">Final Report</span>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Comprehensive analysis ready
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Intermediate Results Display */}
                  {riskBlueprint && (
                    <div className="space-y-3">
                      <h4 className="font-medium text-sm">Risk Blueprint:</h4>
                      <Card className="bg-muted/10">
                        <CardContent className="p-4">
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="font-medium">Risk Capacity:</span>
                              <span className="ml-2">{riskBlueprint.risk_capacity?.level || 'N/A'}</span>
                            </div>
                            <div>
                              <span className="font-medium">Risk Tolerance:</span>
                              <span className="ml-2">{riskBlueprint.risk_tolerance?.level || 'N/A'}</span>
                            </div>
                            <div>
                              <span className="font-medium">Volatility Target:</span>
                              <span className="ml-2">{riskBlueprint.volatility_target || 'N/A'}%</span>
                            </div>
                            <div>
                              <span className="font-medium">Risk Score:</span>
                              <span className="ml-2">{riskBlueprint.risk_score || 'N/A'}/100</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {portfolioAllocation && (
                    <div className="space-y-3">
                      <h4 className="font-medium text-sm">Portfolio Allocation:</h4>
                      <Card className="bg-muted/10">
                        <CardContent className="p-4">
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="font-medium">Expected Return:</span>
                              <span className="ml-2">{(portfolioAllocation.portfolio_metrics?.expected_return * 100 || 0).toFixed(1)}%</span>
                            </div>
                            <div>
                              <span className="font-medium">Volatility:</span>
                              <span className="ml-2">{(portfolioAllocation.portfolio_metrics?.volatility * 100 || 0).toFixed(1)}%</span>
                            </div>
                            <div>
                              <span className="font-medium">Sharpe Ratio:</span>
                              <span className="ml-2">{portfolioAllocation.portfolio_metrics?.sharpe_ratio || 'N/A'}</span>
                            </div>
                            <div>
                              <span className="font-medium">ESG Allocation:</span>
                              <span className="ml-2">{(portfolioAllocation.allocation_summary?.esg_allocation * 100 || 0).toFixed(0)}%</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {securitySelections && (
                    <div className="space-y-3">
                      <h4 className="font-medium text-sm">Security Selection:</h4>
                      <Card className="bg-muted/10">
                        <CardContent className="p-4">
                          <div className="text-sm">
                            <div className="mb-2">
                              <span className="font-medium">Individual Stocks:</span>
                              <span className="ml-2">{Object.keys(securitySelections.equity_selections || {}).length} categories</span>
                            </div>
                            <div className="mb-2">
                              <span className="font-medium">ESG Screening:</span>
                              <span className="ml-2">{securitySelections.esg_screening_results?.excluded_companies?.length || 0} companies excluded</span>
                            </div>
                            <div>
                              <span className="font-medium">Selection Criteria:</span>
                              <span className="ml-2">ESG-focused, expense ratio &lt; 0.25%</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}
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
              <Button 
                variant="outline" 
                size="lg" 
                className="text-lg px-8 py-6 bg-transparent"
                onClick={generatePdfReport}
                disabled={isGeneratingPdf}
              >
                {isGeneratingPdf ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Generating PDF...
                  </>
                ) : pdfDownloadUrl ? (
                  <>
                    <Download className="w-5 h-5 mr-2" />
                    <a href={pdfDownloadUrl} download className="flex items-center">
                      Download PDF Report
                    </a>
                  </>
                ) : (
                  <>
                    <FileText className="w-5 h-5 mr-2" />
                    Generate PDF Report
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
