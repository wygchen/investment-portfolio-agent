"use client"

import type { UserProfile } from "../discovery-flow"
import { Card } from "../ui/card"
import { Label } from "../ui/label"
import { RadioGroup, RadioGroupItem } from "../ui/radio-group"
import { Droplets, CheckCircle2 } from "lucide-react"

type LiquidityStepProps = {
  profile: UserProfile
  updateProfile: (updates: Partial<UserProfile>) => void
}

const EMERGENCY_FUND_OPTIONS = [
  {
    value: "none",
    label: "Less than 1 month",
    description: "Limited emergency savings",
    recommendation: "Build emergency fund before aggressive investing",
  },
  {
    value: "1-3",
    label: "1-3 months",
    description: "Minimal emergency coverage",
    recommendation: "Consider building to 3-6 months",
  },
  {
    value: "3-6",
    label: "3-6 months",
    description: "Standard emergency fund",
    recommendation: "Good foundation for investing",
  },
  {
    value: "6-12",
    label: "6-12 months",
    description: "Strong emergency coverage",
    recommendation: "Excellent liquidity cushion",
  },
  {
    value: "12+",
    label: "12+ months",
    description: "Very strong emergency fund",
    recommendation: "High liquidity ratio supports higher risk capacity",
  },
]

export function LiquidityStep({ profile, updateProfile }: LiquidityStepProps) {
  return (
    <div className="space-y-8">
      <Card className="p-6 bg-accent/50 border-primary/20">
        <p className="text-sm text-foreground">
          Your emergency fund ensures you won't need to sell investments at a bad time. A strong liquidity cushion
          allows for more aggressive investment strategies.
        </p>
      </Card>

      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Droplets className="w-6 h-6 text-primary" />
          <Label className="text-base font-semibold">Emergency Fund Size (in months of expenses)</Label>
        </div>

        <RadioGroup
          value={profile.emergencyFundMonths}
          onValueChange={(value) => updateProfile({ emergencyFundMonths: value })}
          className="space-y-3"
        >
          {EMERGENCY_FUND_OPTIONS.map((option) => (
            <Card
              key={option.value}
              className={`p-5 cursor-pointer transition-all ${
                profile.emergencyFundMonths === option.value
                  ? "border-primary bg-primary/5 shadow-sm ring-2 ring-primary/20"
                  : "hover:border-primary/50"
              }`}
              onClick={() => updateProfile({ emergencyFundMonths: option.value })}
            >
              <div className="flex items-start gap-4">
                <RadioGroupItem value={option.value} id={`emergency-${option.value}`} className="mt-1" />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Label
                      htmlFor={`emergency-${option.value}`}
                      className="font-semibold text-foreground cursor-pointer"
                    >
                      {option.label}
                    </Label>
                    {profile.emergencyFundMonths === option.value && <CheckCircle2 className="w-4 h-4 text-primary" />}
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">{option.description}</p>
                  <div className="flex items-start gap-2 p-2 bg-muted/50 rounded">
                    <span className="text-xs font-medium text-primary">Recommendation:</span>
                    <span className="text-xs text-muted-foreground">{option.recommendation}</span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </RadioGroup>
      </div>

      {profile.emergencyFundMonths && (
        <Card className="p-6 bg-gradient-to-br from-primary/10 to-secondary/10 border-primary/20">
          <h3 className="font-semibold text-foreground mb-3">Liquidity Ratio Assessment</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Emergency Fund Coverage:</span>
              <span className="font-semibold text-primary">
                {EMERGENCY_FUND_OPTIONS.find((o) => o.value === profile.emergencyFundMonths)?.label}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Liquidity Status:</span>
              <span className="font-semibold text-foreground">
                {["none", "1-3"].includes(profile.emergencyFundMonths)
                  ? "Build emergency fund first"
                  : ["3-6"].includes(profile.emergencyFundMonths)
                    ? "Ready for moderate investing"
                    : "Ready for aggressive investing"}
              </span>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
