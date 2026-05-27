import urllib.parse
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
import requests
import streamlit as st

# ─── Constantes ──────────────────────────────────────────────────────────────
MAX_NOTICIAS   = 6
MAX_IDADE_DIAS = 15

TERMOS_BUSCA = [
    "Canoas chuva OR alagamento OR enchente OR inundação",
    "Defesa Civil porto alegre alerta OR temporal OR chuva",
    "Guaíba nível OR enchente OR alagamento",
    "rio grande do sul temporal OR enchente OR alagamento",
]

KEYWORDS_CRITICAS = [
    "emergência", "evacuação", "evacuados", "alerta máximo",
    "estado de calamidade", "desabamento", "vítima", "morto", "mortos",
    "resgate", "desaparecido", "barragem", "rompimento", "colapso",
    "inundação", "alagado", "submerso", "desalojado", "desalojados",
]

KEYWORDS_ALERTA = [
    "alerta", "alagamento", "transbordamento", "chuva intensa",
    "chuva extrema", "temporal", "tempestade", "defesa civil",
    "evacuação preventiva", "enchente", "granizo", "ciclone",
    "nível do guaíba", "guaíba sobe", "guaíba transborda",
]

KEYWORDS_RETROSPECTIVA = [
    "dois anos", "aniversário", "recordação", "memória", "tragédia de 2024",
    "um ano", "três anos", "lembra", "relembra", "completam",
    "após enchente", "pós-enchente", "durante a enchente", "desde a enchente",
    "se reconstruir", "ações isoladas", "marcas que a água",
]

GEO_RS_EXATO = [
    "canoas", "porto alegre", "guaíba", "rio grande do sul",
    "gaúcho", "gaúcha", "região metropolitana", "grande porto alegre",
    "novo hamburgo", "são leopoldo", "alvorada", "viamão", "gravataí",
]

GEO_RS_SIGLA = ["rs", "sul"]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _relevante_geo(titulo: str) -> bool:
    """
    Retorna True se o título menciona ao menos uma região relevante do RS.
    Evita falso positivo de "rs" em palavras como "carros", "metros".
    """
    t = titulo.lower()
    if any(g in t for g in GEO_RS_EXATO):
        return True
    palavras = set(t.replace(",", " ").replace(".", " ").replace(":", " ").split())
    return any(s in palavras for s in GEO_RS_SIGLA)


def _urgencia(titulo: str) -> tuple[str, str]:
    t = titulo.lower()
    if any(k in t for k in KEYWORDS_RETROSPECTIVA):
        return "NOTÍCIA", "#38bdf8"
    if any(k in t for k in KEYWORDS_CRITICAS):
        return "CRÍTICO", "#f43f5e"
    if any(k in t for k in KEYWORDS_ALERTA):
        return "ALERTA", "#fbbf24"
    return "NOTÍCIA", "#38bdf8"


def _parse_dt(entry) -> datetime | None:
    raw = getattr(entry, "published", None)
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc)
    except Exception:
        return None


def _fmt_data(dt: datetime | None) -> str:
    if not dt:
        return ""
    delta = datetime.now(timezone.utc) - dt
    minutos = int(delta.total_seconds() // 60)
    if minutos < 60:
        return f"há {minutos} min"
    if minutos < 1440:
        return f"há {minutos // 60}h"
    return f"há {minutos // 1440}d"


def _fonte(entry) -> str:
    src = getattr(entry, "source", None)
    if src and hasattr(src, "title"):
        return src.title
    titulo = getattr(entry, "title", "")
    if " - " in titulo:
        return titulo.rsplit(" - ", 1)[-1]
    return ""


def _titulo_limpo(entry) -> str:
    titulo = getattr(entry, "title", "Sem título")
    if " - " in titulo:
        return titulo.rsplit(" - ", 1)[0].strip()
    return titulo.strip()


def _deduplicar(noticias: list[dict], limiar: int = 55) -> list[dict]:
    vistos: set[str] = set()
    resultado = []
    for n in noticias:
        chave = n["titulo"].lower()[:limiar]
        if chave not in vistos:
            vistos.add(chave)
            resultado.append(n)
    return resultado


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_todos_os_feeds() -> list[dict]:
    corte   = datetime.now(timezone.utc) - timedelta(days=MAX_IDADE_DIAS)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; HidroBot/1.0)"}
    todas: list[dict] = []

    for termo in TERMOS_BUSCA:
        try:
            enc = urllib.parse.quote(termo)
            url = f"https://news.google.com/rss/search?q={enc}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
            r   = requests.get(url, headers=headers, timeout=8)
            r.raise_for_status()
            feed = feedparser.parse(r.text)

            for entry in feed.entries:
                dt = _parse_dt(entry)
                if dt and dt < corte:
                    continue
                titulo = _titulo_limpo(entry)
                if not _relevante_geo(titulo):
                    continue

                badge, cor = _urgencia(titulo)
                todas.append({
                    "titulo": titulo,
                    "link":   getattr(entry, "link", "#"),
                    "fonte":  _fonte(entry),
                    "data":   _fmt_data(dt),
                    "dt":     dt,
                    "badge":  badge,
                    "cor":    cor,
                })
        except Exception:
            continue

    ordem = {"CRÍTICO": 0, "ALERTA": 1, "NOTÍCIA": 2}
    todas.sort(key=lambda n: (
        ordem[n["badge"]],
        -(n["dt"].timestamp() if n["dt"] else 0)
    ))

    return _deduplicar(todas)


