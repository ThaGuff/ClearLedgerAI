"""
Iron Star Ledger · Powered by PLEX Automation
Interstellar finance navigator — real cashflow, AI coach, plasma-grade insights.
"""

from __future__ import annotations

import io
import os
import re
import zipfile
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import requests
import streamlit as st

# ============================================================
# IRON STAR LEDGER — Interstellar palette
# Deep-space background, neon cosmic accents, brushed-iron texture
# ============================================================
DEEP_SPACE   = "#05060F"    # void — page background
SPACE_DARK   = "#0B0E20"    # nebula floor — sidebar, deep panels
PANEL_BG     = "#11152B"    # cards / metric tiles (slightly lifted)
PANEL_HI     = "#1A1F3D"    # hover lift
NEBULA_PUR   = "#7C3AED"    # primary — purple stellar dust
NEBULA_HI    = "#A78BFA"    # primary glow
COSMIC_CYAN  = "#22D3EE"    # secondary — accent, charts, active state
CYAN_HI      = "#67E8F9"    # cyan glow
STAR_GOLD    = "#FBBF24"    # tertiary — warning / highlight
PLASMA_PINK  = "#F472B6"    # negative
PLASMA_RED   = "#F43F5E"    # alert
IRON_STEEL   = "#64748B"    # brushed metal — borders, muted text
STELLAR_WHT  = "#F1F5F9"    # primary text (off-white, no eye-burn)
NEBULA_DIM   = "#94A3B8"    # secondary text
COSMIC_DUST  = "#475569"    # tertiary text / scrollbar

# Compatibility aliases — keeps the rest of the app working w/o per-line edits
PRIMARY       = NEBULA_PUR
PRIMARY_SOFT  = NEBULA_HI
SECONDARY     = COSMIC_CYAN
SECONDARY_HI  = CYAN_HI
SURFACE       = PANEL_BG
SURFACE_HI    = PANEL_HI
SURFACE_DEEP  = "#1F2440"
NEUTRAL       = DEEP_SPACE
ALERT         = PLASMA_RED
TXT_MAIN      = STELLAR_WHT
TXT_DIM       = NEBULA_DIM
TXT_MUTED     = COSMIC_DUST
BORDER        = "#1E2545"
GRID          = "rgba(124,58,237,0.08)"
SUCCESS       = COSMIC_CYAN
SUCCESS_HI    = CYAN_HI
WARNING       = STAR_GOLD
GOLD          = STAR_GOLD
SKY           = "#3B82F6"

# Category colorway — neon cosmic spectrum
CHART_PALETTE = [
    COSMIC_CYAN,        # 1 cyan
    NEBULA_PUR,         # 2 purple
    STAR_GOLD,          # 3 gold
    "#3B82F6",          # 4 stellar blue
    PLASMA_PINK,        # 5 plasma
    "#10B981",          # 6 emerald nebula
    "#A78BFA",          # 7 lavender
    "#FB923C",          # 8 solar orange
]

# Custom Plotly template — deep space, neon glow, smooth transitions
_tpl = go.layout.Template()
_tpl.layout = go.Layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, ui-sans-serif, system-ui", color=STELLAR_WHT, size=12),
    colorway=CHART_PALETTE,
    title=dict(font=dict(color=STELLAR_WHT, size=15, family="Inter"),
               x=0.01, xanchor="left"),
    xaxis=dict(gridcolor=GRID, zerolinecolor="rgba(124,58,237,0.20)",
               linecolor=BORDER,
               tickfont=dict(color=NEBULA_DIM, size=11),
               showspikes=True, spikecolor=COSMIC_CYAN,
               spikethickness=1, spikedash="dot", spikemode="across"),
    yaxis=dict(gridcolor=GRID, zerolinecolor="rgba(124,58,237,0.20)",
               linecolor=BORDER,
               tickfont=dict(color=NEBULA_DIM, size=11),
               showspikes=True, spikecolor=COSMIC_CYAN,
               spikethickness=1, spikedash="dot"),
    legend=dict(bgcolor="rgba(11,14,32,0.6)",
                font=dict(color=STELLAR_WHT, size=11),
                bordercolor=BORDER, borderwidth=1),
    hoverlabel=dict(bgcolor=PANEL_BG, bordercolor=COSMIC_CYAN,
                    font=dict(color=STELLAR_WHT, family="Inter", size=12)),
    hovermode="x unified",
    margin=dict(t=40, b=30, l=20, r=20),
    transition=dict(duration=500, easing="cubic-in-out"),
)
pio.templates["ironstar"] = _tpl
pio.templates.default = "ironstar"

# Categories that are *not* real spend — exclude from expense math
NON_SPEND_CATEGORIES = {"Transfers", "Income", "Income (unverified)"}

# ============================================================
# Page config + global CSS
# ============================================================
st.set_page_config(
    page_title="Iron Star Ledger · Powered by PLEX Automation",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded",
)

CARD_BG = PANEL_BG  # glass panel surface on the deep-space backdrop

