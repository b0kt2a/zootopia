import json
import random
from collections import Counter
from copy import deepcopy

import pandas as pd
import streamlit as st

st.set_page_config(page_title="ZOOTOPIA GM TOOL", page_icon="🎮", layout="wide")

REGIONS = ["숲", "강", "초원", "동굴"]
ROLES = ["양", "늑대", "여우", "벌", "양치기개", "거북이", "부엉이", "박쥐", "스컹크",]
PHASES = ["설정", "아침", "낮", "밤"]
ABILITY_ORDER = ["유령", "여우", "부엉이", "거북이", "늑대", "벌", "스컹크"]


def default_role_preset(player_count: int) -> dict:
    presets = {
        12: {"양": 4, "늑대": 2, "여우": 1, "벌": 1, "양치기개": 1, "거북이": 1, "부엉이": 1, "박쥐": 0, "스컹크": 1},
        13: {"양": 5, "늑대": 2, "여우": 1, "벌": 1, "양치기개": 1, "거북이": 1, "부엉이": 1, "박쥐": 0, "스컹크": 1},
        14: {"양": 5, "늑대": 3, "여우": 1, "벌": 1, "양치기개": 1, "거북이": 1, "부엉이": 1, "박쥐": 0, "스컹크": 1},
        15: {"양": 5, "늑대": 3, "여우": 1, "벌": 1, "양치기개": 1, "거북이": 1, "부엉이": 1, "박쥐": 1, "스컹크": 1},
        16: {"양": 6, "늑대": 3, "여우": 1, "벌": 1, "양치기개": 1, "거북이": 1, "부엉이": 1, "박쥐": 1, "스컹크": 1},
        17: {"양": 6, "늑대": 3, "여우": 2, "벌": 1, "양치기개": 1, "거북이": 1, "부엉이": 1, "박쥐": 1, "스컹크": 1},
        18: {"양": 6, "늑대": 4, "여우": 2, "벌": 1, "양치기개": 1, "거북이": 1, "부엉이": 1, "박쥐": 1, "스컹크": 1},
        19: {"양": 7, "늑대": 4, "여우": 2, "벌": 1, "양치기개": 1, "거북이": 1, "부엉이": 1, "박쥐": 1, "스컹크": 1},
        20: {"양": 7, "늑대": 4, "여우": 2, "벌": 2, "양치기개": 1, "거북이": 1, "부엉이": 1, "박쥐": 1, "스컹크": 1},
        21: {"양": 8, "늑대": 4, "여우": 2, "벌": 2, "양치기개": 1, "거북이": 1, "부엉이": 1, "박쥐": 1, "스컹크": 1},
        22: {"양": 8, "늑대": 5, "여우": 2, "벌": 2, "양치기개": 1, "거북이": 1, "부엉이": 1, "박쥐": 1, "스컹크": 1},
        23: {"양": 9, "늑대": 5, "여우": 2, "벌": 2, "양치기개": 1, "거북이": 1, "부엉이": 1, "박쥐": 1, "스컹크": 1},
        24: {"양": 9, "늑대": 5, "여우": 2, "벌": 2, "양치기개": 1, "거북이": 2, "부엉이": 1, "박쥐": 1, "스컹크": 1},
        25: {"양": 10, "늑대": 5, "여우": 2, "벌": 2, "양치기개": 1, "거북이": 2, "부엉이": 1, "박쥐": 1, "스컹크": 1},
    }
    return deepcopy(presets[player_count])


def players_template(player_count: int) -> pd.DataFrame:
    preset = default_role_preset(player_count)
    roles = []
    for role in ROLES:
        roles.extend([role] * preset.get(role, 0))
    roles = roles[:player_count]
    if len(roles) < player_count:
        roles.extend(["양"] * (player_count - len(roles)))
    rows = []
    for i in range(player_count):
        role = roles[i]
        rows.append({
            "id": i + 1,
            "이름": f"플레이어{i+1}",
            "역할": role,
            "원래역할": role,
            "생존": True,
            "현재지역": None,
            "메모": "",
            "사망사유": "",
            "보호종료라운드": 0,
        })
    return pd.DataFrame(rows)


