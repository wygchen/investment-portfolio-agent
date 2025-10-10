"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Activity, TrendingUp, TrendingDown, Brain } from "lucide-react"

interface MarketDataWidgetProps {
  className?: string
}

export function MarketDataWidget({ className }: MarketDataWidgetProps) {
  const [marketSignals, setMarketSignals] = useState([
    { name: "Market Sentiment", value: "Bullish", change: "+5.2%", trend: "up" },
    { name: "Volatility Index", value: "13.45", change: "-2.1%", trend: "down" },
    { name: "Alternative Data", value: "Positive", change: "+3.8%", trend: "up" },
  ])

  const [lastUpdate, setLastUpdate] = useState(new Date())

  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdate(new Date())
      // Simulate real-time updates
      setMarketSignals((prev) =>
        prev.map((signal) => ({
          ...signal,
          change: `${signal.trend === "up" ? "+" : "-"}${(Math.random() * 5).toFixed(1)}%`,
        })),
      )
    }, 10000) // Update every 10 seconds

    return () => clearInterval(interval)
  }, [])

  return (
    <Card className={`border-0 shadow-lg ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Brain className="w-5 h-5 text-primary" />
            <span>AI Market Intelligence</span>
          </div>
          <Badge variant="secondary" className="px-2 py-1">
            <Activity className="w-3 h-3 mr-1" />
            Live
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {marketSignals.map((signal, index) => (
          <div key={index} className="flex items-center justify-between">
            <div>
              <div className="font-medium text-sm">{signal.name}</div>
              <div className="text-xs text-muted-foreground">{signal.value}</div>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`text-sm font-medium ${signal.trend === "up" ? "text-chart-4" : "text-destructive"}`}>
                {signal.change}
              </span>
              {signal.trend === "up" ? (
                <TrendingUp className="w-4 h-4 text-chart-4" />
              ) : (
                <TrendingDown className="w-4 h-4 text-destructive" />
              )}
            </div>
          </div>
        ))}
        <div className="pt-2 border-t border-border">
          <div className="text-xs text-muted-foreground">Last updated: {lastUpdate.toLocaleTimeString()}</div>
        </div>
      </CardContent>
    </Card>
  )
}
