import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { useAuthStore } from '../../stores/authStore';
import { GlassCard } from '../../components/GlassCard';
import {
  MessageSquare,
  Bot,
  Send,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  BookOpen,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Trash2,
} from 'lucide-react';
import clsx from 'clsx';

interface SourceCitation {
  document_name: string;
  snippet: string;
  score?: number;
}

interface SuggestedFeedback {
  medicine_id?: string;
  medicine_name: string;
  possible_side_effect: string;
  severity: number;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceCitation[];
  suggested_feedback?: SuggestedFeedback;
  created_at: string;
}

const SAMPLE_QUESTIONS = [
  'What should I do if I miss a dose of my morning medication?',
  'What are common side effects of Metformin and how can I reduce nausea?',
  'Why do ACE inhibitors like Lisinopril sometimes cause a dry cough?',
  'Can I take thyroid medication with morning coffee or food?',
  'How does daily Box breathing help regulate high blood pressure?',
];

export const ChatPage: React.FC = () => {
  const { user, role } = useAuthStore();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadHistory = async () => {
    try {
      const res = await api.get<ChatMessage[]>('/chat/history');
      if (res.success && res.data && res.data.length > 0) {
        setMessages(res.data);
      } else {
        setMessages([
          {
            id: 'welcome',
            role: 'assistant',
            content: `Hello ${user?.full_name || ''}! I am your clinical reference assistant on Adhera. I can answer questions regarding medication routines, missed doses, expected side effects, and lifestyle guidelines based directly on clinical literature.`,
            created_at: new Date().toISOString(),
          },
        ]);
      }
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (queryText?: string) => {
    const text = queryText || inputQuery;
    if (!text.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: Math.random().toString(36).substring(2, 9),
      role: 'user',
      content: text.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInputQuery('');
    setLoading(true);

    try {
      const res = await api.post<any>('/chat/query', { message: userMsg.content });
      if (res.success && res.data) {
        setMessages((prev) => [
          ...prev,
          {
            id: res.data.id || Math.random().toString(36).substring(2, 9),
            role: 'assistant',
            content: res.data.content,
            sources: res.data.sources || [],
            suggested_feedback: res.data.suggested_feedback,
            created_at: res.data.created_at || new Date().toISOString(),
          },
        ]);
      }
    } catch (err) {
      console.error('Chat query failed:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).substring(2, 9),
          role: 'assistant',
          content: 'Unable to reach the clinical knowledge base. Please consult your physician.',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleReportSideEffect = (feedback: SuggestedFeedback) => {
    const params = new URLSearchParams({
      medicine_name: feedback.medicine_name,
      description: `Reported side effect: ${feedback.possible_side_effect}`,
      severity: String(feedback.severity || 2),
    });
    if (feedback.medicine_id) params.set('medicine_id', feedback.medicine_id);
    navigate(`/feedback?${params.toString()}`);
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 h-[calc(100vh-6rem)] flex flex-col">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 shrink-0">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <Bot className="w-7 h-7 text-primary" />
            <span>Clinical Knowledge Assistant</span>
            <span className="text-xs uppercase font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-lg border border-primary/20">
              RAG Grounded
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-on-surface-variant mt-1">
            Grounded medication advice, side-effect guidance, and adherence protocols with zero hallucination.
          </p>
        </div>
      </div>

      {/* Main Chat Container */}
      <GlassCard className="flex-1 flex flex-col overflow-hidden border-white/10 shadow-2xl">
        {/* Safety Disclaimer Banner */}
        <div className="bg-primary/5 border-b border-primary/10 px-4 py-2.5 flex items-center gap-2 text-xs text-primary shrink-0">
          <ShieldCheck className="w-4 h-4 shrink-0" />
          <span>
            Answers are retrieved strictly from uploaded medical guidelines. This does not replace professional medical evaluation.
          </span>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={clsx('flex flex-col', msg.role === 'user' ? 'items-end' : 'items-start')}
            >
              <div className="flex items-start gap-3 max-w-[85%]">
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-xl bg-primary/20 border border-primary/30 flex items-center justify-center text-primary shrink-0 mt-1 shadow-glow">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={clsx(
                    'p-4 rounded-2xl text-xs sm:text-sm leading-relaxed whitespace-pre-wrap',
                    msg.role === 'user'
                      ? 'bg-primary text-surface font-medium rounded-tr-sm shadow-glow'
                      : 'bg-white/5 border border-white/10 text-on-surface rounded-tl-sm'
                  )}
                >
                  {msg.content}

                  {/* 1-Click Side-Effect Reporting */}
                  {msg.suggested_feedback && (
                    <div className="mt-3 p-3 rounded-xl bg-status-warning/10 border border-status-warning/30 text-white">
                      <div className="flex items-center gap-1.5 text-status-warning font-bold text-xs mb-1">
                        <AlertTriangle className="w-4 h-4" />
                        <span>Possible Side Effect Detected</span>
                      </div>
                      <p className="text-xs text-on-surface-variant mb-2.5">
                        {msg.suggested_feedback.possible_side_effect} ({msg.suggested_feedback.medicine_name})
                      </p>
                      <button
                        type="button"
                        onClick={() => handleReportSideEffect(msg.suggested_feedback!)}
                        className="btn-press flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-status-warning text-surface text-xs font-bold hover:bg-status-warning/90 transition-colors"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        <span>Report to My Healthcare Provider</span>
                      </button>
                    </div>
                  )}

                  {/* Document Sources */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-white/10">
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedSources((prev) => ({ ...prev, [msg.id]: !prev[msg.id] }))
                        }
                        className="flex items-center gap-1.5 text-xs text-primary/90 hover:text-primary transition-colors font-semibold"
                      >
                        <BookOpen className="w-3.5 h-3.5" />
                        <span>
                          {msg.sources.length} Verified Document Source
                          {msg.sources.length > 1 ? 's' : ''}
                        </span>
                        {expandedSources[msg.id] ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5" />
                        )}
                      </button>

                      {expandedSources[msg.id] && (
                        <div className="mt-2 space-y-2">
                          {msg.sources.map((src, idx) => (
                            <div
                              key={idx}
                              className="p-2.5 rounded-xl bg-black/40 border border-white/5 text-xs text-on-surface-variant"
                            >
                              <div className="font-bold text-white mb-1 flex items-center justify-between">
                                <span>{src.document_name}</span>
                                {src.score && (
                                  <span className="text-[10px] font-mono text-primary">
                                    Relevance: {src.score}
                                  </span>
                                )}
                              </div>
                              <p className="italic text-[11px]">"{src.snippet}"</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-xs text-primary animate-pulse p-3">
              <Bot className="w-4 h-4" />
              <span>Synthesizing response from verified clinical reference guidelines...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Prompts */}
        {messages.length <= 2 && (
          <div className="p-3 border-t border-white/5 bg-surface-container-lowest/40 shrink-0">
            <span className="text-[10px] uppercase font-bold text-on-surface-variant mb-1.5 block">
              Suggested Topics:
            </span>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_QUESTIONS.map((q, idx) => (
                <button
                  key={idx}
                  type="button"
                  disabled={loading}
                  onClick={() => handleSend(q)}
                  className="text-xs px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-on-surface text-left transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Bar */}
        <div className="p-4 border-t border-white/10 bg-surface-container-low shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-3"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask about medications, side-effects, missed doses..."
              disabled={loading}
              className="flex-1 px-4 py-3 rounded-xl glass-input text-xs sm:text-sm placeholder:text-on-surface-variant/50"
            />
            <button
              type="submit"
              disabled={loading || !inputQuery.trim()}
              className="btn-press px-5 py-3 rounded-xl bg-primary text-surface font-bold text-sm hover:bg-primary-container disabled:opacity-40 transition-colors shadow-glow flex items-center gap-2"
            >
              <span>Ask</span>
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </GlassCard>
    </div>
  );
};