def init_state():
    ss = st.session_state
    if "current_menu" not in ss:
        ss.current_menu = "설정"
    if "player_count" not in ss:
        ss.player_count = 12
    if "players_df" not in ss:
        ss.players_df = players_template(ss.player_count)
    if "round_no" not in ss:
        ss.round_no = 1
    if "phase" not in ss:
        ss.phase = "설정"
    if "logs" not in ss:
        ss.logs = []
    if "vote_history" not in ss:
        ss.vote_history = []
    if "night_results" not in ss:
        ss.night_results = {}
    if "snapshots" not in ss:
        ss.snapshots = []
    if "sealed_region" not in ss:
        ss.sealed_region = "없음"
    if "pending_deaths" not in ss:
        ss.pending_deaths = []    
    if "pending_sealed_region" not in ss:
        ss.pending_sealed_region = "없음"
    if "last_wolf_targets" not in ss:
        ss.last_wolf_targets = {}
    if "last_vote_summary" not in ss:
        ss.last_vote_summary = None
    if "round_summary" not in ss:
        ss.round_summary = {}
    if "sidebar_player_count" not in ss:
        ss.sidebar_player_count = int(ss.player_count)
    if "turtle_protect_map" not in ss:
        ss.turtle_protect_map = {}


def snapshot(label: str):
    st.session_state.snapshots.insert(0, {
        "label": label,
        "round_no": st.session_state.round_no,
        "phase": st.session_state.phase,
        "player_count": st.session_state.player_count,
        "players": st.session_state.players_df.to_dict(orient="records"),
        "logs": deepcopy(st.session_state.logs),
        "vote_history": deepcopy(st.session_state.vote_history),
        "night_results": deepcopy(st.session_state.night_results),
        "sealed_region": st.session_state.sealed_region,
        "pending_sealed_region": st.session_state.pending_sealed_region,
        "last_wolf_targets": deepcopy(st.session_state.last_wolf_targets),
        "last_vote_summary": deepcopy(st.session_state.last_vote_summary),
        "round_summary": deepcopy(st.session_state.round_summary),
        "current_menu": st.session_state.current_menu,
        "pending_deaths": deepcopy(st.session_state.pending_deaths),
        "turtle_protect_map": deepcopy(st.session_state.turtle_protect_map),
    })


def add_log(phase: str, message: str):
    st.session_state.logs.insert(0, {"round": st.session_state.round_no, "phase": phase, "message": message})


def label_for(name: str) -> str:
    df = st.session_state.players_df
    row = df[df["이름"] == name]
    if row.empty:
        return name
    r = row.iloc[0]
    shown_role = r["원래역할"] if not bool(r["생존"]) else r["역할"]
    return f"{r['이름']} ({shown_role})"


def alive_df() -> pd.DataFrame:
    return st.session_state.players_df[st.session_state.players_df["생존"] == True].copy()


def dead_df() -> pd.DataFrame:
    return st.session_state.players_df[st.session_state.players_df["생존"] == False].copy()


def get_row(name: str):
    df = st.session_state.players_df
    row = df[df["이름"] == name]
    return None if row.empty else row.iloc[0]


def protected_names() -> list[str]:
    df = st.session_state.players_df
    return df[(df["생존"] == True) & (df["보호종료라운드"] >= st.session_state.round_no)]["이름"].tolist()


def replace_player_count(new_count: int):
    st.session_state.player_count = int(new_count)
    st.session_state.players_df = players_template(int(new_count))
    st.session_state.round_no = 1
    st.session_state.phase = "설정"
    st.session_state.logs = []
    st.session_state.vote_history = []
    st.session_state.night_results = {}
    st.session_state.snapshots = []
    st.session_state.sealed_region = "없음"
    st.session_state.pending_sealed_region = "없음"
    st.session_state.last_wolf_targets = {}
    st.session_state.last_vote_summary = None
    st.session_state.round_summary = {}
    st.session_state.turtle_protect_map = {}
    st.session_state.pending_deaths = []
    st.session_state.current_menu = "설정"


def kill_player(name: str, reason: str):
    df = st.session_state.players_df
    idx = df.index[df["이름"] == name].tolist()
    if not idx:
        return
    i = idx[0]
    if not bool(df.loc[i, "생존"]):
        return
    original_role = str(df.loc[i, "역할"])
    df.loc[i, "생존"] = False
    df.loc[i, "사망사유"] = f"{name}({original_role}) - {reason}"
    df.loc[i, "역할"] = "유령"

def queue_death(name: str, reason: str):
    if "pending_deaths" not in ss:
        ss.pending_deaths = []

    already = [d["name"] for d in ss.pending_deaths]
    if name not in already:
        ss.pending_deaths.append({"name": name, "reason": reason})

