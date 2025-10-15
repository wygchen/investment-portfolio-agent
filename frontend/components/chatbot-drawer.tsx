"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from "@/components/ui/dialog"
import { 
  MessageCircle, 
  Send, 
  X, 
  Bot, 
  User, 
  Loader2, 
  ChevronDown, 
  ChevronUp,
  ExternalLink,
  Trash2,
  Brain,
  Search,
  FileText
} from "lucide-react"
import { apiClient } from "@/lib/api"

interface ChatMessage {
  id: string
  type: "user" | "assistant"
  content: string
  timestamp: string
  reasoning_trace?: Array<{
    step: number
    action: string
    result: string
    success: boolean
  }>
  sources_used?: Array<{
    title?: string
    url?: string
    snippet?: string
    source_type?: string
  }>
  tools_called?: string[]
}

interface ChatbotDrawerProps {
  userId: string
  isOpen: boolean
  onClose: () => void
}

export function ChatbotDrawer({ userId, isOpen, onClose }: ChatbotDrawerProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [expandedReasoning, setExpandedReasoning] = useState<Set<string>>(new Set())
  const [showSources, setShowSources] = useState<Set<string>>(new Set())
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Load chat history on mount
  useEffect(() => {
    if (isOpen && userId) {
      loadChatHistory()
    }
  }, [isOpen, userId])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const loadChatHistory = async () => {
    try {
      const response = await apiClient.getChatHistory(userId)
      if (response.status === "success") {
        const conversation = response.conversation || []
        const formattedMessages: ChatMessage[] = conversation.map((msg: any, index: number) => ({
          id: `msg-${index}`,
          type: msg.type === "human" ? "user" : "assistant",
          content: msg.content,
          timestamp: msg.timestamp || new Date().toISOString()
        }))
        setMessages(formattedMessages)
      }
    } catch (error) {
      console.error("Error loading chat history:", error)
    }
  }

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      type: "user",
      content: inputMessage,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage("")
    setIsLoading(true)

    try {
      const response = await apiClient.sendChatMessage(userId, inputMessage)
      
      if (response.status === "success") {
        const botResponse: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          type: "assistant",
          content: response.response.answer,
          timestamp: new Date().toISOString(),
          reasoning_trace: response.response.reasoning_trace,
          sources_used: response.response.sources_used,
          tools_called: response.response.tools_called
        }
        setMessages(prev => [...prev, botResponse])
      } else {
        throw new Error("Failed to get response")
      }
    } catch (error) {
      console.error("Error sending message:", error)
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        type: "assistant",
        content: "I apologize, but I encountered an error. Please try again.",
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const clearChatHistory = async () => {
    try {
      await apiClient.clearChatHistory(userId)
      setMessages([])
    } catch (error) {
      console.error("Error clearing chat history:", error)
    }
  }

  const toggleReasoning = (messageId: string) => {
    setExpandedReasoning(prev => {
      const newSet = new Set(prev)
      if (newSet.has(messageId)) {
        newSet.delete(messageId)
      } else {
        newSet.add(messageId)
      }
      return newSet
    })
  }

  const toggleSources = (messageId: string) => {
    setShowSources(prev => {
      const newSet = new Set(prev)
      if (newSet.has(messageId)) {
        newSet.delete(messageId)
      } else {
        newSet.add(messageId)
      }
      return newSet
    })
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl h-[80vh] flex flex-col p-0">
        <DialogHeader className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2">
              <MessageCircle className="w-5 h-5" />
              Portfolio AI Assistant
            </DialogTitle>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={clearChatHistory}
                className="text-muted-foreground hover:text-foreground"
              >
                <Trash2 className="w-4 h-4 mr-1" />
                Clear
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 flex flex-col min-h-0">
          {/* Messages Area */}
          <ScrollArea className="flex-1 px-6 py-4">
            <div className="space-y-4">
              {messages.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium">Welcome to Portfolio AI Assistant</p>
                  <p className="text-sm">Ask me anything about your portfolio, investments, or market conditions.</p>
                </div>
              ) : (
                messages.map((message) => (
                  <div key={message.id} className="flex gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.type === "user" 
                        ? "bg-primary text-primary-foreground" 
                        : "bg-muted text-muted-foreground"
                    }`}>
                      {message.type === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>
                    
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          {message.type === "user" ? "You" : "AI Assistant"}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {formatTimestamp(message.timestamp)}
                        </span>
                      </div>
                      
                      <Card className="bg-card">
                        <CardContent className="p-4">
                          <div className="whitespace-pre-wrap">{message.content}</div>
                          
                          {/* Reasoning Trace */}
                          {message.reasoning_trace && message.reasoning_trace.length > 0 && (
                            <div className="mt-4">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => toggleReasoning(message.id)}
                                className="p-0 h-auto text-xs text-muted-foreground hover:text-foreground"
                              >
                                <Brain className="w-3 h-3 mr-1" />
                                Reasoning Trace
                                {expandedReasoning.has(message.id) ? (
                                  <ChevronUp className="w-3 h-3 ml-1" />
                                ) : (
                                  <ChevronDown className="w-3 h-3 ml-1" />
                                )}
                              </Button>
                              
                              {expandedReasoning.has(message.id) && (
                                <div className="mt-2 space-y-2">
                                  {message.reasoning_trace.map((step, index) => (
                                    <div key={index} className="text-xs bg-muted/50 p-2 rounded">
                                      <div className="flex items-center gap-2">
                                        <Badge variant="outline" className="text-xs">
                                          Step {step.step}
                                        </Badge>
                                        <span className="font-medium">{step.action}</span>
                                        <Badge 
                                          variant={step.success ? "default" : "destructive"}
                                          className="text-xs"
                                        >
                                          {step.success ? "Success" : "Failed"}
                                        </Badge>
                                      </div>
                                      <p className="mt-1 text-muted-foreground">{step.result}</p>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* Sources */}
                          {message.sources_used && message.sources_used.length > 0 && (
                            <div className="mt-4">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => toggleSources(message.id)}
                                className="p-0 h-auto text-xs text-muted-foreground hover:text-foreground"
                              >
                                <FileText className="w-3 h-3 mr-1" />
                                Sources ({message.sources_used.length})
                                {showSources.has(message.id) ? (
                                  <ChevronUp className="w-3 h-3 ml-1" />
                                ) : (
                                  <ChevronDown className="w-3 h-3 ml-1" />
                                )}
                              </Button>
                              
                              {showSources.has(message.id) && (
                                <div className="mt-2 space-y-2">
                                  {message.sources_used.map((source, index) => (
                                    <div key={index} className="text-xs bg-muted/50 p-2 rounded">
                                      <div className="flex items-center gap-2">
                                        <Badge variant="secondary" className="text-xs">
                                          {source.source_type || "Source"}
                                        </Badge>
                                        {source.url && (
                                          <a
                                            href={source.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-primary hover:underline flex items-center gap-1"
                                          >
                                            <ExternalLink className="w-3 h-3" />
                                            {source.title || "Link"}
                                          </a>
                                        )}
                                      </div>
                                      {source.snippet && (
                                        <p className="mt-1 text-muted-foreground">{source.snippet}</p>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* Tools Used */}
                          {message.tools_called && message.tools_called.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {message.tools_called.map((tool, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {tool === "retrieve_portfolio_context" && <Search className="w-3 h-3 mr-1" />}
                                  {tool === "search_web" && <ExternalLink className="w-3 h-3 mr-1" />}
                                  {tool === "synthesize_answer" && <Brain className="w-3 h-3 mr-1" />}
                                  {tool.replace(/_/g, " ")}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  </div>
                ))
              )}
              
              {isLoading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <Card className="bg-card">
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span className="text-sm text-muted-foreground">AI is thinking...</span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="border-t p-4">
            <div className="flex gap-2">
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about your portfolio, investments, or market conditions..."
                disabled={isLoading}
                className="flex-1"
              />
              <Button 
                onClick={sendMessage} 
                disabled={!inputMessage.trim() || isLoading}
                size="sm"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// Floating Action Button Component
export function ChatbotFAB({ userId }: { userId: string }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 rounded-full w-14 h-14 shadow-lg z-50"
        size="lg"
      >
        <MessageCircle className="w-6 h-6" />
      </Button>
      
      <ChatbotDrawer 
        userId={userId}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />
    </>
  )
}
