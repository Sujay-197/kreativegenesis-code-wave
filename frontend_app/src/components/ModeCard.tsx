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
  mode,
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
  // Calculate icon size based on mode - Simple gets larger icons (70%), Expert gets smaller (30%)
  const iconSize = mode === 'simple' ? 24 : 14;
  const badgePadding = mode === 'simple' ? 'px-4 py-1.5' : 'px-3 py-1';
  const badgeTextSize = mode === 'simple' ? 'text-sm' : 'text-xs';

  return (
    <motion.button
      whileHover={{ y: -4, scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      transition={{ duration: 0.2 }}
      onClick={onSelect}
      className={`group relative w-full text-left p-8 rounded-2xl border-2 ${borderClass} bg-forge-surface hover:bg-forge-surface-hover transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent focus-visible:ring-offset-2 focus-visible:ring-offset-forge-dark cursor-pointer`}
    >
      <div className={`inline-flex items-center gap-2 ${badgePadding} rounded-full ${badgeTextSize} font-semibold mb-6 ${badgeClass}`}>
        {React.cloneElement(icon as React.ReactElement, { size: iconSize })}
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