def update_region(name: str, region: str):
    df = st.session_state.players_df
    idx = df.index[df["이름"] == name].tolist()
    if idx:
        df.loc[idx[0], "현재지역"] = region


def apply_pending_seal_if_needed():
    st.session_state.sealed_region = st.session_state.pending_sealed_region
    st.session_state.pending_sealed_region = "없음"


def actor_is_sealed(actor_name: str) -> bool:
    if st.session_state.sealed_region == "없음":
        return False
    row = get_row(actor_name)
    return row is not None and row["현재지역"] == st.session_state.sealed_region


def same_region_candidates(actor_name: str, exclude_names=None, exclude_roles=None, alive_only=True) -> list[str]:
    exclude_names = set(exclude_names or [])
    exclude_roles = set(exclude_roles or [])
    row = get_row(actor_name)
    if row is None:
        return []
    df = st.session_state.players_df.copy()
    if alive_only:
        df = df[df["생존"] == True]
    df = df[df["현재지역"] == row["현재지역"]]
    df = df[~df["이름"].isin(exclude_names)]
    df = df[~df["역할"].isin(exclude_roles)]
    return df["이름"].tolist()


def record_result(key: str, message: str):
    st.session_state.night_results[key] = message


def add_round_summary(message: str):
    summary = st.session_state.round_summary
    key = f"R{st.session_state.round_no}-{st.session_state.phase}"
    summary.setdefault(key, [])
    summary[key].append(message)


def get_result(key: str):
    return st.session_state.night_results.get(key, "")


def save_json_payload():
    return {
        "player_count": st.session_state.player_count,
        "round_no": st.session_state.round_no,
        "phase": st.session_state.phase,
        "players": st.session_state.players_df.to_dict(orient="records"),
        "logs": st.session_state.logs,
        "vote_history": st.session_state.vote_history,
        "night_results": st.session_state.night_results,
        "snapshots": st.session_state.snapshots,
        "sealed_region": st.session_state.sealed_region,
        "pending_sealed_region": st.session_state.pending_sealed_region,
        "last_wolf_targets": st.session_state.last_wolf_targets,
        "last_vote_summary": st.session_state.last_vote_summary,
        "round_summary": st.session_state.round_summary,
        "current_menu": st.session_state.current_menu,
        "pending_deaths": st.session_state.pending_deaths,
        "turtle_protect_map": st.session_state.turtle_protect_map,
    }


init_state()
ss = st.session_state

# Sidebar
st.sidebar.header("게임 컨트롤")
def on_sidebar_player_count_change():
    st.session_state.player_count = int(st.session_state.sidebar_player_count)

st.sidebar.number_input(
    "플레이어 수",
    min_value=12,
    max_value=25,
    step=1,
    key="sidebar_player_count",
    on_change=on_sidebar_player_count_change,
)
sidebar_count = int(st.session_state.sidebar_player_count)

c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("새 게임", use_container_width=True):
        replace_player_count(sidebar_count)
        add_log("설정", f"새 게임 시작: {sidebar_count}명")
        st.rerun()
with c2:
    if st.button("스냅샷 저장", use_container_width=True):
        snapshot("수동 저장")
        st.sidebar.success("저장 완료")

st.sidebar.markdown("---")
st.sidebar.write(f"**현재 라운드:** {ss.round_no}")
st.sidebar.write(f"**현재 단계:** {ss.current_menu}")
st.sidebar.write(f"**봉인지역:** {ss.sealed_region}")
prot = protected_names()
st.sidebar.write("**보호 멤버:** " + (", ".join([label_for(n) for n in prot]) if prot else "없음"))
st.sidebar.write("**발동 순서**")
for i, role in enumerate(ABILITY_ORDER, 1):
    st.sidebar.write(f"{i}. {role}")

n1, n2 = st.sidebar.columns(2)

MENU_FLOW = ["설정", "아침", "낮", "밤"]

with n1:
    if st.button("이전 단계", use_container_width=True):
        if ss.current_menu in MENU_FLOW:
            idx = MENU_FLOW.index(ss.current_menu)
            if idx > 0:
                ss.current_menu = MENU_FLOW[idx - 1]
                ss.phase = ss.current_menu
        st.rerun()

