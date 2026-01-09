/**
 * AI Tools Page
 * صفحه ابزارهای هوش مصنوعی
 */
import { useState, useEffect } from 'react'
import Link from 'next/link'
import Layout from '@/components/Layout'
import { aiApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import { Brain, Sparkles, FileText, Shield, Loader, Send, Copy, RefreshCw, Upload, ArrowRight } from 'lucide-react'

export default function AIToolsPage() {
  const [activeTab, setActiveTab] = useState<'generate' | 'analyze' | 'risk' | 'summary'>('generate')
  const [loading, setLoading] = useState(false)
  const [aiStatus, setAIStatus] = useState<any>(null)
  const [prompt, setPrompt] = useState('')
  const [result, setResult] = useState('')
  const [selectedProvider, setSelectedProvider] = useState('openai')

  useEffect(() => {
    checkAIStatus()
  }, [])

  const checkAIStatus = async () => {
    try {
      const response = await aiApi.status()
      setAIStatus(response.data)
    } catch (error) {
      console.error('AI status check failed:', error)
    }
  }

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt')
      return
    }

    setLoading(true)
    setResult('')

    try {
      const response = await aiApi.generate({
        prompt,
        provider: selectedProvider,
        type: activeTab,
      })
      setResult(response.data.result || response.data.content || JSON.stringify(response.data, null, 2))
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'AI request failed')
      setResult('Error: ' + (error.response?.data?.detail || 'Request failed'))
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(result)
    toast.success('Copied to clipboard')
  }

  const tabs = [
    { id: 'generate', label: 'Generate', icon: Sparkles, description: 'Generate text, emails, reports' },
    { id: 'analyze', label: 'Analyze', icon: FileText, description: 'Analyze documents and data' },
    { id: 'risk', label: 'Risk Assessment', icon: Shield, description: 'Assess customer risk profiles' },
    { id: 'summary', label: 'Summarize', icon: Brain, description: 'Summarize long documents' },
  ]

  const promptTemplates: Record<string, string[]> = {
    generate: [
      'Write a professional email to follow up on pending documents',
      'Generate a credit facility approval letter',
      'Create a customer welcome message',
      'Draft a payment reminder notice',
    ],
    analyze: [
      'Analyze this financial statement and identify key metrics',
      'Review this trade license for compliance issues',
      'Evaluate this customer\'s creditworthiness based on provided data',
    ],
    risk: [
      'Assess the risk profile for a corporate customer in trading sector',
      'Evaluate collateral adequacy for a loan facility',
      'Review KYC compliance status and flag concerns',
    ],
    summary: [
      'Summarize this customer relationship history',
      'Create an executive summary of facility performance',
      'Summarize key findings from audit report',
    ],
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Tools</h1>
            <p className="text-gray-600">Powered by OpenAI, Claude, and Gemini</p>
          </div>
          <div className="flex items-center gap-2">
            {aiStatus?.available ? (
              <span className="badge bg-green-100 text-green-700 flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                AI Available
              </span>
            ) : (
              <span className="badge bg-red-100 text-red-700">AI Unavailable</span>
            )}
          </div>
        </div>

        {/* Upload Center Banner */}
        <Link href="/ai/upload" className="block">
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6 text-white hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 rounded-lg">
                  <Upload size={32} />
                </div>
                <div>
                  <h3 className="text-xl font-bold">AI Upload Center</h3>
                  <p className="text-purple-100">Upload documents and let AI extract & categorize data automatically</p>
                </div>
              </div>
              <ArrowRight size={24} />
            </div>
          </div>
        </Link>

        {/* Tabs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`p-4 rounded-lg text-left transition-all ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-white hover:bg-gray-50 shadow'
                }`}
              >
                <Icon size={24} className="mb-2" />
                <h3 className="font-medium">{tab.label}</h3>
                <p className={`text-sm ${activeTab === tab.id ? 'text-blue-100' : 'text-gray-500'}`}>
                  {tab.description}
                </p>
              </button>
            )
          })}
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Input Section */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium">Input</h3>
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="px-3 py-1 border rounded-lg text-sm"
                >
                  <option value="openai">OpenAI (GPT-4)</option>
                  <option value="anthropic">Claude</option>
                  <option value="google">Gemini</option>
                </select>
              </div>

              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter your prompt or question..."
                rows={6}
                className="w-full px-3 py-2 border rounded-lg resize-none"
              />

              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-gray-500">{prompt.length} characters</p>
                <button
                  onClick={handleGenerate}
                  disabled={loading || !prompt.trim()}
                  className="btn-primary flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader className="animate-spin" size={18} />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Send size={18} />
                      Generate
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Result */}
            {result && (
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-medium">Result</h3>
                  <div className="flex gap-2">
                    <button
                      onClick={copyToClipboard}
                      className="p-2 hover:bg-gray-100 rounded"
                      title="Copy"
                    >
                      <Copy size={18} />
                    </button>
                    <button
                      onClick={handleGenerate}
                      className="p-2 hover:bg-gray-100 rounded"
                      title="Regenerate"
                    >
                      <RefreshCw size={18} />
                    </button>
                  </div>
                </div>
                <div className="prose max-w-none">
                  <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg text-sm overflow-auto max-h-96">
                    {result}
                  </pre>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar - Templates */}
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-medium mb-4">Quick Templates</h3>
            <div className="space-y-2">
              {promptTemplates[activeTab]?.map((template, idx) => (
                <button
                  key={idx}
                  onClick={() => setPrompt(template)}
                  className="w-full p-3 text-left text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  {template}
                </button>
              ))}
            </div>

            <div className="mt-6 pt-6 border-t">
              <h4 className="font-medium mb-3">Tips</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>Be specific with your prompts</li>
                <li>Include context about the customer or facility</li>
                <li>Review and edit AI-generated content before use</li>
                <li>Different providers may give different results</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
