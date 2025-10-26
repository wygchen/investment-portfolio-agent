"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowRight, TrendingUp, Shield, Brain, BarChart3, Users, Zap, AlertTriangle } from "lucide-react"
import Link from "next/link"
import Image from "next/image"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { DisclaimerModal } from "@/components/disclaimer-modal"

// Score Indicator Component for Comparison Table (0-5 scale)
const ScoreIndicator = ({ score, isPortfolioAI }: { score: number; isPortfolioAI: boolean }) => {
  const getScoreColor = (score: number) => {
    if (score >= 4) return 'text-green-600 dark:text-green-500'
    if (score >= 3) return 'text-yellow-600 dark:text-yellow-500'
    if (score >= 2) return 'text-orange-600 dark:text-orange-500'
    if (score >= 1) return 'text-red-600 dark:text-red-500'
    return 'text-muted-foreground'
  }

  const getScoreSymbol = (score: number) => {
    if (score === 5) return '●●●●●'
    if (score === 4) return '●●●●○'
    if (score === 3) return '●●●○○'
    if (score === 2) return '●●○○○'
    if (score === 1) return '●○○○○'
    return '○○○○○'
  }

  return (
    <div className="flex flex-col items-center gap-1">
      <div className={`text-lg font-bold tracking-wider ${getScoreColor(score)}`}>
        {getScoreSymbol(score)}
      </div>
      <div className={`text-xs font-semibold ${isPortfolioAI ? 'text-primary' : 'text-muted-foreground'}`}>
        {score}/5
      </div>
    </div>
  )
}

