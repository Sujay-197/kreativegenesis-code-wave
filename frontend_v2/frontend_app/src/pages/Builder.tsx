import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Sparkles, Code2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import ChatInterface from '../components/ChatInterface';
import BlueprintPanel from '../components/BlueprintPanel';
import type { Message } from '../components/ChatInterface';
import type { RequirementsState } from '../lib/aiEngine';
import RequirementsSummary from '../components/RequirementsSummary';
import GenerationProgress from '../components/GenerationProgress';
import AppPreview from '../components/AppPreview';
import ModeCard from '../components/ModeCard';
import {
  initialRequirements,
  processUserMessage,
  getOpeningMessage,
  generateAppHTML,
  getOverallConfidence,
} from '../lib/aiEngine';

const API_BASE = (import.meta as any).env?.VITE_API_URL
  ? `${(import.meta as any).env.VITE_API_URL}/api`
  : '/api';

type BuilderStage = 'mode-select' | 'chat' | 'summary' | 'generating' | 'preview';

const TOTAL_QUESTIONS = 7;

const generationStages = [
  'Analyzing requirements...',
  'Selecting template...',
  'Generating UI structure...',
  'Wiring business logic...',
  'Finalizing your app...',
];

const toConfidenceValue = (value?: string | null): number => {
  if (!value) return 0;
  if (value.toLowerCase().includes('not yet discussed')) return 0;
  return 75;
};

const mapSpecToRequirements = (spec?: Record<string, string>): RequirementsState => {
  if (!spec) return initialRequirements();
  return {
    auth: { label: 'Auth & Users', value: spec.auth_and_users ?? null, confidence: toConfidenceValue(spec.auth_and_users) },
    data: { label: 'Data & Storage', value: spec.data_and_storage ?? null, confidence: toConfidenceValue(spec.data_and_storage) },
    ui: { label: 'UI Complexity', value: spec.ui_complexity ?? null, confidence: toConfidenceValue(spec.ui_complexity) },
    logic: { label: 'Business Logic', value: spec.business_logic ?? null, confidence: toConfidenceValue(spec.business_logic) },
    integrations: { label: 'Integrations', value: spec.integrations ?? null, confidence: toConfidenceValue(spec.integrations) },
  };
};

const buildHtmlDocument = (html: string, css?: string, js?: string): string => {
  let result = html || '';
  const styleBlock = css ? `<style>${css}</style>` : '';
  const scriptBlock = js ? `<script>${js}</script>` : '';

  if (styleBlock) {
    if (result.includes('</head>')) {
      result = result.replace('</head>', `${styleBlock}</head>`);
    } else {
      result = `${styleBlock}${result}`;
    }
  }

  if (scriptBlock) {
    if (result.includes('</body>')) {
      result = result.replace('</body>', `${scriptBlock}</body>`);
    } else {
      result = `${result}${scriptBlock}`;
    }
  }

  return result;
};

