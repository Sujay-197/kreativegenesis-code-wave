import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Database, Layout, GitBranch, Plug, CheckCircle2, Circle } from 'lucide-react';

// Re-export the canonical type from aiEngine so existing consumers still work
export type { RequirementsState } from '../lib/aiEngine';
import type { RequirementsState } from '../lib/aiEngine';

interface BlueprintPanelProps {
  requirements: RequirementsState;
  questionCount: number;
  totalQuestions: number;
  mode: 'simple' | 'expert';
  appName?: string;
}

const dimensionConfig = [
  { key: 'auth', icon: Users, label: 'Auth & Users' },
  { key: 'data', icon: Database, label: 'Data & Storage' },
  { key: 'ui', icon: Layout, label: 'UI Complexity' },
  { key: 'logic', icon: GitBranch, label: 'Business Logic' },
  { key: 'integrations', icon: Plug, label: 'Integrations' },
] as const;

const BlueprintPanel: React.FC<BlueprintPanelProps> = ({
  requirements,
  questionCount,
  totalQuestions,
  mode,
  appName,
}) => {
  const overallProgress = Math.round(
    (Object.values(requirements).reduce((sum, d) => sum + d.confidence, 0) /
      (Object.values(requirements).length * 100)) *
      100
  );

  return (
    <div className="h-full flex flex-col p-6 gap-6">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-heading text-sm font-semibold text-white">
            {mode === 'simple' ? 'Your App Blueprint' : 'Requirements Map'}
          </h2>
          <span className="text-xs text-forge-muted font-mono">
            {questionCount}/{totalQuestions} questions
          </span>
        </div>

        <div className="w-full h-1.5 bg-forge-border rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-forge-accent to-forge-violet rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${overallProgress}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-forge-muted">Understanding</span>
          <span className="text-xs text-forge-accent font-semibold">{overallProgress}%</span>
        </div>
      </div>

      <AnimatePresence>
        {appName && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-4 rounded-xl bg-gradient-to-br from-forge-accent/10 to-forge-violet/10 border border-forge-accent/20"
          >
            <p className="text-xs text-forge-accent font-semibold uppercase tracking-wider mb-1">App Name</p>
            <p className="text-white font-heading font-bold text-lg">{appName}</p>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex-1 space-y-3">
        {dimensionConfig.map(({ key, icon: Icon, label }) => {
          const dim = requirements[key];
          const hasValue = dim.confidence > 0;

          return (
            <motion.div
              key={key}
              layout
              className={`p-4 rounded-xl border transition-all duration-300 ${
                hasValue
                  ? 'bg-forge-surface border-forge-border'
                  : 'bg-forge-surface/40 border-forge-border/40'
              }`}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-300 ${
                    hasValue
                      ? 'bg-forge-accent/15 text-forge-accent'
                      : 'bg-forge-border/50 text-forge-muted'
                  }`}
                >
                  <Icon size={15} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-forge-muted-light">{label}</span>
                    {hasValue ? (
                      <CheckCircle2 size={13} className="text-forge-accent flex-shrink-0" />
                    ) : (
                      <Circle size={13} className="text-forge-border flex-shrink-0" />
                    )}
                  </div>
                  <AnimatePresence mode="wait">
                    {dim.value ? (
                      <motion.p
                        key={dim.value}
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -4 }}
                        transition={{ duration: 0.2 }}
                        className="text-xs text-forge-text leading-relaxed"
                      >
                        {dim.value}
                      </motion.p>
                    ) : (
                      <motion.p
                        key="empty"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-xs text-forge-muted italic"
                      >
                        {mode === 'simple' ? 'Still learning...' : 'Awaiting input'}
                      </motion.p>
                    )}
                  </AnimatePresence>

                  {hasValue && (
                    <div className="mt-2 w-full h-1 bg-forge-border rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-forge-accent rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${dim.confidence}%` }}
                        transition={{ duration: 0.4, ease: 'easeOut' }}
                      />
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="text-center">
        <p className="text-xs text-forge-muted">
          {mode === 'simple'
            ? 'Powered by Gemini 2.5 Flash'
            : 'Gemini 2.5 Flash · Expert Mode'}
        </p>
      </div>
    </div>
  );
};

export default BlueprintPanel;