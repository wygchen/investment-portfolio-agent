"use client"

import React from 'react'
import { Button } from "@/components/ui/button"
import { AlertTriangle, X } from "lucide-react"

interface DisclaimerModalProps {
  isOpen: boolean
  onAccept: () => void
  onCancel: () => void
}

export const DisclaimerModal: React.FC<DisclaimerModalProps> = ({ 
  isOpen, 
  onAccept, 
  onCancel 
}) => {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
      <div className="bg-card rounded-lg max-w-2xl w-full shadow-2xl border border-border max-h-[90vh] overflow-y-auto animate-in slide-in-from-bottom-4 duration-300">
        {/* Header */}
        <div className="sticky top-0 bg-card border-b border-border px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-yellow-600 dark:text-yellow-500" />
            </div>
            <h2 className="text-2xl font-bold text-foreground">
              Investment Advisory Disclaimer
            </h2>
          </div>
          <button 
            onClick={onCancel}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-6 space-y-6">
          <p className="font-semibold text-lg text-foreground">
            Please read carefully before using PortfolioAI
          </p>
          
          {/* What We Are */}
          <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <h3 className="font-semibold text-foreground mb-3 flex items-center">
              <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs mr-2">✓</span>
              What We Are:
            </h3>
            <ul className="space-y-2 text-sm text-muted-foreground ml-8">
              <li className="flex items-start">
                <span className="mr-2">•</span>
                <span>An AI-powered investment advisory and research tool</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">•</span>
                <span>A platform providing investment suggestions and analysis</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">•</span>
                <span>An educational resource for portfolio management</span>
              </li>
            </ul>
          </div>

          {/* What We Are NOT */}
          <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <h3 className="font-semibold text-foreground mb-3 flex items-center">
              <span className="w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-xs mr-2">✕</span>
              What We Are NOT:
            </h3>
            <ul className="space-y-2 text-sm text-muted-foreground ml-8">
              <li className="flex items-start">
                <span className="mr-2 text-red-500">✕</span>
                <span><strong>We DO NOT</strong> execute trades on your behalf</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2 text-red-500">✕</span>
                <span><strong>We DO NOT</strong> have access to your brokerage accounts</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2 text-red-500">✕</span>
                <span><strong>We DO NOT</strong> manage your investments or funds</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2 text-red-500">✕</span>
                <span><strong>We DO NOT</strong> provide personalized financial, tax, or legal advice</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2 text-red-500">✕</span>
                <span><strong>We ARE NOT</strong> a registered investment advisor (RIA)</span>
              </li>
            </ul>
          </div>

          {/* Your Responsibilities */}
          <div className="border-l-4 border-primary pl-4 py-2 bg-muted/50 rounded-r-lg">
            <h3 className="font-semibold text-foreground mb-3">
              Your Responsibilities:
            </h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start">
                <span className="mr-2">→</span>
                <span>All investment decisions are <strong>solely your responsibility</strong></span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">→</span>
                <span>You must execute all trades through your own brokerage account</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">→</span>
                <span>Consult with licensed professionals before making financial decisions</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">→</span>
                <span>Understand that past performance does not guarantee future results</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">→</span>
                <span>Investing involves risk, including possible loss of principal</span>
              </li>
            </ul>
          </div>

          {/* Agreement Text */}
          <div className="bg-muted/50 rounded-lg p-4 border border-border">
            <p className="text-sm text-muted-foreground italic">
              By clicking <strong>"I Agree - Continue"</strong>, you acknowledge that you have read and understood 
              this disclaimer and agree to use PortfolioAI as an advisory tool only. You understand that we do not 
              execute trades or manage investments on your behalf.
            </p>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="sticky bottom-0 bg-card border-t border-border px-6 py-4 flex gap-3">
          <Button
            onClick={onCancel}
            variant="outline"
            className="flex-1"
            size="lg"
          >
            Cancel
          </Button>
          <Button
            onClick={onAccept}
            className="flex-1 bg-primary hover:bg-primary/90"
            size="lg"
          >
            I Agree - Continue
          </Button>
        </div>
      </div>
    </div>
  )
}
