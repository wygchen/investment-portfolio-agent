"use client"

import type { UserProfile } from "../discovery-flow"
import { Card } from "../ui/card"
import { Label } from "../ui/label"
import { Input } from "../ui/input"
import { Button } from "../ui/button"
import { Slider } from "../ui/slider"
import { Calendar, Plus, X } from "lucide-react"
import { useState } from "react"

type HorizonStepProps = {
  profile: UserProfile
  updateProfile: (updates: Partial<UserProfile>) => void
}

export function HorizonStep({ profile, updateProfile }: HorizonStepProps) {
  const [newMilestone, setNewMilestone] = useState({ date: "", description: "" })

  const handleAddMilestone = () => {
    if (newMilestone.date && newMilestone.description) {
      updateProfile({
        milestones: [...profile.milestones, newMilestone],
      })
      setNewMilestone({ date: "", description: "" })
    }
  }

  const handleRemoveMilestone = (index: number) => {
    updateProfile({
      milestones: profile.milestones.filter((_, i) => i !== index),
    })
  }

  return (
    <div className="space-y-8">
      <Card className="p-6 bg-accent/50 border-primary/20">
        <p className="text-sm text-foreground">
          Your time horizon helps us map your investments to the right risk-return profile. Longer horizons generally
          allow for more growth-oriented strategies.
        </p>
      </Card>

      {/* Overall Time Horizon Slider */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Label className="text-base font-semibold">Overall Investment Time Horizon</Label>
          <span className="text-2xl font-bold text-primary">{profile.timeHorizon} years</span>
        </div>
        <Slider
          value={[profile.timeHorizon]}
          onValueChange={(value) => updateProfile({ timeHorizon: value[0] })}
          min={1}
          max={50}
          step={1}
          className="py-4"
        />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Short-term (1-3 years)</span>
          <span>Medium-term (3-10 years)</span>
          <span>Long-term (10+ years)</span>
        </div>
      </div>

      {/* Time Horizon Band Indicator */}
      <Card className="p-4 bg-muted/50">
        <p className="text-sm">
          <strong className="text-foreground">Time Horizon Band:</strong>{" "}
          <span className="text-primary font-semibold">
            {profile.timeHorizon < 3 ? "Short-term" : profile.timeHorizon <= 10 ? "Medium-term" : "Long-term"}
          </span>
        </p>
      </Card>

      {/* Milestones */}
      <div className="space-y-4">
        <Label className="text-base font-semibold">Specific Financial Milestones</Label>
        <p className="text-sm text-muted-foreground">
          Add important dates when you'll need access to funds (e.g., house down payment, college tuition)
        </p>

        {/* Existing Milestones */}
        {profile.milestones.length > 0 && (
          <div className="space-y-2">
            {profile.milestones.map((milestone, index) => (
              <Card key={index} className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Calendar className="w-4 h-4 text-primary" />
                  <div>
                    <p className="font-medium text-foreground">{milestone.description}</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(milestone.date).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "long",
                      })}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveMilestone(index)}
                  className="text-destructive hover:text-destructive"
                >
                  <X className="w-4 h-4" />
                </Button>
              </Card>
            ))}
          </div>
        )}

        {/* Add New Milestone */}
        <Card className="p-4 space-y-3">
          <div className="grid md:grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="milestone-date" className="text-sm">
                Target Date
              </Label>
              <Input
                id="milestone-date"
                type="month"
                value={newMilestone.date}
                onChange={(e) => setNewMilestone({ ...newMilestone, date: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="milestone-desc" className="text-sm">
                Description
              </Label>
              <Input
                id="milestone-desc"
                placeholder="e.g., Buy house, College tuition"
                value={newMilestone.description}
                onChange={(e) => setNewMilestone({ ...newMilestone, description: e.target.value })}
              />
            </div>
          </div>
          <Button
            onClick={handleAddMilestone}
            variant="outline"
            className="w-full gap-2 bg-transparent"
            disabled={!newMilestone.date || !newMilestone.description}
          >
            <Plus className="w-4 h-4" />
            Add Milestone
          </Button>
        </Card>
      </div>
    </div>
  )
}
