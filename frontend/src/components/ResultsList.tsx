import { CompanyAnalysis } from '../types';
import { ExternalLink, MapPin, Users, Award, Package, Check, AlertTriangle, AlertCircle, TrendingUp, Shield, Globe, DollarSign, Target, Mail } from 'lucide-react';

interface ResultsListProps {
    results: CompanyAnalysis[];
}

export default function ResultsList({ results }: ResultsListProps) {
    if (results.length === 0) return null;

    return (
        <div className="space-y-8 animate-fade-in pb-20">
            <div className="flex items-center justify-between border-b border-white/5 pb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-gradient-to-tr from-blue-500 to-purple-500 rounded-lg">
                        <TrendingUp size={20} className="text-white" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold text-white">Research Results</h2>
                        <p className="text-sm text-slate-400">AI-verified matches based on your criteria</p>
                    </div>
                </div>

                <span className="px-4 py-1.5 bg-slate-800 rounded-full text-sm text-slate-300 border border-slate-700 font-medium">
                    Found {results.length} companies
                </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {results.map((company, idx) => (
                    <div
                        key={idx}
                        className="group relative glass-card rounded-3xl p-6 md:p-8 flex flex-col h-full overflow-hidden"
                        style={{ animationDelay: `${idx * 100}ms` }}
                    >
                        {/* Background Decor */}
                        <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-full blur-2xl -mr-10 -mt-10 transition-all group-hover:bg-purple-500/10" />

                        {/* Card Header */}
                        <div className="flex justify-between items-start gap-4 mb-6 relative z-10">
                            <div>
                                <h3 className="text-xl md:text-2xl font-bold text-slate-100 group-hover:text-blue-300 transition-colors mb-2">
                                    {company.company_name}
                                </h3>
                                <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400">
                                    {company.locations.length > 0 && (
                                        <div className="flex items-center gap-1.5 bg-slate-900/50 px-2.5 py-1 rounded-md">
                                            <MapPin size={14} className="text-indigo-400" />
                                            <span>{company.locations[0]}</span>
                                        </div>
                                    )}
                                    {company.employee_count_estimate && (
                                        <div className="flex items-center gap-1.5 bg-slate-900/50 px-2.5 py-1 rounded-md">
                                            <Users size={14} className="text-cyan-400" />
                                            <span>{company.employee_count_estimate}</span>
                                        </div>
                                    )}
                                    {/* Contact Info */}
                                    {company.contact_info && company.contact_info !== "Unknown" && (
                                        <div className="flex items-center gap-1.5 bg-brand-900/20 px-2.5 py-1 rounded-md border border-brand-500/20 text-brand-200/80">
                                            <Mail size={14} className="text-amber-400" />
                                            <span className="truncate max-w-[150px]" title={company.contact_info}>{company.contact_info}</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <a
                                href={company.website}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-xl text-white font-medium transition-colors shadow-lg shadow-blue-500/20"
                                title="Visit Website"
                            >
                                <span className="hidden sm:inline">Visit Site</span>
                                <ExternalLink size={16} />
                            </a>
                        </div>

                        {/* Relevance Score */}
                        <div className="mb-6">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Relevance Score</span>
                                <div className="flex-1 h-px bg-slate-800" />
                                <span className={`text-sm font-bold ${company.relevance_score >= 80 ? 'text-emerald-400' :
                                    company.relevance_score >= 50 ? 'text-amber-400' : 'text-red-400'
                                    }`}>{company.relevance_score}/100</span>
                            </div>
                            <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden">
                                <div
                                    className={`h-full rounded-full transition-all duration-1000 ${company.relevance_score >= 80 ? 'bg-gradient-to-r from-emerald-600 to-emerald-400' :
                                        company.relevance_score >= 50 ? 'bg-gradient-to-r from-amber-600 to-amber-400' :
                                            'bg-gradient-to-r from-red-600 to-red-400'
                                        }`}
                                    style={{ width: `${company.relevance_score}%` }}
                                />
                            </div>
                        </div>

                        {/* Financials & Strategy (NEW) */}
                        <div className="grid grid-cols-2 gap-4 mb-6 relative z-10 bg-slate-900/40 p-4 rounded-xl border border-white/5">
                            {company.estimated_revenue && (
                                <div className="flex flex-col">
                                    <span className="text-xs text-slate-500 uppercase font-bold mb-1 flex items-center gap-1">
                                        <DollarSign size={10} /> Revenue
                                    </span>
                                    <span className="text-sm text-emerald-300 font-mono font-medium">{company.estimated_revenue}</span>
                                </div>
                            )}
                            {company.market_cap && (
                                <div className="flex flex-col">
                                    <span className="text-xs text-slate-500 uppercase font-bold mb-1 flex items-center gap-1">
                                        <TrendingUp size={10} /> Market Cap
                                    </span>
                                    <span className="text-sm text-blue-300 font-mono font-medium">{company.market_cap}</span>
                                </div>
                            )}
                            {company.strategic_goals && company.strategic_goals.length > 0 && (
                                <div className="col-span-2 mt-2 pt-2 border-t border-white/5">
                                    <span className="text-xs text-slate-500 uppercase font-bold mb-2 flex items-center gap-1">
                                        <Target size={10} /> Strategic Focus
                                    </span>
                                    <div className="flex flex-wrap gap-2">
                                        {company.strategic_goals.slice(0, 3).map((goal, i) => (
                                            <span key={i} className="px-2 py-1 bg-indigo-500/10 text-indigo-300 rounded text-xs border border-indigo-500/20">
                                                {goal}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Summary */}
                        <div className="flex-1 mb-6 relative z-10">
                            <p className="text-slate-400 text-sm leading-relaxed line-clamp-3 group-hover:text-slate-300 transition-colors">
                                {company.summary || "No summary available for this company."}
                            </p>
                        </div>

                        {/* Tags Grid */}
                        <div className="space-y-4 pt-6 border-t border-slate-800/50 relative z-10">

                            {/* Products */}
                            {company.product_categories.length > 0 && (
                                <div className="flex items-start gap-2">
                                    <div className="mt-1">
                                        <Package size={14} className="text-blue-400" />
                                    </div>
                                    <div className="flex flex-wrap gap-1.5">
                                        {company.product_categories.slice(0, 4).map((prod, i) => (
                                            <span key={i} className="px-2 py-0.5 bg-blue-500/10 text-blue-300 rounded text-xs border border-blue-500/20">
                                                {prod}
                                            </span>
                                        ))}
                                        {company.product_categories.length > 4 && (
                                            <span className="px-2 py-0.5 bg-slate-800 text-slate-400 rounded text-xs">
                                                +{company.product_categories.length - 4}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Certifications */}
                            {company.certifications.length > 0 && (
                                <div className="flex items-start gap-2">
                                    <div className="mt-1">
                                        <Shield size={14} className="text-purple-400" />
                                    </div>
                                    <div className="flex flex-wrap gap-1.5">
                                        {company.certifications.slice(0, 3).map((cert, i) => (
                                            <span key={i} className="px-2 py-0.5 bg-purple-500/10 text-purple-300 rounded text-xs border border-purple-500/20">
                                                {cert}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Detailed Data Table */}
                        <div className="mt-8 pt-6 border-t border-slate-800/50 relative z-10 w-full overflow-hidden">
                            <h4 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                                <Package size={14} className="text-blue-400" /> Detailed Analysis
                            </h4>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm text-left text-slate-400">
                                    <thead className="text-xs text-slate-500 uppercase bg-slate-900/50">
                                        <tr>
                                            <th className="px-4 py-3 rounded-l-lg">Category</th>
                                            <th className="px-4 py-3 rounded-r-lg">Details</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-800/30">
                                        {company.founded_year && (
                                            <tr>
                                                <td className="px-4 py-3 font-medium text-slate-300">Founded</td>
                                                <td className="px-4 py-3">{company.founded_year}</td>
                                            </tr>
                                        )}
                                        {company.estimated_revenue && (
                                            <tr>
                                                <td className="px-4 py-3 font-medium text-slate-300">Est. Revenue</td>
                                                <td className="px-4 py-3 text-emerald-400">{company.estimated_revenue}</td>
                                            </tr>
                                        )}
                                        {company.employee_count_estimate && (
                                            <tr>
                                                <td className="px-4 py-3 font-medium text-slate-300">Employees</td>
                                                <td className="px-4 py-3">{company.employee_count_estimate}</td>
                                            </tr>
                                        )}
                                        {company.linkedin_url && (
                                            <tr>
                                                <td className="px-4 py-3 font-medium text-slate-300">Social</td>
                                                <td className="px-4 py-3">
                                                    <a href={company.linkedin_url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline flex items-center gap-1">
                                                        LinkedIn
                                                        {company.follower_count ? <span className="text-slate-500 text-xs">({company.follower_count.toLocaleString()} followers)</span> : null}
                                                    </a>
                                                </td>
                                            </tr>
                                        )}
                                        {company.specialties && company.specialties.length > 0 && (
                                            <tr>
                                                <td className="px-4 py-3 font-medium text-slate-300">Specialties</td>
                                                <td className="px-4 py-3">{company.specialties.join(", ")}</td>
                                            </tr>
                                        )}
                                        {company.contact_info && (
                                            <tr>
                                                <td className="px-4 py-3 font-medium text-slate-300">Contact</td>
                                                <td className="px-4 py-3">{company.contact_info}</td>
                                            </tr>
                                        )}
                                        {company.locations && company.locations.length > 0 && (
                                            <tr>
                                                <td className="px-4 py-3 font-medium text-slate-300">HQ Location</td>
                                                <td className="px-4 py-3">{company.locations.join(", ")}</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                    </div>
                ))}
            </div>
        </div>
    );
}
