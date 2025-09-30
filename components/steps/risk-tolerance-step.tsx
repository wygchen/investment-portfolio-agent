"use client"

import type { UserProfile } from "../discovery-flow"
import { Card } from "../ui/card"
import { Label } from "../ui/label"
import { RadioGroup, RadioGroupItem } from "../ui/radio-group"
import { TrendingDown, AlertTriangle, Briefcase, Home, Zap } from "lucide-react"
import { useState } from "react"

type RiskToleranceStepProps = {
  profile: UserProfile
  updateProfile: (updates: Partial<UserProfile>) => void
}

const SCENARIOS = [
  {
    id: "market",
    icon: TrendingDown,
    title: "Market Volatility",
    question: "Your portfolio drops 20% in value during a market downturn. What would you do?",
    options: [
      {
        value: "conservative",
        label: "Sell immediately",
        description: "I would be very uncomfortable and want to minimize further losses",
      },
      {
        value: "moderate-conservative",
        label: "Sell some holdings",
        description: "I would reduce my exposure but keep some investments",
      },
      {
        value: "moderate",
        label: "Hold steady",
        description: "I would wait it out and not make any changes",
      },
      {
        value: "moderate-aggressive",
        label: "Buy a little more",
        description: "I would see it as a buying opportunity and invest a bit more",
      },
      {
        value: "aggressive",
        label: "Buy significantly more",
        description: "I would invest substantially more to take advantage of lower prices",
      },
    ],
  },
  {
    id: "career",
    icon: Briefcase,
    title: "Career Decision",
    question:
      "You're offered a new job with 50% higher pay but it's at a startup with uncertain future. What would you choose?",
    options: [
      {
        value: "conservative",
        label: "Stay at current job",
        description: "I prefer stability and predictable income over potential gains",
      },
      {
        value: "moderate-conservative",
        label: "Negotiate for more security",
        description: "I'd consider it only with significant equity or guarantees",
      },
      {
        value: "moderate",
        label: "Take it with savings buffer",
        description: "I'd take it if I have 6+ months of expenses saved",
      },
      {
        value: "moderate-aggressive",
        label: "Take the opportunity",
        description: "The upside potential is worth the risk",
      },
      {
        value: "aggressive",
        label: "Take it immediately",
        description: "I'm comfortable with uncertainty for higher rewards",
      },
    ],
  },
  {
    id: "windfall",
    icon: Zap,
    title: "Unexpected Windfall",
    question: "You receive an unexpected $50,000. How would you allocate it?",
    options: [
      {
        value: "conservative",
        label: "High-yield savings",
        description: "Put it all in a safe, FDIC-insured savings account",
      },
      {
        value: "moderate-conservative",
        label: "Mostly bonds, some stocks",
        description: "70% bonds/CDs, 30% diversified stock funds",
      },
      {
        value: "moderate",
        label: "Balanced portfolio",
        description: "50% stocks, 50% bonds/fixed income",
      },
      {
        value: "moderate-aggressive",
        label: "Mostly stocks",
        description: "70% diversified stocks, 30% bonds",
      },
      {
        value: "aggressive",
        label: "Growth investments",
        description: "90%+ in stocks or growth-oriented investments",
      },
    ],
  },
  {
    id: "insurance",
    icon: Home,
    title: "Insurance Decision",
    question: "When choosing insurance, which approach do you prefer?",
    options: [
      {
        value: "conservative",
        label: "Comprehensive coverage",
        description: "Low deductibles, maximum coverage even if premiums are high",
      },
      {
        value: "moderate-conservative",
        label: "Good coverage",
        description: "Moderate deductibles with solid coverage",
      },
      {
        value: "moderate",
        label: "Balanced approach",
        description: "Standard coverage with reasonable deductibles",
      },
      {
        value: "moderate-aggressive",
        label: "Higher deductibles",
        description: "Higher deductibles to save on premiums, self-insure small risks",
      },
      {
        value: "aggressive",
        label: "Minimal coverage",
        description: "Only legally required coverage, self-insure most risks",
      },
    ],
  },
]

const EXPERIENCE_LEVELS = [
  { value: "beginner", label: "Beginner", description: "New to investing" },
  {
    value: "intermediate",
    label: "Intermediate",
    description: "Some investment experience",
  },
  { value: "experienced", label: "Experienced", description: "Seasoned investor" },
]

