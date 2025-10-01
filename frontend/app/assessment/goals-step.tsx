"use client"

import type React from "react"

import { useState } from "react"
import type { UserProfile } from "../../components/discovery-flow"
import { Card } from "../../components/ui/card"
import { Checkbox } from "../../components/ui/checkbox"
import { GripVertical, Target, Home, GraduationCap, TrendingUp, Heart, Plane } from "lucide-react"
import { cn } from "@/lib/utils"

const GOAL_OPTIONS = [
  { id: "retirement", label: "Retirement Planning", icon: Target },
  { id: "house", label: "Buy a Home", icon: Home },
  { id: "education", label: "Education Funding", icon: GraduationCap },
  { id: "wealth", label: "Wealth Growth", icon: TrendingUp },
  { id: "legacy", label: "Legacy & Estate", icon: Heart },
  { id: "travel", label: "Travel & Lifestyle", icon: Plane },
]

type GoalsStepProps = {
  profile: UserProfile
  updateProfile: (updates: Partial<UserProfile>) => void
}

export function GoalsStep({ profile, updateProfile }: GoalsStepProps) {
  const [selectedGoals, setSelectedGoals] = useState<string[]>(profile.goals.map((g) => g.id))
  const [draggedItem, setDraggedItem] = useState<string | null>(null)

  const handleToggleGoal = (goalId: string) => {
    const newSelected = selectedGoals.includes(goalId)
      ? selectedGoals.filter((id) => id !== goalId)
      : [...selectedGoals, goalId]

    setSelectedGoals(newSelected)

    const goals = newSelected.map((id, index) => ({
      id,
      label: GOAL_OPTIONS.find((g) => g.id === id)?.label || "",
      priority: index + 1,
    }))

    updateProfile({ goals })
  }

  const handleDragStart = (goalId: string) => {
    setDraggedItem(goalId)
  }

  const handleDragOver = (e: React.DragEvent, goalId: string) => {
    e.preventDefault()
    if (draggedItem && draggedItem !== goalId) {
      const newSelected = [...selectedGoals]
      const draggedIndex = newSelected.indexOf(draggedItem)
      const targetIndex = newSelected.indexOf(goalId)

      newSelected.splice(draggedIndex, 1)
      newSelected.splice(targetIndex, 0, draggedItem)

      setSelectedGoals(newSelected)

      const goals = newSelected.map((id, index) => ({
        id,
        label: GOAL_OPTIONS.find((g) => g.id === id)?.label || "",
        priority: index + 1,
      }))

      updateProfile({ goals })
    }
  }

  const handleDragEnd = () => {
    setDraggedItem(null)
  }

  return (
    <div className="space-y-6">
      <Card className="p-6 bg-accent/50 border-primary/20">
        <p className="text-sm text-foreground">
          <strong>Select your investment goals</strong> and drag to rank them by priority. Your top goal will help us
          determine the right level of risk for your portfolio.
        </p>
      </Card>

      <div className="grid gap-3">
        {GOAL_OPTIONS.map((goal) => {
          const Icon = goal.icon
          const isSelected = selectedGoals.includes(goal.id)
          const priority = selectedGoals.indexOf(goal.id) + 1

          return (
            <div
              key={goal.id}
              draggable={isSelected}
              onDragStart={() => handleDragStart(goal.id)}
              onDragOver={(e) => handleDragOver(e, goal.id)}
              onDragEnd={handleDragEnd}
              className={cn(
                "flex items-center gap-4 p-4 rounded-lg border-2 transition-all cursor-pointer",
                isSelected ? "border-primary bg-primary/5 shadow-sm" : "border-border bg-card hover:border-primary/50",
              )}
              onClick={() => handleToggleGoal(goal.id)}
            >
              <Checkbox checked={isSelected} className="pointer-events-none" />
              <Icon className={cn("w-5 h-5", isSelected ? "text-primary" : "text-muted-foreground")} />
              <span className={cn("flex-1 font-medium", isSelected ? "text-foreground" : "text-muted-foreground")}>
                {goal.label}
              </span>
              {isSelected && (
                <>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-primary bg-primary/10 px-2 py-1 rounded">
                      Priority #{priority}
                    </span>
                    <GripVertical className="w-5 h-5 text-muted-foreground cursor-grab active:cursor-grabbing" />
                  </div>
                </>
              )}
            </div>
          )
        })}
      </div>

      {selectedGoals.length > 0 && (
        <Card className="p-4 bg-muted/50">
          <p className="text-sm text-muted-foreground">
            <strong className="text-foreground">Your top priority:</strong>{" "}
            {GOAL_OPTIONS.find((g) => g.id === selectedGoals[0])?.label}
          </p>
        </Card>
      )}
    </div>
  )
}