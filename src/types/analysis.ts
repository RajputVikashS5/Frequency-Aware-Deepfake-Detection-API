export type Verdict = 'REAL' | 'FAKE' | 'MISLEADING' | 'UNVERIFIED';

export type AnalysisMode = 'text_image' | 'text_only';

export type EvidenceClassification = 'supports' | 'contradicts' | 'insufficient';

export interface TextAnalysisResult {
  model_label?: string;
  confidence?: number;
  explanation?: string;
  indicators?: string[];
}

export interface ImageAnalysisResult {
  model_label?: string;
  confidence?: number;
  explanation?: string;
  image_text_consistency?: string;
  manipulation_signals?: string[];
}

export interface EvidenceItem {
  source_title: string;
  publisher?: string;
  excerpt: string;
  url: string;
  classification?: EvidenceClassification;
}

export interface AnalysisRequest {
  headline: string;
  article_text: string;
  source_url?: string;
  mode: AnalysisMode;
  image?: File;
}

export interface AnalysisResponse {
  analysis_id: string;
  verdict: Verdict;
  confidence?: number;
  explanation: string;
  text_analysis?: TextAnalysisResult;
  image_analysis?: ImageAnalysisResult | null;
  evidence?: EvidenceItem[];
  created_at: string;
  mode: AnalysisMode;
  headline: string;
  article_text: string;
  source_url?: string;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
}

export interface HistoryEntry {
  analysis_id: string;
  headline: string;
  verdict: Verdict;
  confidence?: number;
  mode: AnalysisMode;
  created_at: string;
  has_image: boolean;
}