with n2:
    if st.button("다음 단계", use_container_width=True):
        if ss.current_menu in MENU_FLOW:
            idx = MENU_FLOW.index(ss.current_menu)
            if idx < len(MENU_FLOW) - 1:
                ss.current_menu = MENU_FLOW[idx + 1]
                ss.phase = ss.current_menu
        st.rerun()

with st.sidebar.expander("데이터 내보내기/불러오기"):
    st.caption("현재 게임 상태를 JSON으로 저장/복구")
    st.download_button("JSON 백업 다운로드", data=json.dumps(save_json_payload(), ensure_ascii=False, indent=2), file_name="gm_tool_backup.json", mime="application/json")
    up = st.file_uploader("JSON 백업 불러오기", type=["json"])
    if up is not None:
        data = json.load(up)
        ss.player_count = int(data.get("player_count", 12))
        ss.players_df = pd.DataFrame(data.get("players", players_template(ss.player_count).to_dict(orient="records")))
        ss.round_no = int(data.get("round_no", 1))
        ss.phase = data.get("phase", "설정")
        ss.logs = data.get("logs", [])
        ss.vote_history = data.get("vote_history", [])
        ss.night_results = data.get("night_results", {})
        ss.snapshots = data.get("snapshots", [])
        ss.sealed_region = data.get("sealed_region", "없음")
        ss.pending_sealed_region = data.get("pending_sealed_region", "없음")
        ss.last_wolf_targets = data.get("last_wolf_targets", {})
        ss.last_vote_summary = data.get("last_vote_summary", None)
        ss.round_summary = data.get("round_summary", {})
        ss.current_menu = data.get("current_menu", ss.phase)
        ss.pending_deaths = data.get("pending_deaths", [])
        ss.turtle_protect_map = data.get("turtle_protect_map", {})
        st.success("불러오기 완료")
        st.rerun()

st.title("🎮ZOOTOPIA GM TOOL")
if "current_menu" not in ss:
    ss.current_menu = "설정"

menu_options = ["설정", "대시보드", "아침", "낮", "밤", "로그/기록"]

menu = st.radio(
    "",
    menu_options,
    horizontal=True,
    index=menu_options.index(ss.current_menu),
)

if menu != ss.current_menu:
    ss.current_menu = menu
    ss.phase = ss.current_menu
    st.rerun()

if ss.current_menu == "설정":
    st.header("⚙️ 설정")
    preset = default_role_preset(ss.player_count)
    st.subheader("역할 추천값")
    with st.form(f"role_form_{ss.player_count}"):
        cols = st.columns(5)
        role_inputs = {}
        for i, role in enumerate(ROLES):
            with cols[i % 5]:
                role_inputs[role] = st.number_input(role, min_value=0, max_value=ss.player_count, value=int(preset.get(role, 0)), step=1)
        total = sum(role_inputs.values())
        st.info(f"현재 역할 합계는 {total}명. 플레이어 수 {ss.player_count}명과 같아야 자동 배정 가능")
        if st.form_submit_button("추천 역할로 플레이어 목록 재구성", use_container_width=True):
            if total != ss.player_count:
                st.error("역할 합계를 플레이어 수와 맞춰줘.")
            else:
                roles = []
                for r in ROLES:
                    roles.extend([r] * int(role_inputs[r]))
                df = ss.players_df.copy()
                if len(df) != ss.player_count:
                    df = players_template(ss.player_count)
                df = df.iloc[:ss.player_count].copy().reset_index(drop=True)
                for i, role in enumerate(roles):
                    df.loc[i, "역할"] = role
                    df.loc[i, "원래역할"] = role
                ss.players_df = df
                add_log("설정", "역할 추천값 적용")
                st.success("재구성 완료")
                st.rerun()

    st.markdown("---")

    with st.form("players_form"):
        edited = st.data_editor(
            ss.players_df,
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("id", disabled=True),
                "이름": st.column_config.TextColumn("이름", required=True),
                "역할": st.column_config.TextColumn("역할", disabled=True),
                "원래역할": st.column_config.TextColumn("원래역할", disabled=True),
                "생존": st.column_config.CheckboxColumn("생존", disabled=True),
                "현재지역": st.column_config.SelectboxColumn("현재지역", options=REGIONS),
                "메모": st.column_config.TextColumn("메모", disabled=True),
                "사망사유": st.column_config.TextColumn("사망사유", disabled=True),
                "보호종료라운드": st.column_config.NumberColumn("보호종료라운드", disabled=True),
            },
            key="players_editor_new"
        )

        c1, c2 = st.columns(2)

        with c1:
            save_clicked = st.form_submit_button("명단 저장", use_container_width=True)

        with c2:
            move_clicked = st.form_submit_button("아침 단계로 이동", use_container_width=True)

    if save_clicked:
        ss.players_df = edited.copy()
        add_log("설정", "플레이어 명단 저장")
        st.success("저장 완료")
        st.rerun()

    if move_clicked:
        ss.players_df = edited.copy()
        ss.current_menu = "아침"
        ss.phase = ss.current_menu
        snapshot("게임 시작")
        st.rerun()

