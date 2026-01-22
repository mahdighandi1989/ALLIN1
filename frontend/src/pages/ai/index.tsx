/**
 * AI Tools Page v2.0
 * صفحه ابزارهای هوش مصنوعی
 */
import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import Link from 'next/link'
import Layout from '@/components/Layout'
import { aiApi } from '@/services/api'
import { useAuth } from '@/hooks/useAuth'
import { toast } from 'react-hot-toast'
import {
  Brain,
  Sparkles,
  FileText,
  Shield,
  Loader2,
  Send,
  Copy,
  RefreshCw,
  Upload,
  ArrowRight,
  CheckCircle,
  XCircle,
  Zap
} from 'lucide-react'

export default function AIToolsPage() {
  const { isLoading, isAuthenticated } = useAuth()
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'generate' | 'analyze' | 'summary'>('generate')
  const [loading, setLoading] = useState(false)
  const [aiStatus, setAIStatus] = useState<any>(null)
  const [prompt, setPrompt] = useState('')
  const [result, setResult] = useState('')
  const [selectedProvider, setSelectedProvider] = useState('')
  const [providers, setProviders] = useState<string[]>([])

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) {
      checkAIStatus()
    }
  }, [isAuthenticated])

  const checkAIStatus = async () => {
    try {
      const response = await aiApi.status()
      setAIStatus(response.data)
      const availableProviders = response.data.available_providers || []
      setProviders(availableProviders)
      if (availableProviders.length > 0 && !selectedProvider) {
        setSelectedProvider(response.data.default_provider || availableProviders[0])
      }
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
      let response
      if (activeTab === 'analyze') {
        response = await aiApi.analyze({
          content: prompt,
          analysis_type: 'summary',
          provider: selectedProvider || undefined,
        })
      } else {
        response = await aiApi.generate({
          prompt,
          provider: selectedProvider || undefined,
        })
      }
      setResult(response.data.result || response.data.content || JSON.stringify(response.data, null, 2))
      toast.success('Generated successfully')
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

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  const tabs = [
    { id: 'generate', label: 'Generate', icon: Sparkles, description: 'Generate text, emails, reports' },
    { id: 'analyze', label: 'Analyze', icon: FileText, description: 'Analyze documents and data' },
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
    summary: [
      'Summarize this customer relationship history',
      'Create an executive summary of facility performance',
      'Summarize key findings from audit report',
    ],
  }

  const providerNames: Record<string, string> = {
    openai: 'OpenAI GPT-4',
    anthropic: 'Claude',
    google: 'Google Gemini',
  }

  return (
    <Layout>
      <Head>
        <title>AI Tools | Banking Operations System</title>
      </Head>

      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Tools</h1>
            <p className="text-gray-500">Powered by OpenAI, Claude, and Gemini</p>
          </div>
          <div className="flex items-center gap-2">
            {providers.length > 0 ? (
              <span className="px-3 py-1.5 bg-green-100 text-green-700 rounded-full text-sm font-medium flex items-center gap-2">
                <CheckCircle size={16} />
                {providers.length} Provider{providers.length > 1 ? 's' : ''} Available
              </span>
            ) : (
              <span className="px-3 py-1.5 bg-red-100 text-red-700 rounded-full text-sm font-medium flex items-center gap-2">
                <XCircle size={16} />
                No Providers Configured
              </span>
            )}
          </div>
        </div>

        {/* Upload Center Banner */}
        <Link href="/ai/upload" className="block">
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6 text-white hover:shadow-lg transition-all group">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 rounded-xl group-hover:bg-white/30 transition-colors">
                  <Upload size={28} />
                </div>
                <div>
                  <h3 className="text-xl font-bold">AI Document Upload</h3>
                  <p className="text-purple-100">Upload documents and let AI extract & categorize data automatically</p>
                </div>
              </div>
              <ArrowRight size={24} className="group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </Link>

        {/* Tabs */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`p-5 rounded-xl text-left transition-all ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                    : 'bg-white hover:bg-gray-50 shadow-sm border border-gray-100'
                }`}
              >
                <Icon size={24} className="mb-3" />
                <h3 className="font-semibold">{tab.label}</h3>
                <p className={`text-sm mt-1 ${activeTab === tab.id ? 'text-blue-100' : 'text-gray-500'}`}>
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
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Input</h3>
                {providers.length > 0 && (
                  <select
                    value={selectedProvider}
                    onChange={(e) => setSelectedProvider(e.target.value)}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {providers.map((p) => (
                      <option key={p} value={p}>{providerNames[p] || p}</option>
                    ))}
                  </select>
                )}
              </div>

              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter your prompt or question..."
                rows={8}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />

              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-gray-500">{prompt.length} characters</p>
                <button
                  onClick={handleGenerate}
                  disabled={loading || !prompt.trim() || providers.length === 0}
                  className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {loading ? (
                    <>
                      <Loader2 className="animate-spin" size={18} />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Zap size={18} />
                      Generate
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Result */}
            {result && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900">Result</h3>
                  <div className="flex gap-2">
                    <button
                      onClick={copyToClipboard}
                      className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                      title="Copy"
                    >
                      <Copy size={18} className="text-gray-600" />
                    </button>
                    <button
                      onClick={handleGenerate}
                      className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                      title="Regenerate"
                    >
                      <RefreshCw size={18} className="text-gray-600" />
                    </button>
                  </div>
                </div>
                <div className="prose max-w-none">
                  <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg text-sm overflow-auto max-h-96 border border-gray-100">
                    {result}
                  </pre>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar - Templates */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <h3 className="font-semibold text-gray-900 mb-4">Quick Templates</h3>
            <div className="space-y-2">
              {promptTemplates[activeTab]?.map((template, idx) => (
                <button
                  key={idx}
                  onClick={() => setPrompt(template)}
                  className="w-full p-3 text-left text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-100"
                >
                  {template}
                </button>
              ))}
            </div>

            <div className="mt-6 pt-6 border-t">
              <h4 className="font-semibold text-gray-900 mb-3">Tips</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-blue-600">•</span>
                  Be specific with your prompts
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600">•</span>
                  Include context about the customer or facility
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600">•</span>
                  Review and edit AI-generated content
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600">•</span>
                  Different providers may give different results
                </li>
              </ul>
            </div>

            {providers.length === 0 && (
              <div className="mt-6 p-4 bg-orange-50 rounded-lg border border-orange-200">
                <p className="text-sm text-orange-800 font-medium">No AI providers configured</p>
                <p className="text-sm text-orange-600 mt-1">
                  Configure API keys in Settings to enable AI features.
                </p>
                <Link href="/settings" className="text-sm text-orange-700 underline mt-2 inline-block">
                  Go to Settings
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}
