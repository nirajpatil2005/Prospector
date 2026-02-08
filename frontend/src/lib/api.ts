import { SearchConfig, ResearchResponse, CompanyAnalysis } from '../types';

const API_BASE_URL = 'http://localhost:8002';

export interface ResearchUpdate {
    type: 'status' | 'company_result' | 'error' | 'done' | 'progress' | 'source_resource' | 'market_insights';
    message?: string;
    data?: CompanyAnalysis;
    source?: { title: string; url: string; };
    insights?: string;
    current?: number;
    total?: number;
}

export async function startResearchStream(
    config: SearchConfig,
    onUpdate: (update: ResearchUpdate) => void
): Promise<void> {
    try {
        const response = await fetch(`${API_BASE_URL}/research`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream',
            },
            body: JSON.stringify(config),
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) throw new Error("No reader available");

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        onUpdate(data);
                    } catch (e) {
                        console.error('Error parsing SSE data:', e, line);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Research stream failed:', error);
        throw error;
    }
}

// Legacy wrapper if needed, but we should switch to stream
export async function startResearch(config: SearchConfig): Promise<ResearchResponse> {
    // This is now just a placeholder or could be implemented by buffering the stream
    // For now we will modify the UI to use startResearchStream
    throw new Error("Use startResearchStream instead");
}
