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
import { ArrowLeft, ArrowRight, Brain, Target, DollarSign, TrendingUp, Shield, Loader2 } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { apiClient, type AssessmentData as APIAssessmentData, handleAPIError } from "@/lib/api"
import { useAssessment, useAPICall } from "@/lib/hooks"

// Interface matching the backend API
interface AssessmentData {
  // Personal Information
  age: number
  income: number
  net_worth: number
  dependents: number

  // Financial Goals
  primary_goal: string
  time_horizon: number
  target_amount: number
  monthly_contribution: number

  // Risk Profile
  risk_tolerance: number
  risk_capacity: string
  previous_experience: string[]
  market_reaction: string

  // Behavioral Factors
  investment_style: string
  rebalancing_frequency: string
  esg_preferences: boolean

  // Additional Context
  special_circumstances?: string
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
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  
  const router = useRouter()
  const { saveAssessmentData, saveUserId, isHydrated } = useAssessment()
  const { execute: submitAssessment } = useAPICall<{ user_id: string; status: string; message: string; assessment_id: string }>()

  // Don't render until hydrated to avoid hydration mismatches
  if (!isHydrated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    )
  }

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

  const handleSubmitAssessment = async () => {
    setIsSubmitting(true)
    setSubmitError(null)
    
    try {
      // Validate required fields
      const requiredFields = [
        'age', 'income', 'net_worth', 'dependents', 'primary_goal', 
        'time_horizon', 'target_amount', 'monthly_contribution', 
        'risk_tolerance', 'risk_capacity', 'previous_experience', 
        'market_reaction', 'investment_style', 'rebalancing_frequency'
      ]
      
      const missingFields = requiredFields.filter(field => 
        assessmentData[field as keyof AssessmentData] === undefined || 
        assessmentData[field as keyof AssessmentData] === null ||
        (Array.isArray(assessmentData[field as keyof AssessmentData]) && 
         (assessmentData[field as keyof AssessmentData] as string[]).length === 0)
      )
      
      if (missingFields.length > 0) {
        setSubmitError(`Please complete all required fields: ${missingFields.join(', ')}`)
        return
      }
      
      // Submit to API
      const result = await submitAssessment(() => 
        apiClient.submitAssessment(assessmentData as APIAssessmentData)
      )
      
      // Save data locally and redirect
      saveAssessmentData(assessmentData)
      saveUserId(result.user_id)
      
      // Redirect to portfolio generation
      router.push('/generate')
      
    } catch (error) {
      const errorMessage = handleAPIError(error)
      setSubmitError(errorMessage)
    } finally {
      setIsSubmitting(false)
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
            <Button 
              onClick={handleSubmitAssessment}
              disabled={isSubmitting}
              className="flex items-center space-x-2 bg-accent hover:bg-accent/90"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <Brain className="w-4 h-4" />
                  <span>Generate Portfolio</span>
                </>
              )}
            </Button>
          )}
        </div>
        
        {/* Error Message */}
        {submitError && (
          <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
            <p className="text-destructive text-sm">{submitError}</p>
          </div>
        )}
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
          <Label htmlFor="net_worth">Current Net Worth ($)</Label>
          <Input
            id="net_worth"
            type="number"
            placeholder="150000"
            value={data.net_worth || ""}
            onChange={(e) => updateData("net_worth", Number.parseInt(e.target.value))}
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
        <RadioGroup value={data.primary_goal} onValueChange={(value) => updateData("primary_goal", value)}>
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
              value={[data.time_horizon || 10]}
              onValueChange={(value) => updateData("time_horizon", value[0])}
              max={40}
              min={1}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-sm text-muted-foreground mt-1">
              <span>1 year</span>
              <span className="font-medium">{data.time_horizon || 10} years</span>
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
            value={data.monthly_contribution || ""}
            onChange={(e) => updateData("monthly_contribution", Number.parseInt(e.target.value))}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="target_amount">Target Portfolio Value ($)</Label>
        <Input
          id="target_amount"
          type="number"
          placeholder="1000000"
          value={data.target_amount || ""}
          onChange={(e) => updateData("target_amount", Number.parseInt(e.target.value))}
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
            value={[data.risk_tolerance || 5]}
            onValueChange={(value) => updateData("risk_tolerance", value[0])}
            max={10}
            min={1}
            step={1}
            className="w-full"
          />
          <div className="flex justify-between text-sm text-muted-foreground mt-1">
            <span>Conservative</span>
            <span className="font-medium">Level {data.risk_tolerance || 5}</span>
            <span>Aggressive</span>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <Label>Financial Risk Capacity</Label>
        <RadioGroup value={data.risk_capacity} onValueChange={(value) => updateData("risk_capacity", value)}>
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
                  checked={data.previous_experience?.includes(option) || false}
                  onCheckedChange={(checked) => {
                    const current = data.previous_experience || []
                    if (checked) {
                      updateData("previous_experience", [...current, option])
                    } else {
                      updateData(
                        "previous_experience",
                        current.filter((item: string) => item !== option),
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
        <RadioGroup value={data.market_reaction} onValueChange={(value) => updateData("market_reaction", value)}>
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
        <RadioGroup value={data.investment_style} onValueChange={(value) => updateData("investment_style", value)}>
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
          value={data.rebalancing_frequency}
          onValueChange={(value) => updateData("rebalancing_frequency", value)}
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
          checked={data.esg_preferences || false}
          onCheckedChange={(checked) => updateData("esg_preferences", checked)}
        />
        <Label htmlFor="esg">Include ESG (Environmental, Social, Governance) investments</Label>
      </div>

      <div className="space-y-2">
        <Label htmlFor="specialCircumstances">Special Circumstances or Preferences</Label>
        <Textarea
          id="specialCircumstances"
          placeholder="Any additional information that might affect your investment strategy..."
          value={data.special_circumstances || ""}
          onChange={(e) => updateData("special_circumstances", e.target.value)}
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
              <span>${data.net_worth?.toLocaleString()}</span>
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
              <span className="capitalize">{data.primary_goal?.replace("-", " ")}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Time Horizon:</span>
              <span>{data.time_horizon} years</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Monthly Investment:</span>
              <span>${data.monthly_contribution?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Target Amount:</span>
              <span>${data.target_amount?.toLocaleString()}</span>
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
              <span>Level {data.risk_tolerance}/10</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Risk Capacity:</span>
              <span className="capitalize">{data.risk_capacity}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Experience:</span>
              <span>{data.previous_experience?.length || 0} asset classes</span>
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
              <span className="capitalize">{data.investment_style}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Rebalancing:</span>
              <span className="capitalize">{data.rebalancing_frequency}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">ESG Focus:</span>
              <span>{data.esg_preferences ? "Yes" : "No"}</span>
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
