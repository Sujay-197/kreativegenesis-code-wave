import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Download, Share2, RefreshCw, ExternalLink, Copy, Check } from 'lucide-react';
import { toast } from 'react-toastify';

interface AppPreviewProps {
  htmlContent: string;
  appName: string;
  onRestart: () => void;
}

/* ── Tiny ZIP builder (no library needed) ── */
function crc32(buf: Uint8Array): number {
  let crc = -1;
  for (let i = 0; i < buf.length; i++) {
    crc = (crc >>> 8) ^ crc32Table[(crc ^ buf[i]) & 0xff];
  }
  return (crc ^ -1) >>> 0;
}
const crc32Table: number[] = (() => {
  const t: number[] = [];
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c;
  }
  return t;
})();

function buildZip(files: { name: string; content: string }[]): Blob {
  const encoder = new TextEncoder();
  const entries: { name: Uint8Array; data: Uint8Array; crc: number; offset: number }[] = [];
  const parts: Uint8Array[] = [];
  let offset = 0;

  for (const f of files) {
    const nameBytes = encoder.encode(f.name);
    const dataBytes = encoder.encode(f.content);
    const crc = crc32(dataBytes);

    // Local file header (30 + name + data)
    const header = new ArrayBuffer(30);
    const hv = new DataView(header);
    hv.setUint32(0, 0x04034b50, true);   // signature
    hv.setUint16(4, 20, true);           // version needed
    hv.setUint16(8, 0x0800, true);       // flag: UTF-8
    hv.setUint16(26, nameBytes.length, true);
    hv.setUint32(14, crc, true);
    hv.setUint32(18, dataBytes.length, true);  // compressed
    hv.setUint32(22, dataBytes.length, true);  // uncompressed

    const headerArr = new Uint8Array(header);
    parts.push(headerArr, nameBytes, dataBytes);
    entries.push({ name: nameBytes, data: dataBytes, crc, offset });
    offset += headerArr.length + nameBytes.length + dataBytes.length;
  }

  // Central directory
  const cdStart = offset;
  for (const e of entries) {
    const cd = new ArrayBuffer(46);
    const dv = new DataView(cd);
    dv.setUint32(0, 0x02014b50, true);   // signature
    dv.setUint16(4, 20, true);           // version made by
    dv.setUint16(6, 20, true);           // version needed
    dv.setUint16(8, 0x0800, true);       // flag: UTF-8
    dv.setUint32(16, e.crc, true);
    dv.setUint32(20, e.data.length, true);
    dv.setUint32(24, e.data.length, true);
    dv.setUint16(28, e.name.length, true);
    dv.setUint32(42, e.offset, true);

    parts.push(new Uint8Array(cd), e.name);
    offset += 46 + e.name.length;
  }

  // End of central directory
  const eocd = new ArrayBuffer(22);
  const ev = new DataView(eocd);
  ev.setUint32(0, 0x06054b50, true);
  ev.setUint16(8, entries.length, true);
  ev.setUint16(10, entries.length, true);
  ev.setUint32(12, offset - cdStart, true);
  ev.setUint32(16, cdStart, true);
  parts.push(new Uint8Array(eocd));

  return new Blob(parts, { type: 'application/zip' });
}

/* ── Split merged HTML into separate index.html / style.css / script.js ── */
function splitHtmlCssJs(html: string): { indexHtml: string; css: string; js: string } {
  let css = '';
  let js = '';
  let doc = html;

  // Extract all inline <style> blocks (skip CDN <link> tags)
  const styleBlocks: string[] = [];
  doc = doc.replace(/<style[^>]*>([\s\S]*?)<\/style>/gi, (_m, content) => {
    styleBlocks.push(content.trim());
    return '';
  });
  css = styleBlocks.join('\n\n');

  // Extract inline <script> blocks (skip CDN <script src="...">)
  const scriptBlocks: string[] = [];
  doc = doc.replace(/<script(?![^>]*\bsrc\s*=)[^>]*>([\s\S]*?)<\/script>/gi, (_m, content) => {
    scriptBlocks.push(content.trim());
    return '';
  });
  js = scriptBlocks.join('\n\n');

  // Insert <link> and <script src> references for the extracted files
  if (css) {
    const cssLink = '  <link rel="stylesheet" href="style.css">';
    if (doc.includes('</head>')) {
      doc = doc.replace('</head>', `${cssLink}\n</head>`);
    }
  }
  if (js) {
    const jsTag = '  <script src="script.js"><\/script>';
    if (doc.includes('</body>')) {
      doc = doc.replace('</body>', `${jsTag}\n</body>`);
    }
  }

  return { indexHtml: doc, css, js };
}

const AppPreview: React.FC<AppPreviewProps> = ({ htmlContent, appName, onRestart }) => {
  const [copied, setCopied] = useState(false);

  const handleDownload = () => {
    const slug = appName.toLowerCase().replace(/\s+/g, '-') || 'app';
    const { indexHtml, css, js } = splitHtmlCssJs(htmlContent);

    const files: { name: string; content: string }[] = [
      { name: 'index.html', content: indexHtml },
    ];
    if (css) files.push({ name: 'style.css', content: css });
    if (js) files.push({ name: 'script.js', content: js });

    const blob = buildZip(files);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${slug}.zip`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`Downloaded ${files.length} files as ZIP!`);
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