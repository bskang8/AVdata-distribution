"""
AVdata Semantic Search — Streamlit UI

Run:
  uv run streamlit run src/avdata/ui/app.py --server.port 8501

검색은 FastAPI를 통해 수행한다 (docs/HOW_TO_RUN.md 참조).
API 서버가 실행 중이어야 함: uv run uvicorn avdata.api.main:app --port 8000
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from avdata.config import (
    EXP002_RESULTS_DIR,
    INDEX_DIR,
    ODD_FIELDS,
    ODD_TAGS_PATH,
    SANFLOW_GAP_PATH,
    TAGS_DIR,
)

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AVdata Search",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ──────────────────────────────────────────────────────────────────
ODD_COVERAGE_PATH  = TAGS_DIR / "odd_coverage.json"
LONGTAIL_PATH      = INDEX_DIR / "longtail_clips.json"
UMAP_PATH          = INDEX_DIR / "umap_coords.parquet"
DIST_HTML_PATH     = INDEX_DIR / "distribution.html"

TAG_COLORS = {
    # time_of_day
    "day":   "#F59E0B", "night": "#1E3A5F", "dawn": "#F97316", "dusk": "#7C3AED",
    # weather
    "clear": "#10B981", "rain": "#3B82F6", "fog":  "#9CA3AF",
    "snow":  "#BAE6FD", "cloudy": "#6B7280",
    # hazard_level
    "none":  "#D1FAE5", "low": "#FEF9C3", "medium": "#FED7AA", "high": "#FEE2E2",
    # road_type
    "highway": "#6366F1", "urban": "#8B5CF6", "intersection": "#EC4899",
    "parking_lot": "#14B8A6", "rural": "#84CC16", "tunnel": "#F43F5E",
    "bridge": "#0EA5E9",
}

TAG_TEXT_COLORS = {
    "night": "#FFFFFF", "highway": "#FFFFFF", "urban": "#FFFFFF",
    "intersection": "#FFFFFF", "tunnel": "#FFFFFF", "bridge": "#FFFFFF",
    "fog": "#1F2937", "snow": "#1F2937",
}


# ── API search (FastAPI 호출) ───────────────────────────────────────────────────
def _api_search(
    query: str,
    method: str,
    odd_filter: dict | None,
    top_k: int,
) -> tuple[list[SimpleNamespace], float]:
    payload = {
        "query": query,
        "method": method,
        "odd_filter": odd_filter,
        "top_k": top_k,
        "include_caption": False,
    }
    resp = httpx.post(f"{API_BASE}/v1/search", json=payload, timeout=60.0)
    resp.raise_for_status()
    data = resp.json()
    results = [SimpleNamespace(**r) for r in data["results"]]
    return results, data["latency_ms"]


# ── Cached resources ───────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_odd_coverage() -> dict:
    if not ODD_COVERAGE_PATH.exists():
        return {}
    return json.loads(ODD_COVERAGE_PATH.read_text())


@st.cache_data(show_spinner=False)
def load_odd_tags() -> dict:
    if not ODD_TAGS_PATH.exists():
        return {}
    return json.loads(ODD_TAGS_PATH.read_text())


@st.cache_data(show_spinner=False)
def load_umap() -> pd.DataFrame | None:
    if not UMAP_PATH.exists():
        return None
    return pd.read_parquet(UMAP_PATH)


@st.cache_data(show_spinner=False)
def load_longtail() -> list[str]:
    if not LONGTAIL_PATH.exists():
        return []
    return json.loads(LONGTAIL_PATH.read_text())


@st.cache_data(show_spinner=False)
def load_gaps() -> list[dict]:
    if not SANFLOW_GAP_PATH.exists():
        return []
    return json.loads(SANFLOW_GAP_PATH.read_text())


@st.cache_data(show_spinner=False)
def transcode_to_h264(video_path: str) -> bytes | None:
    """HEVC(H.265) → H.264 변환 후 bytes 반환. clip_id 단위로 캐시됨."""
    if not Path(video_path).exists():
        return None
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", video_path,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-movflags", "faststart",
                tmp_path,
            ],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            return None
        return Path(tmp_path).read_bytes()
    except Exception:
        return None
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ── Video popup dialog ────────────────────────────────────────────────────────
@st.dialog("영상 재생", width="large")
def _video_popup(clip_id: str) -> None:
    from avdata.config import CAPTION_SUFFIX, CAPTIONS_DIR, VIDEO_SUFFIX, VIDEOS_DIR
    st.caption(f"Clip ID: `{clip_id}`")

    vid_file = VIDEOS_DIR / (clip_id + VIDEO_SUFFIX)
    cap_file = CAPTIONS_DIR / (clip_id + CAPTION_SUFFIX)

    col_vid, col_cap = st.columns([1, 1])

    with col_vid:
        if not vid_file.exists():
            st.error("영상 파일을 찾을 수 없습니다.")
        else:
            with st.spinner("HEVC → H.264 변환 중… (최초 재생 시 약 3초)"):
                video_bytes = transcode_to_h264(str(vid_file))
            if video_bytes:
                st.video(video_bytes, format="video/mp4")
            else:
                st.error("영상 변환에 실패했습니다.")

    with col_cap:
        st.markdown("**캡션**")
        if cap_file.exists():
            st.markdown(
                f'<div style="height:360px;overflow-y:auto;font-size:13px;'
                f'line-height:1.7;background:#f8f9fb;padding:10px 14px;'
                f'border-radius:6px;border:1px solid #e0e6f0">'
                f'{cap_file.read_text(encoding="utf-8", errors="replace")}'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("캡션 파일이 없습니다.")


# ── Helper: render ODD tag pills ───────────────────────────────────────────────
def _tag_pill(value: str) -> str:
    bg   = TAG_COLORS.get(value, "#E5E7EB")
    fg   = TAG_TEXT_COLORS.get(value, "#1F2937")
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:12px;font-size:0.78rem;margin:2px;display:inline-block">'
        f'{value}</span>'
    )


def render_tags(tags: dict) -> str:
    parts = []
    for field, val in tags.items():
        if isinstance(val, list):
            pills = " ".join(_tag_pill(v) for v in val if v != "none")
        else:
            pills = _tag_pill(val) if val not in ("unknown", "") else ""
        if pills:
            parts.append(f"<span style='font-size:0.72rem;color:#6B7280'>{field}:</span> {pills}")
    return " &nbsp; ".join(parts)


# ── Sidebar ────────────────────────────────────────────────────────────────────
def build_sidebar() -> dict:
    st.sidebar.title("🔍 검색 설정")

    method = st.sidebar.radio(
        "검색 방법",
        ["hybrid", "embedding", "bm25"],
        format_func=lambda m: {"hybrid": "🔀 Hybrid", "embedding": "🧠 Embedding", "bm25": "🔤 BM25"}[m],
    )
    top_k = st.sidebar.slider("결과 수 (top_k)", min_value=1, max_value=50, value=10)

    odd_filter: dict = {}
    if method == "hybrid":
        st.sidebar.markdown("---")
        st.sidebar.subheader("🏷️ ODD 필터")
        for field, values in ODD_FIELDS.items():
            options = ["(전체)"] + values
            sel = st.sidebar.selectbox(field, options, key=f"odd_{field}")
            if sel != "(전체)":
                odd_filter[field] = sel

    return {
        "method": method,
        "top_k": top_k,
        "odd_filter": odd_filter or None,
    }


# ── Tab 1: Search ──────────────────────────────────────────────────────────────
def tab_search(cfg: dict):
    from avdata.config import CAPTION_SUFFIX, CAPTIONS_DIR, VIDEO_SUFFIX, VIDEOS_DIR

    st.subheader("시나리오 시맨틱 검색")

    query = st.text_input(
        "검색어를 입력하세요",
        placeholder="예: pedestrian crossing at night intersection",
        label_visibility="collapsed",
    )
    col_btn, col_ex = st.columns([1, 5])
    with col_btn:
        run = st.button("검색", type="primary", use_container_width=True)
    with col_ex:
        st.caption("예시: foggy highway driving · vehicle sudden braking · cyclist entering road unexpectedly")

    if not run or not query.strip():
        return

    with st.spinner("검색 중…"):
        try:
            results, latency_ms = _api_search(
                query=query.strip(),
                method=cfg["method"],
                odd_filter=cfg["odd_filter"],
                top_k=cfg["top_k"],
            )
        except httpx.ConnectError:
            st.error(
                "FastAPI 서버에 연결할 수 없습니다.  \n"
                "`docs/HOW_TO_RUN.md` 를 참고해 API 서버를 먼저 실행하세요:  \n"
                f"`uv run uvicorn avdata.api.main:app --host 0.0.0.0 --port 8000`"
            )
            return
        except httpx.HTTPStatusError as e:
            st.error(f"API 오류 {e.response.status_code}: {e.response.text[:200]}")
            return

    if not results:
        st.warning("결과가 없습니다.")
        return

    odd_tags_all = load_odd_tags()

    st.markdown(
        f"**{len(results)}개 결과** &nbsp;|&nbsp; latency: `{latency_ms:.1f} ms`"
        f" &nbsp;|&nbsp; method: `{cfg['method']}`"
        + (f" &nbsp;|&nbsp; ODD 필터: `{cfg['odd_filter']}`" if cfg["odd_filter"] else ""),
        unsafe_allow_html=True,
    )
    st.markdown("---")

    for r in results:
        tags      = r.tags if r.tags else odd_tags_all.get(r.clip_id, {})
        cap_file  = CAPTIONS_DIR / (r.clip_id + CAPTION_SUFFIX)
        vid_file  = VIDEOS_DIR   / (r.clip_id + VIDEO_SUFFIX)
        has_video = vid_file.exists()

        with st.container():
            # ── Header row: rank badge + clip_id + score ──
            c_rank, c_info = st.columns([1, 11])
            with c_rank:
                st.markdown(
                    f"<div style='background:#6366F1;color:white;border-radius:50%;"
                    f"width:36px;height:36px;display:flex;align-items:center;"
                    f"justify-content:center;font-weight:bold;font-size:1rem'>"
                    f"#{r.rank}</div>",
                    unsafe_allow_html=True,
                )
            with c_info:
                st.markdown(
                    f"`{r.clip_id}` &nbsp; score: **{r.score:.4f}**"
                    + (" &nbsp; 🎬" if has_video else ""),
                    unsafe_allow_html=True,
                )
                if tags:
                    st.markdown(render_tags(tags), unsafe_allow_html=True)

            # ── Expanders: 영상 / 캡션 ──
            exp_cols = st.columns(2) if has_video else [st.container()]

            if has_video:
                with exp_cols[0]:
                    with st.expander("▶ 영상 재생", expanded=False):
                        with st.spinner("HEVC → H.264 변환 중… (첫 재생 시 약 3초)"):
                            video_bytes = transcode_to_h264(str(vid_file))
                        if video_bytes:
                            st.video(video_bytes, format="video/mp4")
                        else:
                            st.error("영상 변환 실패")

            cap_col = exp_cols[1] if has_video else exp_cols[0]
            with cap_col:
                if cap_file.exists():
                    with st.expander("📄 캡션 보기", expanded=False):
                        st.markdown(
                            cap_file.read_text(encoding="utf-8", errors="replace")
                        )

            st.markdown("---")


# ── Tab 2: ODD Coverage ────────────────────────────────────────────────────────
def tab_coverage():
    st.subheader("ODD 필드별 커버리지 및 분포")

    coverage = load_odd_coverage()
    if not coverage:
        st.warning("ODD 커버리지 데이터가 없습니다. `phase3/extract_odd_tags.py`를 먼저 실행하세요.")
        return

    # Coverage gauge row
    cols = st.columns(len(coverage))
    for col, (field, data) in zip(cols, coverage.items()):
        pct = data["coverage_pct"]
        color = "#10B981" if pct >= 80 else "#F59E0B" if pct >= 50 else "#EF4444"
        col.markdown(
            f"<div style='text-align:center'>"
            f"<div style='font-size:1.6rem;font-weight:bold;color:{color}'>{pct:.0f}%</div>"
            f"<div style='font-size:0.75rem;color:#6B7280'>{field}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Bar charts: 2 columns
    fields = list(coverage.items())
    for i in range(0, len(fields), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j >= len(fields):
                break
            field, data = fields[i + j]
            dist = data["distribution"]
            df = (
                pd.DataFrame({"값": list(dist.keys()), "클립 수": list(dist.values())})
                .sort_values("클립 수", ascending=True)
            )
            fig = px.bar(
                df, x="클립 수", y="값", orientation="h",
                title=f"{field}  ({data['coverage_pct']:.1f}% 커버리지)",
                color="클립 수",
                color_continuous_scale="Blues",
            )
            fig.update_layout(
                height=300, margin=dict(l=0, r=0, t=40, b=0),
                showlegend=False, coloraxis_showscale=False,
                yaxis_title="", xaxis_title="클립 수",
            )
            col.plotly_chart(fig, use_container_width=True)


# ── Tab 3: Distribution ────────────────────────────────────────────────────────
def tab_distribution():
    # Video popup trigger: set by play buttons, cleared here to prevent re-open loop
    trigger = st.session_state.get("video_trigger")
    if trigger:
        del st.session_state["video_trigger"]
        _video_popup(trigger)

    st.subheader("임베딩 공간 분포 시각화 (UMAP)")

    umap_df = load_umap()
    longtail = set(load_longtail())

    if umap_df is None:
        if DIST_HTML_PATH.exists():
            st.info("umap_coords.parquet 없음 — 사전 생성된 distribution.html을 표시합니다.")
            html = DIST_HTML_PATH.read_text(encoding="utf-8")
            st.components.v1.html(html, height=900, scrolling=True)
        else:
            st.warning("분포 데이터가 없습니다. `phase4/distribution_analysis.py`를 먼저 실행하세요.")
    else:
        # ── Controls ──
        col_color, col_filter, _ = st.columns([2, 2, 4])
        with col_color:
            color_by = st.selectbox(
                "색상 기준",
                ["density", "time_of_day", "weather", "road_type", "hazard_level", "longtail"],
            )
        with col_filter:
            if color_by in ODD_FIELDS:
                filter_val = st.multiselect(f"{color_by} 필터", ODD_FIELDS[color_by])
            else:
                filter_val = []

        df = umap_df.copy()
        if filter_val and color_by in df.columns:
            df = df[df[color_by].isin(filter_val)]

        df["longtail"] = df["clip_id"].isin(longtail).map({True: "long-tail", False: "normal"})

        if color_by == "density":
            fig = px.scatter(
                df, x="x", y="y", color="density",
                color_continuous_scale="Plasma",
                opacity=0.6, hover_data=["clip_id", "time_of_day", "weather", "road_type"],
                labels={"density": "밀도"},
                title="임베딩 밀도 분포 (높을수록 일반적인 시나리오)",
            )
        else:
            col = "longtail" if color_by == "longtail" else color_by
            color_map = {"long-tail": "#EF4444", "normal": "#6366F1"} if color_by == "longtail" else None
            fig = px.scatter(
                df, x="x", y="y", color=col,
                opacity=0.6,
                hover_data=["clip_id", "time_of_day", "weather", "road_type", "hazard_level"],
                color_discrete_map=color_map,
                title=f"{color_by} 별 클러스터 분포",
            )

        fig.update_traces(marker=dict(size=3))
        fig.update_layout(
            height=600,
            margin=dict(l=0, r=0, t=50, b=0),
            xaxis=dict(showticklabels=False, title=""),
            yaxis=dict(showticklabels=False, title=""),
            legend=dict(itemsizing="constant"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Pre-built full dashboard ──
        if DIST_HTML_PATH.exists():
            with st.expander("전체 대시보드 보기 (사전 생성된 HTML)"):
                html = DIST_HTML_PATH.read_text(encoding="utf-8")
                st.components.v1.html(html, height=900, scrolling=True)

    # ── Long-tail clips ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Long-tail 클립 목록")
    if not longtail:
        st.warning("Long-tail 데이터가 없습니다.")
    else:
        st.caption(f"밀도 하위 5% 클립 {len(longtail):,}개 — 행을 선택하면 영상을 재생할 수 있습니다.")
        lt_df = pd.DataFrame({"clip_id": list(longtail)})
        sel_lt = st.dataframe(
            lt_df,
            use_container_width=True,
            height=320,
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
            key="lt_sel",
        )
        if sel_lt.selection.rows:
            chosen_lt = lt_df.iloc[sel_lt.selection.rows[0]]["clip_id"]
            c1, c2 = st.columns([5, 1])
            c1.info(f"선택된 클립: `{chosen_lt}`")
            if c2.button("▶ 영상 재생", key="lt_play", type="primary", use_container_width=True):
                st.session_state["video_trigger"] = chosen_lt
                st.rerun()

    # ── SANFlow 갭 탐지 결과 ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("SANFlow 갭 탐지 결과 (Phase B)")

    gaps = load_gaps()
    if not gaps:
        st.warning("갭 데이터가 없습니다. `phase6/fit_sanflow.py`를 먼저 실행하세요.")
        return

    # Summary metrics
    noise_cnt = sum(1 for g in gaps if g["is_noise"])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("갭 후보", f"{len(gaps)}개")
    m2.metric("noise 갭 (새 시나리오)", f"{noise_cnt}개 ({noise_cnt/len(gaps)*100:.0f}%)")
    m3.metric("cluster-edge 갭", f"{len(gaps)-noise_cnt}개")
    m4.metric("log_density 범위", f"{min(g['log_density'] for g in gaps):.0f} ~ {max(g['log_density'] for g in gaps):.0f}")

    gap_df = pd.DataFrame([{
        "rank":         g["rank"],
        "clip_id":      g["clip_id"],
        "log_density":  round(g["log_density"], 1),
        "scenario":     g["scenario_name"],
        "유형":          "noise" if g["is_noise"] else "cluster-edge",
        "nearest_cluster": g["nearest_cluster"],
    } for g in gaps])

    # Distribution charts (2×2)
    densities = gap_df["log_density"].tolist()
    ch1, ch2 = st.columns(2)

    with ch1:
        fig_rank = go.Figure()
        fig_rank.add_trace(go.Scatter(
            x=gap_df["rank"], y=densities,
            mode="markers+lines",
            marker=dict(color=densities, colorscale="RdYlGn", size=6,
                        colorbar=dict(title="log p(x)", len=0.55, thickness=12)),
            line=dict(color="#d0d0d0", width=1),
            hovertemplate="Rank %{x}<br>log p(x): %{y:.0f}<extra></extra>",
        ))
        fig_rank.update_layout(
            title="Rank별 log_density (갭 심각도)",
            xaxis_title="Rank (1 = 가장 희귀)", yaxis_title="log p(x)",
            height=320, margin=dict(t=45, b=45, l=65, r=15),
            plot_bgcolor="#fafafa",
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    with ch2:
        sc = gap_df.groupby("scenario").size().reset_index(name="count").sort_values("count")
        fig_sc = px.bar(
            sc, x="count", y="scenario", orientation="h",
            title="시나리오별 갭 클립 수",
            color="count", color_continuous_scale="Reds",
            text="count",
        )
        fig_sc.update_traces(textposition="outside")
        fig_sc.update_layout(
            height=320, margin=dict(t=45, b=45, l=10, r=50),
            coloraxis_showscale=False, yaxis_title="",
        )
        st.plotly_chart(fig_sc, use_container_width=True)

    ch3, ch4 = st.columns([1, 2])

    with ch3:
        noise_counts = gap_df["유형"].value_counts().reset_index()
        noise_counts.columns = ["유형", "count"]
        fig_pie = px.pie(
            noise_counts, values="count", names="유형",
            title="갭 유형 분류",
            hole=0.45,
            color="유형",
            color_discrete_map={"noise": "#e74c3c", "cluster-edge": "#3498db"},
        )
        fig_pie.update_layout(height=320, margin=dict(t=45, b=10, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    with ch4:
        main_d  = [d for d in densities if d > -60000]
        out_d   = [d for d in densities if d <= -60000]
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(x=main_d,  nbinsx=30, name="일반 갭 (rank 2~200)",
                                        marker_color="#3b6fd4", opacity=0.75))
        fig_hist.add_trace(go.Histogram(x=out_d,   nbinsx=5,  name="극단 이상치 (rank 1)",
                                        marker_color="#e74c3c", opacity=0.85))
        fig_hist.update_layout(
            title="log_density 분포 히스토그램",
            barmode="overlay",
            xaxis_title="log p(x)", yaxis_title="클립 수",
            height=320, margin=dict(t=45, b=45, l=60, r=15),
            plot_bgcolor="#fafafa",
            legend=dict(x=0.55, y=0.95, font=dict(size=11)),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # Gap list with click-to-play
    st.caption("행을 선택하면 영상을 재생할 수 있습니다. rank 1이 가장 희귀한 시나리오입니다.")
    sel_gap = st.dataframe(
        gap_df,
        use_container_width=True,
        height=420,
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True,
        key="gap_sel",
        column_config={
            "rank":             st.column_config.NumberColumn("순위",    width="small"),
            "clip_id":          st.column_config.TextColumn("Clip ID",  width="medium"),
            "log_density":      st.column_config.NumberColumn("log p(x)", format="%.1f", width="small"),
            "scenario":         st.column_config.TextColumn("시나리오"),
            "유형":              st.column_config.TextColumn("유형",     width="small"),
            "nearest_cluster":  st.column_config.NumberColumn("클러스터", width="small"),
        },
    )
    if sel_gap.selection.rows:
        chosen_gap = gap_df.iloc[sel_gap.selection.rows[0]]["clip_id"]
        g1, g2 = st.columns([5, 1])
        g1.info(f"선택된 클립: `{chosen_gap}`")
        if g2.button("▶ 영상 재생", key="gap_play", type="primary", use_container_width=True):
            st.session_state["video_trigger"] = chosen_gap
            st.rerun()


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    st.title("🚗 AVdata Semantic Search")
    st.caption("자율주행 클립 83,612개에 대한 시나리오 시맨틱 검색")

    cfg = build_sidebar()

    tab1, tab2, tab3 = st.tabs(["🔍 검색", "📊 ODD 커버리지", "🗺️ 분포 시각화"])

    with tab1:
        tab_search(cfg)
    with tab2:
        tab_coverage()
    with tab3:
        tab_distribution()


if __name__ == "__main__":
    main()