export default function HomePage() {
  const router = useRouter()
  const [showDisclaimer, setShowDisclaimer] = useState(false)

  const handleStartBuilding = () => {
    // Check if user has already accepted disclaimer
    const hasAcceptedDisclaimer = localStorage.getItem('disclaimerAccepted')
    
    if (hasAcceptedDisclaimer === 'true') {
      // User already accepted, proceed directly
      router.push('/assessment')
    } else {
      // Show disclaimer modal
      setShowDisclaimer(true)
    }
  }

  const handleAcceptDisclaimer = () => {
    // Save acceptance to localStorage
    localStorage.setItem('disclaimerAccepted', 'true')
    localStorage.setItem('disclaimerAcceptedDate', new Date().toISOString())
    
    // Close modal and proceed
    setShowDisclaimer(false)
    router.push('/assessment')
  }

  const handleCancelDisclaimer = () => {
    setShowDisclaimer(false)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Disclaimer Modal */}
      <DisclaimerModal 
        isOpen={showDisclaimer}
        onAccept={handleAcceptDisclaimer}
        onCancel={handleCancelDisclaimer}
      />
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Brain className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-semibold text-foreground">PortfolioAI</span>
            </div>
            <nav className="hidden md:flex items-center space-x-8">
              <Link href="#features" className="text-muted-foreground hover:text-foreground transition-colors">
                Features
              </Link>
              <Link href="#comparison" className="text-muted-foreground hover:text-foreground transition-colors">
                Compare
              </Link>
              <Link href="#how-it-works" className="text-muted-foreground hover:text-foreground transition-colors">
                How it Works
              </Link>
              <Link href="#pricing" className="text-muted-foreground hover:text-foreground transition-colors">
                Pricing
              </Link>
            </nav>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
              <Button size="sm" className="bg-primary hover:bg-primary/90">
                Get Started
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-6">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center space-y-8">
            <Badge variant="secondary" className="px-4 py-2 text-sm">
              <Zap className="w-4 h-4 mr-2" />
              {"Powered by Advanced AI & Machine Learning"}
            </Badge>

            <h1 className="text-5xl md:text-7xl font-bold text-balance leading-tight">
              AI-Powered Investment
              <span className="text-accent block">Portfolio Advisor</span>
            </h1>

            <p className="text-xl text-muted-foreground max-w-3xl mx-auto text-balance leading-relaxed">
              Move beyond traditional portfolio theory with our AI advisor that creates personalized, multi-asset
              portfolios tailored to your risk tolerance, goals, and market conditions.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button 
                size="lg" 
                className="bg-primary hover:bg-primary/90 text-lg px-8 py-6"
                onClick={handleStartBuilding}
              >
                Start Building Your Portfolio
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
              <Button variant="outline" size="lg" className="text-lg px-8 py-6 bg-transparent">
                View Live Demo
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-4">
              Advisory service only - We do not execute trades
            </p>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-20 px-6 bg-muted/30">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-4xl font-bold text-balance">Beyond Modern Portfolio Theory</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-balance">
              Our AI addresses the fundamental limitations of traditional investment strategies with dynamic,
              data-driven portfolio optimization.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <Card className="border-0 shadow-lg bg-card">
              <CardContent className="p-8 space-y-4">
                <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center">
                  <Brain className="w-6 h-6 text-accent" />
                </div>
                <h3 className="text-xl font-semibold">Hyper-Personalization</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Move beyond simple risk questionnaires. Our AI analyzes your complete financial profile, behavioral
                  patterns, and life circumstances to create truly personalized portfolios.
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg bg-card">
              <CardContent className="p-8 space-y-4">
                <div className="w-12 h-12 bg-chart-2/10 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-chart-2" />
                </div>
                <h3 className="text-xl font-semibold">Dynamic Rebalancing</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Real-time portfolio optimization using reinforcement learning. Our AI continuously adapts to changing
                  market conditions instead of relying on static, historical models.
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg bg-card">
              <CardContent className="p-8 space-y-4">
                <div className="w-12 h-12 bg-chart-4/10 rounded-lg flex items-center justify-center">
                  <Shield className="w-6 h-6 text-chart-4" />
                </div>
                <h3 className="text-xl font-semibold">Predictive Risk Management</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Advanced stress testing and anomaly detection. Our models simulate market shocks and geopolitical
                  events to ensure portfolio resilience across all conditions.
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg bg-card">
              <CardContent className="p-8 space-y-4">
                <div className="w-12 h-12 bg-chart-3/10 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-6 h-6 text-chart-3" />
                </div>
                <h3 className="text-xl font-semibold">Alternative Data Integration</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Leverage sentiment analysis, satellite imagery, and real-time market signals. Our AI processes
                  unstructured data to identify opportunities before they become mainstream.
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg bg-card">
              <CardContent className="p-8 space-y-4">
                <div className="w-12 h-12 bg-chart-5/10 rounded-lg flex items-center justify-center">
                  <Users className="w-6 h-6 text-chart-5" />
                </div>
                <h3 className="text-xl font-semibold">Multi-Asset Universe</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Access traditional and alternative assets including equities, bonds, REITs, commodities, and
                  cryptocurrencies through a single, intelligent platform.
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg bg-card">
              <CardContent className="p-8 space-y-4">
                <div className="w-12 h-12 bg-destructive/10 rounded-lg flex items-center justify-center">
                  <Zap className="w-6 h-6 text-destructive" />
                </div>
                <h3 className="text-xl font-semibold">Explainable AI</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Transparent decision-making with clear explanations for every recommendation. Understand exactly why
                  our AI suggests specific allocations and adjustments.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* How it Works Section */}
      <section id="how-it-works" className="py-20 px-6 bg-background">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-4xl font-bold text-balance">How It Works</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-balance">
              Our AI-powered platform guides you through a simple 4-step process to build your personalized investment portfolio.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-12">
            {/* Step 1 */}
            <Card className="border-2 border-primary/20 shadow-lg bg-card hover:border-primary/40 transition-colors">
              <CardContent className="p-8">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xl font-bold flex-shrink-0">
                    1
                  </div>
                  <div className="space-y-3">
                    <h3 className="text-2xl font-semibold text-foreground">Complete Risk Assessment</h3>
                    <p className="text-muted-foreground leading-relaxed">
                      Answer a comprehensive questionnaire about your financial goals, time horizon, risk tolerance, 
                      income, savings, and investment preferences. Our AI analyzes your unique situation to understand 
                      your complete financial profile.
                    </p>
                    <div className="flex flex-wrap gap-2 pt-2">
                      <Badge variant="secondary" className="text-xs">Goals & Timeline</Badge>
                      <Badge variant="secondary" className="text-xs">Risk Tolerance</Badge>
                      <Badge variant="secondary" className="text-xs">Financial Situation</Badge>
                      <Badge variant="secondary" className="text-xs">ESG Preferences</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Step 2 */}
            <Card className="border-2 border-chart-2/20 shadow-lg bg-card hover:border-chart-2/40 transition-colors">
              <CardContent className="p-8">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-chart-2 text-white rounded-full flex items-center justify-center text-xl font-bold flex-shrink-0">
                    2
                  </div>
                  <div className="space-y-3">
                    <h3 className="text-2xl font-semibold text-foreground">AI Analysis & Portfolio Generation</h3>
                    <p className="text-muted-foreground leading-relaxed">
                      Our advanced AI agents work together to analyze market conditions, identify suitable investments, 
                      and construct an optimized portfolio tailored to your profile. The system considers thousands of 
                      assets across multiple markets and asset classes.
                    </p>
                    <div className="flex flex-wrap gap-2 pt-2">
                      <Badge variant="secondary" className="text-xs">Market Analysis</Badge>
                      <Badge variant="secondary" className="text-xs">Asset Selection</Badge>
                      <Badge variant="secondary" className="text-xs">Portfolio Optimization</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Step 3 */}
            <Card className="border-2 border-chart-4/20 shadow-lg bg-card hover:border-chart-4/40 transition-colors">
              <CardContent className="p-8">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-chart-4 text-white rounded-full flex items-center justify-center text-xl font-bold flex-shrink-0">
                    3
                  </div>
                  <div className="space-y-3">
                    <h3 className="text-2xl font-semibold text-foreground">Review Recommendations</h3>
                    <p className="text-muted-foreground leading-relaxed">
                      Get detailed insights into your personalized portfolio, including asset allocation, individual 
                      investment recommendations, risk metrics, and expected performance. Each recommendation comes with 
                      clear explanations of why it fits your profile.
                    </p>
                    <div className="flex flex-wrap gap-2 pt-2">
                      <Badge variant="secondary" className="text-xs">Asset Breakdown</Badge>
                      <Badge variant="secondary" className="text-xs">Risk Metrics</Badge>
                      <Badge variant="secondary" className="text-xs">Performance Projections</Badge>
                      <Badge variant="secondary" className="text-xs">AI Explanations</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Step 4 */}
            <Card className="border-2 border-accent/20 shadow-lg bg-card hover:border-accent/40 transition-colors">
              <CardContent className="p-8">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-accent text-accent-foreground rounded-full flex items-center justify-center text-xl font-bold flex-shrink-0">
                    4
                  </div>
                  <div className="space-y-3">
                    <h3 className="text-2xl font-semibold text-foreground">Execute Your Strategy</h3>
                    <p className="text-muted-foreground leading-relaxed">
                      Download your portfolio recommendations and execute trades through your own brokerage account. 
                      We provide clear instructions and ongoing monitoring, but you maintain full control over your 
                      investments at all times.
                    </p>
                    <div className="flex flex-wrap gap-2 pt-2">
                      <Badge variant="secondary" className="text-xs">Export Portfolio</Badge>
                      <Badge variant="secondary" className="text-xs">Trade Instructions</Badge>
                      <Badge variant="secondary" className="text-xs">Ongoing Monitoring</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Important Notice */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 dark:border-yellow-600 rounded-r-lg p-6">
            <div className="flex items-start space-x-3">
              <Shield className="w-6 h-6 text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-semibold text-foreground mb-2">You're Always In Control</h4>
                <p className="text-sm text-muted-foreground">
                  PortfolioAI provides recommendations and insights, but <strong>never executes trades on your behalf</strong>. 
                  You review all suggestions, make your own decisions, and execute trades through your preferred brokerage. 
                  We're here to guide and inform, not to manage your money.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

