import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Sparkles } from 'lucide-react';

export interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

interface ChatInterfaceProps {
  messages: Message[];
  onSend: (text: string) => void;
  isLoading: boolean;
  mode: 'simple' | 'expert';
  disabled?: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ messages, onSend, isLoading, mode, disabled }) => {
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // True once the user has sent at least one message
  const hasUserMessages = messages.some((m) => m.role === 'user');

  // The AI's opening message shown in the centred state
  const openingMessage = messages.find((m) => m.role === 'ai');

  useEffect(() => {
    if (hasUserMessages) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, hasUserMessages]);

  // Auto-focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading || disabled) return;
    onSend(trimmed);
    setInput('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const placeholder =
    mode === 'simple' ? 'Tell me about your idea...' : 'Describe your system requirements...';

  // ── Input box (shared between both layouts) ──────────────────
  const InputBox = (
    <div className="flex items-end gap-3 bg-forge-surface border border-forge-border rounded-xl p-3 focus-within:border-forge-accent/60 focus-within:ring-2 focus-within:ring-forge-accent/20 transition-all duration-200">
      <textarea
        ref={inputRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isLoading || disabled}
        rows={1}
        aria-label="Chat input"
        className="flex-1 bg-transparent text-forge-text placeholder:text-forge-muted text-sm resize-none outline-none leading-relaxed max-h-32 disabled:opacity-50"
        style={{ minHeight: '24px' }}
      />
      <button
        onClick={handleSend}
        disabled={!input.trim() || isLoading || disabled}
        aria-label="Send message"
        className="w-8 h-8 rounded-lg bg-forge-accent hover:bg-forge-accent-hover disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-all duration-200 hover:scale-105 flex-shrink-0"
      >
        {isLoading ? (
          <Loader2 size={14} className="text-white animate-spin" />
        ) : (
          <Send size={14} className="text-white" />
        )}
      </button>
    </div>
  );

  // ── CENTRED layout (no user messages yet, like Claude / ChatGPT) ──
  if (!hasUserMessages) {
    return (
      <div className="flex flex-col h-full items-center justify-center px-4 pb-8">
        <motion.div
          key="centred-chat"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-2xl"
        >
          {/* AI avatar + opening question */}
          {openingMessage && (
            <div className="flex items-start gap-3 mb-8">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-forge-accent to-forge-violet flex items-center justify-center flex-shrink-0 shadow-lg">
                <Sparkles size={15} className="text-white" />
              </div>
              <div className="flex-1 bg-forge-surface border border-forge-border px-5 py-4 rounded-2xl rounded-tl-sm text-forge-text text-sm leading-relaxed">
                {openingMessage.content}
              </div>
            </div>
          )}

          {/* Input box centred */}
          {InputBox}
          <p className="text-forge-muted text-xs mt-3 text-center">
            Press Enter to send · Shift+Enter for new line
          </p>
        </motion.div>
      </div>
    );
  }

  // ── STANDARD layout (user has sent messages) ────────────────
  return (
    <motion.div
      key="standard-chat"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col h-full"
    >
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 scrollbar-thin">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'ai' && (
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-forge-accent to-forge-violet flex items-center justify-center flex-shrink-0 mr-3 mt-0.5">
                  <Sparkles size={12} className="text-white" />
                </div>
              )}
              <div
                className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-forge-accent text-white rounded-tr-sm'
                    : 'bg-forge-surface border border-forge-border text-forge-text rounded-tl-sm'
                }`}
              >
                {msg.content}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start"
          >
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-forge-accent to-forge-violet flex items-center justify-center flex-shrink-0 mr-3 mt-0.5">
              <Sparkles size={12} className="text-white" />
            </div>
            <div className="bg-forge-surface border border-forge-border px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-1.5">
              {[0, 1, 2].map((i) => (
                <motion.span
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-forge-accent"
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                />
              ))}
            </div>
          </motion.div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-forge-border p-4">
        {InputBox}
        <p className="text-forge-muted text-xs mt-2 text-center">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </motion.div>
  );
};

export default ChatInterface;