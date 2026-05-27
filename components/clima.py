import requests
import streamlit as st
from datetime import datetime

# ─── Constantes ──────────────────────────────────────────────────────────────

LAT, LON = -29.91, -51.18

WIND_DIRS = ["N", "NE", "L", "SE", "S", "SO", "O", "NO"]
WIND_FULL = ["Norte", "Nordeste", "Leste", "Sudeste", "Sul", "Sudoeste", "Oeste", "Noroeste"]

WEATHER_MAP = {
    0:  ("☀️",  "Céu limpo"),
    1:  ("🌤️", "Poucas nuvens"),
    2:  ("⛅",  "Parcialmente nublado"),
    3:  ("☁️",  "Nublado"),
    45: ("🌫️", "Neblina"),
    51: ("🌦️", "Garoa leve"),
    61: ("🌧️", "Chuva fraca"),
    63: ("🌧️", "Chuva moderada"),
    71: ("❄️",  "Neve"),
    80: ("🌦️", "Pancadas"),
    95: ("⛈️",  "Tempestade"),
}

DIAS_SEMANA = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]

def get_cardinal(graus: float) -> tuple[str, str]:
    idx = round((graus % 360) / 45) % 8
    return WIND_DIRS[idx], WIND_FULL[idx]


def get_weather(code: int) -> tuple[str, str]:
    return WEATHER_MAP.get(code, ("🌤️", "Variável"))


def fmt_date(date_str: str, index: int) -> str:
    if index == 0:
        return "Hoje"
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return DIAS_SEMANA[d.weekday()]


def progress_bar_html(pct: float, color: str = "#38bdf8") -> str:
    pct = min(max(pct, 0), 100)
    return f"""
    <div style="background:#1e293b;border-radius:4px;height:5px;overflow:hidden;margin-top:6px;">
        <div style="width:{pct}%;height:100%;background:{color};border-radius:4px;transition:width .5s ease;"></div>
    </div>
    <div style="font-size:11px;color:#64748b;margin-top:4px;">{int(pct)}% de probabilidade</div>
    """


def metric_card_html(label: str, value: str, color: str = "#e2e8f0", sub: str = "") -> str:
    sub_html = f'<div style="font-size:11px;color:#64748b;margin-top:2px;">{sub}</div>' if sub else ""
    return f"""
    <div style="text-align:center;">
        <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.1em;">{label}</div>
        <div style="font-size:20px;font-weight:600;color:{color};margin-top:3px;">{value}</div>
        {sub_html}
    </div>
    """

# ─── Fetch ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def fetch_weather() -> dict | None:
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        f"&current_weather=true"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
        f"precipitation_sum,precipitation_probability_max,windspeed_10m_max"
        f"&timezone=America/Sao_Paulo"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"⚠️ Erro ao buscar dados: {e}")
        return None

# ─── Componente principal ────────────────────────────────────────────────────

