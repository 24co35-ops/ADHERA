import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import { useI18n } from '../lib/i18n';
import { GlassCard } from './GlassCard';
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Bot,
  User as UserIcon,
  AlertTriangle,
  BookOpen,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  ShieldCheck,
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

const QUICK_PROMPTS = [
  'What should I do if I miss a dose?',
  'What are common side effects of Metformin?',
  'Can I take blood pressure medication on an empty stomach?',
  'How does breathing exercise improve adherence?',
];

export const ChatDrawer: React.FC = () => {
  const { user, role } = useAuthStore();
  const { t } = useI18n();
  const navigate = useNavigate();

  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      loadHistory();
      setTimeout(scrollToBottom, 100);
    }
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) scrollToBottom();
  }, [messages]);

  const loadHistory = async () => {
    try {
      const res = await api.get<ChatMessage[]>('/chat/history');
      if (res.success && res.data && res.data.length > 0) {
        setMessages(res.data);
      } else if (messages.length === 0) {
        // Initial welcome message
        setMessages([
          {
            id: 'welcome',
            role: 'assistant',
            content:
              'Hello! I am Adhera Clinical Assistant, grounded strictly in verified medication adherence guidelines. How can I help you understand your medications or daily routine today?',
            created_at: new Date().toISOString(),
          },
        ]);
      }
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  };

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: Math.random().toString(36).substring(2, 9),
      role: 'user',
      content: textToSend.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInputQuery('');
    setLoading(true);

    try {
      const res = await api.post<any>('/chat/query', { message: userMsg.content });
      if (res.success && res.data) {
        const assistantMsg: ChatMessage = {
          id: res.data.id || Math.random().toString(36).substring(2, 9),
          role: 'assistant',
          content: res.data.content,
          sources: res.data.sources || [],
          suggested_feedback: res.data.suggested_feedback,
          created_at: res.data.created_at || new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }
    } catch (err) {
      console.error('Failed to query chat:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).substring(2, 9),
          role: 'assistant',
          content:
            'I encountered an issue connecting to the clinical knowledge base. Please verify your connection or consult your healthcare provider directly.',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSourceExpand = (id: string) => {
    setExpandedSources((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleReportSideEffect = (feedback: SuggestedFeedback) => {
    setIsOpen(false);
    // Navigate to feedback page with query parameters
    const params = new URLSearchParams({
      medicine_name: feedback.medicine_name,
      description: `Reported side effect: ${feedback.possible_side_effect}`,
      severity: String(feedback.severity || 2),
    });
    if (feedback.medicine_id) params.set('medicine_id', feedback.medicine_id);
    navigate(`/feedback?${params.toString()}`);
  };

  return (
    <>
      {/* Floating Action Button */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-40 btn-press flex items-center gap-2.5 px-4 py-3 rounded-full bg-gradient-to-r from-primary-dark via-primary to-primary-light text-surface font-bold text-sm shadow-glow hover:scale-105 transition-all duration-200"
          aria-label="Open Medical Assistant Chat"
        >
          <Sparkles className="w-5 h-5 fill-current" />
          <span className="hidden sm:inline">Ask Adhera</span>
        </button>
      )}

      {/* Slide-over Backdrop & Drawer */}
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
            onClick={() => setIsOpen(false)}
          />

          {/* Drawer Container */}
          <div className="relative w-full max-w-lg bg-surface border-l border-white/10 shadow-2xl flex flex-col h-full z-10 animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-surface-container-low">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-glow">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                    <span>{t('chat.title')}</span>
                    <span className="text-[10px] uppercase font-bold text-primary bg-primary/10 px-1.5 py-0.5 rounded">
                      RAG Verified
                    </span>
                  </h3>
                  <p className="text-[11px] text-on-surface-variant">
                    {t('chat.subtitle')}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-on-surface-variant hover:text-white hover:bg-white/10 transition-colors"
                aria-label="Close chat drawer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Safety Banner */}
            <div className="bg-primary/5 border-b border-primary/10 px-4 py-2 flex items-center gap-2 text-[11px] text-primary">
              <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
              <span>{t('chat.disclaimer')}</span>
            </div>

            {/* Chat Messages Stream */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={clsx('flex flex-col', msg.role === 'user' ? 'items-end' : 'items-start')}
                >
                  <div className="flex items-start gap-2 max-w-[88%]">
                    {msg.role === 'assistant' && (
                      <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-primary shrink-0 mt-1">
                        <Bot className="w-3.5 h-3.5" />
                      </div>
                    )}

                    <div
                      className={clsx(
                        'p-3.5 rounded-2xl text-xs sm:text-sm leading-relaxed whitespace-pre-wrap',
                        msg.role === 'user'
                          ? 'bg-primary text-surface font-medium rounded-tr-sm shadow-glow'
                          : 'bg-white/5 border border-white/10 text-on-surface rounded-tl-sm'
                      )}
                    >
                      {msg.content}

                      {/* Side Effect Reporting Action Button */}
                      {msg.suggested_feedback && (
                        <div className="mt-3 p-2.5 rounded-xl bg-status-warning/10 border border-status-warning/30 text-white">
                          <div className="flex items-center gap-1.5 text-status-warning font-bold text-xs mb-1">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span>Possible Side Effect Detected</span>
                          </div>
                          <p className="text-[11px] text-on-surface-variant mb-2">
                            {msg.suggested_feedback.possible_side_effect} ({msg.suggested_feedback.medicine_name})
                          </p>
                          <button
                            type="button"
                            onClick={() => handleReportSideEffect(msg.suggested_feedback!)}
                            className="btn-press flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-status-warning text-surface text-xs font-bold hover:bg-status-warning/90 transition-colors"
                          >
                            <ExternalLink className="w-3 h-3" />
                            <span>Report to My Healthcare Provider</span>
                          </button>
                        </div>
                      )}

                      {/* Source Document Citations */}
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-2.5 pt-2 border-t border-white/10">
                          <button
                            type="button"
                            onClick={() => toggleSourceExpand(msg.id)}
                            className="flex items-center gap-1 text-[11px] text-primary/80 hover:text-primary transition-colors font-semibold"
                          >
                            <BookOpen className="w-3 h-3" />
                            <span>
                              {msg.sources.length} Verified Source
                              {msg.sources.length > 1 ? 's' : ''}
                            </span>
                            {expandedSources[msg.id] ? (
                              <ChevronUp className="w-3 h-3" />
                            ) : (
                              <ChevronDown className="w-3 h-3" />
                            )}
                          </button>

                          {expandedSources[msg.id] && (
                            <div className="mt-2 space-y-1.5">
                              {msg.sources.map((src, idx) => (
                                <div
                                  key={idx}
                                  className="p-2 rounded-lg bg-black/30 border border-white/5 text-[10px] text-on-surface-variant"
                                >
                                  <div className="font-bold text-white mb-0.5">{src.document_name}</div>
                                  <p className="italic">"{src.snippet}"</p>
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
                <div className="flex items-center gap-2 text-xs text-primary animate-pulse p-2">
                  <Bot className="w-4 h-4" />
                  <span>Reviewing clinical reference base...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Quick Prompts Suggestions */}
            {messages.length <= 2 && (
              <div className="px-4 py-2 border-t border-white/5 bg-surface-container-lowest/50">
                <span className="text-[10px] uppercase font-bold text-on-surface-variant mb-1.5 block">
                  Suggested Questions:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {QUICK_PROMPTS.map((prompt, idx) => (
                    <button
                      key={idx}
                      type="button"
                      disabled={loading}
                      onClick={() => handleSend(prompt)}
                      className="text-[11px] px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-on-surface text-left transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input Form */}
            <div className="p-4 border-t border-white/10 bg-surface-container-low">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                className="flex items-center gap-2"
              >
                <input
                  id="chat-drawer-query"
                  name="chatDrawerQuery"
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  placeholder={t('chat.input_placeholder')}
                  disabled={loading}
                  className="flex-1 px-4 py-2.5 rounded-xl glass-input text-xs sm:text-sm placeholder:text-on-surface-variant/50"
                />
                <button
                  type="submit"
                  disabled={loading || !inputQuery.trim()}
                  className="btn-press p-2.5 rounded-xl bg-primary text-surface font-bold hover:bg-primary-container disabled:opacity-40 transition-colors shadow-glow"
                  aria-label="Send query"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
