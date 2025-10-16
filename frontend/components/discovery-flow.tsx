"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { StepIndicator } from "./step-indicator"
import { GoalsStep } from "../app/assessment/goals-step"
import { HorizonStep } from "../app/assessment/horizon-step"
import { RiskToleranceStep } from "../app/assessment/risk-tolerance-step"
import { IncomeStep } from "../app/assessment/income-step"
import { LiabilitiesStep } from "../app/assessment/liabilities-step"
import { LiquidityStep } from "../app/assessment/liquidity-step"
import { ValuesStep } from "../app/assessment/values-step"
import { Button } from "./ui/button"
import { Badge } from "./ui/badge"
import { ArrowLeft, ArrowRight, Brain } from "lucide-react"

export type UserProfile = {
  goals: Array<{ id: string; label: string; priority: number }>
  timeHorizon: number
  milestones: Array<{ date: string; description: string }>
  riskTolerance: string
  experienceLevel: string
  annualIncome: number
  monthlySavings: number
  totalDebt: number
  dependents: number
  emergencyFundMonths: string
  values: {
    avoidIndustries: string[]
    preferIndustries: string[]
    customConstraints: string
  }
  esgPrioritization: boolean
  marketSelection: string[]
}

const STEPS = [
  { id: 1, title: "Investment Goals", description: "What are you investing for?" },
  { id: 2, title: "Time Horizon", description: "When do you need the money?" },
  { id: 3, title: "Risk Tolerance", description: "How comfortable are you with risk?" },
  { id: 4, title: "Income & Savings", description: "Your financial capacity" },
  { id: 5, title: "Liabilities", description: "Debts and responsibilities" },
  { id: 6, title: "Liquidity Needs", description: "Emergency fund planning" },
  { id: 7, title: "Personal Values", description: "ESG and investment preferences" },
]

export function DiscoveryFlow() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)
  const [profile, setProfile] = useState<UserProfile>({
    goals: [],
    timeHorizon: 10,
    milestones: [],
    riskTolerance: "",
    experienceLevel: "",
    annualIncome: 0,
    monthlySavings: 0,
    totalDebt: 0,
    dependents: 0,
    emergencyFundMonths: "",
    values: {
      avoidIndustries: [],
      preferIndustries: [],
      customConstraints: "",
    },
    esgPrioritization: false,
    marketSelection: [],
  })

  const updateProfile = (updates: Partial<UserProfile>) => {
    setProfile((prev) => ({ ...prev, ...updates }))
  }

  const handleNext = async () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1)
    } else {
      // Submit profile to discovery agent backend
      console.log("Final Profile:", profile)
      
      try {
        // Store immediately for Generate page to read and navigate right away
        localStorage.setItem('portfolioai_assessment', JSON.stringify(profile))
        router.push('/generate')

        // Fire-and-forget validation in background
        const assessmentData = {
          goals: profile.goals,
          timeHorizon: profile.timeHorizon,
          riskTolerance: profile.riskTolerance,
          annualIncome: profile.annualIncome,
          monthlySavings: profile.monthlySavings,
          totalDebt: profile.totalDebt,
          emergencyFundMonths: profile.emergencyFundMonths,
          values: profile.values,
          esgPrioritization: profile.esgPrioritization,
          marketSelection: profile.marketSelection
        }

        fetch('http://localhost:8000/api/validate-assessment', { 
          method: 'POST', 
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(assessmentData) 
        }).then(async (response) => {
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            console.error('Failed to validate assessment:', errorData)
          } else {
            const result = await response.json().catch(() => ({}))
            console.log('Assessment validation response:', result)
          }
        }).catch((e) => {
          console.error('Error validating assessment (background):', e)
        })
      } catch (error) {
        console.error('Error preparing navigation to Generate:', error)
        localStorage.setItem('portfolioai_assessment', JSON.stringify(profile))
        router.push('/generate')
      }
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <GoalsStep profile={profile} updateProfile={updateProfile} />
      case 2:
        return <HorizonStep profile={profile} updateProfile={updateProfile} />
      case 3:
        return <RiskToleranceStep profile={profile} updateProfile={updateProfile} />
      case 4:
        return <IncomeStep profile={profile} updateProfile={updateProfile} />
      case 5:
        return <LiabilitiesStep profile={profile} updateProfile={updateProfile} />
      case 6:
        return <LiquidityStep profile={profile} updateProfile={updateProfile} />
      case 7:
        return <ValuesStep profile={profile} updateProfile={updateProfile} />
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Brain className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-semibold text-lg text-foreground">PortfolioAI</span>
          </div>
          <div className="text-sm text-muted-foreground">
            Step {currentStep} of {STEPS.length}
          </div>
        </div>
      </header>

      {/* Progress Indicator */}
      <div className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <StepIndicator steps={STEPS} currentStep={currentStep} />
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2 text-balance">{STEPS[currentStep - 1].title}</h1>
          <p className="text-muted-foreground text-lg">{STEPS[currentStep - 1].description}</p>
        </div>

        {/* Step Content */}
        <div className="mb-8">{renderStep()}</div>

        {/* Navigation */}
        <div className="flex items-center justify-between pt-6 border-t border-border">
          <Button variant="outline" onClick={handleBack} disabled={currentStep === 1} className="gap-2 bg-transparent">
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
          <Button onClick={handleNext} className="gap-2">
            {currentStep === STEPS.length ? "Complete" : "Continue"}
            {currentStep < STEPS.length && <ArrowRight className="w-4 h-4" />}
          </Button>
        </div>
      </div>
    </div>
  )
}
