import React from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

interface GenerationProgressProps {
  stage: string;
  progress: number;
}

const stages = [
  'Analyzing requirements...',
  'Selecting template...',
  'Generating UI structure...',
  'Wiring business logic...',
  'Finalizing your app...',
];

const GenerationProgress: React.FC<GenerationProgressProps> = ({ stage, progress }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center h-full gap-8 p-8"
    >
      <div className="relative w-20 h-20">
        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-forge-accent to-forge-violet opacity-20 animate-ping" />
        <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-forge-accent to-forge-violet flex items-center justify-center">
          <Loader2 size={32} className="text-white animate-spin" />
        </div>
      </div>

      <div className="w-full max-w-xs text-center">
        <p className="text-white font-semibold mb-1">{stage}</p>
        <p className="text-forge-muted text-sm mb-4">{progress}% complete</p>
        <div className="w-full h-2 bg-forge-border rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-forge-accent to-forge-violet rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
          />
        </div>
      </div>

      <div className="space-y-2 w-full max-w-xs">
        {stages.map((s, i) => {
          const stageProgress = (i + 1) * 20;
          const isActive = progress >= stageProgress - 20 && progress < stageProgress;
          const isDone = progress >= stageProgress;
          return (
            <div key={s} className="flex items-center gap-3">
              <div
                className={`w-2 h-2 rounded-full flex-shrink-0 transition-all duration-300 ${
                  isDone
                    ? 'bg-forge-accent'
                    : isActive
                    ? 'bg-forge-accent animate-pulse'
                    : 'bg-forge-border'
                }`}
              />
              <span
                className={`text-xs transition-colors duration-300 ${
                  isDone ? 'text-forge-accent' : isActive ? 'text-white' : 'text-forge-muted'
                }`}
              >
                {s}
              </span>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
};

export default GenerationProgress;