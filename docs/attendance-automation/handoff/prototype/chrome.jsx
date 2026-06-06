/* chrome.jsx — Windows 11 title bar + phase stepper toolbar */

function WinControls() {
  const btn = { width: 46, height: 34, display: "grid", placeItems: "center", border: "none", background: "transparent", color: "var(--ink-2)" };
  return (
    <div style={{ display: "flex", WebkitAppRegion: "no-drag" }}>
      <button style={btn} title="最小化" onMouseEnter={e=>e.currentTarget.style.background="color-mix(in srgb, var(--ink-3) 18%, transparent)"} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
        <svg width="11" height="11" viewBox="0 0 11 11"><path d="M1 5.5h9" stroke="currentColor" strokeWidth="1"/></svg>
      </button>
      <button style={btn} title="最大化" onMouseEnter={e=>e.currentTarget.style.background="color-mix(in srgb, var(--ink-3) 18%, transparent)"} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
        <svg width="11" height="11" viewBox="0 0 11 11"><rect x="1" y="1" width="9" height="9" rx="1.4" fill="none" stroke="currentColor" strokeWidth="1"/></svg>
      </button>
      <button style={{...btn}} title="关闭"
        onMouseEnter={e=>{e.currentTarget.style.background="#d92d20";e.currentTarget.style.color="#fff";}}
        onMouseLeave={e=>{e.currentTarget.style.background="transparent";e.currentTarget.style.color="var(--ink-2)";}}>
        <svg width="11" height="11" viewBox="0 0 11 11"><path d="M1 1l9 9M10 1l-9 9" stroke="currentColor" strokeWidth="1"/></svg>
      </button>
    </div>
  );
}

function TitleBar() {
  return (
    <div style={{
      height: 34, flex: "0 0 34px", display: "flex", alignItems: "center",
      justifyContent: "space-between", background: "var(--surface)",
      borderBottom: "1px solid var(--line)", WebkitAppRegion: "drag", userSelect: "none",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, paddingLeft: 12 }}>
        <span style={{ width: 18, height: 18, borderRadius: 5, background: "linear-gradient(180deg,#52617a,#2f3b4f)", display: "grid", placeItems: "center", boxShadow: "0 1px 2px rgba(15,23,42,.25)" }}>
          <svg width="18" height="18" viewBox="0 0 512 512">
            {/* simplified grid-check: 3 white check cells + accents, matches App icon A */}
            <rect x="118" y="300" width="64" height="64" rx="15" fill="#fff"/>
            <rect x="224" y="224" width="64" height="64" rx="15" fill="#fff"/>
            <rect x="330" y="138" width="64" height="64" rx="15" fill="#fff"/>
            <rect x="118" y="138" width="64" height="64" rx="15" fill="#fff" fillOpacity=".22"/>
            <rect x="330" y="300" width="64" height="64" rx="15" fill="#5b91ee"/>
            <rect x="224" y="370" width="64" height="64" rx="15" fill="#34d27a"/>
          </svg>
        </span>
        <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--ink)" }}>考勤自动化</span>
        <span style={{ fontSize: 12, color: "var(--ink-3)" }}>— 南京六部 · 2026 年 4 月</span>
      </div>
      <WinControls />
    </div>
  );
}

const STEPS = [
  { key: "ready", n: 1, label: "准备" },
  { key: "review", n: 2, label: "复核与决策" },
  { key: "done", n: 3, label: "完成" },
];

function Stepper({ step, onStep, maxStep }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 2 }}>
      {STEPS.map((s, i) => {
        const idx = STEPS.findIndex(x => x.key === step);
        const me = STEPS.findIndex(x => x.key === s.key);
        const active = s.key === step;
        const done = me < idx;
        const reachable = me <= (maxStep ?? 2);
        return (
          <React.Fragment key={s.key}>
            <button onClick={() => reachable && onStep(s.key)} disabled={!reachable}
              style={{
                display: "flex", alignItems: "center", gap: 8, padding: "6px 12px 6px 8px",
                border: "none", borderRadius: 999, background: active ? "var(--accent-soft)" : "transparent",
                color: active ? "var(--accent-strong)" : reachable ? "var(--ink-2)" : "var(--ink-3)",
                cursor: reachable ? "pointer" : "default", opacity: reachable ? 1 : .55,
              }}>
              <span style={{
                width: 20, height: 20, borderRadius: 999, display: "grid", placeItems: "center",
                fontSize: 11, fontWeight: 700,
                background: active ? "var(--accent)" : done ? "color-mix(in srgb, var(--accent) 22%, transparent)" : "var(--surface-3)",
                color: active ? "#fff" : done ? "var(--accent-strong)" : "var(--ink-3)",
                border: active ? "none" : "1px solid var(--line)",
              }}>{done ? <Icon name="check" size={12} sw={2.4} /> : s.n}</span>
              <span style={{ fontSize: 12.5, fontWeight: active ? 650 : 500 }}>{s.label}</span>
            </button>
            {i < STEPS.length - 1 && <span style={{ width: 16, height: 1, background: "var(--line-2)" }} />}
          </React.Fragment>
        );
      })}
    </div>
  );
}

function Toolbar({ step, onStep, maxStep, right }) {
  return (
    <div style={{
      height: 52, flex: "0 0 52px", display: "flex", alignItems: "center",
      justifyContent: "space-between", padding: "0 14px 0 8px",
      background: "var(--surface)", borderBottom: "1px solid var(--line)",
    }}>
      <Stepper step={step} onStep={onStep} maxStep={maxStep} />
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>{right}</div>
    </div>
  );
}

Object.assign(window, { TitleBar, Toolbar, Stepper });
