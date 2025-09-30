"use client"

import type { UserProfile } from "../discovery-flow"
import { Card } from "../ui/card"
import { Label } from "../ui/label"
import { Input } from "../ui/input"
import { DollarSign, TrendingUp } from "lucide-react"

type IncomeStepProps = {
  profile: UserProfile
  updateProfile: (updates: Partial<UserProfile>) => void
}

export function IncomeStep({ profile, updateProfile }: IncomeStepProps) {
  const savingsRate = profile.annualIncome > 0 ? ((profile.monthlySavings * 12) / profile.annualIncome) * 100 : 0

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <div className="space-y-8">
      <Card className="p-6 bg-accent/50 border-primary/20">
        <p className="text-sm text-foreground">
          Your income and savings rate help us calculate your financial capacity to absorb potential losses and
          replenish your portfolio.
        </p>
      </Card>

      {/* Annual Income */}
      <div className="space-y-3">
        <Label htmlFor="annual-income" className="text-base font-semibold">
          Annual Gross Income
        </Label>
        <div className="relative">
          <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            id="annual-income"
            type="number"
            placeholder="0"
            value={profile.annualIncome || ""}
            onChange={(e) => updateProfile({ annualIncome: Number(e.target.value) })}
            className="pl-10 text-lg h-12"
          />
        </div>
        <p className="text-sm text-muted-foreground">Your total annual income before taxes and deductions</p>
      </div>

      {/* Monthly Savings */}
      <div className="space-y-3">
        <Label htmlFor="monthly-savings" className="text-base font-semibold">
          Monthly Savings Amount
        </Label>
        <div className="relative">
          <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            id="monthly-savings"
            type="number"
            placeholder="0"
            value={profile.monthlySavings || ""}
            onChange={(e) => updateProfile({ monthlySavings: Number(e.target.value) })}
            className="pl-10 text-lg h-12"
          />
        </div>
        <p className="text-sm text-muted-foreground">How much you typically save or invest each month</p>
      </div>

      {/* Savings Rate Calculation */}
      {profile.annualIncome > 0 && profile.monthlySavings > 0 && (
        <Card className="p-6 bg-gradient-to-br from-primary/10 to-secondary/10 border-primary/20">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
              <TrendingUp className="w-6 h-6 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-foreground mb-2">Your Savings Rate</h3>
              <div className="flex items-baseline gap-2 mb-2">
                <span className="text-4xl font-bold text-primary">{savingsRate.toFixed(1)}%</span>
                <span className="text-sm text-muted-foreground">
                  ({formatCurrency(profile.monthlySavings * 12)} / year)
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                {savingsRate >= 20
                  ? "Excellent! A high savings rate indicates strong risk capacity."
                  : savingsRate >= 10
                    ? "Good savings rate. This provides decent financial flexibility."
                    : "Consider increasing your savings rate to build stronger risk capacity."}
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
