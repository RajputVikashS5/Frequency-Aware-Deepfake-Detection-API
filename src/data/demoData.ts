import type {
  AnalysisResponse,
  EvidenceItem,
  Verdict,
} from '@/types/analysis';

export const demoVerdicts: Verdict[] = ['REAL', 'FAKE', 'MISLEADING', 'UNVERIFIED'];

const demoEvidence: EvidenceItem[] = [
  {
    source_title: 'Reuters Fact Check',
    publisher: 'Reuters',
    excerpt:
      'Reuters reviewed the claim and found it to be supported by multiple independent sources and official records.',
    url: 'https://www.example.com/reuters-fact-check',
    classification: 'supports',
  },
  {
    source_title: 'Associated Press',
    publisher: 'AP News',
    excerpt:
      'AP could not independently verify the claim; the cited source material was unavailable at time of publication.',
    url: 'https://www.example.com/ap-report',
    classification: 'insufficient',
  },
  {
    source_title: 'Snopes Investigation',
    publisher: 'Snopes',
    excerpt:
      'The image circulating with this story appears to be digitally altered; metadata analysis shows signs of manipulation.',
    url: 'https://www.example.com/snopes-investigation',
    classification: 'contradicts',
  },
];

export function createDemoResponse(
  headline: string,
  articleText: string,
  sourceUrl: string | undefined,
  mode: 'text_image' | 'text_only',
  hasImage: boolean
): AnalysisResponse {
  const verdict: Verdict = 'MISLEADING';
  const now = new Date().toISOString();

  return {
    analysis_id: `demo-${Date.now()}`,
    verdict,
    confidence: 0.72,
    explanation:
      'This is sample data from Demo Mode. The text model found the claim to be partially consistent with known sources, but several key assertions lack corroboration. The overall assessment is "Misleading" because the article combines factual elements with unverified claims.',
    text_analysis: {
      model_label: 'MISLEADING',
      confidence: 0.74,
      explanation:
        'Text analysis (sample): the language uses loaded emotional framing and cites unnamed sources. Some factual claims align with known records, but key assertions are unsupported.',
      indicators: [
        'Emotionally loaded language detected',
        'Reliance on unnamed or anonymous sources',
        'Some factual claims corroborated by external evidence',
        'Clickbait-style headline phrasing',
      ],
    },
    image_analysis:
      mode === 'text_image' && hasImage
        ? {
            model_label: 'SUSPICIOUS',
            confidence: 0.68,
            explanation:
              'Image analysis (sample): the uploaded image shows potential signs of digital alteration. Texture inconsistencies were detected near the subject boundary.',
            image_text_consistency:
              'The image partially matches the narrative in the headline but contains visual elements not referenced in the article text.',
            manipulation_signals: [
              'Possible edge artifacts near subject boundary',
              'Metadata timestamp inconsistent with claimed event date',
            ],
          }
        : null,
    evidence: demoEvidence,
    created_at: now,
    mode,
    headline,
    article_text: articleText,
    source_url: sourceUrl,
  };
}
