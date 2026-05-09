export interface ChatResponse {
  grounded?: boolean;
  answer_sentences?: string[];
  citation_url?: string;
  footer?: string;
  educational_links?: string[];
  retrieval?: {
    detected?: boolean;
    top_score?: number;
    chunk_id?: string;
  };
  timestamp?: string;
  error?: string;
}

export async function sendMessage(query: string): Promise<ChatResponse> {
  const response = await fetch("/api/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}
