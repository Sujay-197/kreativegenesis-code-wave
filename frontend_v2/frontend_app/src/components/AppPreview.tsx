import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Download, Share2, RefreshCw, ExternalLink, Copy, Check } from 'lucide-react';
import { toast } from 'react-toastify';

interface AppPreviewProps {
  htmlContent: string;
  appName: string;
  onRestart: () => void;
}

const AppPreview: React.FC<AppPreviewProps> = ({ htmlContent, appName, onRestart }) => {
  const [copied, setCopied] = useState(false);

  const handleDownload = () => {
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${appName.toLowerCase().replace(/\s+/g, '-')}.html`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('App downloaded successfully!');
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true);
      toast.success('Link copied to clipboard!');
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const srcDoc = htmlContent;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col h-full"
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-forge-border bg-forge-surface rounded-t-xl">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/70" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
            <div className="w-3 h-3 rounded-full bg-green-500/70" />
          </div>
          <span className="text-xs text-forge-muted font-mono ml-2 truncate max-w-[160px]">
            {appName || 'Generated App'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyLink}
            aria-label="Copy share link"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-forge-border text-forge-muted hover:text-white hover:border-forge-muted text-xs transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent"
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            {copied ? 'Copied' : 'Share'}
          </button>
          <button
            onClick={handleDownload}
            aria-label="Download app"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-forge-accent hover:bg-forge-accent-hover text-white text-xs font-semibold transition-all duration-200 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent"
          >
            <Download size={12} />
            Download
          </button>
        </div>
      </div>

      <div className="flex-1 bg-white rounded-b-xl overflow-hidden">
        <iframe
          srcDoc={srcDoc}
          title={`Preview of ${appName}`}
          className="w-full h-full border-0"
          sandbox="allow-scripts allow-same-origin allow-forms"
        />
      </div>

      <div className="mt-4 flex items-center justify-between">
        <p className="text-xs text-forge-muted">
          Your app is ready · Interact with it above
        </p>
        <button
          onClick={onRestart}
          className="flex items-center gap-1.5 text-xs text-forge-muted hover:text-white transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent rounded"
        >
          <RefreshCw size={12} />
          Build another
        </button>
      </div>
    </motion.div>
  );
};

export default AppPreview;