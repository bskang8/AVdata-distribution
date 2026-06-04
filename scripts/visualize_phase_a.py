"""
Phase A 시각화 — 독립 HTML 출력

생성 파일:
  experiments/EXP-002/results/viz_odd_coverage.html   ODD 커버리지 분석
  experiments/EXP-002/results/viz_clusters.html       임베딩 클러스터 분석

실행:
  uv run python scripts/visualize_phase_a.py
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── 경로 ──────────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parents[1]
RESULTS_DIR   = ROOT / "experiments/EXP-002/results"
ACTIVE_DIR    = ROOT / "data/active"
INDEX_DIR     = ROOT / "data/index"

ODD_TAGS_PATH     = ACTIVE_DIR  / "odd_tags.json"
CLIP_IDS_PATH     = ACTIVE_DIR  / "clip_ids.json"
ODD_COV_PATH      = RESULTS_DIR / "odd_coverage_matrix.json"
CLUSTER_PATH      = RESULTS_DIR / "cluster_analysis.json"
CLUSTER_LBL_PATH  = RESULTS_DIR / "cluster_labels.npy"
UMAP_PATH         = INDEX_DIR   / "umap_coords.parquet"

OUT_ODD = RESULTS_DIR / "viz_odd_coverage.html"
OUT_CLU = RESULTS_DIR / "viz_clusters.html"

WEATHER_ORDER  = ["clear", "cloudy", "rain", "snow", "fog"]
TIME_ORDER     = ["day", "night", "dawn", "dusk"]
ROAD_ORDER     = ["highway", "urban", "intersection", "parking_lot", "rural", "tunnel", "bridge"]
HAZARD_ORDER   = ["none", "low", "medium", "high"]


# ════════════════════════════════════════════════════════════════════════════
# 1. viz_odd_coverage.html
# ════════════════════════════════════════════════════════════════════════════

def build_odd_coverage_viz():
    print("Building ODD Coverage viz …")
    cov   = json.loads(ODD_COV_PATH.read_text())
    tags  = json.loads(ODD_TAGS_PATH.read_text())

    # ── (a) weather × road_type 히트맵 ────────────────────────────────
    wx_rd: dict[tuple, int] = defaultdict(int)
    for t in tags.values():
        w = t.get("weather", "unknown")
        r = t.get("road_type", "unknown")
        if w in WEATHER_ORDER and r in ROAD_ORDER:
            wx_rd[(w, r)] += 1

    heat_z, heat_text = [], []
    for w in WEATHER_ORDER:
        row_z, row_t = [], []
        for r in ROAD_ORDER:
            v = wx_rd.get((w, r), 0)
            row_z.append(v if v > 0 else None)
            row_t.append(f"{v:,}" if v > 0 else "0 (gap)")
        heat_z.append(row_z)
        heat_text.append(row_t)

    fig_heat = go.Figure(go.Heatmap(
        z=heat_z, x=ROAD_ORDER, y=WEATHER_ORDER,
        text=heat_text, texttemplate="%{text}",
        colorscale="YlOrRd", reversescale=True,
        colorbar=dict(title="클립 수"),
        hoverongaps=False,
    ))
    # 제로 커버리지 강조 (회색)
    for i, w in enumerate(WEATHER_ORDER):
        for j, r in enumerate(ROAD_ORDER):
            if wx_rd.get((w, r), 0) == 0:
                fig_heat.add_shape(
                    type="rect",
                    x0=j - 0.5, x1=j + 0.5,
                    y0=i - 0.5, y1=i + 0.5,
                    fillcolor="rgba(180,180,180,0.6)",
                    line=dict(width=0),
                )
    fig_heat.update_layout(
        title="weather × road_type 클립 수 (회색=데이터 없음)",
        height=380,
        margin=dict(t=50, b=40),
    )

    # ── (b) time_of_day × road_type 히트맵 ───────────────────────────
    tx_rd: dict[tuple, int] = defaultdict(int)
    for t in tags.values():
        tm = t.get("time_of_day", "unknown")
        r  = t.get("road_type",   "unknown")
        if tm in TIME_ORDER and r in ROAD_ORDER:
            tx_rd[(tm, r)] += 1

    heat_z2, heat_text2 = [], []
    for tm in TIME_ORDER:
        row_z, row_t = [], []
        for r in ROAD_ORDER:
            v = tx_rd.get((tm, r), 0)
            row_z.append(v if v > 0 else None)
            row_t.append(f"{v:,}" if v > 0 else "0 (gap)")
        heat_z2.append(row_z)
        heat_text2.append(row_t)

    fig_heat2 = go.Figure(go.Heatmap(
        z=heat_z2, x=ROAD_ORDER, y=TIME_ORDER,
        text=heat_text2, texttemplate="%{text}",
        colorscale="Blues",
        colorbar=dict(title="클립 수"),
        hoverongaps=False,
    ))
    for i, tm in enumerate(TIME_ORDER):
        for j, r in enumerate(ROAD_ORDER):
            if tx_rd.get((tm, r), 0) == 0:
                fig_heat2.add_shape(
                    type="rect",
                    x0=j - 0.5, x1=j + 0.5,
                    y0=i - 0.5, y1=i + 0.5,
                    fillcolor="rgba(180,180,180,0.6)",
                    line=dict(width=0),
                )
    fig_heat2.update_layout(
        title="time_of_day × road_type 클립 수 (회색=데이터 없음)",
        height=320,
        margin=dict(t=50, b=40),
    )

    # ── (c) 필드별 분포 막대 ──────────────────────────────────────────
    dist = cov["per_field_distribution"]
    bar_figs = []
    field_titles = {
        "weather": "날씨(weather)", "time_of_day": "시간대",
        "road_type": "도로 유형", "hazard_level": "위험 수준",
    }
    field_orders = {
        "weather": WEATHER_ORDER, "time_of_day": TIME_ORDER,
        "road_type": ROAD_ORDER,  "hazard_level": HAZARD_ORDER,
    }
    for field in ["weather", "time_of_day", "road_type", "hazard_level"]:
        d = dist[field]
        order = field_orders[field]
        labels = [v for v in order if v in d] + [v for v in d if v not in order]
        values = [d.get(v, 0) for v in labels]
        unkn   = d.get("unknown", 0)
        pcts   = [f"{v/sum(values)*100:.1f}%" for v in values]
        bar_figs.append(go.Bar(
            x=labels, y=values, text=pcts,
            textposition="outside", name=field_titles[field],
        ))

    fig_bars = make_subplots(rows=2, cols=2, subplot_titles=list(field_titles.values()))
    positions = [(1,1),(1,2),(2,1),(2,2)]
    for i, (bf, pos) in enumerate(zip(bar_figs, positions)):
        fig_bars.add_trace(bf, row=pos[0], col=pos[1])
    fig_bars.update_layout(
        title="ODD 필드별 분포 (unknown 포함)",
        height=520, showlegend=False,
        margin=dict(t=60, b=40),
    )

    # ── (d) 제로 커버리지 갭 분해 막대 ───────────────────────────────
    zero = cov["zero_coverage_combos"]
    gap_weather = Counter(c["weather"]  for c in zero)
    gap_time    = Counter(c["time_of_day"] for c in zero)
    gap_road    = Counter(c["road_type"] for c in zero)
    gap_hazard  = Counter(c["hazard_level"] for c in zero)

    fig_gap = make_subplots(
        rows=1, cols=4,
        subplot_titles=["weather", "time_of_day", "road_type", "hazard_level"],
    )
    for col, (counter, order) in enumerate(
        [(gap_weather, WEATHER_ORDER), (gap_time, TIME_ORDER),
         (gap_road, ROAD_ORDER), (gap_hazard, HAZARD_ORDER)], start=1
    ):
        labels = sorted(counter.keys(), key=lambda x: -counter[x])
        vals   = [counter[k] for k in labels]
        fig_gap.add_trace(
            go.Bar(x=labels, y=vals, text=vals, textposition="outside",
                   marker_color="crimson"),
            row=1, col=col,
        )
    fig_gap.update_layout(
        title=f"제로 커버리지 갭 {cov['zero_coverage_count']}개 — 필드별 등장 횟수",
        height=320, showlegend=False,
        margin=dict(t=60, b=40),
    )

    # ── 조합 HTML ─────────────────────────────────────────────────────
    total = cov["total_clips"]
    covered = cov["covered_combinations"]
    possible = cov["possible_combinations"]
    zero_n = cov["zero_coverage_count"]

    summary_html = f"""
    <div style="font-family:sans-serif;padding:16px;background:#f8fafc;border-radius:8px;margin-bottom:12px">
      <h2 style="margin:0 0 8px">ODD Coverage Matrix — Phase A</h2>
      <span style="margin-right:24px">📦 전체 클립: <b>{total:,}</b></span>
      <span style="margin-right:24px">✅ 커버 조합: <b>{covered}/{possible}</b>
        ({covered/possible:.1%})</span>
      <span style="color:crimson">❌ 제로 커버리지: <b>{zero_n}개</b> ({zero_n/possible:.1%})</span>
    </div>
    """

    with open(OUT_ODD, "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='utf-8'>"
                "<title>ODD Coverage</title></head><body>\n")
        f.write(summary_html)
        f.write(fig_heat.to_html(full_html=False, include_plotlyjs=True))
        f.write(fig_heat2.to_html(full_html=False, include_plotlyjs=False))
        f.write(fig_bars.to_html(full_html=False, include_plotlyjs=False))
        f.write(fig_gap.to_html(full_html=False, include_plotlyjs=False))
        f.write("</body></html>")
    print(f"  → {OUT_ODD}")


# ════════════════════════════════════════════════════════════════════════════
# 2. viz_clusters.html
# ════════════════════════════════════════════════════════════════════════════

def build_cluster_viz():
    print("Building Cluster viz …")

    # ── 데이터 로드 ────────────────────────────────────────────────────
    ca         = json.loads(CLUSTER_PATH.read_text())
    labels_arr = np.load(str(CLUSTER_LBL_PATH))
    clip_ids   = json.loads(CLIP_IDS_PATH.read_text())
    umap_df    = pd.read_parquet(UMAP_PATH, columns=["clip_id", "x", "y", "weather", "time_of_day", "road_type", "hazard_level"])

    # cluster_id → LLM 레이블/size/magnitude 맵
    cluster_meta = {
        c["cluster_id"]: {
            "label":   c["llm_label"] or f"cluster {c['cluster_id']}",
            "size":    c["size"],
            "mag":     c["magnitude"],
            "mag_per": c["mag_per_clip"],
        }
        for c in ca["clusters"]
    }
    bottom_ids = {c["cluster_id"] for c in ca["bottom_50_gap_candidates"]}

    # clip_id → cluster_id 맵핑
    id2lbl = dict(zip(clip_ids, labels_arr.tolist()))
    umap_df["cluster"] = umap_df["clip_id"].map(id2lbl)
    umap_df = umap_df.dropna(subset=["cluster"])
    umap_df["cluster"] = umap_df["cluster"].astype(int)

    # ── (a) 산점도 — 50k 샘플 ─────────────────────────────────────────
    rng     = np.random.default_rng(42)
    sample  = umap_df.sample(min(50_000, len(umap_df)), random_state=42)

    def cluster_label(cid):
        if cid == -1:
            return "noise"
        meta = cluster_meta.get(cid, {})
        lbl  = meta.get("label", f"cluster {cid}")
        sz   = meta.get("size", 0)
        return f"[{cid}] {lbl} (n={sz:,})"

    sample = sample.copy()
    sample["label"]   = sample["cluster"].map(cluster_label)
    sample["is_noise"]= sample["cluster"] == -1
    sample["is_gap"]  = sample["cluster"].isin(bottom_ids)

    # KDE 밀도 등고선 → 노이즈 → 일반 → 갭 레이어 순서로 그리기
    fig_scatter = go.Figure()

    # KDE 밀도 오버레이 (전체 데이터 기반)
    sample_kde = umap_df.sample(min(50_000, len(umap_df)), random_state=0)
    fig_scatter.add_trace(go.Histogram2dContour(
        x=sample_kde["x"], y=sample_kde["y"],
        colorscale=[[0, "rgba(0,0,0,0)"], [0.3, "rgba(255,200,0,0.15)"], [1, "rgba(255,50,0,0.35)"]],
        ncontours=20, showscale=False, hoverinfo="skip",
        name="KDE 밀도", line=dict(width=0),
    ))

    noise_s = sample[sample["is_noise"]]
    fig_scatter.add_trace(go.Scattergl(
        x=noise_s["x"], y=noise_s["y"],
        mode="markers",
        marker=dict(color="lightgray", size=2, opacity=0.3),
        name="noise (22%)",
        hoverinfo="skip",
    ))

    normal_s = sample[~sample["is_noise"] & ~sample["is_gap"]]
    fig_scatter.add_trace(go.Scattergl(
        x=normal_s["x"], y=normal_s["y"],
        mode="markers",
        marker=dict(
            color=normal_s["cluster"],
            colorscale="Turbo",
            size=3, opacity=0.5,
            showscale=False,
        ),
        text=normal_s["label"],
        hovertemplate="%{text}<extra></extra>",
        name="clusters (74개+)",
    ))

    gap_s = sample[sample["is_gap"]]
    fig_scatter.add_trace(go.Scattergl(
        x=gap_s["x"], y=gap_s["y"],
        mode="markers",
        marker=dict(color="crimson", size=4, opacity=0.8),
        text=gap_s["label"],
        hovertemplate="%{text}<extra></extra>",
        name="bottom-50 갭 후보",
    ))

    fig_scatter.update_layout(
        title=f"임베딩 클러스터 2D UMAP (50k 샘플 / 전체 {ca['n_total']:,}개)",
        height=600,
        xaxis_title="UMAP-1", yaxis_title="UMAP-2",
        legend=dict(orientation="h", y=-0.08),
        margin=dict(t=50, b=80),
    )

    # ── (b) 클러스터 크기 × Magnitude 버블 차트 ─────────────────────
    rows = []
    for c in ca["clusters"]:
        rows.append({
            "cluster_id": c["cluster_id"],
            "size":       c["size"],
            "magnitude":  c["magnitude"],
            "mag_per":    c["mag_per_clip"],
            "label":      c["llm_label"] or f"cluster {c['cluster_id']}",
            "is_gap":     c["cluster_id"] in bottom_ids,
        })
    meta_df = pd.DataFrame(rows)

    fig_bubble = px.scatter(
        meta_df,
        x="size", y="mag_per",
        size="magnitude",
        color="is_gap",
        color_discrete_map={True: "crimson", False: "steelblue"},
        hover_name="label",
        hover_data={"cluster_id": True, "size": True,
                    "magnitude": ":.2f", "mag_per": ":.4f", "is_gap": False},
        labels={
            "size": "클러스터 크기 (클립 수)",
            "mag_per": "mag/clip (클립당 다양성)",
            "is_gap": "갭 후보",
        },
        log_x=True,
        title="클러스터 크기 vs mag/clip (버블 크기=magnitude, 빨강=bottom-50 갭 후보)",
        height=480,
    )
    fig_bubble.update_layout(margin=dict(t=50, b=40))

    # ── (c) Bottom-50 갭 후보 테이블 ─────────────────────────────────
    gap_rows = sorted(ca["bottom_50_gap_candidates"], key=lambda x: x["size"])
    tbl_df   = pd.DataFrame([{
        "cluster": c["cluster_id"],
        "size": c["size"],
        "magnitude": c["magnitude"],
        "mag/clip": c["mag_per_clip"],
        "LLM 레이블": c["llm_label"] or "(no label)",
    } for c in gap_rows])

    fig_table = go.Figure(go.Table(
        header=dict(
            values=list(tbl_df.columns),
            fill_color="#1e3a5f", font=dict(color="white", size=12),
            align="left",
        ),
        cells=dict(
            values=[tbl_df[c].tolist() for c in tbl_df.columns],
            fill_color=[
                ["#fef2f2" if r["cluster_id"] in bottom_ids else "white"
                 for r in gap_rows]
            ] * len(tbl_df.columns),
            align="left", font=dict(size=11),
        ),
    ))
    fig_table.update_layout(
        title="Bottom-50 갭 후보 클러스터 (크기 오름차순)",
        height=900,
        margin=dict(t=50, b=20),
    )

    # ── (d) 노이즈 포인트 ODD 태그별 산점도 ─────────────────────────
    noise_full = umap_df[umap_df["cluster"] == -1].copy()
    odd_fields = ["weather", "time_of_day", "road_type", "hazard_level"]

    fig_noise = go.Figure()
    field_trace_ranges: dict[str, tuple[int, int]] = {}
    palettes = [
        px.colors.qualitative.Set1,
        px.colors.qualitative.Set2,
        px.colors.qualitative.Set3,
        px.colors.qualitative.Pastel,
    ]

    trace_idx = 0
    for fi, field in enumerate(odd_fields):
        start = trace_idx
        values = sorted(noise_full[field].dropna().astype(str).unique())
        palette = palettes[fi]
        for i, val in enumerate(values):
            mask = noise_full[field].astype(str) == val
            sub = noise_full[mask]
            fig_noise.add_trace(go.Scattergl(
                x=sub["x"], y=sub["y"],
                mode="markers",
                marker=dict(color=palette[i % len(palette)], size=2, opacity=0.5),
                name=f"{val} ({int(mask.sum()):,})",
                visible=(field == "weather"),
                hoverinfo="skip",
            ))
            trace_idx += 1
        field_trace_ranges[field] = (start, trace_idx)

    total_noise_traces = trace_idx
    dropdown_buttons = []
    for field in odd_fields:
        s, e = field_trace_ranges[field]
        vis = [s <= i < e for i in range(total_noise_traces)]
        dropdown_buttons.append(dict(
            label=field,
            method="update",
            args=[{"visible": vis}, {"title": f"노이즈 포인트 ODD 분포: {field} (전체 노이즈 {len(noise_full):,}개)"}],
        ))

    fig_noise.update_layout(
        title=f"노이즈 포인트 ODD 분포: weather (전체 노이즈 {len(noise_full):,}개)",
        height=570,
        xaxis_title="UMAP-1", yaxis_title="UMAP-2",
        legend=dict(orientation="h", y=-0.14, font=dict(size=10)),
        margin=dict(t=70, b=110),
        updatemenus=[dict(
            buttons=dropdown_buttons,
            direction="down",
            x=0.01, y=1.14,
            showactive=True,
            xanchor="left", yanchor="top",
            bgcolor="white", bordercolor="#ccc",
        )],
        annotations=[dict(
            text="ODD 필드:", x=0.01, y=1.16,
            xref="paper", yref="paper",
            showarrow=False, font=dict(size=12),
        )],
    )

    # ── 조합 HTML ─────────────────────────────────────────────────────
    summary_html = f"""
    <div style="font-family:sans-serif;padding:16px;background:#f8fafc;border-radius:8px;margin-bottom:12px">
      <h2 style="margin:0 0 8px">임베딩 클러스터 분석 — Phase A</h2>
      <span style="margin-right:24px">📦 전체 클립: <b>{ca['n_total']:,}</b></span>
      <span style="margin-right:24px">🔵 클러스터: <b>{ca['n_clusters']}개</b></span>
      <span style="margin-right:24px; color:gray">⬜ 노이즈: <b>{ca['n_noise']:,}</b>
        ({ca['noise_rate']:.1%})</span>
      <span style="color:crimson">🔴 갭 후보(bottom-50): <b>{len(gap_rows)}개</b></span>
    </div>
    """

    with open(OUT_CLU, "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='utf-8'>"
                "<title>Cluster Analysis</title></head><body>\n")
        f.write(summary_html)
        f.write(fig_scatter.to_html(full_html=False, include_plotlyjs=True))
        f.write(fig_noise.to_html(full_html=False, include_plotlyjs=False))
        f.write(fig_bubble.to_html(full_html=False, include_plotlyjs=False))
        f.write(fig_table.to_html(full_html=False, include_plotlyjs=False))
        f.write("</body></html>")
    print(f"  → {OUT_CLU}")


# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    build_odd_coverage_viz()
    build_cluster_viz()
    print("\nDone. 브라우저에서 HTML 파일을 열어 확인하세요.")
