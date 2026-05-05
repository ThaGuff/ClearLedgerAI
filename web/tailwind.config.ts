import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        space: {
          deep: '#020410',
          dark: '#070A1F',
          panel: '#0E1330',
          hud: 'rgba(14, 19, 48, 0.65)',
        },
        cosmic: {
          cyan: '#22D3EE',
          cyanHi: '#67E8F9',
          purple: '#7C3AED',
          purpleHi: '#A78BFA',
          gold: '#FBBF24',
          plasma: '#F472B6',
          danger: '#F43F5E',
          mint: '#34D399',
          steel: '#64748B',
          dim: '#94A3B8',
          starlight: '#F1F5F9',
        },
      },
      fontFamily: {
        display: ['Orbitron', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        hud: '0 0 24px rgba(34, 211, 238, 0.25), inset 0 1px 0 rgba(255,255,255,0.05)',
        glow: '0 0 32px rgba(124, 58, 237, 0.5)',
        cyan: '0 0 28px rgba(34, 211, 238, 0.55)',
      },
      backdropBlur: { xs: '4px' },
      keyframes: {
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        flicker: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.92' },
        },
        breathe: {
          '0%, 100%': { boxShadow: '0 0 18px rgba(34,211,238,0.35)' },
          '50%': { boxShadow: '0 0 36px rgba(34,211,238,0.65)' },
        },
      },
      animation: {
        scanline: 'scanline 4s linear infinite',
        flicker: 'flicker 3s ease-in-out infinite',
        breathe: 'breathe 3.5s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};

export default config;
