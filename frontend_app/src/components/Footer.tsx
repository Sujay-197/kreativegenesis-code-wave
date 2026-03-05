import React from 'react';
import { Link } from 'react-router-dom';
import { Zap, Github, Twitter, Linkedin } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-forge-darker border-t border-forge-border">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          <div className="md:col-span-1">
            <Link to="/" className="flex items-center gap-2 mb-4 group focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent rounded-lg w-fit">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-forge-accent to-forge-violet flex items-center justify-center group-hover:scale-110 transition-transform duration-200">
                <Zap size={16} className="text-white" />
              </div>
              <span className="font-heading font-bold text-xl text-white tracking-tight">
                AppForge <span className="text-forge-accent">AI</span>
              </span>
            </Link>
            <p className="text-forge-muted text-sm leading-relaxed mb-6">
              From idea to working app through conversation. No code required.
            </p>
            <div className="flex items-center gap-3">
              {[
                { icon: Github, label: 'GitHub' },
                { icon: Twitter, label: 'Twitter' },
                { icon: Linkedin, label: 'LinkedIn' },
              ].map(({ icon: Icon, label }) => (
                <button
                  key={label}
                  type="button"
                  aria-label={label}
                  className="w-9 h-9 rounded-lg bg-forge-surface border border-forge-border flex items-center justify-center text-forge-muted hover:text-white hover:border-forge-accent/50 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent"
                >
                  <Icon size={16} />
                </button>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-white font-semibold text-sm mb-4">Product</h3>
            <ul className="space-y-3">
              {[
                { label: 'How It Works', path: '/how-it-works' },
                { label: 'Examples', path: '/examples' },
                { label: 'Start Building', path: '/builder' },
              ].map((item) => (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className="text-forge-muted hover:text-white text-sm transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent rounded"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold text-sm mb-4">Company</h3>
            <ul className="space-y-3">
              {[
              ].map((item) => (
                <li key={item.label}>
                  <Link
                    to={item.path}
                    className="text-forge-muted hover:text-white text-sm transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent rounded"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
              <li>
                <span className="text-forge-muted text-sm">About</span>
              </li>
              <li>
                <span className="text-forge-muted text-sm">Blog</span>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold text-sm mb-4">Legal</h3>
            <ul className="space-y-3">
              {['Privacy Policy', 'Terms of Service', 'Cookie Policy'].map((item) => (
                <li key={item}>
                  <span className="text-forge-muted text-sm">
                    {item}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="border-t border-forge-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-forge-muted text-sm">
            © 2026 AppForge AI. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <span className="text-forge-muted text-sm">Privacy</span>
            <span className="text-forge-muted text-sm">Terms</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;