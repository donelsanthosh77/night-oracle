"""Night Oracle — web interface to SHOW how the system works (not a building block).

    streamlit run app.py

Needs llama-server running (see README). Everything stays on localhost.
"""
import json
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from oracle import agent, config, tools
from oracle.rules import RuleMemory

st.set_page_config(page_title="Night Oracle", page_icon="🍛", layout="wide")


# ---------- sidebar: what is connected ----------
def qwen_ok() -> bool:
    try:
        return requests.get(config.LLM_URL.split("/v1")[0] + "/health", timeout=1).ok
    except requests.RequestException:
        return False


@st.cache_data(show_spinner="Asking the MCP server for its tools…")
def mcp_tools() -> list[str]:
    from oracle import mcp_client
    return [s["function"]["name"] for s in mcp_client.list_schemas()]


with st.sidebar:
    st.header("Connections")
    st.write(("🟢" if qwen_ok() else "🔴") + " **Qwen3.5-4B** · llama.cpp · localhost:8080")
    try:
        st.write("🟢 **MCP server** · tools: " + ", ".join(mcp_tools()))
    except Exception as e:  # show the problem instead of crashing
        st.write(f"🔴 **MCP server** · {e}")

    st.header("Settings")
    use_tools = st.toggle("Give Qwen the tools", value=True,
                          help="Off = Qwen alone, like the 'model alone' benchmark")
    via_mcp = st.toggle("Call tools through MCP", value=True, disabled=not use_tools,
                        help="On: harness → MCP server → tool. Off: harness → tool directly.")
    guard = st.toggle("Number guard", value=True, disabled=not use_tools)

    st.header("House rules (memory)")
    rules = RuleMemory()
    for r in rules.rules:
        st.write(f"• {r['text']}  \n  _{r['source']}, {r['added']}_")
    if not rules.rules:
        st.caption("No rule saved yet. Try: “Owner says: Tuesday is quiet”.")
    st.caption(f"Cost: ~{rules.approx_tokens()} tokens added to every request")


# ---------- the chain, drawn ----------
def flow(active: set[str]) -> str:
    def node(name, label, shape="box"):
        color = "#f4a261" if name in active else "#e9ecef"
        return f'{name} [label="{label}", shape={shape}, style="rounded,filled", fillcolor="{color}"];'
    tool_edge = 'harness -> mcp -> tools;' if via_mcp else 'harness -> tools;'
    return f"""digraph {{ rankdir=LR; node [fontname="Helvetica", fontsize=11];
      {node("user", "You", "ellipse")} {node("harness", "Harness\\nagent.py\\nloop · max 6 steps")}
      {node("qwen", "Qwen3.5-4B\\n(local)")} {node("mcp", "MCP server\\nmcp_server.py")}
      {node("tools", "Tools\\npredict_night · stats\\nask_data · save_rule")}
      {node("guard", "Guard\\nno invented numbers")} {node("answer", "Answer", "ellipse")}
      user -> harness; harness -> qwen [dir=both, label="asks / tool calls"];
      {tool_edge if use_tools else ""}
      harness -> guard -> answer; }}"""


st.title("🍛 Night Oracle")
st.caption("A shift copilot for a 30-seat restaurant, built around a model we do not trust: "
           "Qwen chooses, our code computes, the guard checks.")

tab_chat, tab_model, tab_bench = st.tabs(["Ask", "Model & decision", "Benchmark"])

