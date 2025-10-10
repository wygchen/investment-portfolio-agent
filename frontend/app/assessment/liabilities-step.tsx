"use client"

import type { UserProfile } from "../../components/discovery-flow"
import { Card } from "../../components/ui/card"
import { Label } from "../../components/ui/label"
import { Input } from "../../components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select"
import { DollarSign, Users, AlertCircle } from "lucide-react"

type LiabilitiesStepProps = {
  profile: UserProfile
  updateProfile: (updates: Partial<UserProfile>) => void
}

export function LiabilitiesStep({ profile, updateProfile }: LiabilitiesStepProps) {
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
          Understanding your debts and financial responsibilities helps us assess constraints on your investment
          capacity.
        </p>
      </Card>

      {/* Total Debt */}
      <div className="space-y-3">
        <Label htmlFor="total-debt" className="text-base font-semibold">
          Total Outstanding Debt
        </Label>
        <div className="relative">
          <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            id="total-debt"
            type="number"
            placeholder="0"
            value={profile.totalDebt || ""}
            onChange={(e) => updateProfile({ totalDebt: Number(e.target.value) })}
            className="pl-10 text-lg h-12"
          />
        </div>
        <p className="text-sm text-muted-foreground">Include mortgage, student loans, credit cards, auto loans, etc.</p>
      </div>

      {/* Number of Dependents */}
      <div className="space-y-3">
        <Label htmlFor="dependents" className="text-base font-semibold">
          Number of Dependents
        </Label>
        <Select
          value={profile.dependents.toString()}
          onValueChange={(value) => updateProfile({ dependents: Number(value) })}
        >
          <SelectTrigger id="dependents" className="h-12 text-lg">
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-muted-foreground" />
              <SelectValue placeholder="Select number of dependents" />
            </div>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="0">0 - No dependents</SelectItem>
            <SelectItem value="1">1 dependent</SelectItem>
            <SelectItem value="2">2 dependents</SelectItem>
            <SelectItem value="3">3 dependents</SelectItem>
            <SelectItem value="4">4 dependents</SelectItem>
            <SelectItem value="5">5+ dependents</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-sm text-muted-foreground">Children, elderly parents, or others who depend on your income</p>
      </div>

      {/* Debt-to-Income Ratio */}
      {profile.totalDebt > 0 && profile.annualIncome > 0 && (
        <Card className="p-6 bg-muted/50 border-l-4 border-l-primary">
          <div className="flex items-start gap-4">
            <AlertCircle className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-foreground mb-2">Financial Constraint Analysis</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Debt:</span>
                  <span className="font-semibold text-foreground">{formatCurrency(profile.totalDebt)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Annual Income:</span>
                  <span className="font-semibold text-foreground">{formatCurrency(profile.annualIncome)}</span>
                </div>
                <div className="flex justify-between pt-2 border-t border-border">
                  <span className="text-muted-foreground">Debt-to-Income Ratio:</span>
                  <span className="font-bold text-primary">
                    {((profile.totalDebt / profile.annualIncome) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-3">
                {profile.totalDebt / profile.annualIncome < 2
                  ? "Your debt level is manageable relative to your income."
                  : "Consider debt reduction strategies to improve your risk capacity."}
              </p>
            </div>
          </div>
        </Card>
      )}

      {profile.dependents > 0 && (
        <Card className="p-4 bg-muted/50">
          <p className="text-sm">
            <strong className="text-foreground">Dependents:</strong>{" "}
            <span className="text-primary font-semibold">{profile.dependents}</span>
            <span className="text-muted-foreground ml-2">
              - We'll factor in your family responsibilities when assessing risk capacity
            </span>
          </p>
        </Card>
      )}
    </div>
  )
}