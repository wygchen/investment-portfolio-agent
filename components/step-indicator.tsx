import { Check } from "lucide-react"
import { cn } from "@/lib/utils"

type Step = {
  id: number
  title: string
  description: string
}

type StepIndicatorProps = {
  steps: Step[]
  currentStep: number
}

export function StepIndicator({ steps, currentStep }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-between">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-center flex-1">
          <div className="flex flex-col items-center gap-2 relative">
            <div
              className={cn(
                "w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-colors",
                currentStep > step.id
                  ? "bg-primary text-primary-foreground"
                  : currentStep === step.id
                    ? "bg-primary text-primary-foreground ring-4 ring-primary/20"
                    : "bg-muted text-muted-foreground",
              )}
            >
              {currentStep > step.id ? <Check className="w-5 h-5" /> : step.id}
            </div>
            <span
              className={cn(
                "text-xs font-medium hidden md:block text-center max-w-[100px]",
                currentStep >= step.id ? "text-foreground" : "text-muted-foreground",
              )}
            >
              {step.title}
            </span>
          </div>
          {index < steps.length - 1 && (
            <div
              className={cn("flex-1 h-0.5 mx-2 transition-colors", currentStep > step.id ? "bg-primary" : "bg-border")}
            />
          )}
        </div>
      ))}
    </div>
  )
}
