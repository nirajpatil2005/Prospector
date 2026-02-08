'use client';

import { useState } from 'react';
import { SearchConfig } from '../types';
import { Plus, X, Search, Loader2, Briefcase, Globe, Fingerprint, Users, ShieldCheck, Box } from 'lucide-react';

interface SearchFormProps {
    onSubmit: (config: SearchConfig) => void;
    isLoading: boolean;
}

export default function SearchForm({ onSubmit, isLoading }: SearchFormProps) {
    const [formData, setFormData] = useState<SearchConfig>({
        included_industries: [''],
        required_keywords: [''],
        target_countries: [''],
        excluded_industries: [],
        min_employees: undefined,
        max_employees: undefined,
        required_certifications: [],
        required_product_categories: []
    });

    const handleChange = (field: keyof SearchConfig, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleArrayChange = (field: keyof SearchConfig, index: number, value: string) => {
        const newArray = [...(formData[field] as string[])];
        newArray[index] = value;
        setFormData(prev => ({ ...prev, [field]: newArray }));
    };

    const addArrayItem = (field: keyof SearchConfig) => {
        const currentArray = formData[field] as string[] || [];
        setFormData(prev => ({ ...prev, [field]: [...currentArray, ''] }));
    };

    const removeArrayItem = (field: keyof SearchConfig, index: number) => {
        const currentArray = formData[field] as string[] || [];
        if (currentArray.length > 1) {
            setFormData(prev => ({ ...prev, [field]: currentArray.filter((_, i) => i !== index) }));
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const cleanedConfig = {
            ...formData,
            included_industries: formData.included_industries.filter(Boolean),
            required_keywords: formData.required_keywords.filter(Boolean),
            target_countries: formData.target_countries.filter(Boolean),
            excluded_industries: formData.excluded_industries?.filter(Boolean),
            required_certifications: formData.required_certifications?.filter(Boolean),
            required_product_categories: formData.required_product_categories?.filter(Boolean),
        };
        onSubmit(cleanedConfig);
    };

    return (
        <form onSubmit={handleSubmit} className="glass-card p-8 rounded-3xl relative overflow-hidden">

            {/* Decorative background blurs */}
            <div className="absolute -top-20 -right-20 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="space-y-10 relative z-10">

                {/* Section: Target Profile */}
                <div className="space-y-6">
                    <div className="flex items-center gap-3 border-b border-white/5 pb-2">
                        <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                            <Briefcase size={20} />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-200">Target Profile</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Industries */}
                        <div className="space-y-3">
                            <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                                Target Industries
                            </label>
                            <div className="space-y-2">
                                {formData.included_industries.map((item, index) => (
                                    <div key={index} className="flex gap-2 group">
                                        <input
                                            type="text"
                                            value={item}
                                            onChange={(e) => handleArrayChange('included_industries', index, e.target.value)}
                                            placeholder="e.g. SaaS, Fintech"
                                            className="input-glass w-full px-4 py-3"
                                            required={index === 0}
                                        />
                                        {index === formData.included_industries.length - 1 ? (
                                            <button
                                                type="button"
                                                onClick={() => addArrayItem('included_industries')}
                                                className="p-3 bg-slate-800 hover:bg-blue-600/20 hover:text-blue-400 rounded-xl transition-all border border-slate-700 hover:border-blue-500/30"
                                            >
                                                <Plus size={20} />
                                            </button>
                                        ) : (
                                            <button
                                                type="button"
                                                onClick={() => removeArrayItem('included_industries', index)}
                                                className="p-3 text-slate-600 hover:text-red-400 transition-colors"
                                            >
                                                <X size={20} />
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Locations */}
                        <div className="space-y-3">
                            <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                                <Globe size={14} /> Target Locations
                            </label>
                            <div className="space-y-2">
                                {formData.target_countries.map((item, index) => (
                                    <div key={index} className="flex gap-2 group">
                                        <input
                                            type="text"
                                            value={item}
                                            onChange={(e) => handleArrayChange('target_countries', index, e.target.value)}
                                            placeholder="e.g. USA, Germany"
                                            className="input-glass w-full px-4 py-3"
                                            required={index === 0}
                                        />
                                        {index === formData.target_countries.length - 1 ? (
                                            <button
                                                type="button"
                                                onClick={() => addArrayItem('target_countries')}
                                                className="p-3 bg-slate-800 hover:bg-purple-600/20 hover:text-purple-400 rounded-xl transition-all border border-slate-700 hover:border-purple-500/30"
                                            >
                                                <Plus size={20} />
                                            </button>
                                        ) : (
                                            <button
                                                type="button"
                                                onClick={() => removeArrayItem('target_countries', index)}
                                                className="p-3 text-slate-600 hover:text-red-400 transition-colors"
                                            >
                                                <X size={20} />
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Section: Refinement */}
                <div className="space-y-6">
                    <div className="flex items-center gap-3 border-b border-white/5 pb-2">
                        <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                            <Fingerprint size={20} />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-200">Refinement</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Keywords */}
                        <div className="space-y-3">
                            <label className="text-sm font-medium text-slate-400">Must Have Keywords</label>
                            <div className="space-y-2">
                                {formData.required_keywords.map((item, index) => (
                                    <div key={index} className="flex gap-2 group">
                                        <input
                                            type="text"
                                            value={item}
                                            onChange={(e) => handleArrayChange('required_keywords', index, e.target.value)}
                                            placeholder="e.g. enterprise, ai-driven"
                                            className="input-glass w-full px-4 py-3"
                                            required={index === 0}
                                        />
                                        {index === formData.required_keywords.length - 1 ? (
                                            <button
                                                type="button"
                                                onClick={() => addArrayItem('required_keywords')}
                                                className="p-3 bg-slate-800 hover:bg-pink-600/20 hover:text-pink-400 rounded-xl transition-all border border-slate-700 hover:border-pink-500/30"
                                            >
                                                <Plus size={20} />
                                            </button>
                                        ) : (
                                            <button
                                                type="button"
                                                onClick={() => removeArrayItem('required_keywords', index)}
                                                className="p-3 text-slate-600 hover:text-red-400 transition-colors"
                                            >
                                                <X size={20} />
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Employee Count */}
                        <div className="space-y-3">
                            <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                                <Users size={14} /> Company Size (Employees)
                            </label>
                            <div className="flex gap-4">
                                <div className="relative w-full">
                                    <span className="absolute left-4 top-3.5 text-slate-600 text-xs font-bold">MIN</span>
                                    <input
                                        type="number"
                                        placeholder="0"
                                        value={formData.min_employees || ''}
                                        onChange={(e) => handleChange('min_employees', e.target.value ? parseInt(e.target.value) : undefined)}
                                        className="input-glass w-full pl-12 pr-4 py-3"
                                    />
                                </div>
                                <div className="relative w-full">
                                    <span className="absolute left-4 top-3.5 text-slate-600 text-xs font-bold">MAX</span>
                                    <input
                                        type="number"
                                        placeholder="Any"
                                        value={formData.max_employees || ''}
                                        onChange={(e) => handleChange('max_employees', e.target.value ? parseInt(e.target.value) : undefined)}
                                        className="input-glass w-full pl-12 pr-4 py-3"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Submit Button */}
                <div className="pt-4">
                    <button
                        type="submit"
                        disabled={isLoading}
                        className={`w-full py-5 px-6 rounded-2xl font-bold text-white shadow-xl transition-all duration-300 transform active:scale-[0.98] ${isLoading
                            ? 'bg-slate-800 cursor-not-allowed opacity-70'
                            : 'bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:shadow-purple-500/25 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500'
                            }`}
                    >
                        <div className="flex items-center justify-center gap-3">
                            {isLoading ? (
                                <>
                                    <Loader2 className="animate-spin" size={24} />
                                    <span className="text-lg">Analyzing Market...</span>
                                </>
                            ) : (
                                <>
                                    <Search size={24} />
                                    <span className="text-lg">Start Deep Research</span>
                                </>
                            )}
                        </div>
                    </button>
                </div>
            </div>
        </form>
    );
}