elif ss.current_menu == "대시보드":
    st.header("대시보드")
    adf = alive_df()
    ddf = dead_df()
    cols = st.columns(4)
    for col, region in zip(cols, REGIONS):
        with col:
            st.metric(region, int((adf["현재지역"] == region).sum()))
    st.subheader("지역별 플레이어")
    cols = st.columns(4)
    for col, region in zip(cols, REGIONS):
        with col:
            names = [label_for(n) for n in adf.loc[adf["현재지역"] == region, "이름"].tolist()]
            st.write(f"**{region}**")
            if names:
                for name in names:
                    st.write(f"- {name}")
            else:
                st.caption("없음")
    st.subheader("사망자")
    if ddf.empty:
        st.info("사망자 없음")
    else:
        st.dataframe(ddf[["이름", "원래역할", "현재지역", "사망사유"]], use_container_width=True, hide_index=True)

elif ss.current_menu == "아침":
    st.header("아침: 지역 이동")
    st.info(f"현재 봉인지역: {ss.sealed_region}")
    adf = alive_df()

    if adf.empty:
        st.info("생존자 없음")
    else:
        with st.form(f"morning_move_form_{ss.round_no}"):
            move_map = {}
            cols = st.columns(2)

            for i, name in enumerate(adf["이름"].tolist()):
                row = get_row(name)
                with cols[i % 2]:
                    move_map[name] = st.selectbox(
                        f"{label_for(name)} 이동",
                        REGIONS,
                        index=REGIONS.index(row["현재지역"]),
                        key=f"move_{name}_{ss.round_no}"
                    )

            c1, c2 = st.columns(2)
            with c1:
                save_clicked = st.form_submit_button("아침 이동 저장", use_container_width=True)
            with c2:
                day_clicked = st.form_submit_button("낮 단계로 이동", use_container_width=True)

        if save_clicked:
            for name, region in move_map.items():
                update_region(name, region)
            add_log("아침", "이동 저장")
            st.success("저장 완료")
            st.rerun()

        if day_clicked:
            for name, region in move_map.items():
                update_region(name, region)
            add_log("아침", "이동 저장 후 낮 단계로 이동")
            ss.current_menu = "낮"
            ss.phase = ss.current_menu
            st.rerun()  
                

