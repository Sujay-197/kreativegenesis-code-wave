import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-forge-dark flex items-center justify-center px-6">
      <div className="text-center">
        <p className="font-heading text-8xl font-bold text-forge-accent mb-4">404</p>
        <h1 className="font-heading text-3xl font-bold text-white mb-4">Page not found</h1>
        <p className="text-forge-muted mb-8">The page you're looking for doesn't exist or has been moved.</p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-forge-accent hover:bg-forge-accent-hover text-white font-semibold transition-all duration-200 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent"
        >
          <ArrowLeft size={16} />
          Back to home
        </Link>
      </div>
    </div>
  );
}