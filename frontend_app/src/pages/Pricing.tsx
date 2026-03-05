import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { Check, ArrowRight } from 'lucide-react';

const plans = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    description: 'Perfect for trying AppForge AI and building your first app.',
    features: [
      '3 app generations per month',
      'Simple Mode only',
      'Download as HTML file',
      'Community support',
    ],
    cta: 'Start for free',
    highlighted: false,
  },
  {
    name: 'Builder',
    price: '$19',
    period: 'per month',
    description: 'For individuals and small teams building real tools.',
    features: [
      'Unlimited app generations',
      'Simple + Expert Mode',
      'Download + shareable links',
      'Priority generation queue',
      'Email support',
    ],
    cta: 'Start building',
    highlighted: true,
  },
  {
    name: 'Team',
    price: '$49',
    period: 'per month',
    description: 'For teams that need collaboration and advanced control.',
    features: [
      'Everything in Builder',
      'Team workspace',
      'Version history',
      'Custom templates',
      'Dedicated support',
      'API access',
    ],
    cta: 'Contact us',
    highlighted: false,
  },
];

export default function Pricing() {
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
              Simple, honest pricing
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-forge-muted text-xl"
            >
              Start free. Upgrade when you need more.
            </motion.p>
          </div>
        </section>

        <section className="py-16 bg-forge-darker border-t border-forge-border">
          <div className="max-w-5xl mx-auto px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {plans.map((plan, i) => (
                <motion.div
                  key={plan.name}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.1 }}
                  className={`relative p-8 rounded-2xl border transition-all duration-300 ${
                    plan.highlighted
                      ? 'border-forge-accent bg-gradient-to-b from-forge-accent/10 to-forge-surface'
                      : 'border-forge-border bg-forge-surface hover:border-forge-border/80'
                  }`}
                >
                  {plan.highlighted && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="px-4 py-1 rounded-full bg-forge-accent text-white text-xs font-bold">
                        Most Popular
                      </span>
                    </div>
                  )}

                  <div className="mb-6">
                    <h2 className="font-heading font-bold text-white text-xl mb-1">{plan.name}</h2>
                    <div className="flex items-baseline gap-1 mb-2">
                      <span className="font-heading text-4xl font-bold text-white">{plan.price}</span>
                      <span className="text-forge-muted text-sm">/{plan.period}</span>
                    </div>
                    <p className="text-forge-muted text-sm">{plan.description}</p>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-start gap-3 text-sm">
                        <Check size={15} className="text-forge-accent mt-0.5 flex-shrink-0" />
                        <span className="text-forge-muted-light">{f}</span>
                      </li>
                    ))}
                  </ul>

                  <Link
                    to="/builder"
                    className={`flex items-center justify-center gap-2 w-full px-6 py-3 rounded-xl font-semibold text-sm transition-all duration-200 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent ${
                      plan.highlighted
                        ? 'bg-forge-accent hover:bg-forge-accent-hover text-white'
                        : 'border border-forge-border text-forge-muted hover:text-white hover:border-forge-muted'
                    }`}
                  >
                    {plan.cta}
                    <ArrowRight size={14} />
                  </Link>
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}