st.markdown(
    f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Orbitron:wght@600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        @keyframes twinkle {{
            0%, 100% {{ opacity: 0.85; }}
            50%      {{ opacity: 0.35; }}
        }}
        @keyframes drift {{
            from {{ transform: translateY(0); }}
            to   {{ transform: translateY(-2000px); }}
        }}
        @keyframes pulseGlow {{
            0%, 100% {{ box-shadow: 0 0 18px rgba(124,58,237,.35), 0 0 36px rgba(34,211,238,.18); }}
            50%      {{ box-shadow: 0 0 28px rgba(124,58,237,.55), 0 0 56px rgba(34,211,238,.32); }}
        }}
        @keyframes shimmer {{
            0%   {{ background-position: -200% 0; }}
            100% {{ background-position: 200% 0; }}
        }}

        html, body, [class*="st-"] {{
            font-family: 'Inter', ui-sans-serif, system-ui, sans-serif !important;
        }}

        /* ===== Deep-space stage with nebula gradients ===== */
        .stApp {{
            background:
                radial-gradient(ellipse 70% 45% at 18% 12%, rgba(124,58,237,.32) 0%, transparent 60%),
                radial-gradient(ellipse 60% 40% at 82% 88%, rgba(34,211,238,.22) 0%, transparent 60%),
                radial-gradient(ellipse 50% 30% at 50% 50%, rgba(244,114,182,.10) 0%, transparent 70%),
                linear-gradient(180deg, {DEEP_SPACE} 0%, {SPACE_DARK} 100%);
            color: {STELLAR_WHT};
            background-attachment: fixed;
            position: relative;
            overflow-x: hidden;
        }}
        /* Layered starfield via box-shadow stars */
        .stApp::before, .stApp::after {{
            content: "";
            position: fixed;
            top: 0; left: 0;
            width: 2px; height: 2px;
            background: transparent;
            pointer-events: none;
            z-index: 0;
        }}
        .stApp::before {{
            box-shadow:
                120px 80px #fff, 250px 320px #fff, 410px 540px #ddeaff,
                580px 120px #fff, 720px 380px #cdd9ff, 880px 600px #fff,
                1020px 200px #fff, 1180px 460px #fff, 1320px 700px #c7d4ff,
                1480px 80px #fff, 1620px 540px #fff, 1820px 280px #fff,
                340px 760px #fff, 660px 880px #fff, 980px 940px #fff,
                1240px 820px #ddeaff, 1540px 980px #fff, 80px 1080px #fff,
                440px 1240px #fff, 760px 1380px #c7d4ff, 1080px 1140px #fff,
                1380px 1280px #fff, 1680px 1080px #fff, 200px 1480px #fff,
                540px 1560px #ddeaff, 860px 1640px #fff, 1180px 1480px #fff,
                1500px 1620px #fff, 1820px 1560px #fff, 320px 1820px #fff,
                640px 1880px #c7d4ff, 960px 1940px #fff, 1280px 1820px #fff,
                1600px 1880px #ddeaff;
            animation: twinkle 4s ease-in-out infinite, drift 240s linear infinite;
        }}
        .stApp::after {{
            box-shadow:
                180px 220px #fff, 360px 460px #cdd9ff, 540px 680px #fff,
                820px 240px #fff, 980px 520px #fff, 1140px 760px #ddeaff,
                1300px 320px #fff, 1480px 600px #fff, 1700px 440px #c7d4ff,
                280px 920px #fff, 600px 1040px #ddeaff, 920px 1180px #fff,
                1240px 980px #fff, 1560px 1100px #fff, 1860px 920px #fff,
                160px 1320px #fff, 480px 1380px #cdd9ff, 800px 1500px #fff,
                1120px 1320px #c7d4ff, 1440px 1460px #fff, 1760px 1340px #fff;
            animation: twinkle 6s ease-in-out infinite 1.5s, drift 320s linear infinite;
            opacity: 0.7;
        }}

        /* All Streamlit content sits above the starfield */
        [data-testid="stAppViewContainer"], section[data-testid="stSidebar"] {{
            position: relative;
            z-index: 1;
        }}

        /* ===== Sidebar — galactic console ===== */
        section[data-testid="stSidebar"] {{
            background:
                linear-gradient(180deg, rgba(11,14,32,.92) 0%, rgba(5,6,15,.96) 100%) !important;
            border-right: 1px solid rgba(124,58,237,.35);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
        }}
        section[data-testid="stSidebar"] * {{ color: {STELLAR_WHT}; }}

        /* ===== Typography — cosmic fonts ===== */
        h1 {{
            font-family: 'Orbitron', 'Inter', sans-serif !important;
            font-weight: 800 !important;
            font-size: 2.55rem !important;
            background: linear-gradient(120deg, {COSMIC_CYAN} 0%, {NEBULA_HI} 50%, {STAR_GOLD} 100%);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            color: transparent !important;
            letter-spacing: .02em;
            margin-bottom: .25rem !important;
            text-shadow: 0 0 40px rgba(124,58,237,.4);
        }}
        h2 {{
            font-family: 'Orbitron', 'Inter', sans-serif !important;
            font-weight: 700 !important;
            color: {STELLAR_WHT} !important;
            letter-spacing: .005em;
        }}
        h3 {{
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            font-size: 1.18rem !important;
            color: {STELLAR_WHT} !important;
            letter-spacing: -.005em;
        }}
        h4 {{
            font-weight: 600 !important;
            color: {COSMIC_CYAN} !important;
            font-size: .78rem !important;
            text-transform: uppercase;
            letter-spacing: .14em;
            margin-bottom: .75rem !important;
        }}
        p, label, span, div, li {{ color: {STELLAR_WHT}; }}

        /* ===== Metric cards — glassmorphism HUD ===== */
        [data-testid="stMetric"] {{
            background: linear-gradient(135deg, rgba(26,31,61,.78) 0%, rgba(17,21,43,.65) 100%);
            border: 1px solid rgba(124,58,237,.30);
            border-radius: 16px;
            padding: 20px 22px;
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.06),
                0 4px 24px rgba(5,6,15,.6);
            transition: all .25s cubic-bezier(.4,0,.2,1);
            position: relative;
            overflow: hidden;
        }}
        [data-testid="stMetric"]::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, {COSMIC_CYAN}, {NEBULA_PUR}, transparent);
            opacity: .55;
        }}
        [data-testid="stMetric"]:hover {{
            border-color: {COSMIC_CYAN};
            transform: translateY(-3px);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.08),
                0 0 28px rgba(34,211,238,.35),
                0 8px 32px rgba(124,58,237,.30);
        }}
        [data-testid="stMetricLabel"] {{
            color: {NEBULA_DIM} !important;
            font-size: .76rem !important;
            font-weight: 600 !important;
            letter-spacing: .12em;
            text-transform: uppercase;
            font-family: 'JetBrains Mono', monospace !important;
        }}
        [data-testid="stMetricValue"] {{
            color: {STELLAR_WHT} !important;
            font-weight: 800 !important;
            font-size: 1.85rem !important;
            font-family: 'Orbitron', 'Inter', sans-serif !important;
            letter-spacing: -.01em;
            text-shadow: 0 0 18px rgba(34,211,238,.35);
        }}
        [data-testid="stMetricDelta"] {{
            color: {STAR_GOLD} !important;
            font-size: .78rem !important;
            font-weight: 600 !important;
            font-family: 'JetBrains Mono', monospace !important;
        }}

        /* ===== Tabs — neon command bar ===== */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 6px;
            border-bottom: 1px solid rgba(124,58,237,.25);
            padding-bottom: 2px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background: rgba(17,21,43,.5);
            border: 1px solid rgba(100,116,139,.22);
            border-radius: 10px 10px 0 0;
            padding: 12px 22px;
            color: {NEBULA_DIM} !important;
            font-weight: 600 !important;
            font-size: .92rem;
            letter-spacing: .03em;
            transition: all .2s ease;
            backdrop-filter: blur(8px);
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            color: {COSMIC_CYAN} !important;
            background: rgba(34,211,238,.08);
            border-color: rgba(34,211,238,.4);
            box-shadow: 0 0 16px rgba(34,211,238,.25);
        }}
        .stTabs [aria-selected="true"] {{
            color: {STELLAR_WHT} !important;
            background: linear-gradient(135deg, rgba(124,58,237,.30), rgba(34,211,238,.18)) !important;
            border-color: {COSMIC_CYAN} !important;
            border-bottom: 3px solid {COSMIC_CYAN} !important;
            box-shadow: 0 0 22px rgba(34,211,238,.35);
        }}

        /* ===== Buttons — plasma drive (FIX: explicit white text always visible) ===== */
        .stDownloadButton button, .stButton button {{
            background: linear-gradient(135deg, {NEBULA_PUR} 0%, {COSMIC_CYAN} 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(167,139,250,.55) !important;
            font-weight: 700 !important;
            font-size: .92rem !important;
            letter-spacing: .04em !important;
            text-transform: uppercase;
            border-radius: 10px !important;
            padding: .65rem 1.5rem !important;
            transition: all .25s cubic-bezier(.4,0,.2,1);
            box-shadow:
                0 0 18px rgba(124,58,237,.45),
                inset 0 1px 0 rgba(255,255,255,.18);
            text-shadow: 0 1px 2px rgba(5,6,15,.6);
            position: relative;
            overflow: hidden;
        }}
        .stDownloadButton button *, .stButton button * {{
            color: #FFFFFF !important;
        }}
        .stDownloadButton button:hover, .stButton button:hover {{
            background: linear-gradient(135deg, {COSMIC_CYAN} 0%, {NEBULA_HI} 100%) !important;
            border-color: {CYAN_HI} !important;
            color: #FFFFFF !important;
            transform: translateY(-2px);
            box-shadow:
                0 0 32px rgba(34,211,238,.65),
                0 0 56px rgba(124,58,237,.40),
                inset 0 1px 0 rgba(255,255,255,.25);
        }}
        .stDownloadButton button:active, .stButton button:active {{
            transform: translateY(0);
            box-shadow: 0 0 12px rgba(34,211,238,.4);
        }}

        /* ===== Inputs — holographic terminals ===== */
        input, textarea, .stTextInput input, .stDateInput input,
        [data-baseweb="select"] > div, [data-baseweb="input"] {{
            background: rgba(11,14,32,.7) !important;
            color: {STELLAR_WHT} !important;
            border: 1px solid rgba(124,58,237,.30) !important;
            border-radius: 10px !important;
            font-size: .92rem !important;
            backdrop-filter: blur(6px);
        }}
        input::placeholder, textarea::placeholder {{ color: {COSMIC_DUST} !important; }}
        input:focus, textarea:focus, [data-baseweb="select"] > div:focus-within {{
            border-color: {COSMIC_CYAN} !important;
            box-shadow: 0 0 0 3px rgba(34,211,238,.22), 0 0 18px rgba(34,211,238,.30) !important;
            outline: none !important;
        }}
        [data-baseweb="tag"] {{
            background: linear-gradient(135deg, rgba(124,58,237,.25), rgba(34,211,238,.18)) !important;
            border: 1px solid rgba(124,58,237,.45) !important;
            color: {STELLAR_WHT} !important;
        }}
        [data-baseweb="select"] [data-baseweb="icon"] {{ color: {COSMIC_CYAN} !important; }}

        /* ===== File uploader — docking bay ===== */
        [data-testid="stFileUploader"] section {{
            background: rgba(17,21,43,.55) !important;
            border: 1.5px dashed rgba(34,211,238,.55) !important;
            border-radius: 14px !important;
            backdrop-filter: blur(10px);
            transition: all .25s ease;
        }}
        [data-testid="stFileUploader"] section:hover {{
            border-color: {COSMIC_CYAN} !important;
            background: rgba(34,211,238,.08) !important;
            box-shadow: 0 0 28px rgba(34,211,238,.30);
        }}
        [data-testid="stFileUploader"] small {{ color: {NEBULA_DIM} !important; }}
        [data-testid="stFileUploader"] svg {{ color: {COSMIC_CYAN} !important; }}

        /* ===== Insight cards — telemetry panels ===== */
        .insight-card {{
            background: linear-gradient(135deg, rgba(26,31,61,.78) 0%, rgba(17,21,43,.6) 100%);
            border: 1px solid rgba(124,58,237,.28);
            border-left: 4px solid {COSMIC_CYAN};
            border-radius: 14px;
            padding: 18px 22px; margin-bottom: 14px;
            backdrop-filter: blur(14px);
            box-shadow: 0 4px 18px rgba(5,6,15,.55), inset 0 1px 0 rgba(255,255,255,.04);
            transition: all .2s cubic-bezier(.4,0,.2,1);
        }}
        .insight-card:hover {{
            transform: translateX(3px);
            border-left-color: {NEBULA_HI};
            box-shadow:
                0 4px 24px rgba(5,6,15,.65),
                0 0 22px rgba(124,58,237,.30);
        }}
        .insight-card.warn {{ border-left-color: {PLASMA_RED}; box-shadow: 0 4px 18px rgba(244,63,94,.20); }}
        .insight-card.good {{ border-left-color: #10B981; box-shadow: 0 4px 18px rgba(16,185,129,.18); }}
        .insight-card.info {{ border-left-color: {STAR_GOLD}; box-shadow: 0 4px 18px rgba(251,191,36,.18); }}
        .insight-card.success {{
            border-left-color: #10B981;
            background: linear-gradient(135deg, rgba(16,185,129,.18) 0%, rgba(17,21,43,.6) 50%);
        }}
        .insight-card h4 {{
            margin: 0 0 .5rem 0 !important;
            color: {STELLAR_WHT} !important;
            text-transform: none;
            font-size: 1.04rem !important;
            font-weight: 700 !important;
            letter-spacing: 0;
        }}
        .insight-card div {{ font-size: .94rem; line-height: 1.6; color: {STELLAR_WHT}; }}

        .stat-pill {{
            display: inline-block; padding: .32rem .78rem; border-radius: 999px;
            background: rgba(11,14,32,.7); border: 1px solid rgba(124,58,237,.35);
            color: {NEBULA_DIM}; font-size: .78rem; font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            margin-right: .4rem;
            backdrop-filter: blur(6px);
        }}
        .pill-good {{ background: rgba(16,185,129,.18); border-color: #10B981; color: #6EE7B7; }}
        .pill-warn {{ background: rgba(244,63,94,.18); border-color: {PLASMA_RED}; color: #FDA4AF; }}
        .pill-info {{ background: rgba(251,191,36,.18); border-color: {STAR_GOLD}; color: #FCD34D; }}

        .text-emerald {{ color: #34D399 !important; font-weight: 600; }}
        .text-coral {{ color: {PLASMA_RED} !important; font-weight: 600; }}
        .text-blue {{ color: {COSMIC_CYAN} !important; font-weight: 600; }}
        .text-dim {{ color: {NEBULA_DIM} !important; }}

        .footer {{
            text-align: center; padding: 2rem 0 1rem 0;
            color: {NEBULA_DIM} !important; font-size: .82rem;
            border-top: 1px solid rgba(124,58,237,.25); margin-top: 2.5rem;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: .05em;
        }}
        .footer a {{ color: {COSMIC_CYAN} !important; text-decoration: none; font-weight: 700; }}
        .footer a:hover {{ text-shadow: 0 0 12px rgba(34,211,238,.6); }}

        /* ===== DataFrame — flight-deck table ===== */
        [data-testid="stDataFrame"] {{
            background: rgba(17,21,43,.7) !important;
            border: 1px solid rgba(124,58,237,.30);
            border-radius: 14px; overflow: hidden;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 18px rgba(5,6,15,.55);
        }}
        [data-testid="stDataFrame"] * {{ color: {STELLAR_WHT} !important; }}

        /* ===== Dividers — quantum threads ===== */
        hr, [data-testid="stDivider"] {{
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg, transparent, {NEBULA_PUR}, {COSMIC_CYAN}, {NEBULA_PUR}, transparent) !important;
            margin: 1.5rem 0 !important;
            opacity: .55;
        }}

        /* ===== Alerts ===== */
        [data-testid="stAlert"] {{
            background: rgba(17,21,43,.7) !important;
            border: 1px solid rgba(124,58,237,.35) !important;
            border-radius: 12px !important;
            backdrop-filter: blur(10px);
            color: {STELLAR_WHT} !important;
        }}
        [data-testid="stAlert"] * {{ color: {STELLAR_WHT} !important; }}

        /* ===== Sidebar branding — mission patch ===== */
        .brand-logo {{
            display: flex; align-items: center; gap: .75rem;
            padding: .6rem 0; margin-bottom: 1.25rem;
        }}
        .brand-logo .icon {{
            width: 46px; height: 46px;
            background: radial-gradient(circle at 30% 30%, {NEBULA_HI}, {NEBULA_PUR} 55%, {DEEP_SPACE});
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.5rem;
            color: {STELLAR_WHT};
            border: 1px solid rgba(167,139,250,.6);
            animation: pulseGlow 3.5s ease-in-out infinite;
        }}
        .brand-logo .name {{
            font-family: 'Orbitron', sans-serif !important;
            font-weight: 800; font-size: 1.18rem;
            background: linear-gradient(120deg, {COSMIC_CYAN}, {NEBULA_HI});
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            color: transparent;
            letter-spacing: .04em;
        }}
        .brand-logo .tag {{
            font-size: .66rem; color: {COSMIC_CYAN};
            text-transform: uppercase; letter-spacing: .18em;
            font-family: 'JetBrains Mono', monospace;
        }}

        /* ===== Sidebar Pro tile — warp drive ===== */
        .pro-tile {{
            background: linear-gradient(135deg, {NEBULA_PUR} 0%, {COSMIC_CYAN} 100%);
            border-radius: 14px;
            padding: 1rem 1.1rem;
            color: #FFFFFF !important;
            box-shadow: 0 6px 22px rgba(124,58,237,.55), inset 0 1px 0 rgba(255,255,255,.18);
            position: relative;
            overflow: hidden;
        }}
        .pro-tile::after {{
            content: "";
            position: absolute; inset: 0;
            background: linear-gradient(110deg, transparent 30%, rgba(255,255,255,.18) 50%, transparent 70%);
            background-size: 200% 100%;
            animation: shimmer 4s linear infinite;
            pointer-events: none;
        }}
        .pro-tile * {{ color: #FFFFFF !important; }}

        /* ===== Scrollbars ===== */
        ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
        ::-webkit-scrollbar-track {{ background: {DEEP_SPACE}; }}
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, {NEBULA_PUR}, {COSMIC_CYAN});
            border-radius: 5px;
        }}
        ::-webkit-scrollbar-thumb:hover {{ background: {COSMIC_CYAN}; }}

        /* Toggle */
        [role="switch"][aria-checked="true"] {{
            background: {COSMIC_CYAN} !important;
        }}

        /* ===== Plotly chart container — viewport pane ===== */
        [data-testid="stPlotlyChart"] > div {{
            background: linear-gradient(135deg, rgba(17,21,43,.55) 0%, rgba(11,14,32,.7) 100%);
            border: 1px solid rgba(124,58,237,.28);
            border-radius: 16px;
            padding: 12px;
            backdrop-filter: blur(14px);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.04),
                0 4px 22px rgba(5,6,15,.55);
            transition: box-shadow .25s ease;
        }}
        [data-testid="stPlotlyChart"] > div:hover {{
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.06),
                0 0 26px rgba(34,211,238,.25),
                0 4px 28px rgba(5,6,15,.65);
        }}

        /* ===== Sliders ===== */
        [data-baseweb="slider"] [role="slider"] {{
            background: {COSMIC_CYAN} !important;
            box-shadow: 0 0 12px rgba(34,211,238,.6) !important;
        }}

        /* ===== Expander ===== */
        [data-testid="stExpander"] {{
            background: rgba(17,21,43,.6) !important;
            border: 1px solid rgba(124,58,237,.28) !important;
            border-radius: 12px !important;
            backdrop-filter: blur(10px);
        }}
        [data-testid="stExpander"] summary {{ color: {STELLAR_WHT} !important; }}

        /* ===== Code blocks ===== */
        code, pre {{
            background: rgba(5,6,15,.7) !important;
            color: {COSMIC_CYAN} !important;
            border-radius: 6px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Parsers — robust CSV with cleaning + header detection
# ============================================================
DATE_HINTS = ["date", "posted", "transaction date", "trans date", "post date",
              "posting date", "transaction"]
AMOUNT_HINTS = ["amount", "amt", "value", "total", "transaction amount"]
DEBIT_HINTS = ["debit", "withdrawal", "withdrawals", "money out", "outflow", "spent"]
CREDIT_HINTS = ["credit", "deposit", "deposits", "money in", "inflow"]
PAYEE_HINTS = ["description", "payee", "merchant", "name", "memo", "details",
               "transaction description", "narration", "particulars"]
TYPE_HINTS  = ["transaction type", "trans type", "type", "dr/cr", "debit/credit",
               "credit/debit", "txn type"]
DEBIT_TYPE_TOKENS  = {"debit", "withdrawal", "dr", "purchase", "payment", "fee",
                       "charge", "outflow", "out", "expense", "spend", "sale"}
CREDIT_TYPE_TOKENS = {"credit", "deposit", "cr", "refund", "interest", "inflow",
                       "in", "income", "salary", "payroll"}


def _clean_amount(v) -> Optional[float]:
    """Convert messy money strings to float. Handles $, commas, parens, currency codes."""
    if pd.isna(v):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s or s.lower() in ("nan", "none", "-", "—"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[(),$£€¥₹\s]", "", s).replace("USD", "").replace("CAD", "")
    s = s.replace(",", "").replace("'", "")
    if neg:
        s = "-" + s
    try:
        return float(s)
    except ValueError:
        return None


def _clean_amount_series(s: pd.Series) -> pd.Series:
    return s.apply(_clean_amount)


def _detect_col(cols: list[str], hints: list[str]) -> Optional[str]:
    lowered = {c.lower().strip(): c for c in cols}
    for h in hints:
        for low, orig in lowered.items():
            if h == low:
                return orig
    for h in hints:
        for low, orig in lowered.items():
            if h in low:
                return orig
    return None


def _frame_from_tabular(raw: pd.DataFrame, source_name: str) -> tuple[pd.DataFrame, dict]:
    """Return (parsed_df, detection_meta)."""
    raw = raw.copy()
    raw.columns = [str(c).strip() for c in raw.columns]
    cols = list(raw.columns)
    date_c = _detect_col(cols, DATE_HINTS)
    amt_c = _detect_col(cols, AMOUNT_HINTS)
    debit_c = _detect_col(cols, DEBIT_HINTS)
    credit_c = _detect_col(cols, CREDIT_HINTS)
    payee_c = _detect_col(cols, PAYEE_HINTS)
    type_c  = _detect_col(cols, TYPE_HINTS)
    # Don't double-count: if AMOUNT was matched, ignore Debit/Credit single-word matches
    if amt_c:
        if debit_c == amt_c: debit_c = None
        if credit_c == amt_c: credit_c = None

    meta = {"columns": cols, "date_col": date_c, "amount_col": amt_c,
            "debit_col": debit_c, "credit_col": credit_c, "payee_col": payee_c,
            "type_col": type_c}

    if not date_c:
        raise ValueError(f"No Date column detected. Columns found: {cols}")

    if amt_c:
        amount = _clean_amount_series(raw[amt_c])
        # If amounts are positive-only AND a Type column exists, apply sign by type
        non_null = amount.dropna()
        if len(non_null) > 0 and type_c and (non_null >= 0).all():
            t = raw[type_c].astype(str).str.lower().str.strip()
            sign = pd.Series(1.0, index=amount.index)
            sign[t.apply(lambda x: any(tok in x for tok in DEBIT_TYPE_TOKENS))] = -1.0
            amount = amount.abs() * sign
            meta["sign_applied_from_type"] = True
    elif debit_c or credit_c:
        deb = _clean_amount_series(raw[debit_c]).fillna(0).abs() if debit_c else 0
        cre = _clean_amount_series(raw[credit_c]).fillna(0).abs() if credit_c else 0
        amount = cre - deb
    else:
        raise ValueError(f"No Amount/Debit/Credit column detected. Columns: {cols}")

    parsed_dates = pd.to_datetime(raw[date_c], errors="coerce")
    if parsed_dates.notna().sum() == 0:
        # try day-first
        parsed_dates = pd.to_datetime(raw[date_c], errors="coerce", dayfirst=True)

    df = pd.DataFrame({
        "date": parsed_dates,
        "amount": amount,
        "payee": raw[payee_c].astype(str).str.strip() if payee_c else "Unknown",
        "source": source_name,
    }).dropna(subset=["date", "amount"]).reset_index(drop=True)

    if df.empty:
        raise ValueError(f"All rows had unparseable dates or amounts. Detected: date={date_c}, amount={amt_c or f'{debit_c}/{credit_c}'}")

    return df, meta


def _read_csv_smart(text: str, source_name: str) -> pd.DataFrame:
    """Try multiple delimiters + skip 0-5 preamble lines, pick best column count."""
    best = None
    best_cols = 0
    for skip in range(0, 6):
        for sep in (",", ";", "\t", "|"):
            try:
                df = pd.read_csv(io.StringIO(text), sep=sep, engine="python",
                                 skiprows=skip, on_bad_lines="skip")
                if df.shape[1] > best_cols and df.shape[0] > 0:
                    # Prefer if any common keyword shows in headers
                    cols_low = " ".join(str(c).lower() for c in df.columns)
                    score = df.shape[1]
                    if any(k in cols_low for k in DATE_HINTS): score += 5
                    if any(k in cols_low for k in AMOUNT_HINTS + DEBIT_HINTS + CREDIT_HINTS): score += 5
                    if score > best_cols:
                        best, best_cols = df, score
            except Exception:
                continue
    if best is None or best.empty:
        raise ValueError(f"Could not read CSV: {source_name}")
    return best


def parse_csv(file) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Returns (parsed_df, detection_meta, raw_df_for_remap)."""
    file.seek(0)
    raw_bytes = file.read()
    text = None
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            text = raw_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError(f"Could not decode CSV: {file.name}")
    raw = _read_csv_smart(text, file.name)
    parsed, meta = _frame_from_tabular(raw, file.name)
    return parsed, meta, raw


def parse_excel(file) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    raw = pd.read_excel(file, engine="openpyxl" if file.name.lower().endswith("xlsx") else None)
    parsed, meta = _frame_from_tabular(raw, file.name)
    return parsed, meta, raw


def _parse_ofx_text(text: str, source_name: str) -> pd.DataFrame:
    try:
        from ofxparse import OfxParser
        ofx = OfxParser.parse(io.BytesIO(text.encode("utf-8")))
        rows = []
        for account in ofx.accounts:
            for t in account.statement.transactions:
                rows.append({
                    "date": pd.to_datetime(t.date),
                    "amount": float(t.amount),
                    "payee": (t.payee or t.memo or "Unknown").strip(),
                    "source": source_name,
                })
        if rows:
            return pd.DataFrame(rows)
    except Exception:
        pass
    rows: list[dict] = []
    for block in re.findall(r"<STMTTRN>(.*?)</STMTTRN>", text, re.DOTALL | re.IGNORECASE):
        def grab(tag):
            m = re.search(rf"<{tag}>([^<\r\n]+)", block, re.IGNORECASE)
            return m.group(1).strip() if m else ""
        d, a = grab("DTPOSTED"), grab("TRNAMT")
        if not d or not a: continue
        try:
            rows.append({
                "date": pd.to_datetime(d[:8], format="%Y%m%d", errors="coerce"),
                "amount": float(a),
                "payee": grab("NAME") or grab("MEMO") or "Unknown",
                "source": source_name,
            })
        except Exception:
            continue
    if not rows:
        raise ValueError(f"No transactions in {source_name}")
    return pd.DataFrame(rows).dropna(subset=["date"])


def parse_ofx(file) -> tuple[pd.DataFrame, dict, Optional[pd.DataFrame]]:
    file.seek(0)
    raw = file.read()
    text = raw.decode("utf-8", "ignore") if isinstance(raw, bytes) else raw
    return _parse_ofx_text(text, file.name), {"format": "OFX"}, None


def parse_qfx(file) -> tuple[pd.DataFrame, dict, Optional[pd.DataFrame]]:
    file.seek(0)
    raw = file.read()
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for name in z.namelist():
                if name.lower().endswith((".qfx", ".qbo", ".ofx", ".xml")):
                    with z.open(name) as f:
                        return (_parse_ofx_text(f.read().decode("utf-8", "ignore"), file.name),
                                {"format": "QFX (zip)"}, None)
        raise ValueError(f"No QFX/OFX in zip {file.name}")
    return _parse_ofx_text(raw.decode("utf-8", "ignore"), file.name), {"format": "QFX"}, None


def parse_any(file) -> tuple[pd.DataFrame, dict, Optional[pd.DataFrame]]:
    n = file.name.lower()
    if n.endswith(".csv"):           return parse_csv(file)
    if n.endswith((".xlsx", ".xls")): return parse_excel(file)
    if n.endswith(".ofx"):           return parse_ofx(file)
    if n.endswith((".qbo", ".qfx")): return parse_qfx(file)
    raise ValueError(f"Unsupported file type: {file.name}")


def remap_tabular(raw: pd.DataFrame, source: str, date_col: str,
                  payee_col: str, amount_col: Optional[str],
                  debit_col: Optional[str], credit_col: Optional[str]) -> pd.DataFrame:
    """Manual remap from raw dataframe."""
    if amount_col:
        amount = _clean_amount_series(raw[amount_col])
    elif debit_col or credit_col:
        deb = _clean_amount_series(raw[debit_col]).fillna(0) if debit_col else 0
        cre = _clean_amount_series(raw[credit_col]).fillna(0) if credit_col else 0
        amount = cre - deb
    else:
        raise ValueError("Must select either Amount, or Debit/Credit columns")
    df = pd.DataFrame({
        "date": pd.to_datetime(raw[date_col], errors="coerce"),
        "amount": amount,
        "payee": raw[payee_col].astype(str).str.strip() if payee_col else "Unknown",
        "source": source,
    }).dropna(subset=["date", "amount"]).reset_index(drop=True)
    return df


# ============================================================
# Categorization (expanded keywords + normalization)
# ============================================================
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("Income",        ["salary","payroll","direct dep","paycheck","stripe payout","interest payment",
                       "dividend","refund","reimbursement","tax refund","ach credit","irs treas"]),
    ("Housing",       ["rent","mortgage","hoa","property tax","landlord","property mgmt",
                       "apartment","leasing","real estate"]),
    ("Utilities",     ["electric","pg&e","con ed","water","sewer","internet","comcast","xfinity",
                       "att","at&t","verizon","tmobile","t-mobile","spectrum","cellular","sprint",
                       "duke energy","national grid","gas company","cox comm"]),
    ("Groceries",     ["whole foods","trader joe","safeway","kroger","costco","wegmans","publix",
                       "aldi","sprouts","albertsons","grocery","supermarket","walmart","heb",
                       "harris teeter","stop shop","food lion","meijer","giant"]),
    ("Dining",        ["starbucks","mcdonald","chipotle","doordash","uber eats","grubhub",
                       "restaurant","cafe","coffee","pizza","sushi","panera","chick-fil-a",
                       "subway","taco bell","wendy","burger","kfc","dunkin","sonic","denny"]),
    ("Transport",     ["uber","lyft","shell","chevron","exxon","bp gas","gas station","parking",
                       "transit","metro","amtrak","airline","delta","united","southwest",
                       "american air","jetblue","alaska air","mta","bart","caltrain","toll"]),
    ("Subscriptions", ["netflix","spotify","hulu","disney+","disney plus","hbo","max ","youtube",
                       "apple.com/bill","apple bill","icloud","adobe","github","openai","claude",
                       "anthropic","chatgpt","notion","dropbox","patreon","peacock","paramount",
                       "audible","kindle unlim","crunchyroll","prime video","linkedin"]),
    ("Shopping",      ["amazon","amzn","ebay","etsy","best buy","apple store","nike","nordstrom",
                       "macy","ikea","home depot","lowe","wayfair","target","tj maxx","ross",
                       "marshalls","old navy","gap","zara","h&m","sephora"]),
    ("Health",        ["pharmacy","cvs","walgreens","doctor","clinic","hospital","dental",
                       "vision","medical","blue cross","aetna","kaiser","cigna","humana",
                       "rite aid","quest diag","labcorp"]),
    ("Fitness",       ["gym","peloton","equinox","planet fitness","yoga","crossfit","24 hour fit",
                       "lifetime fit","la fitness","orangetheory"]),
    ("Entertainment", ["movie","amc","regal","theater","concert","ticketmaster","stubhub","steam",
                       "playstation","xbox","nintendo","cinemark","fandango"]),
    ("Personal Care", ["salon","barber","spa","nails","sephora","ulta","supercuts","massage"]),
    ("Insurance",     ["geico","progressive","state farm","allstate","insurance","liberty mut",
                       "farmers ins","nationwide"]),
    ("Education",     ["tuition","udemy","coursera","school","university","college","sallie mae",
                       "nelnet","loan servicing","masterclass","skillshare"]),
    ("Travel",        ["hotel","airbnb","marriott","hilton","expedia","booking","hyatt","ihg",
                       "vrbo","kayak","priceline"]),
    ("Fees & Interest",["fee","interest charge","overdraft","atm","service charge","late fee",
                        "annual fee","foreign trans"]),
    ("Transfers",     ["transfer","zelle","venmo","cash app","paypal","wire","ach transfer"]),
]


def _normalize(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = re.sub(r"[*#]", " ", s)
    s = re.sub(r"\d{4,}", " ", s)  # strip long digit blocks (txn ids)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def categorize(payee: str, amount: float) -> str:
    """Categorize by payee keywords first; sign only used as a tiebreaker."""
    p = _normalize(payee)
    # 1) Try keyword match across ALL categories (sign-agnostic)
    for cat, kw in CATEGORY_RULES:
        if any(k in p for k in kw):
            # Don't tag a clear outflow as Income just because keyword overlaps
            if cat == "Income" and amount < 0:
                continue
            return cat
    # 2) No keyword hit — use sign as last resort
    if amount > 0:
        return "Income (unverified)"
    return "Other"


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("date").reset_index(drop=True)
    df["category"] = [categorize(p, a) for p, a in zip(df["payee"], df["amount"])]
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["weekday"] = df["date"].dt.day_name()
    df["abs_amount"] = df["amount"].abs()
    df["type"] = np.where(df["amount"] > 0, "Income", "Expense")
    # Running balance (treat first txn as zero baseline)
    df["running_balance"] = df["amount"].cumsum()
    return df


# ============================================================
# Subscription detector
# ============================================================
def detect_subscriptions(df: pd.DataFrame) -> pd.DataFrame:
    """Detect recurring charges. Two strategies:
       (1) Repeat-payee with stable cadence (works on 30+ day windows)
       (2) Keyword fallback for single-month uploads (catches Netflix etc.)"""
    exp = df[df["amount"] < 0].copy()
    if exp.empty: return pd.DataFrame()
    exp["payee_norm"] = exp["payee"].apply(_normalize)
    out = []

    # Strategy 1: cadence-based detection
    for _, g in exp.groupby("payee_norm"):
        if len(g) < 2: continue
        g = g.sort_values("date")
        deltas = g["date"].diff().dt.days.dropna()
        if deltas.empty: continue
        gap = float(deltas.median())
        if not (5 <= gap <= 35 or 85 <= gap <= 95): continue
        amts = g["amount"].abs()
        if amts.std() / (amts.mean() + 1e-9) > 0.25: continue
        cadence = ("Weekly" if gap < 10 else "Bi-Weekly" if gap < 20
                   else "Monthly" if gap < 40 else "Quarterly")
        mult = {"Weekly":52,"Bi-Weekly":26,"Monthly":12,"Quarterly":4}[cadence]
        out.append({
            "Merchant": g["payee"].iloc[-1],
            "Cadence": cadence,
            "Avg Charge": float(amts.mean()),
            "Last Charged": g["date"].max(),
            "Charges": int(len(g)),
            "Annual Cost": float(amts.mean() * mult),
            "Detected By": "Cadence",
        })

    # Strategy 2: keyword fallback (catches single-month uploads)
    seen = {row["Merchant"].lower() for row in out}
    sub_kw = [k for _, kws in CATEGORY_RULES if _ == "Subscriptions"  # noqa: E741
              for k in kws]
    sub_kw = [k for cat, kws in CATEGORY_RULES if cat == "Subscriptions" for k in kws]
    for _, g in exp.groupby("payee_norm"):
        merchant = g["payee"].iloc[-1]
        if merchant.lower() in seen: continue
        p = _normalize(merchant)
        if not any(k in p for k in sub_kw): continue
        amts = g["amount"].abs()
        out.append({
            "Merchant": merchant,
            "Cadence": "Monthly (est)",
            "Avg Charge": float(amts.mean()),
            "Last Charged": g["date"].max(),
            "Charges": int(len(g)),
            "Annual Cost": float(amts.mean() * 12),
            "Detected By": "Keyword",
        })

    return (pd.DataFrame(out).sort_values("Annual Cost", ascending=False).reset_index(drop=True)
            if out else pd.DataFrame())


# ============================================================
# Health Score + Reasoning
# ============================================================
def compute_health(df: pd.DataFrame) -> dict:
    """Honest financial health score.

    Key fixes vs naïve version:
      • Transfers / unverified income are excluded from real income & expenses
      • Monthly figures use **actual day-span** (not number of calendar months)
      • Stability re-weights when there are <2 full months of data
      • Renamed Runway → Savings Buffer (it's a ratio, not actual emergency runway)
    """
    if df.empty:
        return {"score": 0, "components": {}, "metrics": {}, "reasoning": []}

    # --- Real income & expenses (exclude transfers + unverified income) ---
    spend_mask = df["amount"] < 0
    real_spend_mask = spend_mask & ~df["category"].isin(NON_SPEND_CATEGORIES)
    income_mask = (df["amount"] > 0) & (df["category"] == "Income")

    income = float(df.loc[income_mask, "amount"].sum())
    expenses = float(-df.loc[real_spend_mask, "amount"].sum())
    transfers = float(df.loc[df["category"] == "Transfers", "amount"].abs().sum())
    unverified_income = float(df.loc[df["category"] == "Income (unverified)", "amount"].sum())
    net = income - expenses

    # --- Real day-span based "per month" math ---
    days = max(1, (df["date"].max() - df["date"].min()).days + 1)
    months_span = days / 30.4375  # average month length
    monthly_expense = expenses / months_span if months_span > 0 else expenses
    monthly_income  = income   / months_span if months_span > 0 else income

    # --- Component scores ---
    ratio = expenses / income if income > 0 else 1.0
    e_score = 1.0 if ratio <= 0.5 else 0.0 if ratio >= 1.0 else 1.0 - (ratio - 0.5) / 0.5

    sr = (net / income) if income > 0 else 0.0
    s_score = 1.0 if sr >= 0.15 else max(0.0, sr / 0.15) if sr > 0 else 0.0

    # Use **net** monthly (not raw amount) for stability so transfers don't poison it
    monthly_net = (df.loc[~df["category"].isin({"Transfers"})]
                     .set_index("date")
                     .resample("ME")["amount"].sum())
    months = max(1, len(monthly_net))
    have_stability = len(monthly_net) >= 2 and monthly_net.abs().mean() > 0
    if have_stability:
        cv = float(monthly_net.std() / (monthly_net.abs().mean() + 1e-9))
        st_score = max(0.0, 1.0 - min(cv, 1.0))
    else:
        cv, st_score = 0.0, None  # signal: not enough data

    buffer_months = (net / monthly_expense) if monthly_expense > 0 else 0.0
    r_score = 1.0 if buffer_months >= 3 else max(0.0, buffer_months / 3)

    # --- Dynamic re-weighting when stability is unmeasurable ---
    if st_score is None:
        # redistribute the 20% stability weight onto expense-ratio (12) + savings-rate (8)
        weights = {"e": 0.52, "s": 0.38, "st": 0.0, "r": 0.10}
        st_display, cv_display = 0, 0.0
    else:
        weights = {"e": 0.40, "s": 0.30, "st": 0.20, "r": 0.10}
        st_display, cv_display = round(st_score * 100, 1), cv

    score = round((weights["e"]*e_score + weights["s"]*s_score
                   + weights["st"]*(st_score or 0) + weights["r"]*r_score) * 100, 1)

    # --- Plain-English explanations ---
    if ratio < 0.5:
        e_txt = "Excellent — well under the 50% ceiling. Disposable income is healthy."
    elif ratio >= 1.0:
        e_txt = f"🚨 Spending **${expenses-income:,.0f}** more than earned. Every dollar in is going out."
    else:
        e_txt = f"Above the 50% target. Trimming **${(expenses-income*0.5):,.0f}** lands you on the ideal."

    if sr >= 0.15:
        s_txt = "Building wealth on autopilot. Consider directing surplus to investments."
    elif sr > 0:
        s_txt = f"Saving **{sr*100:.1f}%** of income. Need **${(income*0.15 - net):,.0f}** more in net to hit the 15% target."
    else:
        s_txt = f"Negative savings — drawing down by **${-net:,.0f}** over this period."

    if st_score is None:
        st_txt = (f"Need at least 2 full months of data to gauge stability. "
                  f"Currently spans **{months_span:.1f} months** — keep uploading.")
    elif cv < 0.3:
        st_txt = f"Monthly cashflow is rock-solid (CV **{cv:.2f}**). Predictable budgeting."
    elif cv < 0.7:
        st_txt = f"Some swings (CV **{cv:.2f}**). Maintain a buffer for variable months."
    else:
        st_txt = f"Highly volatile (CV **{cv:.2f}**) — irregular income or lumpy bills are stressing the budget."

    if buffer_months >= 3:
        r_txt = f"Net surplus would cover **{buffer_months:.1f} months** of spend. Solid cushion."
    elif buffer_months > 0:
        r_txt = f"Surplus covers only **{buffer_months:.1f} months** of spend. Build to 3+ months."
    else:
        r_txt = "No surplus to bank — focus on reducing the largest expense category first."

    reasoning = [
        {"name":"Expense Ratio","weight":int(weights["e"]*100),"score":round(e_score*100,1),
         "metric":f"{ratio*100:.1f}%","ideal":"< 50%","explanation":e_txt},
        {"name":"Savings Rate","weight":int(weights["s"]*100),"score":round(s_score*100,1),
         "metric":f"{sr*100:.1f}%","ideal":"≥ 15%","explanation":s_txt},
        {"name":"Cashflow Stability","weight":int(weights["st"]*100),"score":st_display,
         "metric":(f"CV {cv:.2f}" if st_score is not None else "n/a"),
         "ideal":"low variance","explanation":st_txt},
        {"name":"Savings Buffer","weight":int(weights["r"]*100),"score":round(r_score*100,1),
         "metric":f"{buffer_months:.1f} mo","ideal":"≥ 3 mo","explanation":r_txt},
    ]
    return {
        "score": score,
        "components": {r["name"]: r["score"] for r in reasoning},
        "metrics": {
            "income": income, "expenses": expenses, "net": net,
            "transfers": transfers, "unverified_income": unverified_income,
            "monthly_expense": monthly_expense, "monthly_income": monthly_income,
            "savings_rate": sr, "expense_ratio": ratio,
            "buffer_months": buffer_months, "runway_months": buffer_months,  # back-compat alias
            "monthly_count": months, "days_span": days, "months_span": months_span,
        },
        "reasoning": reasoning,
    }


def score_band(s: float) -> tuple[str, str]:
    if s < 40: return "Critical", ALERT
    if s < 70: return "Fair", GOLD
    return "Strong", SECONDARY_HI


# ============================================================
# Insights
# ============================================================
def build_insights(df: pd.DataFrame, subs: pd.DataFrame, health: dict) -> list[dict]:
    insights: list[dict] = []
    m = health["metrics"]
    cats = df[df["amount"] < 0].groupby("category")["amount"].sum().abs().sort_values(ascending=False)
    if not cats.empty and m["expenses"] > 0:
        top_cat, top_val = cats.index[0], cats.iloc[0]
        share = top_val / m["expenses"] * 100
        if share > 35:
            insights.append({"type":"warn",
                "title": f"{top_cat} dominates your spending",
                "body": f"<b>{share:.0f}%</b> of expenses (<span class='text-coral'>${top_val:,.0f}</span>) "
                        f"go to <b>{top_cat}</b>. Trimming 15% saves "
                        f"<span class='text-emerald'>${top_val*0.15:,.0f}/mo</span> "
                        f"= <b>${top_val*0.15*12:,.0f}/yr</b>."})
    if not subs.empty:
        annual = subs["Annual Cost"].sum()
        insights.append({"type":"info",
            "title": f"{len(subs)} recurring subscriptions detected",
            "body": f"Locked into <b>${annual/12:,.0f}/mo</b> "
                    f"(${annual:,.0f}/yr). Top: <b>{subs.iloc[0]['Merchant']}</b> "
                    f"(${subs.iloc[0]['Annual Cost']:,.0f}/yr)."})
    exp = df[df["amount"] < 0].copy()
    if len(exp) >= 10:
        amts = exp["amount"].abs()
        z = (amts - amts.mean()) / (amts.std() + 1e-9)
        out = exp[z > 2.5].sort_values("amount").head(3)
        if not out.empty:
            lines = "<br>".join([f"• <b>${row['amount']:,.2f}</b> · {row['payee']} · {row['date']:%b %d}"
                                 for _, row in out.iterrows()])
            insights.append({"type":"info",
                "title": f"{len(out)} unusually large transactions",
                "body": f"These are 2.5+ standard deviations above your average:<br>{lines}"})
    if m["income"] > 0:
        sr = m["savings_rate"]
        if sr < 0:
            insights.append({"type":"warn",
                "title": "Spending exceeds income",
                "body": f"You spent <b>${-m['net']:,.0f} more</b> than you earned. "
                        "Trim discretionary categories first (Dining, Subscriptions, Shopping)."})
        elif sr >= 0.20:
            insights.append({"type":"good",
                "title": f"Strong savings rate ({sr*100:.0f}%)",
                "body": f"Banking <b>${m['net']:,.0f}</b>. Auto-invest into a low-cost index fund "
                        "or max tax-advantaged accounts."})
    dow = exp.groupby(exp["date"].dt.day_name())["amount"].sum().abs()
    if not dow.empty and len(dow) > 3:
        worst = dow.idxmax()
        if dow[worst] > dow.mean() * 1.4:
            insights.append({"type":"info",
                "title": f"{worst}s are your highest-spend day",
                "body": f"You spend <b>${dow[worst]:,.0f}</b> on {worst}s — "
                        f"{(dow[worst]/dow.mean()-1)*100:.0f}% above weekly average."})
    if health["score"] >= 70:
        insights.append({"type":"good",
            "title": "Financially healthy",
            "body": f"Score <b>{health['score']}/100</b>. Time to play offense — "
                    "increase investments and tax optimization."})
    return insights


# ============================================================
# AI Coach
# ============================================================
OLLAMA_URL   = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3:latest")
# Headers required for free-tier ngrok tunnels (skip the browser interstitial)
_OLLAMA_HEADERS = {
    "ngrok-skip-browser-warning": "true",
    "User-Agent": "IronStarLedger/1.0",
}


def ai_coach_narrative(df: pd.DataFrame, subs: pd.DataFrame, health: dict) -> str:
    m = health["metrics"]
    cats = df[df["amount"] < 0].groupby("category")["amount"].sum().abs().sort_values(ascending=False).head(5)
    summary = {
        "score": health["score"], "income": round(m["income"],2),
        "expenses": round(m["expenses"],2), "net": round(m["net"],2),
        "savings_rate_pct": round(m["savings_rate"]*100,1),
        "expense_ratio_pct": round(m["expense_ratio"]*100,1),
        "runway_months": round(m["runway_months"],1),
        "top_categories": {k: round(float(v),2) for k,v in cats.to_dict().items()},
        "subscription_monthly": round(float(subs["Annual Cost"].sum())/12,2) if not subs.empty else 0,
    }
    prompt = (
        "You are a CFP-level money coach. Given this JSON, write a punchy markdown coaching memo "
        "(≤350 words) with sections: **Where you stand**, **Top 3 wins this month**, **Risks**, "
        f"**90-day game plan**. Use concrete dollar figures.\n\nData: {summary}"
    )
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0.4, "num_predict": 900}},
            headers=_OLLAMA_HEADERS,
            timeout=int(os.environ.get("OLLAMA_TIMEOUT", "300")),
        )
        r.raise_for_status()
        text = r.json().get("response", "").strip()
        if text:
            return text
        return _fallback_narrative(summary, "Empty Ollama response")
    except Exception as e:
        return _fallback_narrative(summary, f"Ollama unreachable at {OLLAMA_URL} — {e}")


def _fallback_narrative(s: dict, err: Optional[str] = None) -> str:
    band, _ = score_band(s["score"])
    sr, er = s["savings_rate_pct"], s["expense_ratio_pct"]
    top = list(s["top_categories"].items())[:3]
    note = f"\n\n_AI coach offline — using rule-based memo{f' ({err})' if err else ''}. Set `OLLAMA_URL` (default `http://localhost:11434`) and `OLLAMA_MODEL` (default `llama3:latest`) to enable live coaching._"
    lines = [
        f"### {band} · Score {s['score']}/100", "",
        "**Where you stand**",
        f"- Income: **${s['income']:,.0f}** · Expenses: **${s['expenses']:,.0f}** · Net: **${s['net']:,.0f}**",
        f"- Savings rate: **{sr:.1f}%** (target ≥15%) · Expense ratio: **{er:.1f}%** (target <50%)",
        f"- Runway: **{s['runway_months']:.1f} months** · Subs: **${s['subscription_monthly']:,.0f}/mo**", "",
        "**Top 3 wins this month**",
    ]
    for cat, val in top:
        lines.append(f"- Trim **{cat}** by 15% → save **${val*0.15:,.0f}/mo** (**${val*0.15*12:,.0f}/yr**)")
    if s["subscription_monthly"] > 50:
        lines.append(f"- Audit subscriptions — cancelling 25% saves **${s['subscription_monthly']*0.25*12:,.0f}/yr**")
    lines += ["", "**Risks**"]
    risks_added = False
    if sr < 10: lines.append("- ⚠️ Savings rate <10% — vulnerable to any income shock."); risks_added=True
    if s["runway_months"] < 3: lines.append("- ⚠️ Emergency fund <3 months — single bill can destabilize."); risks_added=True
    if er > 90: lines.append("- 🚨 Spending nearly all you earn. Lifestyle creep is the #1 killer."); risks_added=True
    if not risks_added: lines.append("- No critical risks — focus on optimization.")
    lines += ["", "**90-day game plan**",
        "- **Days 1–14:** List every recurring charge. Cancel anything unused 30+ days.",
        f"- **Days 15–45:** Auto-transfer **{max(10, int(sr+5))}%** of every paycheck to a HYSA.",
        "- **Days 46–90:** Move excess into Roth IRA / 401k match / HSA.", note]
    return "\n".join(lines)


# ============================================================
# Demo data
# ============================================================
def load_demo() -> pd.DataFrame:
    rng = pd.date_range(end=datetime.today(), periods=180, freq="D")
    np.random.seed(7)
    rows = []
    payees = ["Whole Foods","Trader Joe's","Amazon","Starbucks","Doordash","Uber",
              "Shell Gas","Costco","Target","Chipotle","Best Buy","CVS Pharmacy"]
    for d in rng:
        if d.day in (1, 15):
            rows.append({"date":d,"amount":3400.0,"payee":"Acme Corp Payroll","source":"demo"})
        if d.day == 3:
            rows.append({"date":d,"amount":-1850.0,"payee":"Property Management Rent","source":"demo"})
        if d.day == 5:
            rows.append({"date":d,"amount":-89.99,"payee":"AT&T Wireless","source":"demo"})
            rows.append({"date":d,"amount":-15.49,"payee":"Netflix","source":"demo"})
            rows.append({"date":d,"amount":-11.99,"payee":"Spotify","source":"demo"})
            rows.append({"date":d,"amount":-19.99,"payee":"Adobe Creative","source":"demo"})
        if d.day == 12:
            rows.append({"date":d,"amount":-42.00,"payee":"Planet Fitness Gym","source":"demo"})
        for _ in range(np.random.poisson(2)):
            p = payees[np.random.randint(len(payees))]
            amt = -float(np.round(np.random.uniform(8, 140), 2))
            rows.append({"date":d,"amount":amt,"payee":p,"source":"demo"})
    return pd.DataFrame(rows)


# ============================================================
# SIDEBAR
# ============================================================
if "raw_files" not in st.session_state:
    st.session_state["raw_files"] = {}   # filename -> raw_df (for tabular formats)
if "remaps" not in st.session_state:
    st.session_state["remaps"] = {}      # filename -> parsed_df

with st.sidebar:
    st.markdown(
        f"<div class='brand-logo'>"
        f"<div class='icon'>🪐</div>"
        f"<div><div class='name'>Iron Star Ledger</div>"
        f"<div class='tag'>Powered by PLEX Automation</div></div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("<h4>Upload statements</h4>", unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Drop files",
        type=["csv", "xlsx", "xls", "ofx", "qbo", "qfx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="CSV, Excel (.xlsx/.xls), OFX, or QFX/QBO",
    )
    use_demo = st.toggle("Use demo data", value=not uploaded)

    st.markdown(
        f"<div style='margin-top:1rem;padding:.95rem;border:1px solid rgba(124,58,237,.30);"
        f"border-radius:12px;background:rgba(17,21,43,.6);backdrop-filter:blur(10px);'>"
        f"<div style='color:{COSMIC_CYAN};font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;font-weight:700;font-family:JetBrains Mono,monospace;'>◆ Telemetry</div>"
        f"<div style='font-size:.85rem;color:{STELLAR_WHT};margin-top:.45rem;line-height:1.75;'>"
        "✓ CSV (auto-detect delimiter)<br>"
        "✓ Excel (.xlsx, .xls)<br>"
        "✓ OFX, QFX, QBO</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='pro-tile' style='margin-top:1.25rem;'>"
        "<div style='font-weight:700;font-size:.78rem;"
        "letter-spacing:.14em;text-transform:uppercase;font-family:Orbitron,sans-serif;'>"
        "★ Iron Star Pro</div>"
        "<div style='margin:.55rem 0;font-size:.88rem;line-height:1.55;'>"
        "Live AI coaching · Smart alerts · Multi-account sync · PDF reports</div>"
        "<div style='font-size:1.85rem;font-weight:800;letter-spacing:-.01em;font-family:Orbitron,sans-serif;'>"
        "$9<span style='font-size:.78rem;font-weight:500;opacity:.85;'> /mo</span></div>"
        "<a href='#' style='display:block;margin-top:.75rem;text-align:center;padding:.65rem;"
        "background:rgba(5,6,15,.55);border:1px solid rgba(255,255,255,.35);"
        "border-radius:10px;text-decoration:none;"
        "font-weight:700;font-size:.88rem;letter-spacing:.06em;text-transform:uppercase;'>Engage Warp →</a>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<p style='color:{NEBULA_DIM};font-size:.72rem;text-align:center;"
                "margin-top:1.25rem;letter-spacing:.08em;font-family:JetBrains Mono,monospace;'>"
                "🔒 In-memory · Never stored on servers</p>", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================
st.markdown(
    "<h1>★ Iron Star Ledger</h1>"
    f"<p style='color:{NEBULA_DIM};font-size:1.05rem;margin:.25rem 0 1.5rem 0;font-weight:500;"
    "letter-spacing:.04em;font-family:JetBrains Mono,monospace;'>"
    "Charting your financial galaxy — real cashflow, AI navigator, plasma-grade insights.</p>",
    unsafe_allow_html=True,
)

# ============================================================
# Load + parse
# ============================================================
parsed_frames: list[pd.DataFrame] = []
needs_remap: list[tuple[str, pd.DataFrame, dict, str]] = []  # (name, raw_df, meta, error)

if uploaded:
    for f in uploaded:
        # Use cached remap if user previously fixed this file
        cache_key = f"{f.name}::{f.size}"
        if cache_key in st.session_state["remaps"]:
            parsed_frames.append(st.session_state["remaps"][cache_key])
            continue
        try:
            parsed, meta, raw = parse_any(f)
            parsed_frames.append(parsed)
            st.session_state["raw_files"][cache_key] = (raw, meta)
        except Exception as e:
            # If tabular, try to capture raw for remap UI
            try:
                if f.name.lower().endswith(".csv"):
                    f.seek(0)
                    raw_bytes = f.read()
                    text = None
                    for enc in ("utf-8","utf-8-sig","latin-1","cp1252"):
                        try: text = raw_bytes.decode(enc); break
                        except UnicodeDecodeError: continue
                    if text:
                        raw = _read_csv_smart(text, f.name)
                        needs_remap.append((cache_key, raw, {}, str(e)))
                        continue
                elif f.name.lower().endswith((".xlsx",".xls")):
                    f.seek(0)
                    raw = pd.read_excel(f, engine="openpyxl" if f.name.lower().endswith("xlsx") else None)
                    needs_remap.append((cache_key, raw, {}, str(e)))
                    continue
            except Exception:
                pass
            st.error(f"❌ **{f.name}** — {e}")

if use_demo and not parsed_frames and not needs_remap:
    parsed_frames.append(load_demo())

# ----- Manual column-mapping UI -----
if needs_remap:
    st.markdown("### 🛠 Column mapping needed")
    st.caption("We couldn't auto-detect the columns. Pick them manually below — we'll remember it for this session.")
    for cache_key, raw, _, err in needs_remap:
        name = cache_key.split("::")[0]
        with st.expander(f"⚙️ Map columns for {name}", expanded=True):
            st.write(f"**Issue:** {err}")
            st.write("**File preview (first 5 rows):**")
            st.dataframe(raw.head(), use_container_width=True, hide_index=True)
            cols = ["—"] + list(raw.columns.astype(str))
            c1, c2, c3 = st.columns(3)
            with c1:
                date_pick = st.selectbox("Date column", cols, key=f"d_{cache_key}")
                payee_pick = st.selectbox("Description / Payee", cols, key=f"p_{cache_key}")
            with c2:
                amt_pick = st.selectbox("Amount column (signed)", cols, key=f"a_{cache_key}")
            with c3:
                deb_pick = st.selectbox("Debit column (optional)", cols, key=f"db_{cache_key}")
                cre_pick = st.selectbox("Credit column (optional)", cols, key=f"cr_{cache_key}")
            if st.button(f"✓ Apply mapping for {name}", key=f"apply_{cache_key}"):
                try:
                    remapped = remap_tabular(
                        raw, name,
                        date_col=None if date_pick == "—" else date_pick,
                        payee_col=None if payee_pick == "—" else payee_pick,
                        amount_col=None if amt_pick == "—" else amt_pick,
                        debit_col=None if deb_pick == "—" else deb_pick,
                        credit_col=None if cre_pick == "—" else cre_pick,
                    )
                    if remapped.empty:
                        st.error("Mapping produced 0 valid rows — double check the columns.")
                    else:
                        st.session_state["remaps"][cache_key] = remapped
                        st.success(f"✓ Mapped {len(remapped)} transactions. Reloading…")
                        st.rerun()
                except Exception as e:
                    st.error(f"Mapping failed: {e}")
    if not parsed_frames:
        st.stop()

if not parsed_frames:
    st.markdown(
        f"<div style='text-align:center;padding:4rem 2rem;border:1.5px dashed rgba(34,211,238,.5);"
        f"border-radius:18px;background:linear-gradient(135deg,rgba(17,21,43,.7),rgba(11,14,32,.5));"
        f"backdrop-filter:blur(14px);box-shadow:0 6px 28px rgba(5,6,15,.6),0 0 32px rgba(124,58,237,.20);'>"
        f"<div style='font-size:3.6rem;filter:drop-shadow(0 0 18px rgba(34,211,238,.5));'>🛰️</div>"
        f"<h3 style='color:{STELLAR_WHT};margin:.85rem 0;font-family:Orbitron,sans-serif;'>Awaiting transmission…</h3>"
        f"<p style='color:{NEBULA_DIM};max-width:520px;margin:0 auto;font-size:.95rem;'>"
        "Beam up a <b style='color:" + COSMIC_CYAN + ";'>CSV</b>, <b style='color:" + COSMIC_CYAN + ";'>Excel</b>, "
        "<b style='color:" + COSMIC_CYAN + ";'>OFX</b>, or <b style='color:" + COSMIC_CYAN + ";'>QFX</b> file via the sidebar — "
        "or activate demo data to launch the bridge view.</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="footer">★ Iron Star Ledger · Powered by <a href="#">PLEX Automation</a></div>', unsafe_allow_html=True)
    st.stop()

raw_df = pd.concat(parsed_frames, ignore_index=True).sort_values("date").reset_index(drop=True)
df_all = enrich(raw_df)

# Quick stats banner about parsing success
st.markdown(
    f"<div style='display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:1rem;'>"
    f"<span class='stat-pill pill-good'>✓ {len(df_all):,} transactions loaded</span>"
    f"<span class='stat-pill'>{df_all['source'].nunique()} source(s)</span>"
    f"<span class='stat-pill'>{df_all['date'].min():%b %Y} → {df_all['date'].max():%b %Y}</span>"
    f"<span class='stat-pill'>{df_all['category'].nunique()} categories</span>"
    "</div>",
    unsafe_allow_html=True,
)

# ============================================================
# FILTER BAR
# ============================================================
fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])
min_d, max_d = df_all["date"].min().date(), df_all["date"].max().date()
with fc1:
    date_range = st.date_input("📅 Date range", value=(min_d, max_d),
                               min_value=min_d, max_value=max_d)
with fc2:
    sources = st.multiselect("🏦 Source", sorted(df_all["source"].unique()),
                             default=sorted(df_all["source"].unique()))
with fc3:
    cats_avail = sorted(df_all["category"].unique())
    selected_cats = st.multiselect("🏷️ Category", cats_avail, default=cats_avail)
with fc4:
    search = st.text_input("🔎 Search payee", "", placeholder="Amazon, Starbucks…")

start_d = pd.to_datetime(date_range[0]) if isinstance(date_range, tuple) else pd.to_datetime(date_range)
end_d = pd.to_datetime(date_range[1]) if isinstance(date_range, tuple) and len(date_range) > 1 else pd.to_datetime(max_d)

df = df_all[
    (df_all["date"] >= start_d) & (df_all["date"] <= end_d + timedelta(days=1)) &
    (df_all["source"].isin(sources)) & (df_all["category"].isin(selected_cats))
]
if search.strip():
    df = df[df["payee"].str.contains(search.strip(), case=False, na=False)]

if df.empty:
    st.warning("No transactions match current filters.")
    st.stop()

health = compute_health(df)
subs = detect_subscriptions(df)
metrics = health["metrics"]
band, band_color = score_band(health["score"])

# ============================================================
# TOP METRICS
# ============================================================
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Income", f"${metrics['income']:,.0f}")
m2.metric("Expenses", f"${metrics['expenses']:,.0f}")
m3.metric("Net", f"${metrics['net']:,.0f}",
          delta=f"{metrics['savings_rate']*100:.1f}% saved")
m4.metric("Subs / month", f"${(subs['Annual Cost'].sum()/12) if not subs.empty else 0:,.0f}")
m5.metric("Health Score", f"{health['score']}", delta=band)

st.markdown("---")

# ============================================================
# TABS
# ============================================================
tab_overview, tab_spend, tab_subs, tab_insights, tab_coach, tab_data = st.tabs(
    ["Overview", "Spending", "Subscriptions", "Insights", "AI Coach", "Transactions"]
)

# ---------- OVERVIEW ----------
with tab_overview:
    c1, c2 = st.columns([2, 1])
    with c1:
        # Auto-bucket: monthly if >=2 months, weekly otherwise, daily if <14 days
        days_span = (df["date"].max() - df["date"].min()).days + 1
        if days_span < 14:
            freq, freq_label, fmt = "D", "Daily", "%b %d"
        elif days_span < 70:
            freq, freq_label, fmt = "W", "Weekly", "Wk %b %d"
        else:
            freq, freq_label, fmt = "ME", "Monthly", "%b %Y"
        st.markdown(f"<h4>{freq_label} Cashflow</h4>", unsafe_allow_html=True)

        # Exclude transfers from cashflow (they're noise, not real income/spend)
        cashflow_df = df[~df["category"].isin({"Transfers"})].copy()
        bucket = (cashflow_df.set_index("date").resample(freq)["amount"]
                  .agg(income=lambda s: s[s>0].sum(), expenses=lambda s: -s[s<0].sum())
                  .reset_index())
        bucket["net"] = bucket["income"] - bucket["expenses"]
        bucket["label"] = bucket["date"].dt.strftime(fmt)

        fig = go.Figure()
        fig.add_bar(name="Income", x=bucket["label"], y=bucket["income"],
                    marker=dict(color=SECONDARY,
                                line=dict(color=PRIMARY, width=0.5)),
                    hovertemplate="<b>%{x}</b><br>Income: <b>$%{y:,.0f}</b><extra></extra>")
        fig.add_bar(name="Expenses", x=bucket["label"], y=bucket["expenses"],
                    marker=dict(color=ALERT, opacity=.85,
                                line=dict(color="#B91C1C", width=0.5)),
                    hovertemplate="<b>%{x}</b><br>Expenses: <b>$%{y:,.0f}</b><extra></extra>")
        fig.add_scatter(name="Net", x=bucket["label"], y=bucket["net"],
                        mode="lines+markers",
                        line=dict(color=PRIMARY, width=3, shape="spline", smoothing=.6),
                        marker=dict(size=11, color=PRIMARY, symbol="circle",
                                    line=dict(color=NEUTRAL, width=2)),
                        hovertemplate="<b>%{x}</b><br>Net: <b>$%{y:,.0f}</b><extra></extra>")
        fig.update_layout(barmode="group", height=400,
                          legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"),
                          hovermode="x unified",
                          margin=dict(t=50, b=30, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown("<h4>Health Score</h4>", unsafe_allow_html=True)
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health["score"],
            number={"font":{"size":52,"color":band_color,"family":"Inter"},
                    "suffix":f"<span style='font-size:14px;color:{TXT_MUTED}'>/100</span>"},
            gauge={
                "axis":{"range":[0,100],"tickcolor":TXT_MUTED,
                        "tickfont":{"color":TXT_DIM,"size":10},
                        "tickwidth":1,"ticklen":4},
                "bar":{"color":band_color, "thickness":0.32,
                       "line":{"color":NEUTRAL,"width":2}},
                "bgcolor":SURFACE, "borderwidth":0,
                "steps":[
                    {"range":[0,40],"color":"rgba(239,68,68,0.18)"},
                    {"range":[40,70],"color":"rgba(184,148,90,0.20)"},
                    {"range":[70,100],"color":"rgba(31,111,84,0.22)"},
                ],
                "threshold":{"line":{"color":PRIMARY,"width":4},"thickness":.78,"value":health["score"]},
            },
        ))
        fig.update_layout(height=290, margin=dict(t=20,b=10,l=20,r=20),
                          paper_bgcolor=CARD_BG)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"<div style='text-align:center;font-weight:700;color:{band_color};"
            f"font-size:1.05rem;letter-spacing:.06em;text-transform:uppercase;margin-top:-.5rem;'>{band}</div>",
            unsafe_allow_html=True,
        )

    # Headline numbers + transparency about excluded items
    if metrics.get("transfers", 0) > 0 or metrics.get("unverified_income", 0) > 0:
        notes = []
        if metrics.get("transfers", 0) > 0:
            notes.append(f"<b>${metrics['transfers']:,.0f}</b> in transfers excluded")
        if metrics.get("unverified_income", 0) > 0:
            notes.append(f"<b>${metrics['unverified_income']:,.0f}</b> in unverified income held aside")
        st.markdown(
            f"<div style='margin:.25rem 0 1rem 0;padding:.6rem .9rem;background:{SURFACE};"
            f"border-left:3px solid {SECONDARY};border-radius:8px;font-size:.85rem;color:{PRIMARY};'>"
            f"📋 <b>For accuracy:</b> " + " · ".join(notes) +
            ". These don't count toward the health score." + "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<h4>Score breakdown</h4>", unsafe_allow_html=True)
    rcols = st.columns(4)
    for i, comp in enumerate(health["reasoning"]):
        with rcols[i]:
            cc = SECONDARY_HI if comp["score"] >= 70 else GOLD if comp["score"] >= 40 else ALERT
            st.markdown(
                f"""<div class='insight-card' style='border-left-color:{cc};'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <span style='font-weight:700;font-size:.92rem;color:{PRIMARY};'>{comp['name']}</span>
                        <span style='color:{TXT_MUTED};font-size:.72rem;font-family:JetBrains Mono;font-weight:600;'>{comp['weight']}%</span>
                    </div>
                    <div style='font-size:1.85rem;font-weight:800;color:{cc};margin:.4rem 0;letter-spacing:-.02em;'>{comp['score']}<span style='font-size:.85rem;color:{TXT_MUTED};font-weight:500;'>/100</span></div>
                    <div style='color:{TXT_DIM};font-family:JetBrains Mono;font-size:.74rem;letter-spacing:.02em;'>
                        {comp['metric']} · ideal {comp['ideal']}
                    </div>
                    <div style='margin-top:.6rem;font-size:.86rem;line-height:1.55;color:{TXT_MAIN};'>{comp['explanation']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    # Running balance chart — gives a clear "where am I trending?" picture
    st.markdown("<h4>Cumulative cash position</h4>", unsafe_allow_html=True)
    bal = df.sort_values("date")[["date", "running_balance"]].copy()
    fig = go.Figure()
    fig.add_scatter(x=bal["date"], y=bal["running_balance"], mode="lines",
                    fill="tozeroy",
                    line=dict(color=PRIMARY, width=2.5, shape="spline", smoothing=.4),
                    fillcolor="rgba(31,111,84,0.18)",
                    hovertemplate="<b>%{x|%b %d, %Y}</b><br>Position: <b>$%{y:,.0f}</b><extra></extra>")
    fig.add_hline(y=0, line=dict(color=ALERT, width=1, dash="dot"),
                  annotation_text="break-even", annotation_position="bottom right",
                  annotation_font=dict(color=ALERT, size=10))
    fig.update_layout(height=280, margin=dict(t=15,b=15),
                      hovermode="x unified",
                      xaxis=dict(rangeslider=dict(visible=True, thickness=.04, bgcolor=SURFACE)))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------- SPENDING ----------
with tab_spend:
    exp = df[(df["amount"] < 0) & (~df["category"].isin(NON_SPEND_CATEGORIES))].copy()
    if exp.empty:
        st.info("No real expenses in current filter (transfers and income are excluded).")
    else:
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("<h4>Spending by category</h4>", unsafe_allow_html=True)
            cat_sum = exp.groupby("category")["abs_amount"].sum().sort_values(ascending=False).reset_index()
            cat_sum["pct"] = cat_sum["abs_amount"] / cat_sum["abs_amount"].sum() * 100
            fig = go.Figure(go.Pie(
                labels=cat_sum["category"], values=cat_sum["abs_amount"],
                hole=0.62, sort=False,
                marker=dict(colors=CHART_PALETTE,
                            line=dict(color=CARD_BG, width=2)),
                textposition="outside", textinfo="label+percent",
                textfont=dict(family="Inter", size=11, color=PRIMARY),
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
                pull=[0.04 if i == 0 else 0 for i in range(len(cat_sum))],
            ))
            # Center total
            fig.update_layout(
                height=420, showlegend=False, margin=dict(t=10,b=10),
                annotations=[dict(text=f"<b>${cat_sum['abs_amount'].sum():,.0f}</b><br>"
                                       f"<span style='font-size:.7rem;color:{TXT_DIM}'>total spend</span>",
                                  x=0.5, y=0.5, font=dict(size=18, color=PRIMARY, family="Inter"),
                                  showarrow=False)],
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with sc2:
            st.markdown("<h4>Top merchants</h4>", unsafe_allow_html=True)
            top_m = exp.groupby("payee")["abs_amount"].sum().nlargest(12).sort_values().reset_index()
            top_m["pct"] = top_m["abs_amount"] / exp["abs_amount"].sum() * 100
            fig = go.Figure(go.Bar(
                x=top_m["abs_amount"], y=top_m["payee"], orientation="h",
                marker=dict(
                    color=top_m["abs_amount"],
                    colorscale=[[0, SURFACE_HI], [0.5, SECONDARY], [1, PRIMARY]],
                    line=dict(color=PRIMARY, width=0.5),
                ),
                customdata=top_m["pct"],
                hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<br>%{customdata:.1f}% of spend<extra></extra>",
                text=[f"${v:,.0f}" for v in top_m["abs_amount"]],
                textposition="outside", textfont=dict(color=PRIMARY, size=11, family="Inter"),
            ))
            fig.update_layout(height=420, xaxis_title=None, yaxis_title=None,
                              margin=dict(t=10,b=10,l=10,r=60))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown("<h4>Drill-down: category → merchant</h4>", unsafe_allow_html=True)
        tree = exp.groupby(["category","payee"])["abs_amount"].sum().reset_index()
        fig = px.treemap(tree, path=["category","payee"], values="abs_amount",
                         color="abs_amount",
                         color_continuous_scale=[[0,SURFACE],[.5,SECONDARY],[1,PRIMARY]])
        fig.update_traces(marker=dict(line=dict(color=NEUTRAL, width=2.5), cornerradius=4),
                          hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percentParent} of category<extra></extra>",
                          textfont=dict(family="Inter", size=12, color=NEUTRAL))
        fig.update_layout(height=480, margin=dict(t=10,b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown("<h4>Inspect a category</h4>", unsafe_allow_html=True)
        drill_cat = st.selectbox("Category", cat_sum["category"].tolist(),
                                 label_visibility="collapsed")
        drill_df = exp[exp["category"] == drill_cat].sort_values("date", ascending=False)
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Total spent", f"${drill_df['abs_amount'].sum():,.2f}")
        d2.metric("Transactions", f"{len(drill_df):,}")
        d3.metric("Avg per txn", f"${drill_df['abs_amount'].mean():,.2f}")
        d4.metric("Largest", f"${drill_df['abs_amount'].max():,.2f}")

        # Auto-bucket trend
        d_span = (drill_df["date"].max() - drill_df["date"].min()).days + 1
        t_freq, t_label = ("D", "Daily") if d_span < 21 else ("W", "Weekly")
        trend = drill_df.set_index("date").resample(t_freq)["abs_amount"].sum().reset_index()
        fig = go.Figure()
        fig.add_scatter(x=trend["date"], y=trend["abs_amount"], mode="lines+markers",
                        fill="tozeroy",
                        line=dict(color=SECONDARY, width=2.5, shape="spline", smoothing=.5),
                        marker=dict(size=8, color=PRIMARY, line=dict(color=NEUTRAL, width=1.5)),
                        fillcolor="rgba(31,111,84,0.20)",
                        hovertemplate="<b>%{x|%b %d, %Y}</b><br>$%{y:,.0f}<extra></extra>")
        fig.update_layout(height=280, title=f"{t_label} spend · {drill_cat}",
                          margin=dict(t=45,b=10), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.dataframe(
            drill_df[["date","payee","amount","source"]].rename(
                columns={"date":"Date","payee":"Payee","amount":"Amount","source":"Source"}),
            hide_index=True, use_container_width=True,
            column_config={
                "Date": st.column_config.DateColumn(format="YYYY-MM-DD"),
                "Amount": st.column_config.NumberColumn(format="$%.2f"),
            },
        )

# ---------- SUBSCRIPTIONS ----------
with tab_subs:
    if subs.empty:
        st.info("No recurring charges detected. Try a longer date range or upload more months.")
    else:
        annual = subs["Annual Cost"].sum()
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Subscriptions", len(subs))
        s2.metric("Per month", f"${annual/12:,.0f}")
        s3.metric("Per year", f"${annual:,.0f}")
        s4.metric("10-year cost", f"${annual*10:,.0f}")

        st.markdown("<h4>Recurring charges</h4>", unsafe_allow_html=True)
        fig = go.Figure(go.Bar(
            x=subs["Annual Cost"], y=subs["Merchant"], orientation="h",
            marker=dict(
                color=subs["Annual Cost"],
                colorscale=[[0, SURFACE_HI], [.5, SECONDARY], [1, PRIMARY]],
                line=dict(color=PRIMARY, width=0.5),
            ),
            text=[f"${v:,.0f}/yr · {c}" for v, c in zip(subs["Annual Cost"], subs["Cadence"])],
            textposition="outside", textfont=dict(color=PRIMARY, size=11, family="Inter"),
            customdata=np.stack([subs["Cadence"], subs["Charges"], subs["Avg Charge"]], axis=-1),
            hovertemplate=("<b>%{y}</b><br>"
                           "Annual: <b>$%{x:,.0f}</b><br>"
                           "Cadence: %{customdata[0]}<br>"
                           "Charges seen: %{customdata[1]}<br>"
                           "Avg charge: $%{customdata[2]:,.2f}<extra></extra>"),
        ))
        fig.update_layout(height=max(300, len(subs)*38),
                          xaxis_title=None, yaxis_title=None,
                          yaxis=dict(autorange="reversed"),
                          margin=dict(t=15, b=15, l=10, r=80))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.dataframe(
            subs.rename(columns={"Detected By": "Detection"}),
            hide_index=True, use_container_width=True,
            column_config={
                "Avg Charge": st.column_config.NumberColumn(format="$%.2f"),
                "Annual Cost": st.column_config.NumberColumn(format="$%.2f"),
                "Last Charged": st.column_config.DateColumn(format="YYYY-MM-DD"),
            },
        )

        st.markdown("<h4>Cancellation simulator</h4>", unsafe_allow_html=True)
        to_cancel = st.multiselect("Select subscriptions to cancel:",
                                   subs["Merchant"].tolist(),
                                   label_visibility="collapsed")
        if to_cancel:
            saved = subs[subs["Merchant"].isin(to_cancel)]["Annual Cost"].sum()
            st.markdown(
                f"<div class='insight-card good'>"
                f"<h4>Projected savings</h4>"
                f"<div style='font-size:1.05rem;'>"
                f"<span class='text-emerald'>${saved/12:,.2f}/mo</span> · "
                f"<span class='text-blue'>${saved:,.2f}/yr</span> · "
                f"<b>${saved*10:,.0f}</b> over 10 years</div></div>",
                unsafe_allow_html=True,
            )

# ---------- INSIGHTS ----------
with tab_insights:
    insights = build_insights(df, subs, health)
    if not insights:
        st.info("No notable insights yet — upload more data for richer analysis.")
    for ins in insights:
        st.markdown(
            f"<div class='insight-card {ins['type']}'>"
            f"<h4>{ins['title']}</h4><div>{ins['body']}</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<h4>Spending heatmap · day-of-week × week</h4>", unsafe_allow_html=True)
    exp = df[(df["amount"] < 0) & (~df["category"].isin(NON_SPEND_CATEGORIES))].copy()
    if not exp.empty:
        exp["dow"] = exp["date"].dt.day_name()
        exp["week"] = exp["date"].dt.to_period("W").dt.start_time
        heat = exp.pivot_table(index="dow", columns="week",
                               values="abs_amount", aggfunc="sum", fill_value=0)
        order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        heat = heat.reindex([d for d in order if d in heat.index])
        fig = px.imshow(heat, aspect="auto",
                        color_continuous_scale=[[0,NEUTRAL],[.3,SURFACE],[.7,SECONDARY],[1,PRIMARY]],
                        labels=dict(color="$ spent"))
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Week of %{x|%b %d}<br>$%{z:,.0f}<extra></extra>",
                          xgap=2, ygap=2)
        fig.update_layout(height=340, margin=dict(t=10,b=10),
                          coloraxis_colorbar=dict(thickness=12, len=.7,
                                                   tickfont=dict(color=TXT_DIM, size=10)))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------- AI COACH ----------
with tab_coach:
    # Probe Ollama health quickly
    ollama_ok = False
    ollama_err = ""
    try:
        _r = requests.get(f"{OLLAMA_URL}/api/tags", headers=_OLLAMA_HEADERS, timeout=3)
        ollama_ok = _r.status_code == 200
    except Exception as _e:
        ollama_err = str(_e)
    if ollama_ok:
        st.markdown(
            f"<div class='insight-card success'>"
            f"<h4>🟢 Ollama connected</h4>"
            f"Model: <code>{OLLAMA_MODEL}</code> · Endpoint: <code>{OLLAMA_URL}</code>"
            "</div>", unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='insight-card info'>"
            f"<h4>Ollama not reachable</h4>"
            f"Tried <code>{OLLAMA_URL}</code>. Set <code>OLLAMA_URL</code> + <code>OLLAMA_MODEL</code> "
            f"in Railway → Variables (e.g. <code>http://host.docker.internal:11434</code> for local, "
            f"or your tunneled ngrok URL). Showing rule-based memo below."
            f"{f'<br><small>{ollama_err}</small>' if ollama_err else ''}"
            "</div>", unsafe_allow_html=True,
        )
    if st.button("Generate coaching memo", type="primary"):
        with st.spinner("Analyzing your finances…"):
            st.session_state["coach_memo"] = ai_coach_narrative(df, subs, health)
    memo = st.session_state.get("coach_memo") or ai_coach_narrative(df, subs, health)
    st.markdown(f"<div class='insight-card' style='font-size:.95rem;'>{memo}</div>",
                unsafe_allow_html=True)

# ---------- TRANSACTIONS ----------
with tab_data:
    st.markdown(f"<h4>{len(df):,} transactions</h4>", unsafe_allow_html=True)
    # Compute running balance over the *filtered* set (chronological), then display newest first
    show = df.sort_values("date").copy()
    show["Running Balance"] = show["amount"].cumsum()
    show = show.sort_values("date", ascending=False)[
        ["date","payee","category","amount","source","Running Balance"]
    ].rename(columns={"date":"Date","payee":"Payee","category":"Category",
                      "amount":"Amount","source":"Source"})
    st.dataframe(
        show, hide_index=True, use_container_width=True, height=560,
        column_config={
            "Date": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Payee": st.column_config.TextColumn(width="large"),
            "Category": st.column_config.TextColumn(width="medium"),
            "Amount": st.column_config.NumberColumn(format="$%.2f"),
            "Running Balance": st.column_config.NumberColumn(format="$%.2f"),
        },
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Export filtered CSV", csv_bytes,
        file_name=f"clearledger_{datetime.today():%Y%m%d}.csv",
        mime="text/csv",
    )

# ============================================================
# Optional GHL webhook
# ============================================================
ghl_url = os.environ.get("GHL_WEBHOOK_URL")
if ghl_url:
    try:
        import requests
        requests.post(ghl_url, json={
            "score": health["score"], "income": metrics["income"],
            "expenses": metrics["expenses"], "net": metrics["net"],
            "savings_rate": metrics["savings_rate"],
        }, timeout=3)
    except Exception:
        pass

# ============================================================
# FOOTER
# ============================================================
st.markdown(
    "<div class='footer'>★ Iron Star Ledger · Powered by <a href='#'>PLEX Automation</a> · "
    "<a href='https://github.com/ThaGuff/ClearLedgerAI'>GitHub</a> · "
    "Bank-grade in-memory processing</div>",
    unsafe_allow_html=True,
)
