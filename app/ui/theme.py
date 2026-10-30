"""界面配色与样式。"""
import html
import re

INK = "#0f0f11"
PANEL = "#191a1f"
PANEL_SOFT = "#22232a"
LINE = "#34353d"
TEXT = "#e8e4dc"
TEXT_DIM = "#9a958c"
GOLD = "#c8a35a"
JADE = "#6fa08a"
CINNABAR = "#d0654f"

FONT_SERIF = "'Songti SC','Source Han Serif SC','Noto Serif CJK SC','STSong','SimSun',serif"
FONT_SANS = "'PingFang SC','Microsoft YaHei','Noto Sans CJK SC',sans-serif"


def stylesheet():
    return f"""
QWidget {{
  background: {INK};
  color: {TEXT};
  font-family: {FONT_SANS};
  font-size: 13px;
}}
QMainWindow, QDialog {{ background: {INK}; }}
QSplitter::handle {{ background: {INK}; }}
QTabWidget::pane {{
  border: none;
  border-top: 1px solid {LINE};
  background: {INK};
}}
QTabBar {{
  background: {INK};
  border: none;
}}
QTabBar::tab {{
  background: transparent;
  color: {TEXT_DIM};
  padding: 12px 22px;
  margin-right: 2px;
  font-family: {FONT_SERIF};
  font-size: 15px;
  border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
  color: {GOLD};
  border-bottom: 2px solid {GOLD};
}}
QTabBar::tab:hover {{ color: {TEXT}; }}
QLabel {{ background: transparent; }}
QLabel#title {{
  font-family: {FONT_SERIF};
  font-size: 21px;
  color: {TEXT};
  letter-spacing: 3px;
}}
QLabel#subtitle {{ color: {TEXT_DIM}; font-size: 12px; letter-spacing: 1px; }}
QLabel#section {{
  font-family: {FONT_SERIF};
  font-size: 15px;
  color: {GOLD};
  letter-spacing: 2px;
  padding: 2px 0 6px 0;
}}
QLabel#hint {{ color: {TEXT_DIM}; font-size: 12px; }}
QLabel#metric {{ color: {TEXT}; font-size: 12px; }}
QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit, QPlainTextEdit {{
  background: {PANEL_SOFT};
  border: 1px solid {LINE};
  border-radius: 3px;
  padding: 7px 9px;
  color: {TEXT};
  selection-background-color: {GOLD};
  selection-color: {INK};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {{ border: 1px solid {GOLD}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
  background: {PANEL_SOFT};
  border: 1px solid {LINE};
  selection-background-color: {GOLD};
  selection-color: {INK};
}}
QPushButton {{
  background: {PANEL_SOFT};
  border: 1px solid {LINE};
  border-radius: 3px;
  padding: 8px 16px;
  color: {TEXT};
}}
QPushButton:hover {{ border: 1px solid {GOLD}; color: {GOLD}; }}
QPushButton:disabled {{ color: #5d5a55; border: 1px solid #2a2b31; }}
QPushButton#primary {{
  background: {GOLD};
  border: 1px solid {GOLD};
  color: {INK};
  font-weight: 600;
}}
QPushButton#primary:hover {{ background: #dcb871; color: {INK}; }}
QPushButton#ghost {{ background: transparent; }}
QFrame#card {{
  background: {PANEL};
  border: 1px solid {LINE};
  border-radius: 4px;
}}
QFrame#cardSoul {{ background: {PANEL}; border: 1px solid {GOLD}; border-radius: 4px; }}
QFrame#cardLimit {{ background: {PANEL}; border: 1px solid {JADE}; border-radius: 4px; }}
QFrame#cardEmpty {{ background: {PANEL}; border: 1px dashed {LINE}; border-radius: 4px; }}
QTextBrowser, QTextEdit {{
  background: {PANEL};
  border: 1px solid {LINE};
  border-radius: 4px;
  padding: 14px;
}}
QTableWidget {{
  background: {PANEL};
  border: 1px solid {LINE};
  gridline-color: {LINE};
  alternate-background-color: {PANEL_SOFT};
}}
QHeaderView::section {{
  background: {PANEL_SOFT};
  border: none;
  border-right: 1px solid {LINE};
  border-bottom: 1px solid {LINE};
  padding: 7px 8px;
  color: {TEXT_DIM};
  font-weight: 500;
}}
QTableWidget::item {{ padding: 5px 8px; }}
QScrollBar:vertical {{ background: {INK}; width: 10px; margin: 0; }}
QScrollBar:horizontal {{ background: {INK}; height: 10px; margin: 0; }}
QScrollBar::handle {{ background: #3a3b44; border-radius: 5px; }}
QScrollBar::handle:hover {{ background: {GOLD}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QProgressBar {{
  background: {PANEL_SOFT};
  border: 1px solid {LINE};
  border-radius: 3px;
  height: 8px;
  text-align: center;
}}
QProgressBar::chunk {{ background: {GOLD}; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
  width: 14px; height: 14px;
  border: 1px solid {LINE};
  border-radius: 2px;
  background: {PANEL_SOFT};
}}
QCheckBox::indicator:checked {{ background: {GOLD}; border: 1px solid {GOLD}; }}
QStatusBar {{ background: {INK}; color: {TEXT_DIM}; }}
"""