# ---------- tab 1: chat with the full trace ----------
with tab_chat:
    diagram = st.empty()
    diagram.graphviz_chart(flow(set()))
    st.caption("Try: “How busy is next Sunday with the biryani special?” · "
               "“Which day had the fewest guests in 2025?” · “Owner says: Tuesday is quiet”")

    if "history" not in st.session_state:
        st.session_state.history = []
    for h in st.session_state.history:
        st.chat_message("user").write(h["question"])
        st.chat_message("assistant").write(h["answer"])

    q = st.chat_input("Ask Night Oracle…")
    if q:
        st.chat_message("user").write(q)
        if not qwen_ok():
            st.error("Qwen is not running. Start llama-server first (see README).")
            st.stop()
        with st.spinner("Qwen is thinking…"):
            t = agent.ask(q, use_tools=use_tools, guard=guard, via_mcp=via_mcp and use_tools)
        st.chat_message("assistant").write(t["answer"])

        active = {"user", "harness", "qwen", "answer"}
        if t["steps"]:
            active |= {"tools"} | ({"mcp"} if via_mcp else set())
        if use_tools and guard:
            active.add("guard")
        diagram.graphviz_chart(flow(active))

        with st.expander("🔍 How this answer was made", expanded=True):
            st.markdown(f"**1. Question** → harness ({'tools via MCP' if t['via'] == 'mcp' else 'tools direct'})")
            for i, s in enumerate(t["steps"], start=2):
                st.markdown(f"**{i}. Qwen called `{s['tool']}`** "
                            f"({s.get('seconds', '?')} s, {'through MCP' if t['via'] == 'mcp' else 'direct'})")
                c1, c2 = st.columns(2)
                c1.caption("Arguments chosen by Qwen")
                c1.json(s["args"])
                c2.caption("Result computed by our code")
                c2.json(s["result"])
            if not t["steps"]:
                st.markdown("**2. No tool called** — Qwen answered alone.")
            if "guard_first_try" in t:
                bad = t["guard_first_try"]
                st.markdown("**Guard:** " + ("✅ every number comes from a tool" if not bad else
                            f"⚠️ invented numbers {bad} → Qwen had to rewrite"))
                if "blocked_answer" in t:
                    st.error(f"Blocked answer: {t['blocked_answer']}")
        st.session_state.history.append(t)

# ---------- tab 2: the model and the decision ----------
with tab_model:
    from oracle.decision import evaluate as decision_eval
    from oracle.model import evaluate as model_eval

    m = model_eval()
    c1, c2, c3 = st.columns(3)
    c1.metric("Model error (MAE)", f"{m['mae_model']} guests")
    c2.metric("Baseline error", f"{m['mae_baseline']} guests",
              delta=f"{m['mae_model'] - m['mae_baseline']:.2f}", delta_color="inverse")
    c3.metric("90% range covers", f"{m['interval_coverage_90']:.0%} of nights")
    st.subheader("What the model learned (guests added or removed)")
    eff = {k: v for k, v in m["effects_in_guests"].items() if k != "monday_base"}
    st.bar_chart(pd.Series(eff, name="guests"), horizontal=True)
    st.caption(f"Base: a plain Monday ≈ {m['effects_in_guests']['monday_base']} guests. "
               "Trained on everything before the last 12 weeks, tested on the last 12 weeks.")

    st.subheader("Decision: call the 3rd cook? (P(guests > 20) ≥ threshold)")
    conf = decision_eval()
    st.dataframe(pd.DataFrame(conf).T.rename_axis("threshold"), width="stretch")
    st.caption(f"Chosen threshold: {config.THIRD_COOK_THRESHOLD} — low on purpose: "
               "a missing cook costs more than one extra person.")

    st.subheader("Try the prediction tool directly")
    d = st.date_input("Night")
    cc1, cc2, cc3 = st.columns(3)
    w = cc1.selectbox("Weather", list(tools.WEATHER))
    rain = cc2.checkbox("Rain")
    bir = cc3.checkbox("Biryani special")
    st.json(tools.predict_night(d.isoformat(), rain, w, bir))

# ---------- tab 3: benchmark results ----------
with tab_bench:
    rows = []
    for f in sorted(Path("bench").glob("results*.json")):
        r = json.loads(f.read_text())
        for mode, v in r.items():
            rows.append({"file": f.name, "mode": mode, "mean": v["mean"], "std": v["std"],
                         "held_out": v.get("held_out", {}).get("mean")})
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch")
        st.caption("results.json = v1 (Qwen writes pandas) · results_v2 = stats tool · "
                   "results_v3 = + 5 held-out questions")
    else:
        st.info("No results yet: python -m bench.run_bench --runs 3")
