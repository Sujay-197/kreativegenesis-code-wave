import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Edit3, Rocket } from 'lucide-react';
import type { RequirementsState } from '../lib/aiEngine';

interface RequirementsSummaryProps {
  requirements: RequirementsState;
  summaryParagraph?: string;
  appName: string;
  mode: 'simple' | 'expert';
  onConfirm: () => void;
  onEdit: () => void;
}

const RequirementsSummary: React.FC<RequirementsSummaryProps> = ({
  requirements,
  summaryParagraph,
  appName,
  mode,
  onConfirm,
  onEdit,
}) => {
  const items = Object.values(requirements).filter((d) => d.value);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="p-6 rounded-2xl border border-forge-accent/30 bg-gradient-to-br from-forge-surface to-forge-surface-hover"
    >
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 rounded-xl bg-forge-accent/15 flex items-center justify-center">
          <CheckCircle2 size={20} className="text-forge-accent" />
        </div>
        <div>
          <h3 className="font-heading font-bold text-white text-lg">
            {mode === 'simple' ? "Here's what I understood" : 'Requirements Summary'}
          </h3>
          <p className="text-forge-muted text-xs">Review before generating your app</p>
        </div>
      </div>

      {appName && (
        <div className="mb-4 px-4 py-3 rounded-xl bg-forge-accent/10 border border-forge-accent/20">
          <p className="text-xs text-forge-accent font-semibold uppercase tracking-wider mb-0.5">App Name</p>
          <p className="text-white font-semibold">{appName}</p>
        </div>
      )}

      <div className="space-y-3 mb-6">
        {mode === 'simple' && summaryParagraph ? (
          <div className="px-4 py-3 rounded-xl bg-forge-accent/10 border border-forge-accent/20">
            <p className="text-sm leading-relaxed text-forge-text">{summaryParagraph}</p>
          </div>
        ) : (
          items.map((dim, i) => (
            <motion.div
              key={dim.label}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.06 }}
              className="flex items-start gap-3"
            >
              <CheckCircle2 size={14} className="text-forge-accent mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-xs font-semibold text-forge-muted-light">{dim.label}: </span>
                <span className="text-xs text-forge-text">{dim.value}</span>
              </div>
            </motion.div>
          ))
        )}
      </div>

      <div className="flex gap-3">
        <button
          onClick={onEdit}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-forge-border text-forge-muted hover:text-white hover:border-forge-muted transition-all duration-200 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent"
        >
          <Edit3 size={14} />
          Edit
        </button>
        <button
          onClick={onConfirm}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-forge-accent hover:bg-forge-accent-hover text-white text-sm font-semibold transition-all duration-200 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent"
        >
          <Rocket size={14} />
          Generate App
        </button>
      </div>
    </motion.div>
  );
};

export default RequirementsSummary;