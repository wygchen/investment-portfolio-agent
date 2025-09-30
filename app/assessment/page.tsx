"use client"

import React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Checkbox } from "@/components/ui/checkbox"
import { Slider } from "@/components/ui/slider"
import { ArrowLeft, ArrowRight, Brain, Target, DollarSign, TrendingUp, Shield } from "lucide-react"
import Link from "next/link"

interface AssessmentData {
  // Personal Information
  age: number
  income: number
  netWorth: number
  dependents: number

  // Financial Goals
  primaryGoal: string
  timeHorizon: number
  targetAmount: number
  monthlyContribution: number

  // Risk Profile
  riskTolerance: number
  riskCapacity: string
  previousExperience: string[]
  marketReaction: string

  // Behavioral Factors
  investmentStyle: string
  rebalancingFrequency: string
  esgPreferences: boolean

  // Additional Context
  specialCircumstances: string
}

const steps = [
  { id: 1, title: "Personal Profile", icon: Target },
  { id: 2, title: "Financial Goals", icon: DollarSign },
  { id: 3, title: "Risk Assessment", icon: Shield },
  { id: 4, title: "Investment Preferences", icon: TrendingUp },
  { id: 5, title: "Final Review", icon: Brain },
]

export default function AssessmentPage() {
  const [currentStep, setCurrentStep] = useState(1)
  const [assessmentData, setAssessmentData] = useState<Partial<AssessmentData>>({})

  const updateData = (field: string, value: any) => {
    setAssessmentData((prev) => ({ ...prev, [field]: value }))
  }

  const nextStep = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const progress = (currentStep / steps.length) * 100

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Brain className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-semibold text-foreground">PortfolioAI</span>
            </Link>
            <Badge variant="secondary" className="px-3 py-1">
              AI Risk Assessment
            </Badge>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Progress Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold">Investment Profile Assessment</h1>
            <span className="text-sm text-muted-foreground">
              Step {currentStep} of {steps.length}
            </span>
          </div>
          <Progress value={progress} className="h-2 mb-6" />

          {/* Step Indicators */}
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const Icon = step.icon
              const isActive = currentStep === step.id
              const isCompleted = currentStep > step.id

              return (
                <div key={step.id} className="flex flex-col items-center space-y-2">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors ${
                      isActive
                        ? "bg-primary border-primary text-primary-foreground"
                        : isCompleted
                          ? "bg-accent border-accent text-accent-foreground"
                          : "border-border text-muted-foreground"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <span
                    className={`text-xs font-medium ${
                      isActive ? "text-primary" : isCompleted ? "text-accent" : "text-muted-foreground"
                    }`}
                  >
                    {step.title}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Step Content */}
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              {React.createElement(steps[currentStep - 1].icon, { className: "w-6 h-6 text-primary" })}
              <span>{steps[currentStep - 1].title}</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {currentStep === 1 && <PersonalProfileStep data={assessmentData} updateData={updateData} />}
            {currentStep === 2 && <FinancialGoalsStep data={assessmentData} updateData={updateData} />}
            {currentStep === 3 && <RiskAssessmentStep data={assessmentData} updateData={updateData} />}
            {currentStep === 4 && <InvestmentPreferencesStep data={assessmentData} updateData={updateData} />}
            {currentStep === 5 && <FinalReviewStep data={assessmentData} />}
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <Button
            variant="outline"
            onClick={prevStep}
            disabled={currentStep === 1}
            className="flex items-center space-x-2 bg-transparent"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Previous</span>
          </Button>

          {currentStep < steps.length ? (
            <Button onClick={nextStep} className="flex items-center space-x-2">
              <span>Continue</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          ) : (
            <Link href="/generate">
              <Button className="flex items-center space-x-2 bg-accent hover:bg-accent/90">
                <Brain className="w-4 h-4" />
                <span>Generate Portfolio</span>
              </Button>
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}

function PersonalProfileStep({
  data,
  updateData,
}: { data: Partial<AssessmentData>; updateData: (field: string, value: any) => void }) {
  return (
    <div className="space-y-6">
      <p className="text-muted-foreground">
        Help us understand your current financial situation to create a personalized investment strategy.
      </p>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="age">Age</Label>
          <Input
            id="age"
            type="number"
            placeholder="35"
            value={data.age || ""}
            onChange={(e) => updateData("age", Number.parseInt(e.target.value))}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="dependents">Number of Dependents</Label>
          <Input
            id="dependents"
            type="number"
            placeholder="2"
            value={data.dependents || ""}
            onChange={(e) => updateData("dependents", Number.parseInt(e.target.value))}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="income">Annual Income ($)</Label>
          <Input
            id="income"
            type="number"
            placeholder="75000"
            value={data.income || ""}
            onChange={(e) => updateData("income", Number.parseInt(e.target.value))}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="netWorth">Current Net Worth ($)</Label>
          <Input
            id="netWorth"
            type="number"
            placeholder="150000"
            value={data.netWorth || ""}
            onChange={(e) => updateData("netWorth", Number.parseInt(e.target.value))}
          />
        </div>
      </div>
    </div>
  )
}

function FinancialGoalsStep({
  data,
  updateData,
}: { data: Partial<AssessmentData>; updateData: (field: string, value: any) => void }) {
  return (
    <div className="space-y-6">
      <p className="text-muted-foreground">
        Define your investment objectives and timeline to align your portfolio with your life goals.
      </p>

      <div className="space-y-4">
        <Label>Primary Investment Goal</Label>
        <RadioGroup value={data.primaryGoal} onValueChange={(value) => updateData("primaryGoal", value)}>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="retirement" id="retirement" />
            <Label htmlFor="retirement">Retirement Planning</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="wealth-building" id="wealth-building" />
            <Label htmlFor="wealth-building">Long-term Wealth Building</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="major-purchase" id="major-purchase" />
            <Label htmlFor="major-purchase">Major Purchase (Home, Education)</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="income-generation" id="income-generation" />
            <Label htmlFor="income-generation">Income Generation</Label>
          </div>
        </RadioGroup>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label>Investment Time Horizon (Years)</Label>
          <div className="px-3">
            <Slider
              value={[data.timeHorizon || 10]}
              onValueChange={(value) => updateData("timeHorizon", value[0])}
              max={40}
              min={1}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-sm text-muted-foreground mt-1">
              <span>1 year</span>
              <span className="font-medium">{data.timeHorizon || 10} years</span>
              <span>40+ years</span>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="monthlyContribution">Monthly Investment Amount ($)</Label>
          <Input
            id="monthlyContribution"
            type="number"
            placeholder="1000"
            value={data.monthlyContribution || ""}
            onChange={(e) => updateData("monthlyContribution", Number.parseInt(e.target.value))}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="targetAmount">Target Portfolio Value ($)</Label>
        <Input
          id="targetAmount"
          type="number"
          placeholder="1000000"
          value={data.targetAmount || ""}
          onChange={(e) => updateData("targetAmount", Number.parseInt(e.target.value))}
        />
      </div>
    </div>
  )
}

function RiskAssessmentStep({
  data,
  updateData,
}: { data: Partial<AssessmentData>; updateData: (field: string, value: any) => void }) {
  return (
    <div className="space-y-6">
      <p className="text-muted-foreground">
        We assess both your risk tolerance (comfort with uncertainty) and risk capacity (financial ability to handle
        losses).
      </p>

      <div className="space-y-4">
        <Label>Risk Tolerance Level</Label>
        <div className="px-3">
          <Slider
            value={[data.riskTolerance || 5]}
            onValueChange={(value) => updateData("riskTolerance", value[0])}
            max={10}
            min={1}
            step={1}
            className="w-full"
          />
          <div className="flex justify-between text-sm text-muted-foreground mt-1">
            <span>Conservative</span>
            <span className="font-medium">Level {data.riskTolerance || 5}</span>
            <span>Aggressive</span>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <Label>Financial Risk Capacity</Label>
        <RadioGroup value={data.riskCapacity} onValueChange={(value) => updateData("riskCapacity", value)}>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="low" id="low-capacity" />
            <Label htmlFor="low-capacity">Low - Cannot afford significant losses</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="moderate" id="moderate-capacity" />
            <Label htmlFor="moderate-capacity">Moderate - Can handle some volatility</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="high" id="high-capacity" />
            <Label htmlFor="high-capacity">High - Can withstand substantial losses</Label>
          </div>
        </RadioGroup>
      </div>

      <div className="space-y-4">
        <Label>Previous Investment Experience (Select all that apply)</Label>
        <div className="grid grid-cols-2 gap-4">
          {["Stocks", "Bonds", "ETFs", "Mutual Funds", "Real Estate", "Cryptocurrencies", "Options", "Commodities"].map(
            (option) => (
              <div key={option} className="flex items-center space-x-2">
                <Checkbox
                  id={option}
                  checked={data.previousExperience?.includes(option) || false}
                  onCheckedChange={(checked) => {
                    const current = data.previousExperience || []
                    if (checked) {
                      updateData("previousExperience", [...current, option])
                    } else {
                      updateData(
                        "previousExperience",
                        current.filter((item) => item !== option),
                      )
                    }
                  }}
                />
                <Label htmlFor={option}>{option}</Label>
              </div>
            ),
          )}
        </div>
      </div>

      <div className="space-y-4">
        <Label>Market Downturn Reaction</Label>
        <RadioGroup value={data.marketReaction} onValueChange={(value) => updateData("marketReaction", value)}>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="sell-immediately" id="sell-immediately" />
            <Label htmlFor="sell-immediately">Sell immediately to avoid further losses</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="wait-and-see" id="wait-and-see" />
            <Label htmlFor="wait-and-see">Wait and see, might sell if it gets worse</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="hold-steady" id="hold-steady" />
            <Label htmlFor="hold-steady">Hold steady and stick to the plan</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="buy-more" id="buy-more" />
            <Label htmlFor="buy-more">Buy more at lower prices</Label>
          </div>
        </RadioGroup>
      </div>
    </div>
  )
}

function InvestmentPreferencesStep({
  data,
  updateData,
}: { data: Partial<AssessmentData>; updateData: (field: string, value: any) => void }) {
  return (
    <div className="space-y-6">
      <p className="text-muted-foreground">Customize your investment approach based on your preferences and values.</p>

      <div className="space-y-4">
        <Label>Investment Style Preference</Label>
        <RadioGroup value={data.investmentStyle} onValueChange={(value) => updateData("investmentStyle", value)}>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="passive" id="passive" />
            <Label htmlFor="passive">Passive - Low-cost index funds and ETFs</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="active" id="active" />
            <Label htmlFor="active">Active - AI-driven stock selection and timing</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="hybrid" id="hybrid" />
            <Label htmlFor="hybrid">Hybrid - Mix of passive and active strategies</Label>
          </div>
        </RadioGroup>
      </div>

      <div className="space-y-4">
        <Label>Portfolio Rebalancing Frequency</Label>
        <RadioGroup
          value={data.rebalancingFrequency}
          onValueChange={(value) => updateData("rebalancingFrequency", value)}
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="monthly" id="monthly" />
            <Label htmlFor="monthly">Monthly - Maximum responsiveness</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="quarterly" id="quarterly" />
            <Label htmlFor="quarterly">Quarterly - Balanced approach</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="annually" id="annually" />
            <Label htmlFor="annually">Annually - Minimal trading costs</Label>
          </div>
        </RadioGroup>
      </div>

      <div className="flex items-center space-x-2">
        <Checkbox
          id="esg"
          checked={data.esgPreferences || false}
          onCheckedChange={(checked) => updateData("esgPreferences", checked)}
        />
        <Label htmlFor="esg">Include ESG (Environmental, Social, Governance) investments</Label>
      </div>

      <div className="space-y-2">
        <Label htmlFor="specialCircumstances">Special Circumstances or Preferences</Label>
        <Textarea
          id="specialCircumstances"
          placeholder="Any additional information that might affect your investment strategy..."
          value={data.specialCircumstances || ""}
          onChange={(e) => updateData("specialCircumstances", e.target.value)}
          rows={4}
        />
      </div>
    </div>
  )
}

function FinalReviewStep({ data }: { data: Partial<AssessmentData> }) {
  return (
    <div className="space-y-6">
      <p className="text-muted-foreground">
        Review your profile before we generate your personalized AI-driven portfolio recommendation.
      </p>

      <div className="grid md:grid-cols-2 gap-6">
        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-lg">Personal Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Age:</span>
              <span>{data.age} years</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Annual Income:</span>
              <span>${data.income?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Net Worth:</span>
              <span>${data.netWorth?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Dependents:</span>
              <span>{data.dependents}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-lg">Investment Goals</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Primary Goal:</span>
              <span className="capitalize">{data.primaryGoal?.replace("-", " ")}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Time Horizon:</span>
              <span>{data.timeHorizon} years</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Monthly Investment:</span>
              <span>${data.monthlyContribution?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Target Amount:</span>
              <span>${data.targetAmount?.toLocaleString()}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-lg">Risk Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Risk Tolerance:</span>
              <span>Level {data.riskTolerance}/10</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Risk Capacity:</span>
              <span className="capitalize">{data.riskCapacity}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Experience:</span>
              <span>{data.previousExperience?.length || 0} asset classes</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-lg">Preferences</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Investment Style:</span>
              <span className="capitalize">{data.investmentStyle}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Rebalancing:</span>
              <span className="capitalize">{data.rebalancingFrequency}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">ESG Focus:</span>
              <span>{data.esgPreferences ? "Yes" : "No"}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="bg-accent/10 border border-accent/20 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-2">
          <Brain className="w-5 h-5 text-accent" />
          <span className="font-semibold text-accent">AI Analysis Ready</span>
        </div>
        <p className="text-sm text-muted-foreground">
          Our AI will analyze your complete profile using advanced machine learning algorithms to create a personalized
          portfolio that balances your risk tolerance, capacity, and investment goals.
        </p>
      </div>
    </div>
  )
}