elif ss.current_menu == "낮":
    st.header("낮: 양 투표")
    adf = alive_df()
    sheep_df = adf[adf["원래역할"] == "양"].copy()
    sheep_counts = sheep_df["현재지역"].value_counts().reindex(REGIONS, fill_value=0)
    max_count = int(sheep_counts.max()) if len(sheep_counts) else 0
    top_regions = [r for r, c in sheep_counts.items() if c == max_count and c > 0]
    if len(top_regions) != 1:
        st.warning("양 수 동률로 투표 없음")
        if top_regions:
            st.write("동률 지역: " + ", ".join(top_regions))
        if ss.last_vote_summary:
            st.info(ss.last_vote_summary)
        if st.button("밤 단계로 이동", use_container_width=True):
            ss.current_menu = "밤"
            ss.phase = ss.current_menu
            st.rerun()
    else:
        vote_region = top_regions[0]
        voters = sheep_df[sheep_df["현재지역"] == vote_region]["이름"].tolist()
        candidates = adf[adf["현재지역"] == vote_region]["이름"].tolist()
        st.info(f"양이 가장 많은 지역: {vote_region}")
        st.info("투표할 양: " + ", ".join([label_for(n) for n in voters]) if voters else "없음")
        with st.form(f"day_vote_form_{ss.round_no}"):
            vote_map = {}
            cols = st.columns(2)
            for i, voter in enumerate(voters):
                opts = [c for c in candidates if c != voter]
                if not opts:
                    opts = [voter]
                with cols[i % 2]:
                    vote_map[voter] = st.selectbox(f"{label_for(voter)}의 투표", options=opts, format_func=label_for, key=f"vote_{voter}_{ss.round_no}")
            c1, c2 = st.columns(2)
            submitted = c1.form_submit_button("투표 집계", use_container_width=True)
            move_night = c2.form_submit_button("밤 단계로 이동", use_container_width=True)
            if submitted:
                counter = Counter(vote_map.values())
                if counter:
                    max_votes = max(counter.values())
                    top = [n for n, v in counter.items() if v == max_votes]
                    if len(top) == 1:
                        target = top[0]
                        kill_player(target, "낮 투표 처형")
                        summary = f"가장 많은 득표자 - {label_for(target)} 처형"
                    else:
                        summary = "투표 결과 동률 - 아무 일도 일어나지 않음"
                    ss.last_vote_summary = summary
                    ss.vote_history.insert(0, {"round": ss.round_no, "region": vote_region, "votes": dict(counter), "summary": summary})
                    add_log("낮", summary)
                    st.rerun()
            if move_night:
                ss.current_menu = "밤"
                ss.phase = ss.current_menu
                st.rerun()
        if ss.last_vote_summary:
            st.success(ss.last_vote_summary)
        if ss.vote_history:
            latest = ss.vote_history[0]
            st.subheader("최근 투표 결과")
            rdf = pd.DataFrame([{"대상": label_for(k), "득표수": v} for k, v in latest["votes"].items()]).sort_values(["득표수", "대상"], ascending=[False, True])
            st.dataframe(rdf, use_container_width=True, hide_index=True)