{/* Competitor Comparison Section - Surfshark-Style Design */}
<section id="comparison" className="py-20 px-6 bg-muted/30">
  <div className="container mx-auto max-w-7xl">
    <div className="text-center space-y-4 mb-16">
      <Badge variant="secondary" className="px-4 py-2 text-sm mb-4">
        <BarChart3 className="w-4 h-4 mr-2" />
        Market Comparison
      </Badge>
      <h2 className="text-4xl font-bold text-balance">
        See How We Compare to Other Investment Platforms
      </h2>
      <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-balance">
        Compare key AI features across top investment platforms.
      </p>
    </div>

    {/* Comparison Table - Desktop */}
    <div className="hidden lg:block overflow-x-auto">
      <div className="min-w-[1000px]">
        {/* Header Row */}
        <div className="grid grid-cols-6 gap-4 mb-6">
          <div className="col-span-1"></div>
          
          {/* PortfolioAI Column Header */}
          <div className="col-span-1">
            <Card className="border-2 border-primary shadow-xl bg-gradient-to-br from-primary via-primary to-primary/90 text-primary-foreground">
              <CardContent className="p-8 text-center">
                <div className="w-14 h-14 bg-primary-foreground/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <Brain className="w-8 h-8 text-primary-foreground" />
                </div>
                <h3 className="font-bold text-xl text-primary-foreground mb-2">PortfolioAI</h3>
                <Badge variant="secondary" className="bg-primary-foreground text-primary font-semibold">Best AI Features</Badge>
              </CardContent>
            </Card>
          </div>

          {/* Betterment */}
          <div className="col-span-1">
            <Card className="border border-border bg-card">
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-3 overflow-hidden">
                  <Image src="/betterment-logo.png" alt="Betterment" width={48} height={48} className="object-contain" />
                </div>
                <h3 className="font-semibold text-base text-foreground">Betterment</h3>
                <p className="text-xs text-muted-foreground mt-1">Robo-Advisor</p>
              </CardContent>
            </Card>
          </div>

          {/* Wealthfront */}
          <div className="col-span-1">
            <Card className="border border-border bg-card">
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-3 overflow-hidden">
                  <Image src="/wealthfront-logo.png" alt="Wealthfront" width={48} height={48} className="object-contain" />
                </div>
                <h3 className="font-semibold text-base text-foreground">Wealthfront</h3>
                <p className="text-xs text-muted-foreground mt-1">Robo-Advisor</p>
              </CardContent>
            </Card>
          </div>

          {/* M1 Finance */}
          <div className="col-span-1">
            <Card className="border border-border bg-card">
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-3 overflow-hidden">
                  <Image src="/m1-logo.png" alt="M1 Finance" width={48} height={48} className="object-contain" />
                </div>
                <h3 className="font-semibold text-base text-foreground">M1 Finance</h3>
                <p className="text-xs text-muted-foreground mt-1">Hybrid Platform</p>
              </CardContent>
            </Card>
          </div>

          {/* Empower */}
          <div className="col-span-1">
            <Card className="border border-border bg-card">
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-3 overflow-hidden">
                  <Image src="/empower-logo.png" alt="Empower" width={48} height={48} className="object-contain" />
                </div>
                <h3 className="font-semibold text-base text-foreground">Empower</h3>
                <p className="text-xs text-muted-foreground mt-1">Wealth Management</p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Feature Rows with Surfshark-style highlighting */}
        <div className="space-y-2">
          {[
            { 
              name: '24/7 AI Chatbot', 
                scores: [4, 0, 0, 0, 2],
                details: ['LLM powered assistant', 'Email support only', 'Email support only', 'Not available', 'Human advisor access']
              },
              { 
                name: 'AI News Analysis', 
                scores: [5, 2, 2, 0, 3],
                details: ['Multi-source real-time AI', 'Basic market alerts', 'Basic market alerts', 'Not available', 'Market updates']
              },
              { 
                name: 'Sentiment Analysis', 
                scores: [4, 1, 2, 0, 1],
                details: ['Advanced social + news AI', 'Basic market indicators', 'Basic sentiment metrics', 'Not available', 'Basic market sentiment']
              },
              { 
                name: 'Personalization', 
                scores: [5, 4, 4, 3, 4],
                details: ['100+ personalization factors', 'Goal-based planning', 'Advanced planning tools', 'Pie-based portfolios', 'Advisor access']
              },
              { 
                name: 'Rebalancing', 
                scores: [4, 4, 5, 5, 4],
                details: ['Real-time AI-driven', 'Automatic rebalancing', 'Daily rebalancing', 'Dynamic rebalancing', 'Automatic rebalancing']
              },
              { 
                name: 'Explainability', 
                scores: [5, 3, 3, 0, 2],
                details: ['Full AI transparency', 'Partial explanations', 'Partial explanations', 'Not available', 'Via advisor only']
              }
            ].map((feature, idx) => (
              <div key={idx} className="relative grid grid-cols-6 gap-4 items-center py-4 px-4 bg-card rounded-lg border border-border z-10">
                <div className="col-span-1 font-medium text-foreground text-sm">
                  {feature.name}
                </div>
                {feature.scores.map((score, scoreIdx) => (
                  <div 
                    key={scoreIdx} 
                    className={`col-span-1 text-center py-2 rounded-lg group relative cursor-pointer transition-all ${
                      scoreIdx === 0 ? 'bg-primary/5 border-2 border-primary/30' : ''
                    }`}
                  >
                    <ScoreIndicator score={score} isPortfolioAI={scoreIdx === 0} />
                    {/* Hover Tooltip */}
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-3 bg-popover border border-border rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 pointer-events-none">
                      <p className="text-xs text-popover-foreground font-medium text-center">
                        {feature.details[scoreIdx]}
                      </p>
                      <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 w-2 h-2 bg-popover border-r border-b border-border rotate-45"></div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
            
            {/* CTA Button Row */}
            <div className="relative grid grid-cols-6 gap-4 items-center py-6 px-4 z-10">
              <div className="col-span-1"></div>
              <div className="col-span-1 text-center">
                <Button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold" onClick={handleStartBuilding}>
                  Get Started
                </Button>
              </div>
              <div className="col-span-4"></div>
            </div>
          </div>
      </div>
    </div>

    {/* Mobile View - Card Style with Scores */}
    <div className="lg:hidden space-y-4">
      {[
        { 
          name: 'PortfolioAI', 
          recommended: true,
          scores: { chatbot: 4, news: 5, personalization: 5, sentiment: 4, rebalancing: 4, explainability: 5 },
          icon: <Brain className="w-5 h-5" />
        },
        { 
          name: 'Betterment',
          scores: { chatbot: 0, news: 2, personalization: 4, sentiment: 1, rebalancing: 4, explainability: 3 },
          icon: <span className="font-bold text-blue-600 dark:text-blue-400">B</span>
        },
        { 
          name: 'Wealthfront',
          scores: { chatbot: 0, news: 2, personalization: 4, sentiment: 2, rebalancing: 5, explainability: 3 },
          icon: <span className="font-bold text-purple-600 dark:text-purple-400">W</span>
        },
        { 
          name: 'M1 Finance',
          scores: { chatbot: 0, news: 0, personalization: 3, sentiment: 0, rebalancing: 5, explainability: 0 },
          icon: <span className="font-bold text-red-600 dark:text-red-400">M1</span>
        },
        { 
          name: 'Empower',
          scores: { chatbot: 2, news: 3, personalization: 4, sentiment: 1, rebalancing: 4, explainability: 2 },
          icon: <span className="font-bold text-green-600 dark:text-green-400">E</span>
        }
      ].map((platform) => (
        <Card key={platform.name} className={platform.recommended ? 'border-2 border-primary shadow-2xl bg-gradient-to-br from-primary/5 to-primary/10' : 'border border-border'}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${platform.recommended ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                  {platform.icon}
                </div>
                <h3 className="font-bold text-lg">{platform.name}</h3>
              </div>
              {platform.recommended && <Badge className="bg-primary">Best AI</Badge>}
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: '24/7 Chatbot', score: platform.scores.chatbot },
                { label: 'News Analysis', score: platform.scores.news },
                { label: 'Sentiment AI', score: platform.scores.sentiment },
                { label: 'Personalization', score: platform.scores.personalization },
                { label: 'Rebalancing', score: platform.scores.rebalancing },
                { label: 'Explainability', score: platform.scores.explainability }
              ].map((item, idx) => (
                <div key={idx} className={`flex flex-col gap-1 p-3 rounded-lg ${platform.recommended ? 'bg-primary/10' : 'bg-muted/50'}`}>
                  <span className="text-xs text-muted-foreground font-medium">{item.label}</span>
                  <div className="flex items-center gap-2">
                    <div className={`text-xs font-bold ${platform.recommended && item.score >= 4 ? 'text-primary' : item.score >= 5 ? 'text-green-600 dark:text-green-400' : item.score >= 4 ? 'text-green-600 dark:text-green-500' : item.score >= 3 ? 'text-yellow-600 dark:text-yellow-500' : item.score >= 2 ? 'text-orange-600 dark:text-orange-500' : item.score >= 1 ? 'text-red-600 dark:text-red-500' : 'text-muted-foreground'}`}>
                      {item.score === 5 ? '●●●●●' : item.score === 4 ? '●●●●○' : item.score === 3 ? '●●●○○' : item.score === 2 ? '●●○○○' : item.score === 1 ? '●○○○○' : '○○○○○'}
                    </div>
                    <span className="text-xs font-semibold text-muted-foreground">{item.score}/5</span>
                  </div>
                </div>
              ))}
            </div>
            
            {platform.recommended && (
              <Button className="w-full mt-6 bg-primary hover:bg-primary/90" onClick={handleStartBuilding}>
                Get Started
              </Button>
            )}
          </CardContent>
        </Card>
      ))}
    </div>

    {/* Disclaimer Note */}
    <div className="mt-8 text-center">
      <p className="text-sm text-muted-foreground">
        * Comparison based on publicly available information as of October 2025. Features subject to change. 
        Always verify current offerings on provider websites.
      </p>
    </div>
  </div>
</section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="container mx-auto max-w-4xl">
          <Card className="border-0 shadow-xl bg-primary text-primary-foreground">
            <CardContent className="p-12 text-center space-y-6">
              <h2 className="text-3xl md:text-4xl font-bold text-balance">
                Ready to Transform Your Investment Strategy?
              </h2>
              <p className="text-xl opacity-90 max-w-2xl mx-auto text-balance leading-relaxed">
                Join thousands of investors who have moved beyond traditional portfolio theory to AI-driven,
                personalized wealth management.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
                <Button 
                  size="lg" 
                  variant="secondary" 
                  className="text-lg px-8 py-6"
                  onClick={handleStartBuilding}
                >
                  Start Your Risk Assessment
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  className="text-lg px-8 py-6 border-primary-foreground/20 text-primary-foreground hover:bg-primary-foreground/10 bg-transparent"
                >
                  Schedule a Demo
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-muted/30 py-12 px-6">
        <div className="container mx-auto max-w-6xl">
          {/* Disclaimer Section */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 dark:border-yellow-600 rounded-r-lg p-6 mb-8">
            <h4 className="font-semibold text-foreground mb-3 flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2 text-yellow-600 dark:text-yellow-500" />
              Important Disclaimer
            </h4>
            <div className="text-sm text-muted-foreground space-y-2">
              <p>
                <strong>PortfolioAI is an investment advisory and educational platform only.</strong> We do not execute trades, 
                manage funds, or provide personalized financial advice. All investment recommendations are 
                suggestions based on AI analysis and should not be considered as financial advice.
              </p>
              <p>
                <strong className="text-foreground">We do not:</strong> Execute trades • Access your brokerage accounts • Manage your investments • 
                Guarantee returns • Provide tax or legal advice
              </p>
              <p>
                By using this platform, you acknowledge that all investment decisions are made at your own risk. 
                Please consult with a licensed financial advisor before making any investment decisions. 
                Past performance does not guarantee future results.
              </p>
            </div>
          </div>

          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 bg-primary rounded-md flex items-center justify-center">
                <Brain className="w-4 h-4 text-primary-foreground" />
              </div>
              <span className="font-semibold text-foreground">PortfolioAI</span>
            </div>
            <div className="flex items-center space-x-6 text-sm text-muted-foreground">
              <Link href="#" className="hover:text-foreground transition-colors">
                Privacy Policy
              </Link>
              <Link href="#" className="hover:text-foreground transition-colors">
                Terms of Service
              </Link>
              <Link href="#" className="hover:text-foreground transition-colors">
                Contact
              </Link>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-border text-center text-sm text-muted-foreground">
            <p>© 2025 PortfolioAI. Built with advanced AI and machine learning technologies.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
