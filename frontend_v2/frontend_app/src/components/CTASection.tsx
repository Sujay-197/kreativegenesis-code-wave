import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

const CTASection: React.FC = () => {
  return (
    <section className="py-24 bg-forge-darker border-t border-forge-border">
      <div className="max-w-4xl mx-auto px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-heading text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to build something?
          </h2>
          <p className="text-forge-muted text-lg mb-10 max-w-xl mx-auto">
            Join thousands of builders who turned their ideas into working apps — without writing a single line of code.
          </p>
          <Link
            to="/builder"
            className="inline-flex items-center gap-2 px-10 py-4 rounded-full bg-forge-accent hover:bg-forge-accent-hover text-white font-semibold text-lg transition-all duration-200 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent focus-visible:ring-offset-2 focus-visible:ring-offset-forge-darker"
          >
            Start Building Free
            <ArrowRight size={20} />
          </Link>
        </motion.div>
      </div>
    </section>
  );
};

export default CTASection;