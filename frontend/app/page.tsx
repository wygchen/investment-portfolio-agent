"use client"
import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowRight, TrendingUp, Shield, Brain, BarChart3, Users, Zap } from "lucide-react"
import Link from "next/link"

export default function HomePage() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return <div className="min-h-screen bg-background" />
  }
  return (
    <div className="min-h-screen bg-background">
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
              <Link href="/assessment">
                <Button size="lg" className="bg-primary hover:bg-primary/90 text-lg px-8 py-6">
                  Start Building Your Portfolio
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Button variant="outline" size="lg" className="text-lg px-8 py-6 bg-transparent">
                View Live Demo
              </Button>
            </div>
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
                <Link href="/assessment">
                  <Button size="lg" variant="secondary" className="text-lg px-8 py-6">
                    Start Your Risk Assessment
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
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
