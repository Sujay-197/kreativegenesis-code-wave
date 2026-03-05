import React from 'react';
import { motion } from 'framer-motion';
import { MessageSquare, Eye, Download, Zap, Shield, Cpu } from 'lucide-react';

const features = [
  {
    icon: MessageSquare,
    title: 'Adaptive Question Engine',
    description:
      'AI asks only the most relevant next question based on your previous answers. No forms, no overwhelm — just a natural conversation.',
  },
  {
    icon: Eye,
    title: 'Live Blueprint Visualizer',
    description:
      'Watch your app take shape in real time as you answer questions. See exactly what is being understood before generation begins.',
  },
  {
    icon: Zap,
    title: 'Instant Generation',
    description:
      'From confirmed requirements to a working app in seconds. Powered by a dual-model AI chain for reliability and quality.',
  },
  {
    icon: Shield,
    title: 'Requirements Confirmation',
    description:
      'Review a plain-English summary of what the AI understood before it builds anything. Correct misunderstandings before they become bugs.',
  },
  {
    icon: Download,
    title: 'Download & Deploy',
    description:
      'Get a fully self-contained HTML file you can open in any browser, host anywhere, or share via a generated link.',
  },
  {
    icon: Cpu,
    title: 'Two Modes, One Platform',
    description:
      'Simple Mode for non-technical users. Expert Mode for developers who want speed and precision. Switch anytime.',
  },
];

const FeaturesSection: React.FC = () => {
  return (
    <section className="py-24 bg-forge-darker border-t border-forge-border">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="font-heading text-4xl md:text-5xl font-bold text-white mb-4">
            Built different, by design
          </h2>
          <p className="text-forge-muted text-lg max-w-2xl mx-auto">
            The intelligence layer before generation is what makes AppForge AI different from every other no-code tool.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              className="group p-8 rounded-2xl border border-forge-border bg-forge-surface hover:border-forge-accent/30 hover:bg-forge-surface-hover hover:-translate-y-1 transition-all duration-300"
            >
              <div className="w-12 h-12 rounded-xl bg-forge-accent/10 flex items-center justify-center mb-5 group-hover:bg-forge-accent/20 transition-colors duration-300">
                <feature.icon size={22} className="text-forge-accent" />
              </div>
              <h3 className="font-heading font-bold text-white text-lg mb-3">{feature.title}</h3>
              <p className="text-forge-muted text-sm leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;