elif ss.current_menu == "밤":
    st.header("밤")
    adf = alive_df()
    dead = dead_df()
    # 유령
    with st.expander("유령 단계", expanded=True):
        ghost_count = 1 if len(dead) > 0 else 0
        if ghost_count == 0:
            st.info("사용 가능한 유령 없음")
        else:
            for idx in range(ghost_count):
                key = f"유령_{ss.round_no}_{idx}"
                st.markdown(f"**유령 행동 #{idx+1}**")
                target_opts = adf["이름"].tolist()
                cols = st.columns(2)
                target = cols[0].selectbox("대상자1", options=target_opts, format_func=label_for, key=f"ghost_target_{key}")
                region = cols[1].selectbox("이동지역1", options=REGIONS, key=f"ghost_region_{key}")
                if st.button("유령 액션 저장", key=f"ghost_save_{key}"):
                    update_region(target, region)
                    msg = f"{label_for(target)} -> {region} 이동"
                    record_result(key, msg)
                    add_log("밤", f"유령: {msg}")
                    st.rerun()
                if get_result(key):
                    st.success(get_result(key))

    def role_cards(role: str):
        if role == "유령":
            return

        if role == "벌":
            with st.expander("벌 단계", expanded=False):
                interactions = []
                for wolf_name, target_name in ss.last_wolf_targets.items():
                    target_row = get_row(target_name)
                    if target_row is None:
                        continue
                    target_original = target_row["원래역할"] if pd.notna(target_row["원래역할"]) else target_row["역할"]
                    if target_original == "벌":
                        interactions.append((wolf_name, target_name))

                if not interactions:
                    st.info("표시할 플레이어 없음.")
                else:
                    for idx, (wolf_name, bee_name) in enumerate(interactions, 1):
                        st.markdown(f"**벌 행동 #{idx}**")
                        st.caption(f"지목한 늑대: {label_for(wolf_name)}")
                        st.caption(f"반격한 벌: {label_for(bee_name)}")
                        st.success(f"{label_for(bee_name)} / {label_for(wolf_name)} - 벌의 반격으로 늑대와 함께 사망")
            return

        actors = adf[adf["역할"] == role]["이름"].tolist()
        with st.expander(f"{role} 단계", expanded=(role == "여우")):
            if not actors:
                st.info(f"생존한 {role} 없음")
                return

            for idx, actor in enumerate(actors):
                key = f"{role}_{ss.round_no}_{idx}"
                st.markdown(f"**{role} 행동 #{idx+1}**")
                st.caption(f"행동자: {label_for(actor)}")

                if actor_is_sealed(actor):
                    msg = f"봉인지역 ({ss.sealed_region})이라서 능력 발동 안됨"
                    st.warning(msg)
                    record_result(key, msg)
                    add_log("밤", f"{label_for(actor)} 봉인지역 무효")
                    add_round_summary(f"{role}: {label_for(actor)} 봉인지역으로 무효")
                    continue

                if role == "여우":
                    opts1 = [n for n in adf[~adf["역할"].isin(["여우"])]["이름"].tolist() if n != actor]
                    if len(opts1) < 2:
                        st.info("표시할 플레이어 없음.")
                    else:
                        t1 = st.selectbox("대상1", options=opts1, format_func=label_for, key=f"fox_t1_{key}")
                        opts2 = [n for n in opts1 if n != t1]
                        t2 = st.selectbox("대상2", options=opts2, format_func=label_for, key=f"fox_t2_{key}")
                        if st.button("여우 액션 저장", key=f"save_{key}"):
                            r1 = get_row(t1)["현재지역"]
                            r2 = get_row(t2)["현재지역"]
                            update_region(t1, r2)
                            update_region(t2, r1)
                            msg = f"{label_for(t1)} / {r1}, {label_for(t2)} / {r2} -> {label_for(t1)} / {r2}, {label_for(t2)} / {r1}"
                            record_result(key, msg)
                            add_log("밤", f"여우: {msg}")
                            add_round_summary(f"여우: {label_for(t1)} / {r1} ↔ {label_for(t2)} / {r2}")
                            st.rerun()

                elif role == "부엉이":
                    opts = same_region_candidates(actor, exclude_names=[actor], exclude_roles=["부엉이"])
                    if not opts:
                        st.info("표시할 플레이어 없음.")
                        if st.button("부엉이 액션 저장", key=f"save_{key}"):
                            record_result(key, "표시할 플레이어 없음.")
                            add_round_summary("부엉이: 표시할 플레이어 없음")
                            st.rerun()
                    else:
                        t1 = st.selectbox("대상1", options=opts, format_func=label_for, key=f"owl_t1_{key}")
                        if st.button("부엉이 액션 저장", key=f"save_{key}"):
                            row = get_row(t1)
                            shown = row["원래역할"] if not bool(row["생존"]) else row["역할"]
                            if shown == "박쥐":
                                shown = random.choice(["양", "늑대", "여우", "거북이"])
                            msg = f"{row['이름']} - {shown}"
                            record_result(key, msg)
                            add_log("밤", f"부엉이: {msg}")
                            add_round_summary(f"부엉이: {label_for(t1)} 확인 결과 = {shown}")
                            st.rerun()

                elif role == "거북이":
                    opts = same_region_candidates(actor, exclude_names=[], exclude_roles=[])
                    if not opts:
                        st.info("표시할 플레이어 없음.")
                    else:
                        current_target = ss.turtle_protect_map.get(actor)
                        if current_target:
                            st.caption(f"현재 보호 대상: {label_for(current_target)}")
                        t1 = st.selectbox("대상1", options=opts, format_func=label_for, key=f"turtle_t1_{key}")
                        if st.button("거북이 액션 저장", key=f"save_{key}"):
                            old_target = ss.turtle_protect_map.get(actor)
                            if old_target and old_target != t1:
                                other_targets = [v for k, v in ss.turtle_protect_map.items() if k != actor]
                                if old_target not in other_targets:
                                    old_idx = ss.players_df.index[ss.players_df["이름"] == old_target].tolist()
                                    if old_idx:
                                        ss.players_df.loc[old_idx[0], "보호종료라운드"] = 0

                            ss.turtle_protect_map[actor] = t1
                            idxr = ss.players_df.index[ss.players_df["이름"] == t1][0]
                            ss.players_df.loc[idxr, "보호종료라운드"] = ss.round_no + 1

                            if old_target and old_target != t1:
                                msg = f"{label_for(old_target)} 보호 해제, {label_for(t1)} - 새 보호"
                                add_round_summary(f"거북이: {label_for(actor)} 보호 대상 변경 {label_for(old_target)} → {label_for(t1)}")
                            else:
                                msg = f"{label_for(t1)} - 보호"
                                add_round_summary(f"거북이: {label_for(t1)} 보호")

                            record_result(key, msg)
                            add_log("밤", f"거북이: {msg}")
                            st.rerun()

                elif role == "늑대":
                    opts = same_region_candidates(actor)
                    if not opts:
                        st.info("표시할 플레이어 없음.")
                    else:
                        t1 = st.selectbox("대상1", options=opts, format_func=label_for, key=f"wolf_t1_{key}")
                        if st.button("늑대 액션 저장", key=f"save_{key}"):
                            ss.last_wolf_targets[actor] = t1
                            target_row = get_row(t1)
                            target_original = target_row["원래역할"] if pd.notna(target_row["원래역할"]) else target_row["역할"]

                            if target_original == "늑대":
                                msg = f"{label_for(t1)} - 늑대가 늑대를 선택해서 아무 일도 일어나지 않음"
                                add_round_summary(f"늑대: {label_for(actor)} 가 {label_for(t1)} 선택, 아무 일도 일어나지 않음")
                            elif t1 in protected_names():
                                msg = f"{label_for(t1)} - 보호 상태라 아무 일도 일어나지 않음"
                                add_round_summary(f"늑대: {label_for(actor)} 가 {label_for(t1)} 공격, 보호로 무효")
                            elif target_original == "벌":
                                queue_death(t1, f"{label_for(actor)} 공격")
                                queue_death(actor, f"{label_for(t1)} 반격")
                                msg = f"{label_for(t1)} / {label_for(actor)} - 벌의 반격으로 늑대 함께 사망"
                                add_round_summary(f"늑대/벌: {label_for(actor)} 와 {label_for(t1)} 함께 사망")
                            else:
                                queue_death(t1, f"{label_for(actor)} 공격")
                                msg = f"{label_for(t1)} - 사망"
                                add_round_summary(f"늑대: {label_for(actor)} 가 {label_for(t1)} 공격")

                            record_result(key, msg)
                            add_log("밤", f"늑대: {msg}")
                            st.rerun()

                elif role == "스컹크":
                    region = st.selectbox("지역선택", options=REGIONS, key=f"skunk_region_{key}")
                    if st.button("스컹크 액션 저장", key=f"save_{key}"):
                        ss.pending_sealed_region = region
                        msg = f"다음 라운드 봉인지역: {region}"
                        record_result(key, msg)
                        add_log("밤", f"스컹크: {msg}")
                        add_round_summary(f"스컹크: 다음 라운드 봉인지역 = {region}")
                        st.rerun()

                if get_result(key):
                    st.success(get_result(key))

    for role in ["여우", "부엉이", "거북이", "늑대", "벌", "스컹크"]:
        role_cards(role)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("밤 결과 저장", use_container_width=True):
            st.success("저장 완료")
    with c2:
        if st.button("다음 라운드로 이동", use_container_width=True):
            for death in ss.pending_deaths:
                kill_player(death["name"], death["reason"])
            apply_pending_seal_if_needed()
            ss.night_results = {}
            ss.last_wolf_targets = {}
            ss.pending_deaths = []
            ss.round_no += 1
            ss.current_menu = "아침"
            ss.phase = ss.current_menu
            st.rerun()

