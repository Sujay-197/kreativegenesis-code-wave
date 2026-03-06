import React from 'react';
import { motion } from 'framer-motion';
import { Palette, Layout, Type, Zap } from 'lucide-react';
import type { StylePreferences, ColorSchemeId, SidebarStyle, LayoutDensity } from '../lib/aiEngine';
import { COLOR_SCHEMES, BRAND_ICONS } from '../lib/aiEngine';

interface StylePickerProps {
  preferences: StylePreferences;
  onChange: (prefs: StylePreferences) => void;
}

const StylePicker: React.FC<StylePickerProps> = ({ preferences, onChange }) => {
  const update = (patch: Partial<StylePreferences>) =>
    onChange({ ...preferences, ...patch });

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-forge-accent/15 flex items-center justify-center">
          <Palette size={20} className="text-forge-accent" />
        </div>
        <div>
          <h3 className="font-heading font-bold text-white text-lg">
            Make it yours
          </h3>
          <p className="text-forge-muted text-xs">
            Personalize your app's look & feel
          </p>
        </div>
      </div>

      {/* Color Scheme */}
      <div>
        <label className="text-xs font-semibold text-forge-muted-light uppercase tracking-wider mb-2 block">
          Color Scheme
        </label>
        <div className="grid grid-cols-3 gap-2">
          {(Object.values(COLOR_SCHEMES)).map((scheme) => {
            const active = preferences.colorScheme === scheme.id;
            return (
              <button
                key={scheme.id}
                onClick={() => update({ colorScheme: scheme.id as ColorSchemeId })}
                className={`relative flex items-center gap-2 px-3 py-2.5 rounded-xl border text-left transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent ${
                  active
                    ? 'border-forge-accent bg-forge-accent/10 ring-1 ring-forge-accent/40'
                    : 'border-forge-border hover:border-forge-muted bg-forge-surface'
                }`}
              >
                <div className="flex gap-1">
                  <span
                    className="w-4 h-4 rounded-full"
                    style={{ background: scheme.primary }}
                  />
                  <span
                    className="w-4 h-4 rounded-full"
                    style={{ background: scheme.accent }}
                  />
                </div>
                <span className={`text-xs font-medium ${active ? 'text-white' : 'text-forge-muted-light'}`}>
                  {scheme.name}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Sidebar Style */}
      <div>
        <label className="text-xs font-semibold text-forge-muted-light uppercase tracking-wider mb-2 block">
          <Layout size={12} className="inline mr-1 -mt-0.5" />
          Sidebar Style
        </label>
        <div className="flex gap-2">
          {(['gradient', 'solid', 'dark'] as SidebarStyle[]).map((style) => {
            const active = preferences.sidebarStyle === style;
            const scheme = COLOR_SCHEMES[preferences.colorScheme];
            const preview =
              style === 'gradient'
                ? scheme.gradient
                : style === 'dark'
                  ? 'linear-gradient(180deg, #1a1a2e 10%, #16213e 100%)'
                  : scheme.primary;
            return (
              <button
                key={style}
                onClick={() => update({ sidebarStyle: style })}
                className={`flex-1 flex flex-col items-center gap-1.5 px-3 py-2.5 rounded-xl border transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent ${
                  active
                    ? 'border-forge-accent bg-forge-accent/10'
                    : 'border-forge-border hover:border-forge-muted bg-forge-surface'
                }`}
              >
                <div
                  className="w-6 h-8 rounded"
                  style={{ background: preview }}
                />
                <span className={`text-xs capitalize ${active ? 'text-white font-semibold' : 'text-forge-muted-light'}`}>
                  {style}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Font Style */}
      <div>
        <label className="text-xs font-semibold text-forge-muted-light uppercase tracking-wider mb-2 block">
          <Type size={12} className="inline mr-1 -mt-0.5" />
          Font Style
        </label>
        <div className="flex gap-2">
          {([
            { id: 'modern' as const, label: 'Modern', sample: 'Inter' },
            { id: 'classic' as const, label: 'Classic', sample: 'Source Sans' },
            { id: 'rounded' as const, label: 'Rounded', sample: 'Nunito' },
          ]).map((font) => {
            const active = preferences.fontStyle === font.id;
            return (
              <button
                key={font.id}
                onClick={() => update({ fontStyle: font.id })}
                className={`flex-1 px-3 py-2.5 rounded-xl border text-center transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent ${
                  active
                    ? 'border-forge-accent bg-forge-accent/10'
                    : 'border-forge-border hover:border-forge-muted bg-forge-surface'
                }`}
              >
                <span className={`text-xs ${active ? 'text-white font-semibold' : 'text-forge-muted-light'}`}>
                  {font.label}
                </span>
                <span className="block text-[10px] text-forge-muted mt-0.5">
                  {font.sample}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Layout Density */}
      <div>
        <label className="text-xs font-semibold text-forge-muted-light uppercase tracking-wider mb-2 block">
          <Zap size={12} className="inline mr-1 -mt-0.5" />
          Density
        </label>
        <div className="flex gap-2">
          {(['comfortable', 'compact'] as LayoutDensity[]).map((d) => {
            const active = preferences.density === d;
            return (
              <button
                key={d}
                onClick={() => update({ density: d })}
                className={`flex-1 px-3 py-2.5 rounded-xl border text-center capitalize transition-all duration-150 text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent ${
                  active
                    ? 'border-forge-accent bg-forge-accent/10 text-white font-semibold'
                    : 'border-forge-border hover:border-forge-muted bg-forge-surface text-forge-muted-light'
                }`}
              >
                {d}
              </button>
            );
          })}
        </div>
      </div>

      {/* Brand Icon */}
      <div>
        <label className="text-xs font-semibold text-forge-muted-light uppercase tracking-wider mb-2 block">
          Brand Icon
        </label>
        <div className="flex flex-wrap gap-2">
          {BRAND_ICONS.map((bi) => {
            const active = preferences.brandIcon === bi.id;
            return (
              <button
                key={bi.id}
                onClick={() => update({ brandIcon: bi.id })}
                title={bi.label}
                className={`w-9 h-9 rounded-lg border flex items-center justify-center transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent ${
                  active
                    ? 'border-forge-accent bg-forge-accent/15 text-forge-accent'
                    : 'border-forge-border hover:border-forge-muted bg-forge-surface text-forge-muted-light hover:text-white'
                }`}
              >
                <i className={bi.icon} />
              </button>
            );
          })}
        </div>
      </div>

      {/* Mini Preview */}
      <div className="mt-4 p-3 rounded-xl border border-forge-border bg-forge-surface overflow-hidden">
        <p className="text-[10px] text-forge-muted-light uppercase tracking-wider mb-2 font-semibold">
          Preview
        </p>
        <div className="flex rounded-lg overflow-hidden border border-forge-border h-28">
          {/* Sidebar preview */}
          <div
            className="w-16 flex flex-col items-center pt-3 gap-2"
            style={{
              background:
                preferences.sidebarStyle === 'gradient'
                  ? COLOR_SCHEMES[preferences.colorScheme].gradient
                  : preferences.sidebarStyle === 'dark'
                    ? '#1a1a2e'
                    : COLOR_SCHEMES[preferences.colorScheme].primary,
            }}
          >
            <i
              className={`fas fa-${preferences.brandIcon} text-white text-sm`}
            />
            <div className="w-8 h-0.5 bg-white/20 rounded" />
            <div className="space-y-1.5 w-full px-2">
              <div className="w-full h-1.5 bg-white/30 rounded" />
              <div className="w-3/4 h-1.5 bg-white/15 rounded" />
              <div className="w-full h-1.5 bg-white/15 rounded" />
            </div>
          </div>
          {/* Content preview */}
          <div className="flex-1 bg-[#f8f9fc] p-2">
            <div className="h-3 w-20 bg-gray-200 rounded mb-2" />
            <div className="flex gap-1 mb-2">
              <div
                className="flex-1 h-6 rounded"
                style={{
                  borderLeft: `3px solid ${COLOR_SCHEMES[preferences.colorScheme].primary}`,
                  background: '#fff',
                }}
              />
              <div
                className="flex-1 h-6 rounded"
                style={{
                  borderLeft: `3px solid ${COLOR_SCHEMES[preferences.colorScheme].accent}`,
                  background: '#fff',
                }}
              />
            </div>
            <div className="bg-white rounded p-1 space-y-1">
              <div className="h-1.5 w-full bg-gray-100 rounded" />
              <div className="h-1.5 w-3/4 bg-gray-100 rounded" />
              <div className="h-1.5 w-5/6 bg-gray-100 rounded" />
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default StylePicker;