def render_clima():
    # CSS global
    st.markdown("""
    <style>
    .weather-card {
        background: #0a1628;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    }
    .weather-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,.35);
        border-color: rgba(56,189,248,.35);
    }
    .section-label {
        font-size: 10px;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: .12em;
        margin-bottom: 12px;
    }
    .alert-box {
        background: rgba(251,191,36,.07);
        border: 1px solid rgba(251,191,36,.3);
        border-radius: 10px;
        padding: 12px 16px;
        color: #fbbf24;
        font-size: 13px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Cabeçalho
    st.markdown("""
    <div style="border-bottom:1px solid rgba(56,189,248,.15);padding-bottom:16px;margin-bottom:20px;">
        <div style="font-size:22px;font-weight:700;
                    background:linear-gradient(135deg,#38bdf8,#818cf8);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            Situação Meteorológica
        </div>
        <div style="font-size:11px;color:#475569;letter-spacing:.1em;margin-top:4px;">
            CANOAS / GUAÍBA · RS &nbsp;·&nbsp;
    """ + datetime.now().strftime("%d/%m/%Y %H:%M") + """
        </div>
    </div>
    """, unsafe_allow_html=True)

    data = fetch_weather()
    if not data:
        return

    atual  = data.get("current_weather", {})
    diario = data.get("daily", {})
    times  = diario.get("time", [])

    wind_spd = atual.get("windspeed") or atual.get("wind_speed_10m", 0)
    wind_deg = atual.get("winddirection") or atual.get("wind_direction_10m", 0)
    w_short, w_full = get_cardinal(wind_deg)
    south_wind = 135 <= wind_deg <= 225

    today_code = (diario.get("weather_code") or [0])[0]
    today_emoji, today_label = get_weather(today_code)
    today_max  = (diario.get("temperature_2m_max")           or ["--"])[0]
    today_min  = (diario.get("temperature_2m_min")           or ["--"])[0]
    today_rain = (diario.get("precipitation_sum")            or [0])[0]
    today_prob = (diario.get("precipitation_probability_max")or [0])[0]

    # ── Condições atuais ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Condições Atuais</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(56,189,248,.08),rgba(129,140,248,.08));
                    border:1px solid rgba(56,189,248,.2);border-radius:12px;padding:18px; height: 130px;">
            <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;">Tempo Agora</div>
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:40px;line-height:1;">{today_emoji}</span>
                <div>
                    <div style="font-size:14px;color:#e2e8f0;">{today_label}</div>
                    <div style="font-size:24px;color:#f43f5e;font-weight:600;margin-top:2px;">
                        {today_max}°
                        <span style="font-size:14px;color:#38bdf8;margin-left:6px;">{today_min}°</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        arrow_transform = f"rotate({wind_deg}, 24, 24)"
        st.markdown(f"""
        <div style="background:#0a1628;border:1px solid #1e293b;border-radius:12px;padding:18px; height: 130px;">
            <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;">Vento Guaíba</div>
            <div style="display:flex;align-items:center;gap:14px;">
                <svg width="52" height="52" viewBox="0 0 48 48">
                    <circle cx="24" cy="24" r="22" fill="none" stroke="rgba(56,189,248,.2)" stroke-width="1.5"/>
                    <text x="24" y="10" text-anchor="middle" fill="#64748b" font-size="7" font-family="monospace">N</text>
                    <text x="39" y="27" text-anchor="middle" fill="#64748b" font-size="7" font-family="monospace">L</text>
                    <text x="24" y="42" text-anchor="middle" fill="#64748b" font-size="7" font-family="monospace">S</text>
                    <text x="9" y="27" text-anchor="middle" fill="#64748b" font-size="7" font-family="monospace">O</text>
                    <g transform="{arrow_transform}">
                        <polygon points="24,6 27,22 24,20 21,22" fill="#f43f5e"/>
                        <polygon points="24,42 27,26 24,28 21,26" fill="rgba(148,163,184,.4)"/>
                    </g>
                    <circle cx="24" cy="24" r="3" fill="#38bdf8"/>
                </svg>
                <div>
                    <div style="font-size:22px;color:#e2e8f0;font-weight:600;">
                        {wind_spd} <span style="font-size:13px;color:#64748b;">km/h</span>
                    </div>
                    <div style="font-size:12px;color:#38bdf8;margin-top:2px;">{w_full} ({wind_deg}°)</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        prob_pct = min(max(float(today_prob), 0), 100)
        st.markdown(f"""
        <div style="background:#0a1628;border:1px solid #1e293b;border-radius:12px;padding:18px; height: 130px;">
            <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;">Precipitação Hoje</div>
            <div style="font-size:24px;color:#38bdf8;font-weight:600;">
                {today_rain} <span style="font-size:13px;color:#64748b;">mm</span>
            </div>
            <div style="background:#1e293b;border-radius:4px;height:5px;overflow:hidden;margin-top:10px;">
                <div style="width:{prob_pct}%;height:100%;background:#38bdf8;border-radius:4px;"></div>
            </div>
            <div style="font-size:11px;color:#64748b;margin-top:4px;">{int(prob_pct)}% de probabilidade</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Alerta vento sul ──────────────────────────────────────────────────────
    if south_wind:
        st.markdown("""
        <div class="alert-box">
            ⚠️ Ventos do quadrante <strong>Sul</strong> tendem a represar a água do Guaíba.
            Monitore o nível do lago.
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Previsão 7 dias ───────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Previsão · 7 Dias</div>', unsafe_allow_html=True)

    cols = st.columns(7)
    codes     = diario.get("weather_code", [])
    max_temps = diario.get("temperature_2m_max", [])
    min_temps = diario.get("temperature_2m_min", [])
    rains     = diario.get("precipitation_sum", [])
    probs     = diario.get("precipitation_probability_max", [])
    wind_max  = diario.get("windspeed_10m_max", [])

    for i, t in enumerate(times[:7]):
        day_label = fmt_date(t, i)
        code = codes[i] if i < len(codes) else 0
        emoji, _ = get_weather(code)
        mx = max_temps[i] if i < len(max_temps) else "--"
        mn = min_temps[i] if i < len(min_temps) else "--"
        rn = rains[i]    if i < len(rains)     else 0
        pb = probs[i]    if i < len(probs)      else 0

        with cols[i]:
            st.markdown(f"""
            <div class="weather-card">
                <div style="font-size:11px;color:#64748b;text-transform:uppercase;
                            letter-spacing:.06em;margin-bottom:6px;">{day_label}</div>
                <div style="font-size:28px;margin:6px 0;line-height:1;">{emoji}</div>
                <div style="font-size:16px;color:#f43f5e;font-weight:600;">{mx}°</div>
                <div style="font-size:12px;color:#38bdf8;">{mn}°</div>
                <div style="margin-top:10px;padding-top:8px;border-top:1px solid #1e293b;
                            font-size:10px;color:#475569;line-height:1.8;">
                    💧 {rn} mm<br>{int(pb)}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Painel de detalhes ──────────────────────────────────────────────────
    st.markdown('<div class="section-label">Detalhes do Dia</div>', unsafe_allow_html=True)

    day_options = []
    for i, t in enumerate(times[:7]):
        label = fmt_date(t, i)
        d = datetime.strptime(t, "%Y-%m-%d")
        day_options.append(f"{label} — {d.strftime('%d/%m')}")

    selected_idx = st.selectbox(
        "Selecionar dia",
        options=range(len(day_options)),
        format_func=lambda i: day_options[i],
        label_visibility="collapsed",
    )

    if selected_idx is not None and times:
        sc = codes[selected_idx]     if selected_idx < len(codes)     else 0
        sx = max_temps[selected_idx] if selected_idx < len(max_temps) else "--"
        sn = min_temps[selected_idx] if selected_idx < len(min_temps) else "--"
        sr = rains[selected_idx]     if selected_idx < len(rains)     else 0
        sp = probs[selected_idx]     if selected_idx < len(probs)      else 0
        sw = wind_max[selected_idx]  if selected_idx < len(wind_max)  else "--"
        se, sl = get_weather(sc)

        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        with mc1:
            st.markdown(metric_card_html("Máxima", f"{sx}°C", "#f43f5e"), unsafe_allow_html=True)
        with mc2:
            st.markdown(metric_card_html("Mínima", f"{sn}°C", "#38bdf8"), unsafe_allow_html=True)
        with mc3:
            st.markdown(metric_card_html("Chuva", f"{sr} mm", "#818cf8"), unsafe_allow_html=True)
        with mc4:
            st.markdown(metric_card_html("Probabilidade", f"{int(sp)}%", "#34d399"), unsafe_allow_html=True)
        with mc5:
            st.markdown(metric_card_html("Vento Máx.", f"{sw} km/h", "#fbbf24"), unsafe_allow_html=True)

    # ── Rodapé ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="margin-top:24px;padding-top:14px;border-top:1px solid #1e293b;
                font-size:10px;color:#334155;letter-spacing:.06em;
                display:flex;justify-content:space-between;">
        <span>Fonte: Open-Meteo API · Canoas RS ({LAT}, {LON})</span>
        <span>Cache: 10 min · Atualizado às {datetime.now().strftime('%H:%M')}</span>
    </div>
    """, unsafe_allow_html=True)