# ─── Componente principal ────────────────────────────────────────────────────

def render_noticias():
    st.markdown("""
    <style>
    .news-card {
        background: #0a1628;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 10px;
        transition: border-color .18s ease, transform .18s ease;
    }
    .news-card:hover {
        border-color: rgba(56,189,248,.35);
        transform: translateX(3px);
    }
    .news-badge {
        display: inline-block;
        font-size: 9px;
        font-weight: 700;
        letter-spacing: .12em;
        padding: 2px 7px;
        border-radius: 4px;
        margin-bottom: 8px;
        font-family: monospace;
    }
    .news-title {
        font-size: 14px;
        color: #e2e8f0;
        line-height: 1.5;
        margin-bottom: 10px;
    }
    .news-meta {
        font-size: 11px;
        color: #475569;
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
    }
    .news-fonte { color: #64748b; }
    .news-link {
        color: #38bdf8;
        text-decoration: none;
        font-size: 11px;
        letter-spacing: .04em;
        margin-left: auto;
    }
    .news-link:hover { text-decoration: underline; }
    .news-empty {
        background: rgba(56,189,248,.05);
        border: 1px solid rgba(56,189,248,.15);
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        color: #475569;
        font-size: 13px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Cabeçalho ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="border-bottom:1px solid rgba(244,63,94,.15);padding-bottom:16px;margin-bottom:20px;">
        <div style="font-size:22px;font-weight:700;
                    background:linear-gradient(135deg,#f43f5e,#fbbf24);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            Alertas e Notícias
        </div>
        <div style="font-size:11px;color:#475569;letter-spacing:.1em;margin-top:4px;">
            CANOAS · PORTO ALEGRE · REGIÃO METROPOLITANA
            &nbsp;·&nbsp; ÚLTIMOS {MAX_IDADE_DIAS} DIAS · Cache: 5 min
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch ──────────────────────────────────────────────────────────────────
    try:
        with st.spinner("Carregando notícias..."):
            noticias = _fetch_todos_os_feeds()
    except Exception as e:
        st.markdown(f"""
        <div style="background:rgba(244,63,94,.08);border:1px solid rgba(244,63,94,.3);
                    border-radius:10px;padding:14px 18px;color:#f43f5e;font-size:13px;">
            ⚠️ Erro ao carregar o feed: {e}
        </div>
        """, unsafe_allow_html=True)
        return

    if not noticias:
        st.markdown(f"""
        <div class="news-empty">
            ✅ Nenhuma ocorrência encontrada nos últimos {MAX_IDADE_DIAS} dias.
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Contadores (apenas das notícias exibidas) ──────────────────────────────
    exibidas  = noticias[:MAX_NOTICIAS]
    criticos  = sum(1 for n in exibidas if n["badge"] == "CRÍTICO")
    alertas   = sum(1 for n in exibidas if n["badge"] == "ALERTA")
    noticias_ = sum(1 for n in exibidas if n["badge"] == "NOTÍCIA")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div style="background:rgba(244,63,94,.08);border:1px solid rgba(244,63,94,.2);
                    border-radius:10px;padding:10px;text-align:center;">
            <div style="font-size:22px;color:#f43f5e;font-weight:700;">{criticos}</div>
            <div style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:.1em;margin-top:2px;">Críticos</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="background:rgba(251,191,36,.07);border:1px solid rgba(251,191,36,.2);
                    border-radius:10px;padding:10px;text-align:center;">
            <div style="font-size:22px;color:#fbbf24;font-weight:700;">{alertas}</div>
            <div style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:.1em;margin-top:2px;">Alertas</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div style="background:rgba(56,189,248,.06);border:1px solid rgba(56,189,248,.15);
                    border-radius:10px;padding:10px;text-align:center;">
            <div style="font-size:22px;color:#38bdf8;font-weight:700;">{noticias_}</div>
            <div style="font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:.1em;margin-top:2px;">Notícias</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.12em;margin-bottom:10px;">Últimas Ocorrências</div>', unsafe_allow_html=True)

    # ── Cards ──────────────────────────────────────────────────────────────────
    for n in exibidas:
        fonte_html = f'<span class="news-fonte">· {n["fonte"]}</span>' if n["fonte"] else ""
        data_html  = f'<span>{n["data"]}</span>' if n["data"] else ""
        st.markdown(f"""
        <div class="news-card">
            <span class="news-badge" style="background:rgba(0,0,0,.3);color:{n['cor']};
                  border:1px solid {n['cor']}40;">{n['badge']}</span>
            <div class="news-title">{n['titulo']}</div>
            <div class="news-meta">
                {data_html}
                {fonte_html}
                <a href="{n['link']}" target="_blank" class="news-link">Ler matéria →</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Rodapé ─────────────────────────────────────────────────────────────────
    termo_principal = urllib.parse.quote(TERMOS_BUSCA[0])
    url_web = f"https://news.google.com/search?q={termo_principal}&hl=pt-BR&gl=BR&ceid=BR:pt-419"

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    col_btn, col_info = st.columns([5, 3])
    with col_btn:
        st.link_button("Ver mais no Google News →", url_web, use_container_width=True)
    with col_info:
        st.markdown(f"""
        <div style="font-size:10px;color:#334155;letter-spacing:.06em;padding-top:10px;">
            {datetime.now().strftime('%H:%M')} · {len(exibidas)} de {len(noticias)} resultados
        </div>
        """, unsafe_allow_html=True)
