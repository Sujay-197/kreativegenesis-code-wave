import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';
import Particles from './Particles';

const HeroSection: React.FC = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-forge-dark">
      <div className="absolute inset-0 pointer-events-none">
        <div style={{ width: '100%', height: '100%', position: 'absolute' }}>
          <Particles
            particleColors={["#ffffff"]}
            particleCount={200}
            particleSpread={10}
            speed={0.1}
            particleBaseSize={100}
            moveParticlesOnHover={false}
            alphaParticles={false}
            disableRotation={false}
            pixelRatio={1}
          />
        </div>
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-forge-accent/8 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-forge-violet/8 rounded-full blur-3xl" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff08_1px,transparent_1px),linear-gradient(to_bottom,#ffffff08_1px,transparent_1px)] bg-[size:64px_64px]" />
      </div>

      <div className="relative max-w-4xl mx-auto px-6 lg:px-8 text-center py-24">
<motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="font-heading text-5xl md:text-6xl lg:text-7xl font-bold text-white leading-tight mb-6"
        >
          Build apps through{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-forge-accent to-forge-violet">
            conversation
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-forge-muted text-lg md:text-xl leading-relaxed mb-10 max-w-2xl mx-auto"
        >
          InNovus asks the right questions, understands your needs, and generates a working
          web application — no code, no complexity, no compromise.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link
            to="/builder"
            className="flex items-center gap-2 px-8 py-4 rounded-full bg-forge-accent hover:bg-forge-accent-hover text-white font-semibold text-base transition-all duration-200 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent focus-visible:ring-offset-2 focus-visible:ring-offset-forge-dark"
          >
            Start Building
            <ArrowRight size={18} />
          </Link>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="mt-16 flex items-center justify-center gap-8 text-sm text-forge-muted"
        >
          <span className="flex items-center gap-2 text-white">BUILT BY TEAM CODE WAVE</span>
        </motion.div>
      </div>
    </section>
  );
};

export default HeroSection;