from __future__ import annotations

import html
from pathlib import Path

import pandas as pd


def build(shortlist: pd.DataFrame, output: Path, title: str = 'A-SCOPE Research Queue') -> None:
    columns = [c for c in ['code','name','primary_archetype','evidence_stage','opportunity_score','investability_score','research_priority','data_confidence','open_p0_count'] if c in shortlist]
    rows = []
    for _, row in shortlist.head(100).iterrows():
        cells = ''.join(f'<td>{html.escape(str(row.get(col, "")))}</td>' for col in columns)
        rows.append(f'<tr>{cells}</tr>')
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>body{{font-family:Arial,"Microsoft YaHei",sans-serif;margin:0;background:#f4f7fb;color:#172033}}header{{background:#0d315f;color:white;padding:30px}}main{{padding:24px;max-width:1500px;margin:auto}}table{{width:100%;border-collapse:collapse;background:white}}th{{background:#173f6c;color:white;padding:10px;position:sticky;top:0}}td{{padding:9px;border-bottom:1px solid #d9e3ef}}.note{{background:#eaf3ff;border-left:5px solid #1465a7;padding:14px;margin-bottom:18px}}</style></head><body><header><h1>{html.escape(title)}</h1></header><main><div class="note">研究优先级不是买入信号。进入可执行观察池仍需REOS-S完成P0、三情景、Premortem、失效日期与风险预算。</div><table><thead><tr>{''.join(f'<th>{html.escape(c)}</th>' for c in columns)}</tr></thead><tbody>{''.join(rows)}</tbody></table></main></body></html>"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding='utf-8')