def _inline(text):
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def markdown_to_html(markdown_text):
    """把 markdown 渲染成适合 QTextBrowser 的 HTML。"""
    lines = (markdown_text or "").splitlines()
    out = []
    in_list = False
    in_code = False
    in_quote = False

    def close_all():
        nonlocal in_list, in_quote
        if in_list:
            out.append("</ul>")
            in_list = False
        if in_quote:
            out.append("</blockquote>")
            in_quote = False

    for raw in lines:
        line = raw.rstrip()
        if line.strip().startswith("```"):
            if in_code:
                out.append("</pre>")
                in_code = False
            else:
                close_all()
                out.append('<pre style="background:#22232a;padding:10px;border-radius:3px;">')
                in_code = True
            continue
        if in_code:
            out.append(html.escape(line))
            continue

        stripped = line.strip()
        if not stripped:
            close_all()
            continue
        if stripped.startswith("#"):
            close_all()
            level = min(len(stripped) - len(stripped.lstrip("#")), 4)
            out.append(f"<h{level} style='color:{GOLD};margin:14px 0 8px 0;'>{_inline(stripped.lstrip('#').strip())}</h{level}>")
            continue
        if stripped.startswith(">"):
            if not in_quote:
                close_all()
                out.append(f"<blockquote style='border-left:2px solid {GOLD};margin:8px 0;padding:4px 0 4px 12px;color:{TEXT_DIM};'>")
                in_quote = True
            out.append(f"<div>{_inline(stripped.lstrip('>').strip())}</div>")
            continue
        if re.match(r"^[-*]\s+", stripped):
            if not in_list:
                close_all()
                out.append(f"<ul style='margin:6px 0 6px 18px;color:{TEXT};'>")
                in_list = True
            out.append(f"<li>{_inline(re.sub(r'^[-*]\s+', '', stripped))}</li>")
            continue
        if stripped.startswith("|"):
            close_all()
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            row = "".join(f"<td style='padding:5px 10px;border-bottom:1px solid {LINE};'>{_inline(c)}</td>" for c in cells)
            out.append(f"<tr>{row}</tr>")
            continue
        close_all()
        out.append(f"<p style='margin:8px 0;line-height:1.75;'>{_inline(stripped)}</p>")

    close_all()
    if in_code:
        out.append("</pre>")

    body = "\n".join(out)
    body = re.sub(r"(<tr>.*?</tr>)", r"<table style='border-collapse:collapse;'>\1</table>", body, flags=re.S)
    return f"<div style='font-family:{FONT_SANS};color:{TEXT};'>{body}</div>"


def reading_card_html(card):
    """把解读卡片渲染成 HTML 片段。"""
    title = html.escape(str(card.get("title", "")))
    badge = html.escape(str(card.get("badge", "")))
    body = card.get("body", "")
    accent = GOLD
    if card.get("teal"):
        accent = JADE
    if card.get("highlight"):
        accent = CINNABAR

    bars = ""
    for prob in card.get("probabilities", []) or []:
        try:
            pct = max(0, min(100, int(prob.get("pct", 0))))
        except (TypeError, ValueError):
            continue
        label = html.escape(str(prob.get("label", "")))
        bars += (
            f"<div style='margin-top:6px;'>"
            f"<span style='color:{TEXT_DIM};font-size:12px;'>{label}</span>"
            f"<span style='color:{TEXT_DIM};font-size:12px;float:right;'>{pct}%</span>"
            f"<div style='background:{PANEL_SOFT};border-radius:3px;height:6px;margin-top:4px;'>"
            f"<div style='background:{accent};width:{pct}%;height:6px;border-radius:3px;'></div></div></div>"
        )

    return (
        f"<div style='border:1px solid {LINE};border-left:3px solid {accent};"
        f"border-radius:4px;padding:14px 16px;margin:12px 0;background:{PANEL};'>"
        f"<div style='font-family:{FONT_SERIF};font-size:15px;color:{TEXT};'>{title}</div>"
        f"<div style='color:{TEXT_DIM};font-size:12px;margin-top:2px;'>{badge}</div>"
        f"<div style='margin-top:10px;line-height:1.85;'>{body}</div>{bars}</div>"
    )
