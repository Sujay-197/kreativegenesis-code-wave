import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';

interface ModeCardProps {
  mode: 'simple' | 'expert';
  title: string;
  subtitle: string;
  description: string;
  features: string[];
  icon: React.ReactNode;
  accentClass: string;
  borderClass: string;
  badgeClass: string;
  onSelect: () => void;
}

const ModeCard: React.FC<ModeCardProps> = ({
  title,
  subtitle,
  description,
  features,
  icon,
  accentClass,
  borderClass,
  badgeClass,
  onSelect,
}) => {
  return (
    <motion.button
      whileHover={{ y: -4, scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      transition={{ duration: 0.2 }}
      onClick={onSelect}
      className={`group relative w-full text-left p-8 rounded-2xl border-2 ${borderClass} bg-forge-surface hover:bg-forge-surface-hover transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent focus-visible:ring-offset-2 focus-visible:ring-offset-forge-dark cursor-pointer`}
    >
      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold mb-6 ${badgeClass}`}>
        {icon}
        {subtitle}
      </div>

      <h2 className="font-heading text-2xl font-bold text-white mb-3">{title}</h2>
      <p className="text-forge-muted text-sm leading-relaxed mb-6">{description}</p>

      <ul className="space-y-2 mb-8">
        {features.map((f) => (
          <li key={f} className="flex items-center gap-2 text-sm text-forge-muted-light">
            <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${accentClass}`} />
            {f}
          </li>
        ))}
      </ul>

      <div className={`flex items-center gap-2 text-sm font-semibold ${accentClass.replace('bg-', 'text-')} group-hover:gap-3 transition-all duration-200`}>
        Get Started
        <ArrowRight size={16} />
      </div>
    </motion.button>
  );
};

export default ModeCard;