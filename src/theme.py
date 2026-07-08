"""Visual theme + small reusable UI helpers.

The color theme itself lives in .streamlit/config.toml (Streamlit's native
theming). This module adds the extra CSS needed for card/metric styling
that Streamlit doesn't expose through config alone, plus tiny helpers so
views.py doesn't repeat raw `st.markdown(..., unsafe_allow_html=True)`
calls everywhere.
"""

from __future__ import annotations

import streamlit as st

from src.config import BRAND


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
          .block-container {{ padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1320px; }}
          h1, h2, h3 {{ letter-spacing: -0.01em; }}

          .eyebrow {{
            font-family: 'IBM Plex Mono', 'Courier New', monospace;
            font-size: 0.75rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: {BRAND['gold']};
            display: block;
            margin-bottom: 6px;
          }}

          .muted {{ opacity: 0.72; font-size: 0.95rem; }}

          div[data-testid="stMetric"] {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 16px 18px;
            border-radius: 14px;
          }}
          div[data-testid="stMetricLabel"] {{ opacity: 0.7; }}

          .card {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 3px solid {BRAND['gold']};
            border-radius: 14px;
            padding: 18px 22px;
          }}
          .card--teal {{ border-left-color: {BRAND['teal']}; }}

          button[data-baseweb="tab"] {{ font-weight: 600; }}
          [data-testid="stSidebar"] {{ border-right: 1px solid rgba(255,255,255,0.08); }}
          .stDataFrame {{ border-radius: 10px; overflow: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def eyebrow(text: str) -> None:
    st.markdown(f'<span class="eyebrow">{text}</span>', unsafe_allow_html=True)


def muted(text: str) -> None:
    st.markdown(f'<div class="muted">{text}</div>', unsafe_allow_html=True)


def card_open(variant: str = "") -> None:
    css_class = "card card--teal" if variant == "teal" else "card"
    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)


def card_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)