export default function Builder() {
  const [stage, setStage] = useState<BuilderStage>('mode-select');
  const [mode, setMode] = useState<'simple' | 'expert'>('simple');
  const [messages, setMessages] = useState<Message[]>([]);
  const [requirements, setRequirements] = useState<RequirementsState>(initialRequirements());
  const [appName, setAppName] = useState('');
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [questionCount, setQuestionCount] = useState(0);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generationStage, setGenerationStage] = useState(generationStages[0]);
  const [generatedHTML, setGeneratedHTML] = useState('');
  const [showGreeting, setShowGreeting] = useState(false);
  const [greetingMode, setGreetingMode] = useState<'simple' | 'expert'>('simple');
  const conversationHistory = useRef<{ role: 'user' | 'ai'; content: string }[]>([]);
  const sessionIdRef = useRef<string | null>(null);
  const greetingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const selectMode = useCallback((selectedMode: 'simple' | 'expert') => {
    setMode(selectedMode);
    setGreetingMode(selectedMode);
    // Show greeting card, auto-dismiss after 2.5 s
    setShowGreeting(true);
    if (greetingTimerRef.current) clearTimeout(greetingTimerRef.current);
    greetingTimerRef.current = setTimeout(() => setShowGreeting(false), 2500);

    const opening = getOpeningMessage(selectedMode);
    const openingMsg: Message = {
      id: crypto.randomUUID(),
      role: 'ai',
      content: opening,
      timestamp: new Date(),
    };
    conversationHistory.current = [{ role: 'ai', content: opening }];
    setMessages([openingMsg]);
    setStage('chat');
  }, []);

  // Cleanup greeting timer on unmount
  useEffect(() => {
    return () => { if (greetingTimerRef.current) clearTimeout(greetingTimerRef.current); };
  }, []);

  const handleSend = useCallback(
    async (text: string) => {
      if (isAiLoading) return;

      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: text,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsAiLoading(true);

      // Try backend first, fall back to local engine
      let nextQuestion = '';
      let updatedRequirements = requirements;
      let detectedName = '';
      let isReady = false;

      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 20000);

        const endpoint = mode === 'expert' ? `${API_BASE}/chat/tailored` : `${API_BASE}/chat/simple`;
        const payload = mode === 'expert'
          ? { session_id: sessionIdRef.current, message: text }
          : { session_id: sessionIdRef.current, user_message: text };

        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!res.ok) throw new Error(`API ${res.status}`);

        const data = await res.json();
        sessionIdRef.current = data.session_id;
        nextQuestion = data.next_question;

        if (mode === 'expert') {
          updatedRequirements = mapSpecToRequirements(data.technical_spec);
          isReady = (data.confidence_score ?? 0) >= 80;
        } else {
          // Map backend requirements_object into our local RequirementsState
          if (data.requirements_object) {
            const ro = data.requirements_object;
            updatedRequirements = {
              auth: { label: 'Auth & Users', value: ro.auth_and_users || null, confidence: ro.auth_and_users ? 75 : 0 },
              data: { label: 'Data & Storage', value: ro.data_and_storage || null, confidence: ro.data_and_storage ? 75 : 0 },
              ui: { label: 'UI Complexity', value: ro.ui_complexity || null, confidence: ro.ui_complexity ? 70 : 0 },
              logic: { label: 'Business Logic', value: ro.business_logic || null, confidence: ro.business_logic ? 65 : 0 },
              integrations: { label: 'Integrations', value: ro.integrations || null, confidence: ro.integrations ? 60 : 0 },
            };
          }

          isReady = (data.confidence_score ?? 0) >= 80;
        }
      } catch {
        // Fallback to fully local engine
        console.warn('Backend unavailable — using local AI engine');
        const result = processUserMessage(text, conversationHistory.current, requirements, mode);
        nextQuestion = result.nextQuestion;
        updatedRequirements = result.updatedRequirements;
        detectedName = result.appName;
        isReady = result.isReady;
      }

      conversationHistory.current = [
        ...conversationHistory.current,
        { role: 'user', content: text },
      ];

      setRequirements(updatedRequirements);
      if (detectedName) setAppName(detectedName);
      setQuestionCount((c) => c + 1);

      if (isReady) {
        const summaryMsg: Message = {
          id: crypto.randomUUID(),
          role: 'ai',
          content:
            mode === 'simple'
              ? "I think I have a solid understanding of what you need. Let me show you a summary of your app before I build it."
              : "Requirements confidence threshold reached. Review the spec below before initiating generation.",
          timestamp: new Date(),
        };
        conversationHistory.current = [
          ...conversationHistory.current,
          { role: 'ai', content: summaryMsg.content },
        ];
        setMessages((prev) => [...prev, summaryMsg]);
        setIsAiLoading(false);
        setTimeout(() => setStage('summary'), 800);
      } else {
        const aiMsg: Message = {
          id: crypto.randomUUID(),
          role: 'ai',
          content: nextQuestion,
          timestamp: new Date(),
        };
        conversationHistory.current = [
          ...conversationHistory.current,
          { role: 'ai', content: nextQuestion },
        ];
        setMessages((prev) => [...prev, aiMsg]);
        setIsAiLoading(false);
      }
    },
    [isAiLoading, requirements, mode]
  );

  const handleConfirmGenerate = useCallback(() => {
    setStage('generating');
    setGenerationProgress(0);

    let stageIndex = 0;
    const interval = setInterval(() => {
      setGenerationProgress((p) => {
        const next = p + 4 + Math.random() * 6;
        const clamped = Math.min(next, 95);
        const newStageIndex = Math.floor((clamped / 100) * generationStages.length);
        if (newStageIndex !== stageIndex && newStageIndex < generationStages.length) {
          stageIndex = newStageIndex;
          setGenerationStage(generationStages[stageIndex]);
        }
        return clamped;
      });
    }, 200);

    // Try backend generate, fall back to local
    (async () => {
      let html = '';
      try {
        const endpoint = mode === 'expert' ? `${API_BASE}/generate/tailored` : `${API_BASE}/generate`;
        const payload = mode === 'expert'
          ? { session_id: sessionIdRef.current }
          : {
            session_id: sessionIdRef.current,
            requirements_object: {
              auth_and_users: requirements.auth.value ?? '',
              data_and_storage: requirements.data.value ?? '',
              ui_complexity: requirements.ui.value ?? '',
              business_logic: requirements.logic.value ?? '',
              integrations: requirements.integrations.value ?? '',
            },
          };

        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!res.ok) throw new Error(`API ${res.status}`);

        if (mode === 'expert') {
          const data = await res.json();
          if (!data?.code?.html) throw new Error('Missing HTML in response');
          html = buildHtmlDocument(data.code.html, data.code.css, data.code.js);
        } else {
          const data = await res.json();
          const appId = data.app_id;
          if (!appId) throw new Error('Missing app_id in response');

          const appRes = await fetch(`${API_BASE}/apps/${appId}`);
          if (!appRes.ok) throw new Error(`Fetch app ${appRes.status}`);
          const appData = await appRes.json();
          html = buildHtmlDocument(appData.html, appData.css, appData.js);
        }
      } catch {
        console.warn('Backend generate unavailable — using local generation');
        html = generateAppHTML(requirements, appName || 'My App', mode);
      }

      clearInterval(interval);
      setGenerationProgress(100);
      setGenerationStage('App ready!');
      setGeneratedHTML(html);
      setTimeout(() => setStage('preview'), 500);
    })();
  }, [requirements, appName, mode]);

  const handleRestart = useCallback(() => {
    setStage('mode-select');
    setMessages([]);
    setRequirements(initialRequirements());
    setAppName('');
    setQuestionCount(0);
    setGenerationProgress(0);
    setGeneratedHTML('');
    conversationHistory.current = [];
    sessionIdRef.current = null;
  }, []);

  const confidence = getOverallConfidence(requirements);

  return (
    <div className="min-h-screen bg-forge-dark flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-forge-border bg-forge-darker">
        <Link
          to="/"
          className="flex items-center gap-2 text-forge-muted hover:text-white transition-colors duration-200 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent rounded"
        >
          <ArrowLeft size={16} />
          Back to home
        </Link>
        <Link
          to="/"
          className="flex items-center gap-2 hover:opacity-80 transition-opacity duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent rounded"
        >
          <div className="w-6 h-6 rounded-md bg-gradient-to-br from-forge-accent to-forge-violet flex items-center justify-center">
            <Sparkles size={12} className="text-white" />
          </div>
          <span className="font-heading font-bold text-white text-sm">
            InNovus
          </span>
        </Link>
        {stage !== 'mode-select' && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-forge-muted">
              {mode === 'simple' ? 'Simple Mode' : 'Expert Mode'}
            </span>
            <button
              onClick={() => {
                const newMode = mode === 'simple' ? 'expert' : 'simple';
                setMode(newMode);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-forge-border text-forge-muted hover:text-white hover:border-forge-muted text-xs transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent"
            >
              <Code2 size={12} />
              Switch
            </button>
          </div>
        )}
        {stage === 'mode-select' && <div className="w-24" />}
      </div>

      <div className="flex-1 flex overflow-hidden">
        <AnimatePresence mode="wait">
          {stage === 'mode-select' && (
            <motion.div
              key="mode-select"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.3 }}
              className="flex-1 flex items-center justify-center p-8"
            >
              <div className="w-full max-w-3xl">
                <div className="text-center mb-12">
                  <h1 className="font-heading text-4xl font-bold text-white mb-3">
                    How would you like to build?
                  </h1>
                  <p className="text-forge-muted text-lg">
                    Choose the experience that fits you best. You can switch anytime.
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <ModeCard
                    mode="simple"
                    title="Simple Mode"
                    subtitle="For everyone"
                    description="Describe your idea in plain language. I'll ask friendly questions and handle all the technical details."
                    features={[
                      'Jargon-free conversation',
                      'Visual blueprint updates live',
                      'Ready in under 15 minutes',
                      'No technical knowledge needed',
                    ]}
                    icon={<Sparkles size={12} />}
                    accentClass="bg-forge-accent"
                    borderClass="border-forge-accent/30 hover:border-forge-accent/60"
                    badgeClass="bg-forge-accent/15 text-forge-accent"
                    onSelect={() => selectMode('simple')}
                  />
                  <ModeCard
                    mode="expert"
                    title="Expert Mode"
                    subtitle="For developers"
                    description="Speak in technical shorthand. Define entities, routes, and logic precisely. Maximum speed and control."
                    features={[
                      'Technical spec language',
                      'Entity & route definitions',
                      'Architecture-aware questions',
                      'Ready in under 10 minutes',
                    ]}
                    icon={<Code2 size={12} />}
                    accentClass="bg-forge-emerald"
                    borderClass="border-forge-emerald/30 hover:border-forge-emerald/60"
                    badgeClass="bg-forge-emerald/15 text-forge-emerald"
                    onSelect={() => selectMode('expert')}
                  />
                </div>
              </div>
            </motion.div>
          )}

          {(stage === 'chat' || stage === 'summary') && (
            <motion.div
              key="chat-layout"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="flex-1 flex overflow-hidden"
            >
              {/* Chat column — full-width until first message, then leaves room for panel */}
              <div
                className={`flex-1 flex flex-col overflow-hidden transition-all duration-500 ${
                  questionCount > 0 ? 'border-r border-forge-border' : ''
                }`}
              >
                <div className="flex-1 overflow-hidden">
                  <ChatInterface
                    messages={messages}
                    onSend={handleSend}
                    isLoading={isAiLoading}
                    mode={mode}
                    disabled={stage === 'summary'}
                  />
                </div>
                <AnimatePresence>
                  {stage === 'summary' && (
                    <motion.div
                      initial={{ opacity: 0, y: 16 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 16 }}
                      transition={{ duration: 0.3 }}
                      className="p-4 border-t border-forge-border"
                    >
                      <RequirementsSummary
                        requirements={requirements}
                        appName={appName}
                        mode={mode}
                        onConfirm={handleConfirmGenerate}
                        onEdit={() => setStage('chat')}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Blueprint panel — slides in from right after first message */}
              <AnimatePresence>
                {questionCount > 0 && (
                  <motion.div
                    key="blueprint"
                    initial={{ width: 0, opacity: 0 }}
                    animate={{ width: 'auto', opacity: 1 }}
                    exit={{ width: 0, opacity: 0 }}
                    transition={{ duration: 0.4, ease: 'easeOut' }}
                    className="w-80 xl:w-96 flex-shrink-0 overflow-y-auto bg-forge-darker"
                  >
                    <BlueprintPanel
                      requirements={requirements}
                      questionCount={questionCount}
                      totalQuestions={TOTAL_QUESTIONS}
                      mode={mode}
                      appName={appName}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}

          {stage === 'generating' && (
            <motion.div
              key="generating"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="flex-1"
            >
              <GenerationProgress stage={generationStage} progress={generationProgress} />
            </motion.div>
          )}

          {stage === 'preview' && (
            <motion.div
              key="preview"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="flex-1 p-6 overflow-hidden flex flex-col"
            >
              <AppPreview
                htmlContent={generatedHTML}
                appName={appName || 'My App'}
                onRestart={handleRestart}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {stage === 'chat' && (
        <div className="px-6 py-2 border-t border-forge-border bg-forge-darker flex items-center justify-between">
          <span className="text-xs text-forge-muted">
            Understanding your requirements — {Math.round(confidence)}% confident
          </span>
          {confidence >= 60 && questionCount >= 5 && (
            <button
              onClick={() => setStage('summary')}
              className="text-xs text-forge-accent hover:text-forge-accent-hover transition-colors duration-200 font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent rounded"
            >
              I'm ready to generate →
            </button>
          )}
        </div>
      )}

      {/* ── Greeting card overlay ─────────────────────────────── */}
      <AnimatePresence>
        {showGreeting && (
          <motion.div
            key="greeting-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="greeting-backdrop"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.88, y: 24 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: -16 }}
              transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              className="relative px-10 py-8 rounded-3xl border border-forge-accent/30 bg-gradient-to-br from-forge-darker/90 to-forge-surface/90 shadow-2xl text-center max-w-sm mx-4"
            >
              {/* Sparkle icon */}
              <div className="w-14 h-14 rounded-full bg-gradient-to-br from-forge-accent to-forge-violet flex items-center justify-center mx-auto mb-4 shadow-lg">
                <Sparkles size={26} className="text-white" />
              </div>
              <h2 className="font-heading text-2xl font-bold text-white mb-2">
                {greetingMode === 'simple' ? 'Let\'s build something!' : 'Ready to architect!'}
              </h2>
              <p className="text-forge-muted-light text-sm leading-relaxed">
                {greetingMode === 'simple'
                  ? 'I\'ll ask a few easy questions to understand your vision.'
                  : 'Describe your system requirements — I\'ll handle the rest.'}
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}