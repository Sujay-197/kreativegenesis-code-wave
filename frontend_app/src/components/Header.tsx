import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const navLinks = [
  { label: 'How It Works', path: '/how-it-works' },
  { label: 'Examples', path: '/examples' },
  { label: 'Pricing', path: '/pricing' },
];

const Header: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-forge-dark/95 backdrop-blur-md border-b border-forge-border shadow-lg'
          : 'bg-transparent backdrop-blur-sm'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link
            to="/"
            className="flex items-center gap-2 group focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent rounded-lg"
            aria-label="AppForge AI home"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-forge-accent to-forge-violet flex items-center justify-center group-hover:scale-110 transition-transform duration-200">
              <Zap size={16} className="text-white" />
            </div>
            <span className="font-heading font-bold text-xl text-white tracking-tight">
              AppForge <span className="text-forge-accent">AI</span>
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-8" aria-label="Primary navigation">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`relative text-sm font-medium transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent rounded px-1 py-0.5 group ${
                  location.pathname === link.path
                    ? 'text-forge-accent'
                    : 'text-forge-muted hover:text-white'
                }`}
              >
                {link.label}
                <span
                  className={`absolute -bottom-0.5 left-0 h-px bg-forge-accent transition-all duration-200 ${
                    location.pathname === link.path ? 'w-full' : 'w-0 group-hover:w-full'
                  }`}
                />
              </Link>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-4">
            <Link
              to="/builder"
              className="px-5 py-2.5 rounded-full bg-forge-accent hover:bg-forge-accent-hover text-white text-sm font-semibold transition-all duration-200 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent focus-visible:ring-offset-2 focus-visible:ring-offset-forge-dark"
            >
              Start Building
            </Link>
          </div>

          <button
            className="md:hidden p-2 rounded-lg text-forge-muted hover:text-white hover:bg-forge-surface transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-expanded={mobileOpen}
            aria-controls="mobile-nav"
            aria-label={mobileOpen ? 'Close navigation' : 'Open navigation'}
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            id="mobile-nav"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="md:hidden bg-forge-dark/98 backdrop-blur-md border-b border-forge-border"
          >
            <nav className="max-w-7xl mx-auto px-6 py-4 flex flex-col gap-1" aria-label="Mobile navigation">
              {navLinks.map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent ${
                    location.pathname === link.path
                      ? 'text-forge-accent bg-forge-accent/10'
                      : 'text-forge-muted hover:text-white hover:bg-forge-surface'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
              <Link
                to="/builder"
                className="mt-2 px-4 py-3 rounded-full bg-forge-accent hover:bg-forge-accent-hover text-white text-sm font-semibold text-center transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent"
              >
                Start Building
              </Link>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
};

export default Header;