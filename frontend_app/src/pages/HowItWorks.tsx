import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import HowItWorksSection from '../components/HowItWorksSection';
import { ArrowRight, MessageSquare, Eye, CheckCircle2, Download } from 'lucide-react';

const detailedSteps = [
  {
    icon: MessageSquare,
    number: '01',
    title: 'Choose your mode',
    headline: 'Two modes, one platform',
    body: 'Simple Mode is designed for non-technical users — warm, conversational, jargon-free. Expert Mode is for developers who want to describe entities, routes, and logic in technical shorthand. Both modes produce the same quality output. You can switch between them at any point during your session.',
  },
  {
    icon: MessageSquare,
    number: '02',
    title: 'Answer smart questions',
    headline: 'The AI that listens before it builds',
    body: 'AppForge AI uses an adaptive question engine powered by Gemini 2.5 Flash. It maintains a running understanding of your requirements across five dimensions: authentication, data, UI complexity, business logic, and integrations. It asks only the most uncertainty-reducing question at each step — never repeating itself, never following a fixed script.',
  },
  {
    icon: Eye,
    number: '03',
    title: 'Watch your blueprint form',
    headline: 'See your app take shape in real time',
    body: 'As you answer each question, the Live Blueprint Visualizer updates instantly. You can see exactly what the AI has understood about your app before a single line of code is written. This transparency builds trust and catches misunderstandings early.',
  },
  {
    icon: CheckCircle2,
    number: '04',
    title: 'Confirm your requirements',
    headline: 'Review before you build',
    body: 'Before generating anything, AppForge AI presents a clear summary of what it understood. In Simple Mode this reads like a plain English description. In Expert Mode it reads like a technical spec. You can correct anything before proceeding.',
  },
  {
    icon: Download,
    number: '05',
    title: 'Get your working app',
    headline: 'A real app, not a mockup',
    body: 'The generated application is a fully functional, self-contained HTML file with embedded CSS and JavaScript. It runs in any browser with no setup required. Data is stored in localStorage for immediate use. Download it, host it anywhere, or share via a generated link.',
  },
];

export default function HowItWorks() {
  return (
    <>
      <Header />
      <main>
        <section className="pt-32 pb-16 bg-forge-dark">
          <div className="max-w-4xl mx-auto px-6 lg:px-8 text-center">
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="font-heading text-5xl md:text-6xl font-bold text-white mb-6"
            >
              How AppForge AI works
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-forge-muted text-xl leading-relaxed"
            >
              The intelligence layer before generation is what makes AppForge AI different. Here's exactly what happens when you build.
            </motion.p>
          </div>
        </section>

        <section className="py-16 bg-forge-darker border-t border-forge-border">
          <div className="max-w-4xl mx-auto px-6 lg:px-8">
            <div className="space-y-16">
              {detailedSteps.map((step, i) => (
                <motion.div
                  key={step.number}
                  initial={{ opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.05 }}
                  className="grid grid-cols-1 md:grid-cols-5 gap-8 items-start"
                >
                  <div className="md:col-span-1 flex md:flex-col items-center md:items-start gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-forge-accent/20 to-forge-violet/20 border border-forge-accent/30 flex items-center justify-center flex-shrink-0">
                      <span className="font-heading font-bold text-forge-accent text-sm">{step.number}</span>
                    </div>
                  </div>
                  <div className="md:col-span-4">
                    <h2 className="font-heading text-2xl font-bold text-white mb-2">{step.headline}</h2>
                    <p className="text-forge-muted leading-relaxed">{step.body}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <HowItWorksSection />

        <section className="py-16 bg-forge-darker border-t border-forge-border">
          <div className="max-w-4xl mx-auto px-6 lg:px-8 text-center">
            <h2 className="font-heading text-3xl font-bold text-white mb-4">Ready to try it?</h2>
            <p className="text-forge-muted mb-8">No account required. Start building in seconds.</p>
            <Link
              to="/builder"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-forge-accent hover:bg-forge-accent-hover text-white font-semibold transition-all duration-200 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent focus-visible:ring-offset-2 focus-visible:ring-offset-forge-darker"
            >
              Start Building Free
              <ArrowRight size={18} />
            </Link>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}