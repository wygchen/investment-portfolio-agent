"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Brain, Zap, Shield, BarChart3, CheckCircle, ArrowRight, Sparkles, Loader2, AlertCircle } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { apiClient, type PortfolioRecommendation, type AssessmentData, type StreamEventHandlers, handleAPIError } from "@/lib/api"


const aiProcessingSteps = [
  {
    id: 1,
    title: "Analyzing Risk Profile",
    description: "Processing risk tolerance and capacity data",
    eventType: "risk_analysis",
  },
  {
    id: 2,
    title: "Security Selection",
    description: "Selecting specific securities and analyzing market conditions",
    eventType: "selection",
  },
  {
    id: 3,
    title: "Portfolio Optimization",
    description: "Running mean-variance optimization with AI enhancements",
    eventType: "portfolio_construction",
  },
  {
    id: 4,
    title: "Report Generation",
    description: "Generating comprehensive investment report",
    eventType: "communication",
  },
]

export default function GeneratePage() {
  const [isGenerating, setIsGenerating] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [assessmentData, setAssessmentData] = useState<AssessmentData | null>(null)
  const [streamProgress, setStreamProgress] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set())
  const [activeStep, setActiveStep] = useState<string | null>(null)
  const [isHydrated, setIsHydrated] = useState(false)
  const [riskBlueprint, setRiskBlueprint] = useState<any | null>(null)
  const [selectionSummary, setSelectionSummary] = useState<any | null>(null)
  
  const router = useRouter()

  // Hydration check - only run on client side
  useEffect(() => {
    setIsHydrated(true)
  }, [])

  // Load assessment data on component mount - only after hydration
  useEffect(() => {
    if (!isHydrated) return

    const loadAssessmentData = () => {
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

    const data = loadAssessmentData()
    if (!data) {
      // Redirect back to assessment if no data
      setTimeout(() => router.push('/assessment'), 2000)
    }
  }, [router, isHydrated])

  // Handle streaming API call
  useEffect(() => {
    if (!assessmentData || error) return

    if (isGenerating) {
      generatePortfolioWithStreaming(assessmentData)
    }
  }, [assessmentData, error, isGenerating])

  const generatePortfolioWithStreaming = async (data: AssessmentData) => {
    try {
      console.log('Starting streaming portfolio generation with assessment data:', data)
      
      // Normalize sector preferences to yfinance sector names if present
      const sectorIdToYfSector: Record<string, string> = {
        'technology': 'Technology',
        'healthcare': 'Healthcare',
        'renewable-energy': 'Energy',
        'consumer-cyclical': 'Consumer Cyclical',
        'consumer-defensive': 'Consumer Defensive',
        'financials': 'Financial Services',
        'industrials': 'Industrials',
        'real-estate': 'Real Estate',
        'utilities': 'Utilities',
        'communication-services': 'Communication Services',
        'basic-materials': 'Basic Materials',
      }
      const yfSectors = new Set(Object.values(sectorIdToYfSector))
      const preferIds: string[] | undefined = (data as any)?.values?.preferIndustries
      const mappedSectors = Array.isArray(preferIds)
        ? Array.from(new Set(
            preferIds
              .map((id) => sectorIdToYfSector[id])
              .filter((name): name is string => Boolean(name))
          ))
        : undefined

      const normalizedData: any = { ...data }
      if (mappedSectors && mappedSectors.length > 0) {
        normalizedData.personal_values = {
          ...(normalizedData.personal_values || {}),
          esg_preferences: {
            ...(normalizedData.personal_values?.esg_preferences || {}),
            prefer_industries: mappedSectors,
          },
        }
      }

      // Kick off validation in background; do not block streaming
      apiClient.validateAssessment(normalizedData).catch((e) => {
        console.warn('Assessment validation (non-blocking) failed:', e)
      })
      
      // Set up streaming event handlers
      const streamHandlers: StreamEventHandlers = {
        onRiskAnalysisStarted: (data) => {
          console.log('Risk analysis started:', data)
          setActiveStep('risk_analysis')
          setStreamProgress(data.progress || 30)
        },
        onRiskAnalysisComplete: (data) => {
          console.log('Risk analysis complete:', data)
          // Merge top-level fields so UI can display even if not nested
          const merged = data?.risk_blueprint
            ? { ...data.risk_blueprint, risk_score: data.risk_score, volatility_target: data.volatility_target }
            : (data?.risk_summary ?? null)
          setRiskBlueprint(merged)
          setCompletedSteps(prev => new Set([...prev, 'risk_analysis']))
          // Clear active step if no immediate next-started event arrives
          setActiveStep(null)
          setStreamProgress(data.progress || 50)
        },
        onSelectionStarted: (data) => {
          console.log('Selection started:', data)
          setActiveStep('selection')
          setStreamProgress(data.progress || 60)
        },
        onSelectionComplete: (data) => {
          console.log('Selection complete:', data)
          setSelectionSummary(
            data?.selection_summary ??
            data?.security_selections ??
            data?.selection ??
            null
          )
          setCompletedSteps(prev => new Set([...prev, 'selection']))
          // Clear active step to avoid appearing stuck in selection
          setActiveStep(null)
          setStreamProgress(data.progress || 80)
          console.log('Selection step marked complete, activeStep cleared')
        },
        onPortfolioConstructionStarted: (data) => {
          console.log('Portfolio construction started:', data)
          setActiveStep('portfolio_construction')
          setStreamProgress(data.progress || 70)
        },
        onPortfolioConstructionComplete: (data) => {
          console.log('Portfolio construction complete:', data)
          setCompletedSteps(prev => new Set([...prev, 'portfolio_construction']))
          setStreamProgress(data.progress || 85)
        },
        onCommunicationStarted: (data) => {
          console.log('Communication started:', data)
          setActiveStep('communication')
          setStreamProgress(data.progress || 90)
        },
        onFinalReportComplete: (data) => {
          console.log('Final report complete:', data)
          setCompletedSteps(prev => new Set([...prev, 'communication']))
          setStreamProgress(100)
          
          // Convert final report to portfolio format
          const finalReport = data.final_report || {}
          const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#F97316', '#06B6D4']
          const portfolioData = {
            allocation: finalReport.individual_holdings?.map((holding: any, index: number) => ({
              name: holding.name || `Asset ${index + 1}`,
              percentage: holding.allocation_percent || 0,
              amount: holding.value || 0,
              color: colors[index % colors.length],
              rationale: `Selected based on AI analysis`
            })) || [],
            expected_return: finalReport.executive_summary?.expected_annual_return?.replace('%', '') || 7.6,
            volatility: 14.5,
            sharpe_ratio: 0.52,
            risk_score: 50,
            confidence: 85
          }
          
          // Save portfolio data for dashboard
          if (typeof window !== 'undefined') {
            localStorage.setItem('portfolioai_portfolio', JSON.stringify(portfolioData))
          }
          
          // Auto-redirect to dashboard after a brief delay
          setTimeout(() => {
            router.push('/dashboard')
          }, 1200)
        },
        onError: (error) => {
          console.error('Streaming error:', error)
          setError(error)
          setIsGenerating(false)
        }
      }
      
      // Start streaming
      await apiClient.generateReportStream(normalizedData, streamHandlers)
      
    } catch (err) {
      console.error('Error generating portfolio with streaming:', err)
      setError(handleAPIError(err))
      setIsGenerating(false)
    }
  }


  // Show loading state during hydration
  if (!isHydrated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center mx-auto">
            <Brain className="w-8 h-8 text-accent animate-pulse" />
          </div>
          <h1 className="text-2xl font-bold">Loading...</h1>
          <p className="text-muted-foreground">Initializing your portfolio generation</p>
        </div>
      </div>
    )
  }

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
              
              {/* Progress Bar */}
              <div className="max-w-md mx-auto space-y-2">
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>Progress</span>
                  <span>{streamProgress}%</span>
                </div>
                <Progress value={streamProgress} className="h-2" />
              </div>
            </div>

            {/* Processing Steps */}
            <Card className="border-0 shadow-lg max-w-3xl mx-auto">
              <CardContent className="p-8">
                <div className="space-y-6">
                  {aiProcessingSteps.map((step, index) => {
                    const isActive = activeStep === step.eventType
                    const isCompleted = completedSteps.has(step.eventType)
                    const isUpcoming = !isActive && !isCompleted

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
                          {isActive && <Progress value={streamProgress} className="mt-2 h-1" />}
                        </div>
                        {isActive && <Zap className="w-5 h-5 text-accent animate-pulse" />}
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Interim Results: Risk Blueprint - Show until selection completes */}
            {completedSteps.has('risk_analysis') && !completedSteps.has('selection') && (
              <Card className="border-0 shadow-lg max-w-3xl mx-auto">
                <CardHeader>
                  <CardTitle>Risk Blueprint</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {riskBlueprint ? (
                    <div className="space-y-2 text-sm">
                      {riskBlueprint.risk_profile && (
                        <div>
                          <span className="font-medium">Profile: </span>
                          <span className="text-muted-foreground">{String(riskBlueprint.risk_profile)}</span>
                        </div>
                      )}
                      {(riskBlueprint.capacity || riskBlueprint.risk_capacity) && (
                        <div>
                          <span className="font-medium">Capacity: </span>
                          <span className="text-muted-foreground">{String(riskBlueprint.capacity ?? riskBlueprint.risk_capacity?.level ?? '')}</span>
                        </div>
                      )}
                      {riskBlueprint.risk_tolerance?.level && (
                        <div>
                          <span className="font-medium">Tolerance: </span>
                          <span className="text-muted-foreground">{String(riskBlueprint.risk_tolerance.level)}</span>
                        </div>
                      )}
                      {typeof (riskBlueprint.score ?? riskBlueprint.risk_score) !== 'undefined' && (
                        <div>
                          <span className="font-medium">Score: </span>
                          <span className="text-muted-foreground">{String(riskBlueprint.score ?? riskBlueprint.risk_score)}</span>
                        </div>
                      )}
                      {typeof riskBlueprint.volatility_target !== 'undefined' && (
                        <div>
                          <span className="font-medium">Volatility target: </span>
                          <span className="text-muted-foreground">{String(riskBlueprint.volatility_target)}%</span>
                        </div>
                      )}
                      {riskBlueprint.recommended_allocation && (
                        <div>
                          <span className="font-medium">Recommended allocation: </span>
                          <span className="text-muted-foreground">{
                            Object.entries(riskBlueprint.recommended_allocation)
                              .map(([k,v]: any) => `${k}: ${(Number(v)*100).toFixed(0)}%`).join(', ')
                          }</span>
                        </div>
                      )}
                      {Array.isArray(riskBlueprint.key_factors) && riskBlueprint.key_factors.length > 0 && (
                        <div>
                          <span className="font-medium">Key factors: </span>
                          <span className="text-muted-foreground">{riskBlueprint.key_factors.join(', ')}</span>
                        </div>
                      )}
                      {Array.isArray(riskBlueprint.guardrails) && riskBlueprint.guardrails.length > 0 && (
                        <div>
                          <span className="font-medium">Guardrails: </span>
                          <span className="text-muted-foreground">{riskBlueprint.guardrails.join(', ')}</span>
                        </div>
                      )}
                      {!riskBlueprint.risk_profile && !(riskBlueprint.capacity || riskBlueprint.risk_capacity) && typeof (riskBlueprint.score ?? riskBlueprint.risk_score) === 'undefined' && (
                        <div className="text-muted-foreground">Risk analysis complete. No detailed blueprint provided.</div>
                      )}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">Risk analysis complete.</div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Interim Results: Security Selection - Show after selection completes */}
            {completedSteps.has('selection') && (
              <Card className="border-0 shadow-lg max-w-3xl mx-auto">
                <CardHeader>
                  <CardTitle>Security Selection</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {selectionSummary ? (
                    <div className="space-y-2 text-sm">
                      {Array.isArray(selectionSummary.top_picks) && selectionSummary.top_picks.length > 0 && (
                        <div>
                          <span className="font-medium">Top picks: </span>
                          <span className="text-muted-foreground">{selectionSummary.top_picks.map((p: any) => (p?.ticker || p?.name || String(p))).join(', ')}</span>
                        </div>
                      )}
                      {/* If backend sends preset security_selections structure */}
                      {selectionSummary.equity_selections && (
                        <div>
                          <span className="font-medium">Equities: </span>
                          <span className="text-muted-foreground">{
                            Object.values(selectionSummary.equity_selections).flat().slice(0, 6).map((p: any) => p?.ticker || p?.name).join(', ')
                          }</span>
                        </div>
                      )}
                      {Array.isArray(selectionSummary.sectors) && selectionSummary.sectors.length > 0 && (
                        <div>
                          <span className="font-medium">Sectors: </span>
                          <span className="text-muted-foreground">{selectionSummary.sectors.join(', ')}</span>
                        </div>
                      )}
                      {selectionSummary.strategy && (
                        <div>
                          <span className="font-medium">Strategy: </span>
                          <span className="text-muted-foreground">{String(selectionSummary.strategy)}</span>
                        </div>
                      )}
                      {!selectionSummary.top_picks && !selectionSummary.sectors && !selectionSummary.strategy && !selectionSummary.equity_selections && (
                        <div className="text-muted-foreground">Selection complete. No detailed summary provided.</div>
                      )}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">Selection complete.</div>
                  )}
                </CardContent>
              </Card>
            )}

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
            {/* Completion Message */}
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-chart-4/10 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle className="w-8 h-8 text-chart-4" />
              </div>
              <h1 className="text-3xl font-bold">Portfolio Generation Complete!</h1>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Your AI-optimized portfolio has been generated and saved. Redirecting to your dashboard...
              </p>
              <div className="flex items-center justify-center space-x-2">
                <Loader2 className="w-5 h-5 animate-spin text-primary" />
                <span className="text-sm text-muted-foreground">Preparing your dashboard</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
