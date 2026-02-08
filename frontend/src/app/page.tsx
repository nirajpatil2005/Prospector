'use client';

import { useState } from 'react';
import SearchForm from '@/components/SearchForm';
import ResultsList from '@/components/ResultsList';
import { SearchConfig, CompanyAnalysis } from '@/types';
import { startResearchStream, ResearchUpdate } from '@/lib/api';
import { Sparkles, Loader2, ExternalLink, Globe } from 'lucide-react';

export default function Home() {
  const [results, setResults] = useState<CompanyAnalysis[]>([]);
  const [sources, setSources] = useState<{ title: string; url: string; }[]>([]);
  const [insights, setInsights] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [progress, setProgress] = useState<{ current: number, total: number } | null>(null);

  const handleSearch = async (config: SearchConfig) => {
    setIsLoading(true);
    setError(null);
    setResults([]); // Clear previous results
    setSources([]); // Clear previous sources
    setInsights("");
    setStatusMessage("Initializing research agent...");
    setProgress(null);

    try {
      await startResearchStream(config, (update: ResearchUpdate) => {
        if (update.type === 'status') {
          setStatusMessage(update.message || "");
        } else if (update.type === 'progress') {
          setProgress({ current: update.current || 0, total: update.total || 0 });
        } else if (update.type === 'source_resource') {
          if (update.source) {
            setSources(prev => [...prev, update.source!]);
          }
        } else if (update.type === 'company_result') {
          if (update.data) {
            setResults(prev => [...prev, update.data!]);
          }
        } else if (update.type === 'market_insights') {
          if (update.insights) setInsights(update.insights);
        } else if (update.type === 'error') {
          setError(update.message || "Unknown error stream");
          setIsLoading(false);
        } else if (update.type === 'done') {
          setIsLoading(false);
          setStatusMessage("Research completed.");
        }
      });
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred while connecting to the research engine.');
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-cosmic text-slate-100 font-sans selection:bg-purple-500/30 overflow-x-hidden">
      {/* Grid Pattern Overlay */}
      <div className="fixed inset-0 bg-grid-pattern pointer-events-none opacity-20" />

      {/* Navbar */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-slate-950/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-gradient-to-tr from-purple-600 to-blue-600 rounded-lg">
              <Sparkles size={18} className="text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
              Prospector AI
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm font-medium text-gray-400">
            <a href="#" className="hover:text-white transition-colors">History</a>
            <a href="#" className="hover:text-white transition-colors">Settings</a>
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 border-2 border-slate-900" />
          </div>
        </div>
      </nav>

      <div className="relative max-w-7xl mx-auto px-6 py-12 md:py-20 space-y-12">

        {/* Hero Section */}
        <header className="text-center space-y-6 relative max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-xs font-semibold text-purple-300 mb-4 animate-fade-in uppercase tracking-wider">
            <span>Powered by Gemini 2.0</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white drop-shadow-lg">
            Deep Market <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-blue-400">Research</span>
          </h1>

          <p className="text-lg md:text-xl text-slate-400 leading-relaxed">
            Autonomous agent that crawls, analyzes, and synthesizes market data to find your perfect B2B prospects.
          </p>
        </header>

        {/* Search Interface */}
        <section className="animate-fade-in max-w-4xl mx-auto relative z-10" style={{ animationDelay: '200ms' }}>
          <SearchForm onSubmit={handleSearch} isLoading={isLoading} />

          {/* Status Bar */}
          {isLoading && (
            <div className="mt-6 p-4 rounded-xl bg-slate-900/50 border border-white/10 backdrop-blur-md animate-fade-in">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3 text-purple-300">
                  <Loader2 className="animate-spin" size={20} />
                  <span className="font-medium text-sm">{statusMessage}</span>
                </div>
                {progress && (
                  <span className="text-xs text-slate-400 font-mono">
                    {progress.current} / {progress.total}
                  </span>
                )}
              </div>
              {progress && progress.total > 0 && (
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-500"
                    style={{ width: `${(progress.current / progress.total) * 100}%` }}
                  />
                </div>
              )}
            </div>
          )}
        </section>

        {/* Discovery Sources Section */}
        {sources.length > 0 && (
          <section className="animate-fade-in max-w-4xl mx-auto mb-8">
            <div className="flex items-center gap-2 mb-4">
              <div className="p-1.5 bg-blue-500/10 rounded-lg">
                <Globe size={16} className="text-blue-400" />
              </div>
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Discovery Sources</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {sources.map((source, idx) => (
                <a
                  key={idx}
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors group"
                >
                  <div className="p-2 bg-slate-800 rounded-lg group-hover:bg-blue-500/20 group-hover:text-blue-400 transition-colors text-slate-400">
                    <ExternalLink size={14} />
                  </div>
                  <span className="text-sm text-slate-300 truncate font-medium">{source.title || source.url}</span>
                </a>
              ))}
            </div>
          </section>
        )}

        {/* Market Insights Report */}
        {insights && (
          <section className="animate-fade-in max-w-4xl mx-auto mb-12 relative z-10">
            <div className="flex items-center gap-2 mb-4">
              <div className="p-1.5 bg-purple-500/10 rounded-lg">
                <Sparkles size={16} className="text-purple-400" />
              </div>
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">AI Market Insights</h3>
            </div>
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-purple-500/20 backdrop-blur-xl shadow-2xl shadow-purple-900/10">
              <div className="prose prose-invert prose-sm max-w-none text-slate-300">
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">{insights}</pre>
              </div>
            </div>
          </section>
        )}

        {/* Error State */}
        {error && (
          <div className="max-w-4xl mx-auto animate-fade-in p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-200 flex items-center gap-3">
            <div className="p-2 bg-red-500/20 rounded-lg min-w-fit">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" x2="12" y1="8" y2="12" /><line x1="12" x2="12.01" y1="16" y2="16" /></svg>
            </div>
            <div>
              <p className="font-semibold text-sm">Research Failed</p>
              <p className="text-xs opacity-80">{error}</p>
            </div>
          </div>
        )}

        {/* Results Interface */}
        <section className="animate-fade-in" style={{ animationDelay: '400ms' }}>
          <ResultsList results={results} />
        </section>

      </div>

      {/* Footer */}
      <footer className="border-t border-white/5 mt-20 py-8 text-center text-slate-500 text-sm">
        <p>&copy; {new Date().getFullYear()} Prospector AI. Built for deep market analysis.</p>
      </footer>
    </main>
  );
}
