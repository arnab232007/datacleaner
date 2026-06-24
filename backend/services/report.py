"""
Report generator: produces a PDF (ReportLab) and an HTML dashboard (Jinja2 + inline Plotly).
"""
import os
import json
import pandas as pd
from datetime import datetime


def generate_reports(df_raw: pd.DataFrame, df_clean: pd.DataFrame,
                     summary: dict, job_id: str, reports_dir: str):
    _generate_html(df_raw, df_clean, summary, job_id, reports_dir)
    _generate_pdf(summary, job_id, reports_dir)


# ── HTML Report ────────────────────────────────────────────────────────────────

def _generate_html(df_raw, df_clean, summary, job_id, reports_dir):
    null_before = {col: int(df_raw[col].isnull().sum()) for col in df_raw.columns}
    null_after  = {col: int(df_clean[col].isnull().sum()) for col in df_clean.columns
                   if col in df_raw.columns}

    chart_labels = list(null_before.keys())[:20]
    chart_before = [null_before.get(c, 0) for c in chart_labels]
    chart_after  = [null_after.get(c, 0) for c in chart_labels]

    audit_html = "".join(f"<li>{a}</li>" for a in summary.get("audit_log", []))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Data Quality Report — {job_id[:8]}</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:system-ui,sans-serif;background:#0f1117;color:#e2e8f0;padding:24px}}
  h1{{font-size:1.6rem;font-weight:600;margin-bottom:4px}}
  .sub{{color:#94a3b8;font-size:.875rem;margin-bottom:24px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:28px}}
  .card{{background:#1e2130;border-radius:10px;padding:16px;border:1px solid #2d3352}}
  .card .val{{font-size:2rem;font-weight:700;color:#7c8dff;line-height:1.1}}
  .card .lbl{{font-size:.75rem;color:#94a3b8;margin-top:4px}}
  .section{{background:#1e2130;border-radius:10px;padding:20px;margin-bottom:20px;border:1px solid #2d3352}}
  .section h2{{font-size:1rem;font-weight:600;margin-bottom:14px;color:#c7d2fe}}
  ul.audit{{padding-left:18px;color:#94a3b8;font-size:.8125rem;line-height:2}}
  #chart1,#chart2{{height:320px}}
</style>
</head>
<body>
<h1>Data Quality Report</h1>
<p class="sub">Job {job_id[:8]} &nbsp;·&nbsp; Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>

<div class="grid">
  <div class="card"><div class="val">{summary['original_rows']:,}</div><div class="lbl">Original rows</div></div>
  <div class="card"><div class="val">{summary['cleaned_rows']:,}</div><div class="lbl">Cleaned rows</div></div>
  <div class="card"><div class="val">{summary['removed_rows']:,}</div><div class="lbl">Rows removed</div></div>
  <div class="card"><div class="val">{summary['nulls_fixed']:,}</div><div class="lbl">Nulls fixed</div></div>
  <div class="card"><div class="val">{summary['duplicates_removed']:,}</div><div class="lbl">Duplicates removed</div></div>
  <div class="card"><div class="val">{summary['outliers_handled']:,}</div><div class="lbl">Outliers handled</div></div>
</div>

<div class="section"><h2>Missing values — before vs after (top 20 columns)</h2><div id="chart1"></div></div>
<div class="section"><h2>Row count before vs after</h2><div id="chart2"></div></div>
<div class="section"><h2>Cleaning actions log</h2><ul class="audit">{audit_html}</ul></div>

<script>
Plotly.newPlot('chart1',
  [{{name:'Before',type:'bar',x:{json.dumps(chart_labels)},y:{json.dumps(chart_before)},marker:{{color:'#e05260'}}}},
   {{name:'After', type:'bar',x:{json.dumps(chart_labels)},y:{json.dumps(chart_after)}, marker:{{color:'#22c55e'}}}}],
  {{barmode:'group',paper_bgcolor:'transparent',plot_bgcolor:'transparent',
    font:{{color:'#e2e8f0',size:11}},margin:{{t:10,b:60,l:40,r:10}},
    xaxis:{{tickangle:-45}},yaxis:{{gridcolor:'#2d3352'}}}},
  {{responsive:true,displayModeBar:false}});

Plotly.newPlot('chart2',
  [{{type:'bar',x:['Original','Cleaned'],y:[{summary['original_rows']},{summary['cleaned_rows']}],
     marker:{{color:['#7c8dff','#22c55e']}}}}],
  {{paper_bgcolor:'transparent',plot_bgcolor:'transparent',
    font:{{color:'#e2e8f0',size:12}},margin:{{t:10,b:40,l:40,r:10}},
    yaxis:{{gridcolor:'#2d3352'}}}},
  {{responsive:true,displayModeBar:false}});
</script>
</body></html>"""

    with open(os.path.join(reports_dir, f"{job_id}.html"), "w", encoding="utf-8") as f:
        f.write(html)


# ── PDF Report ─────────────────────────────────────────────────────────────────

def _generate_pdf(summary: dict, job_id: str, reports_dir: str):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm

        path = os.path.join(reports_dir, f"{job_id}.pdf")
        doc = SimpleDocTemplate(path, pagesize=A4,
                                 leftMargin=2*cm, rightMargin=2*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("title", parent=styles["Heading1"],
                                     fontSize=18, textColor=colors.HexColor("#1e293b"))
        body_style  = ParagraphStyle("body",  parent=styles["Normal"], fontSize=10,
                                     leading=16, textColor=colors.HexColor("#334155"))

        story = [
            Paragraph("Data Quality Report", title_style),
            Paragraph(f"Job: {job_id[:8]}  ·  {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style),
            Spacer(1, 0.5*cm),
        ]

        metrics = [
            ["Metric", "Value"],
            ["Original rows",       f"{summary['original_rows']:,}"],
            ["Cleaned rows",        f"{summary['cleaned_rows']:,}"],
            ["Rows removed",        f"{summary['removed_rows']:,}"],
            ["Nulls fixed",         f"{summary['nulls_fixed']:,}"],
            ["Duplicates removed",  f"{summary['duplicates_removed']:,}"],
            ["Outliers handled",    f"{summary['outliers_handled']:,}"],
            ["Columns dropped",     f"{summary['cols_dropped']:,}"],
        ]
        t = Table(metrics, colWidths=[9*cm, 7*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#1e40af")),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#f8fafc"), colors.white]),
            ("GRID",        (0,0), (-1,-1), 0.25, colors.HexColor("#cbd5e1")),
            ("PADDING",     (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("Cleaning actions log", styles["Heading2"]))

        for action in summary.get("audit_log", []):
            story.append(Paragraph(f"• {action}", body_style))

        doc.build(story)

    except ImportError:
        # ReportLab not installed — write a plain text stub PDF placeholder
        path = os.path.join(reports_dir, f"{job_id}.pdf")
        with open(path, "wb") as f:
            f.write(b"%PDF-1.4\n% ReportLab not installed - install it to get real PDFs.\n")
