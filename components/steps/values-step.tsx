"use client"

import type { UserProfile } from "../discovery-flow"
import { Card } from "../ui/card"
import { Label } from "../ui/label"
import { Textarea } from "../ui/textarea"
import { Badge } from "../ui/badge"
import { Leaf, Factory, Heart, Zap, Building2, Pill, ShoppingBag, Cpu } from "lucide-react"
import { cn } from "@/lib/utils"

type ValuesStepProps = {
  profile: UserProfile
  updateProfile: (updates: Partial<UserProfile>) => void
}

const AVOID_INDUSTRIES = [
  { id: "tobacco", label: "Tobacco", icon: Factory },
  { id: "alcohol", label: "Alcohol", icon: ShoppingBag },
  { id: "gambling", label: "Gambling", icon: Heart },
  { id: "weapons", label: "Weapons & Defense", icon: Zap },
  { id: "fossil-fuels", label: "Fossil Fuels", icon: Factory },
]

const PREFER_INDUSTRIES = [
  { id: "renewable-energy", label: "Renewable Energy", icon: Leaf },
  { id: "healthcare", label: "Healthcare", icon: Pill },
  { id: "technology", label: "Technology", icon: Cpu },
  { id: "sustainable", label: "Sustainable Companies", icon: Leaf },
  { id: "local", label: "Local Businesses", icon: Building2 },
]

export function ValuesStep({ profile, updateProfile }: ValuesStepProps) {
  const toggleAvoidIndustry = (industryId: string) => {
    const current = profile.values.avoidIndustries
    const updated = current.includes(industryId) ? current.filter((id) => id !== industryId) : [...current, industryId]

    updateProfile({
      values: { ...profile.values, avoidIndustries: updated },
    })
  }

  const togglePreferIndustry = (industryId: string) => {
    const current = profile.values.preferIndustries
    const updated = current.includes(industryId) ? current.filter((id) => id !== industryId) : [...current, industryId]

    updateProfile({
      values: { ...profile.values, preferIndustries: updated },
    })
  }

  return (
    <div className="space-y-8">
      <Card className="p-6 bg-accent/50 border-primary/20">
        <p className="text-sm text-foreground">
          Your personal values and ESG preferences help us construct a portfolio that aligns with your beliefs while
          meeting your financial goals.
        </p>
      </Card>

      {/* Industries to Avoid */}
      <div className="space-y-4">
        <Label className="text-base font-semibold">Industries to Avoid</Label>
        <p className="text-sm text-muted-foreground">Select industries you prefer not to invest in</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {AVOID_INDUSTRIES.map((industry) => {
            const Icon = industry.icon
            const isSelected = profile.values.avoidIndustries.includes(industry.id)

            return (
              <Card
                key={industry.id}
                className={cn(
                  "p-4 cursor-pointer transition-all",
                  isSelected ? "border-destructive bg-destructive/5 shadow-sm" : "hover:border-destructive/50",
                )}
                onClick={() => toggleAvoidIndustry(industry.id)}
              >
                <div className="flex flex-col items-center text-center gap-2">
                  <Icon className={cn("w-6 h-6", isSelected ? "text-destructive" : "text-muted-foreground")} />
                  <span
                    className={cn("text-sm font-medium", isSelected ? "text-destructive" : "text-muted-foreground")}
                  >
                    {industry.label}
                  </span>
                </div>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Industries to Prefer */}
      <div className="space-y-4">
        <Label className="text-base font-semibold">Preferred Industries & Values</Label>
        <p className="text-sm text-muted-foreground">Select industries or values you want to prioritize</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {PREFER_INDUSTRIES.map((industry) => {
            const Icon = industry.icon
            const isSelected = profile.values.preferIndustries.includes(industry.id)

            return (
              <Card
                key={industry.id}
                className={cn(
                  "p-4 cursor-pointer transition-all",
                  isSelected ? "border-primary bg-primary/5 shadow-sm" : "hover:border-primary/50",
                )}
                onClick={() => togglePreferIndustry(industry.id)}
              >
                <div className="flex flex-col items-center text-center gap-2">
                  <Icon className={cn("w-6 h-6", isSelected ? "text-primary" : "text-muted-foreground")} />
                  <span className={cn("text-sm font-medium", isSelected ? "text-primary" : "text-muted-foreground")}>
                    {industry.label}
                  </span>
                </div>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Custom Constraints */}
      <div className="space-y-3">
        <Label htmlFor="custom-constraints" className="text-base font-semibold">
          Additional Preferences or Constraints
        </Label>
        <Textarea
          id="custom-constraints"
          placeholder="e.g., I want to invest in companies with strong diversity policies, or I prefer dividend-paying stocks..."
          value={profile.values.customConstraints}
          onChange={(e) =>
            updateProfile({
              values: { ...profile.values, customConstraints: e.target.value },
            })
          }
          className="min-h-[120px] resize-none"
        />
        <p className="text-sm text-muted-foreground">
          Share any other investment preferences or ethical considerations
        </p>
      </div>

      {/* Summary */}
      {(profile.values.avoidIndustries.length > 0 || profile.values.preferIndustries.length > 0) && (
        <Card className="p-6 bg-muted/50">
          <h3 className="font-semibold text-foreground mb-4">Your Values Summary</h3>
          <div className="space-y-4">
            {profile.values.avoidIndustries.length > 0 && (
              <div>
                <p className="text-sm text-muted-foreground mb-2">Avoiding:</p>
                <div className="flex flex-wrap gap-2">
                  {profile.values.avoidIndustries.map((id) => {
                    const industry = AVOID_INDUSTRIES.find((i) => i.id === id)
                    return (
                      <Badge key={id} variant="destructive" className="gap-1">
                        {industry?.label}
                      </Badge>
                    )
                  })}
                </div>
              </div>
            )}
            {profile.values.preferIndustries.length > 0 && (
              <div>
                <p className="text-sm text-muted-foreground mb-2">Preferring:</p>
                <div className="flex flex-wrap gap-2">
                  {profile.values.preferIndustries.map((id) => {
                    const industry = PREFER_INDUSTRIES.find((i) => i.id === id)
                    return (
                      <Badge key={id} className="gap-1 bg-primary text-primary-foreground">
                        {industry?.label}
                      </Badge>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}