elif ss.current_menu == "로그/기록":
    st.header("로그 / 기록")
    if ss.logs:
        st.dataframe(pd.DataFrame(ss.logs), use_container_width=True, hide_index=True)
    else:
        st.info("로그 없음")
    st.subheader("스냅샷")
    if not ss.snapshots:
        st.info("스냅샷 없음")
    else:
        for i, item in enumerate(ss.snapshots):
            c1, c2 = st.columns([3, 1])
            c1.write(f"{i+1}. {item['label']} (R{item['round_no']} / {item.get('current_menu', item['phase'])})")
            if c2.button("복원", key=f"restore_{i}"):
                ss.player_count = item["player_count"]
                ss.players_df = pd.DataFrame(item["players"])
                ss.round_no = item["round_no"]
                ss.phase = item["phase"]
                ss.logs = item["logs"]
                ss.vote_history = item["vote_history"]
                ss.night_results = item["night_results"]
                ss.sealed_region = item["sealed_region"]
                ss.pending_sealed_region = item["pending_sealed_region"]
                ss.last_wolf_targets = item["last_wolf_targets"]
                ss.last_vote_summary = item["last_vote_summary"]
                ss.round_summary = item.get("round_summary", {})
                ss.current_menu = item.get("current_menu", item["phase"])
                ss.sidebar_player_count = int(ss.player_count)
                ss.pending_deaths = item.get("pending_deaths", [])
                ss.turtle_protect_map = item.get("turtle_protect_map", {})
                st.rerun()