export function RiskToleranceStep({ profile, updateProfile }: RiskToleranceStepProps) {
  const [scenarioResponses, setScenarioResponses] = useState<Record<string, string>>({})

  const handleScenarioResponse = (scenarioId: string, value: string) => {
    const newResponses = { ...scenarioResponses, [scenarioId]: value }
    setScenarioResponses(newResponses)

    const responses = Object.values(newResponses)
    if (responses.length > 0) {
      const riskScores: Record<string, number> = {
        conservative: 1,
        "moderate-conservative": 2,
        moderate: 3,
        "moderate-aggressive": 4,
        aggressive: 5,
      }

      const avgScore = responses.reduce((sum, r) => sum + (riskScores[r] || 0), 0) / responses.length
      let overallRisk = "moderate"

      if (avgScore <= 1.5) overallRisk = "conservative"
      else if (avgScore <= 2.5) overallRisk = "moderate-conservative"
      else if (avgScore <= 3.5) overallRisk = "moderate"
      else if (avgScore <= 4.5) overallRisk = "moderate-aggressive"
      else overallRisk = "aggressive"

      updateProfile({ riskTolerance: overallRisk })
    }
  }

  return (
    <div className="space-y-8">
      <Card className="p-6 bg-accent/50 border-primary/20">
        <p className="text-sm text-foreground">
          Understanding your psychological comfort with risk through various life situations helps us build a portfolio
          you can stick with during market volatility.
        </p>
      </Card>

      {SCENARIOS.map((scenario, index) => {
        const Icon = scenario.icon
        return (
          <div key={scenario.id} className="space-y-4">
            <div className="flex items-start gap-3 p-4 bg-muted/50 rounded-lg border border-border">
              <Icon className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-primary">Scenario {index + 1}</span>
                  <span className="text-xs text-muted-foreground">•</span>
                  <span className="text-xs font-medium text-muted-foreground">{scenario.title}</span>
                </div>
                <p className="text-sm text-foreground mt-1 font-medium">{scenario.question}</p>
              </div>
            </div>

            <RadioGroup
              value={scenarioResponses[scenario.id] || ""}
              onValueChange={(value) => handleScenarioResponse(scenario.id, value)}
              className="space-y-3"
            >
              {scenario.options.map((option) => (
                <Card
                  key={option.value}
                  className={`p-4 cursor-pointer transition-all ${
                    scenarioResponses[scenario.id] === option.value
                      ? "border-primary bg-primary/5 shadow-sm"
                      : "hover:border-primary/50"
                  }`}
                  onClick={() => handleScenarioResponse(scenario.id, option.value)}
                >
                  <div className="flex items-start gap-3">
                    <RadioGroupItem value={option.value} id={`${scenario.id}-${option.value}`} className="mt-1" />
                    <div className="flex-1">
                      <Label
                        htmlFor={`${scenario.id}-${option.value}`}
                        className="font-semibold text-foreground cursor-pointer"
                      >
                        {option.label}
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">{option.description}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </RadioGroup>
          </div>
        )
      })}

      {/* Experience Level */}
      <div className="space-y-4">
        <Label className="text-base font-semibold">Investment Experience</Label>
        <RadioGroup
          value={profile.experienceLevel}
          onValueChange={(value) => updateProfile({ experienceLevel: value })}
          className="grid md:grid-cols-3 gap-3"
        >
          {EXPERIENCE_LEVELS.map((level) => (
            <Card
              key={level.value}
              className={`p-4 cursor-pointer transition-all ${
                profile.experienceLevel === level.value
                  ? "border-primary bg-primary/5 shadow-sm"
                  : "hover:border-primary/50"
              }`}
              onClick={() => updateProfile({ experienceLevel: level.value })}
            >
              <div className="flex flex-col items-center text-center gap-2">
                <RadioGroupItem value={level.value} id={`exp-${level.value}`} />
                <Label htmlFor={`exp-${level.value}`} className="font-semibold text-foreground cursor-pointer">
                  {level.label}
                </Label>
                <p className="text-xs text-muted-foreground">{level.description}</p>
              </div>
            </Card>
          ))}
        </RadioGroup>
      </div>

      {profile.riskTolerance && (
        <Card className="p-4 bg-muted/50 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-primary mt-0.5" />
          <div>
            <p className="text-sm">
              <strong className="text-foreground">Overall Risk Tolerance:</strong>{" "}
              <span className="text-primary font-semibold capitalize">{profile.riskTolerance.replace("-", " ")}</span>
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Based on your responses across {Object.keys(scenarioResponses).length} life scenarios
            </p>
          </div>
        </Card>
      )}
    </div>
  )
}
