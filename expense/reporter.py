import os
import re
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv


def _md_to_html(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Tableaux markdown
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "|" in line and i + 1 < len(lines) and re.match(r"[\s|:-]+$", lines[i + 1].replace("|", "")):
            # Entête
            headers = [c.strip() for c in line.strip().strip("|").split("|")]
            html = "<table style='border-collapse:collapse;width:100%;font-size:13px;margin:8px 0'>"
            html += "<thead><tr>" + "".join(f"<th style='border:1px solid #e5e7eb;padding:6px 10px;background:#f9fafb;text-align:left'>{h}</th>" for h in headers) + "</tr></thead><tbody>"
            i += 2  # skip séparateur
            while i < len(lines) and "|" in lines[i]:
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                html += "<tr>" + "".join(f"<td style='border:1px solid #e5e7eb;padding:6px 10px'>{c}</td>" for c in cells) + "</tr>"
                i += 1
            html += "</tbody></table>"
            out.append(html)
            continue
        out.append(line)
        i += 1
    text = "\n".join(out)

    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"^#{1,3} (.+)$", r"<strong>\1</strong>", text, flags=re.MULTILINE)
    text = re.sub(r"^- (.+)$", r"• \1", text, flags=re.MULTILINE)
    text = text.replace("\n\n", "<br><br>").replace("\n", "<br>")
    return text

load_dotenv()

BADGE_COLORS = {
    "montant_eleve": "#dc2626",
    "doublon": "#d97706",
    "pattern_ml": "#7c3aed",
}

BADGE_LABELS = {
    "montant_eleve": "Seuil absolu",
    "doublon": "Doublon",
    "pattern_ml": "Pattern ML",
}


def _narrative(summary: dict, anomalies: list[dict]) -> str:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "moonshotai/kimi-k2"),
        max_tokens=1500,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un analyste financier interne. Redige un rapport d'audit en francais, "
                    "professionnel et concis. Structure: 1) Synthese (2 phrases), "
                    "2) Anomalies detectees (une ligne par anomalie, explication metier claire), "
                    "3) Recommandations (2-3 actions concretes). Ton direct, pas de jargon inutile."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Resume des depenses:\n{json.dumps(summary, ensure_ascii=False, indent=2)}"
                    f"\n\nAnomalies detectees:\n{json.dumps(anomalies, ensure_ascii=False, indent=2)}"
                ),
            },
        ],
    )
    return response.choices[0].message.content


def generate_report(summary: dict, anomalies: list[dict], output_path: str) -> str:
    narrative = _narrative(summary, anomalies)
    narrative_html = _md_to_html(narrative)

    anomaly_rows = ""
    for a in anomalies:
        color = BADGE_COLORS.get(a["type"], "#6b7280")
        label = BADGE_LABELS.get(a["type"], a["type"])
        score_html = f"<span style='font-size:11px;color:#6b7280'>{a['score']:.2f}</span>" if a.get("score") else ""
        employe_html = f"<span style='font-size:11px;color:#6b7280'>{a.get('employe', '')}</span>"
        centre_html = f"<span style='font-size:11px;color:#9ca3af'>{a.get('centre_cout', '')}</span>"
        anomaly_rows += (
            f"<tr>"
            f"<td>{a['date']}</td>"
            f"<td><span class='badge' style='background:{color}'>{label}</span> {score_html}</td>"
            f"<td>{a['fournisseur']}</td>"
            f"<td>{a['categorie']}</td>"
            f"<td>{employe_html}<br>{centre_html}</td>"
            f"<td class='amount'>{a['montant']:,.2f} EUR</td>"
            f"<td class='detail'>{a['detail']}</td>"
            f"</tr>"
        )

    cat_rows = "".join(
        f"<tr><td>{cat}</td><td class='amount'>{amt:,.2f} EUR</td></tr>"
        for cat, amt in sorted(summary["par_categorie"].items(), key=lambda x: -x[1])
    )

    emp_rows = "".join(
        f"<tr><td>{emp}</td><td class='amount'>{amt:,.2f} EUR</td></tr>"
        for emp, amt in sorted(summary.get("par_employe", {}).items(), key=lambda x: -x[1])
    )

    cc_rows = "".join(
        f"<tr><td>{cc}</td><td class='amount'>{amt:,.2f} EUR</td></tr>"
        for cc, amt in sorted(summary.get("par_centre_cout", {}).items(), key=lambda x: -x[1])
    )

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Rapport Analyse Depenses - {datetime.now().strftime('%d/%m/%Y')}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; background: #f9fafb; color: #1f2937; padding: 32px; }}
  h1 {{ font-size: 22px; font-weight: 700; margin-bottom: 4px; }}
  .meta {{ font-size: 13px; color: #6b7280; margin-bottom: 32px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 32px; }}
  .grid3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
  .card {{ background: white; border: 1px solid #e5e7eb; border-radius: 10px; padding: 20px; }}
  .card h3 {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #9ca3af; margin-bottom: 8px; }}
  .card p {{ font-size: 24px; font-weight: 700; }}
  .card.alert {{ border-left: 4px solid #dc2626; }}
  .section {{ background: white; border: 1px solid #e5e7eb; border-radius: 10px; padding: 24px; margin-bottom: 24px; }}
  .section h2 {{ font-size: 15px; font-weight: 600; margin-bottom: 16px; }}
  .analysis {{ font-size: 14px; line-height: 1.7; color: #374151; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; padding: 10px 12px; background: #f9fafb; border-bottom: 2px solid #e5e7eb; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: top; }}
  tr:hover td {{ background: #f9fafb; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; color: white; white-space: nowrap; }}
  .amount {{ font-family: monospace; font-weight: 600; }}
  .detail {{ color: #6b7280; font-size: 12px; }}
</style>
</head>
<body>
<h1>Rapport Analyse Depenses</h1>
<p class="meta">Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')} - Periode: {summary['periode']}</p>

<div class="grid">
  <div class="card">
    <h3>Total depenses</h3>
    <p>{summary['total_depenses']:,.0f} EUR</p>
  </div>
  <div class="card">
    <h3>Nombre de lignes</h3>
    <p>{summary['total_lignes']}</p>
  </div>
  <div class="card alert">
    <h3>Anomalies detectees</h3>
    <p>{len(anomalies)}</p>
  </div>
</div>

<div class="section">
  <h2>Analyse IA</h2>
  <div class="analysis">{narrative_html}</div>
</div>

<div class="section">
  <h2>Anomalies ({len(anomalies)})</h2>
  <table>
    <thead><tr><th>Date</th><th>Type</th><th>Fournisseur</th><th>Catégorie</th><th>Employé / CC</th><th>Montant</th><th>Détail</th></tr></thead>
    <tbody>{anomaly_rows}</tbody>
  </table>
</div>

<div class="grid3">
  <div class="section">
    <h2>Par catégorie</h2>
    <table>
      <thead><tr><th>Catégorie</th><th>Total</th></tr></thead>
      <tbody>{cat_rows}</tbody>
    </table>
  </div>
  <div class="section">
    <h2>Par employé</h2>
    <table>
      <thead><tr><th>Employé</th><th>Total</th></tr></thead>
      <tbody>{emp_rows}</tbody>
    </table>
  </div>
  <div class="section">
    <h2>Par centre de coût</h2>
    <table>
      <thead><tr><th>Centre</th><th>Total</th></tr></thead>
      <tbody>{cc_rows}</tbody>
    </table>
  </div>
</div>

</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    return output_path
