import React from 'react';
import { motion } from 'framer-motion';

const steps = [
  {
    number: '01',
    title: 'Choose your mode',
    description: 'Select Simple Mode for a friendly conversation or Expert Mode for technical precision.',
  },
  {
    number: '02',
    title: 'Answer smart questions',
    description: 'The AI asks 5–9 targeted questions, inferring your needs from context — never repeating itself.',
  },
  {
    number: '03',
    title: 'Review your blueprint',
    description: 'Confirm the AI understood correctly. Edit anything before a single line of code is written.',
  },
  {
    number: '04',
    title: 'Get your working app',
    description: 'Preview it live, interact with it, then download or share via a generated link.',
  },
];

const HowItWorksSection: React.FC = () => {
  return (
    <section className="py-24 bg-forge-dark">
      <div className="max-w-4xl mx-auto px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="font-heading text-4xl md:text-5xl font-bold text-white mb-4">
            From idea to app in 4 steps
          </h2>
          <p className="text-forge-muted text-lg">
            The fastest path from a problem to a working solution.
          </p>
        </motion.div>

        <div className="relative">
          <div className="absolute left-8 top-8 bottom-8 w-px bg-gradient-to-b from-forge-accent via-forge-violet to-transparent hidden md:block" />

          <div className="space-y-8">
            {steps.map((step, i) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                className="flex gap-6 md:gap-8"
              >
                <div className="flex-shrink-0 w-16 h-16 rounded-2xl bg-gradient-to-br from-forge-accent/20 to-forge-violet/20 border border-forge-accent/30 flex items-center justify-center">
                  <span className="font-heading font-bold text-forge-accent text-sm">{step.number}</span>
                </div>
                <div className="flex-1 pt-3">
                  <h3 className="font-heading font-bold text-white text-xl mb-2">{step.title}</h3>
                  <p className="text-forge-muted leading-relaxed">{step.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorksSection;