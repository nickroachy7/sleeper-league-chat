'use client'

import { useState, useRef, useEffect } from 'react'
import Image from 'next/image'
import { Trophy, RotateCcw, Send, Bot, TrendingUp, Calendar, Users, ArrowRightLeft } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const sessionId = useRef(`session-${Date.now()}`)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
    
    // Add data-label attributes to table cells for mobile viewing
    const tables = document.querySelectorAll('.markdown-content table')
    tables.forEach(table => {
      const headerCells = table.querySelectorAll('thead th')
      const headers: string[] = []
      
      headerCells.forEach(th => {
        headers.push(th.textContent?.trim() || '')
      })
      
      const rows = table.querySelectorAll('tbody tr')
      rows.forEach(row => {
        const cells = row.querySelectorAll('td')
        const firstCell = cells[0]
        const rowLabel = firstCell?.textContent?.trim() || ''
        
        cells.forEach((cell, index) => {
          if (index === 0) {
            // First cell is the row label itself
            cell.setAttribute('data-label', 'Category')
          } else if (headers[index] && rowLabel) {
            // Combine column header and row label for context
            // e.g., "Javier's Silk Road - Gave Up"
            cell.setAttribute('data-label', `${headers[index]} - ${rowLabel}`)
          } else if (headers[index]) {
            cell.setAttribute('data-label', headers[index])
          }
        })
      })
    })
  }, [messages])

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId.current
        })
      })

      const data = await response.json()
      
      if (data.response) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
      } else {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: 'Sorry, I encountered an error. Please try again.' 
        }])
      }
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I could not connect to the server. Please try again later.' 
      }])
    } finally {
      setLoading(false)
    }
  }

  const resetChat = () => {
    setMessages([])
    sessionId.current = `session-${Date.now()}`
  }

  return (
    <div className="flex flex-col h-screen" style={{ backgroundColor: 'var(--charcoal-darkest)' }}>
      {/* Header - Sticky */}
      <header className="sticky top-0 z-10 px-4 sm:px-6 py-3 sm:py-4" style={{ backgroundColor: 'var(--charcoal-dark)', borderBottom: '1px solid var(--border-color)' }}>
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center">
            <Image 
              src="/yapsports-logo.webp" 
              alt="YapSports Logo" 
              width={120} 
              height={120}
              className="rounded w-24 sm:w-32"
            />
          </div>
          <button
            onClick={resetChat}
            className="px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm transition-all flex items-center gap-2 hover:opacity-80"
            style={{ backgroundColor: 'var(--charcoal-light)', color: 'var(--text-primary)' }}
          >
            <RotateCcw className="w-3 h-3 sm:w-4 sm:h-4" />
            <span className="hidden sm:inline">New Chat</span>
            <span className="sm:hidden">New</span>
          </button>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 sm:py-8">
        <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <h2 className="text-2xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
                Welcome to Your Fantasy League Assistant!
              </h2>
              <p className="mb-8" style={{ color: 'var(--text-secondary)' }}>
                I can help you with standings, rosters, matchups, transactions, and more.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                {[
                  { text: 'What are the current standings?', icon: TrendingUp },
                  { text: 'Show me week 5 results', icon: Calendar },
                  { text: 'Who owns Travis Kelce?', icon: Users },
                  { text: 'Show me recent trades', icon: ArrowRightLeft }
                ].map((example, i) => {
                  const IconComponent = example.icon
                  return (
                    <button
                      key={i}
                      onClick={() => setInput(example.text)}
                      className="p-4 rounded-lg text-left text-sm transition-all hover:opacity-80 flex items-center gap-3"
                      style={{ 
                        backgroundColor: 'var(--charcoal-base)',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--border-color)'
                      }}
                    >
                      <IconComponent className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--accent-green)' }} />
                      <span>{example.text}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {messages.map((message, i) => (
            <div
              key={i}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'user' ? (
                // User message - with bubble
                <div 
                  className="max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 sm:px-5 py-2.5 sm:py-3 text-sm sm:text-base"
                  style={{ backgroundColor: 'var(--accent-green)', color: 'white' }}
                >
                  <div className="whitespace-pre-wrap leading-relaxed">
                    {message.content}
                  </div>
                </div>
              ) : (
                // Assistant message - no bubble, just content with icon
                <div className="max-w-[95%] sm:max-w-[85%] flex items-start gap-2 sm:gap-3">
                  <div 
                    className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1"
                    style={{ backgroundColor: 'var(--charcoal-base)', border: '1px solid var(--border-color)' }}
                  >
                    <Bot className="w-5 h-5" style={{ color: 'var(--accent-green)' }} />
                  </div>
                  <div className="flex-1 pt-1">
                    <div className="markdown-content leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="flex items-start gap-3">
                <div 
                  className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1"
                  style={{ backgroundColor: 'var(--charcoal-base)', border: '1px solid var(--border-color)' }}
                >
                  <Bot className="w-5 h-5" style={{ color: 'var(--accent-green)' }} />
                </div>
                <div className="flex gap-1 pt-2">
                  <div className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--text-secondary)', animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--text-secondary)', animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--text-secondary)', animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input - Sticky */}
      <div className="sticky bottom-0 z-10 px-4 sm:px-6 py-3 sm:py-4" style={{ backgroundColor: 'var(--charcoal-dark)', borderTop: '1px solid var(--border-color)' }}>
        <form onSubmit={sendMessage} className="max-w-4xl mx-auto">
          <div className="flex gap-2 sm:gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your fantasy league..."
              className="flex-1 px-4 sm:px-5 py-2.5 sm:py-3 rounded-xl focus:outline-none transition-all text-sm sm:text-base"
              style={{ 
                backgroundColor: 'var(--charcoal-base)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)'
              }}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="w-10 h-10 sm:w-12 sm:h-12 rounded-full transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 flex items-center justify-center flex-shrink-0"
              style={{ 
                backgroundColor: 'var(--accent-green)',
                color: 'white'
              }}
            >
              <Send className="w-4 h-4 sm:w-5 sm:h-5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
