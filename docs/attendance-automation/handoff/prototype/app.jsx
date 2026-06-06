/* app.jsx — root: state, phase routing, three-column workbench, tweaks */

const ACCENTS = {
  slate:    { "--accent": "#475569", "--accent-strong": "#334155", "--accent-deep": "#1e293b", "--accent-soft": "#e8edf3", "--accent-ring": "rgba(71,85,105,.30)" },
  indigo:   { "--accent": "#4f46e5", "--accent-strong": "#4338ca", "--accent-deep": "#312e81", "--accent-soft": "#e8e8fb", "--accent-ring": "rgba(79,70,229,.28)" },
  teal:     { "--accent": "#0e7c66", "--accent-strong": "#0b6353", "--accent-deep": "#0a3f36", "--accent-soft": "#dcefe9", "--accent-ring": "rgba(14,124,102,.26)" },
  graphite: { "--accent": "#3f3f46", "--accent-strong": "#27272a", "--accent-deep": "#18181b", "--accent-soft": "#ececee", "--accent-ring": "rgba(63,63,70,.26)" },
};

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "mood": "cool",
  "theme": "light",
  "accent": "slate",
  "showChrome": true
}/*EDITMODE-END*/;

// -------- center header (search / filter / next-issue) --------
function CenterHeader({ search, setSearch, filter, setFilter, onNext, anomalyCount, pendingCount }) {
  const tabs = [["all", "全部"], ["anomaly", "有异常"], ["pending", "待归类"]];
  return (
    <div style={{ flex: "0 0 auto", display: "flex", alignItems: "center", gap: 10, padding: "9px 14px", borderBottom: "1px solid var(--line)", background: "var(--surface)" }}>
      <div style={{ position: "relative", width: 196 }}>
        <span style={{ position: "absolute", left: 9, top: "50%", transform: "translateY(-50%)", color: "var(--ink-3)" }}><Icon name="search" size={15} /></span>
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="搜索姓名 / 工号 / 职位"
          style={{ width: "100%", padding: "7px 9px 7px 30px", fontSize: 12.5, border: "1px solid var(--line-2)", borderRadius: 8, background: "var(--surface-2)", color: "var(--ink)", outline: "none" }}
          onFocus={(e) => e.target.style.borderColor = "var(--accent)"} onBlur={(e) => e.target.style.borderColor = "var(--line-2)"} />
      </div>
      <div style={{ display: "flex", background: "var(--surface-2)", border: "1px solid var(--line)", borderRadius: 8, padding: 2 }}>
        {tabs.map(([k, l]) => (
          <button key={k} onClick={() => setFilter(k)} style={{ display: "inline-flex", alignItems: "center", gap: 5, padding: "5px 11px", border: "none", borderRadius: 6, fontSize: 12, fontWeight: 600,
            background: filter === k ? "var(--surface)" : "transparent", color: filter === k ? "var(--ink)" : "var(--ink-3)", boxShadow: filter === k ? "var(--shadow-1)" : "none" }}>
            {l}{k === "pending" && pendingCount > 0 && <span className="tnum" style={{ fontSize: 10, fontWeight: 700, color: "#fff", background: "var(--accent)", borderRadius: 999, padding: "0 5px", minWidth: 16, textAlign: "center" }}>{pendingCount}</span>}
          </button>
        ))}
      </div>
      <div style={{ flex: 1 }} />
      <button onClick={onNext} style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "7px 12px", border: "1px solid var(--line-2)", borderRadius: 8, background: "var(--surface)", color: "var(--ink-2)", fontSize: 12.5, fontWeight: 600 }}>
        <Icon name="next-issue" size={15} /> 跳到下一个异常
      </button>
    </div>
  );
}

// -------- advanced settings drawer --------
function AdvancedDrawer({ open, onClose }) {
  return (
    <>
      <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 120, background: "rgba(15,23,42,.34)", opacity: open ? 1 : 0, pointerEvents: open ? "auto" : "none", transition: "opacity .2s" }} />
      <div style={{ position: "fixed", top: 0, right: 0, bottom: 0, width: 380, maxWidth: "90%", zIndex: 121, background: "var(--surface)", borderLeft: "1px solid var(--line)", boxShadow: "var(--shadow-3)", transform: open ? "translateX(0)" : "translateX(100%)", transition: "transform .24s cubic-bezier(.4,0,.2,1)", display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "16px 18px", borderBottom: "1px solid var(--line)", display: "flex", alignItems: "center", gap: 10 }}>
          <Icon name="settings" size={18} />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 14.5, fontWeight: 700, color: "var(--ink)" }}>高级设置</div>
            <div style={{ fontSize: 11.5, color: "var(--ink-3)" }}>多数月份无需改动</div>
          </div>
          <button onClick={onClose} style={{ border: "none", background: "transparent", color: "var(--ink-3)" }}><Icon name="x" size={18} /></button>
        </div>
        <div style={{ flex: 1, overflow: "auto", padding: 18, display: "flex", flexDirection: "column", gap: 20 }}>
          <Field label="不计加班名单" hint="名单内人员本月加班一律不计">
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              <Tag text="张伟" removable /><AddTag />
            </div>
          </Field>
          <Field label="个别人迟到阈值" hint="默认 09:00；个别人可单独放宽">
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Tag text="赵敏 → 09:05" removable /><AddTag />
            </div>
          </Field>
          <Field label="只红字（不加底色）名单" hint="名单内人员的迟到只标红字，不铺红底">
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}><AddTag /></div>
          </Field>
        </div>
        <div style={{ padding: "14px 18px", borderTop: "1px solid var(--line)", background: "var(--surface-2)", display: "flex", justifyContent: "flex-end", gap: 9 }}>
          <button onClick={onClose} style={ghostBtn2}>关闭</button>
          <button onClick={onClose} style={primaryBtn}>应用并重算</button>
        </div>
      </div>
    </>
  );
}
function Field({ label, hint, children }) {
  return (<div><div style={{ fontSize: 12.5, fontWeight: 700, color: "var(--ink)" }}>{label}</div><div style={{ fontSize: 11, color: "var(--ink-3)", margin: "2px 0 9px" }}>{hint}</div>{children}</div>);
}
function Tag({ text, removable }) {
  return (<span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 12, fontWeight: 600, color: "var(--ink)", background: "var(--surface-3)", border: "1px solid var(--line)", borderRadius: 7, padding: "4px 8px" }}>{text}{removable && <span style={{ color: "var(--ink-3)", cursor: "pointer", lineHeight: 0 }}><Icon name="x" size={12} /></span>}</span>);
}
function AddTag() {
  return (<button style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 12, fontWeight: 600, color: "var(--ink-3)", background: "transparent", border: "1.5px dashed var(--line-2)", borderRadius: 7, padding: "4px 9px" }}>+ 添加</button>);
}

// -------- toast --------
function Toast({ msg }) {
  if (!msg) return null;
  return (<div style={{ position: "fixed", bottom: 22, left: "50%", transform: "translateX(-50%)", zIndex: 400, display: "flex", alignItems: "center", gap: 9, padding: "10px 16px", background: "var(--accent-deep)", color: "#fff", borderRadius: 10, boxShadow: "var(--shadow-3)", fontSize: 13, fontWeight: 500, animation: "toastIn .2s ease" }}>
    <Icon name="check" size={16} sw={2.4} />{msg}
    <style>{`@keyframes toastIn{from{opacity:0;transform:translate(-50%,8px)}to{opacity:1;transform:translate(-50%,0)}}`}</style>
  </div>);
}

// -------- workbench (phase ②) --------
function Workbench(props) {
  const { employees, included, leavers, pendingList, keepDecisions, activeCell, scrollTarget,
          search, setSearch, filter, setFilter, fullSet, mood,
          onClassify, onKeep, onLocate, onSelectCell, onReclassify, onNext, onAdvancedOpen, onAdoptAll,
          anomalyCount, pendingCount } = props;
  const deep = mood === "deep";
  return (
    <div style={{ flex: 1, minHeight: 0, display: "grid", gridTemplateColumns: "312px minmax(0,1fr) 332px" }}>
      <div data-theme={deep ? "dark" : undefined} style={{ minHeight: 0 }}>
        <TodoPanel employees={employees} leavers={leavers} pendingList={pendingList} keepDecisions={keepDecisions}
          activeCell={activeCell} onClassify={onClassify} onKeep={onKeep} onLocate={onLocate} onAdvancedOpen={onAdvancedOpen} onAdoptAll={onAdoptAll} />
      </div>
      <div style={{ display: "flex", flexDirection: "column", minHeight: 0, minWidth: 0, background: "var(--surface)" }}>
        <CenterHeader search={search} setSearch={setSearch} filter={filter} setFilter={setFilter} onNext={onNext} anomalyCount={anomalyCount} pendingCount={pendingCount} />
        <div style={{ flex: 1, minHeight: 0 }}>
          <AttGrid employees={employees} calendar={AttData.calendar} included={included} filter={filter} search={search}
            activeCell={activeCell} scrollTarget={scrollTarget} onSelectCell={onSelectCell} onReclassify={onReclassify} fullSet={fullSet} />
        </div>
      </div>
      <Inspector employees={employees} activeCell={activeCell} included={included} />
    </div>
  );
}

// =================== App ===================
function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [step, setStep] = React.useState(location.hash === "#review" ? "review" : location.hash === "#done" ? "done" : "ready");
  const [maxStep, setMaxStep] = React.useState(location.hash ? 2 : 0);
  const [readyVariant, setReadyVariant] = React.useState("ok");
  const [, force] = React.useState(0);
  const bump = () => force(v => v + 1);

  const employees = React.useRef(AttData.employees).current;
  const leavers = React.useRef(employees.filter(e => e.needsKeepDecision)).current;
  const pendingList = React.useRef(
    employees.flatMap(e => Object.entries(e.cells)
      .filter(([, c]) => c && c.status === "pending")
      .map(([d, c]) => ({ empId: e.id, day: +d, suggest: c.suggest, reason: c.reason })))
  ).current;

  const [keepDecisions, setKeepDecisions] = React.useState({});
  const [activeCell, setActiveCell] = React.useState(null);
  const [scrollTarget, setScrollTarget] = React.useState(null);
  const [search, setSearch] = React.useState("");
  const [filter, setFilter] = React.useState("all");
  const [advancedOpen, setAdvancedOpen] = React.useState(false);
  const [exportOpen, setExportOpen] = React.useState(false);
  const [toast, setToast] = React.useState(null);
  const toastTimer = React.useRef(null);
  const showToast = (m) => { setToast(m); clearTimeout(toastTimer.current); toastTimer.current = setTimeout(() => setToast(null), 2200); };

  const included = React.useMemo(() => {
    const s = new Set(employees.map(e => e.id));
    Object.entries(keepDecisions).forEach(([id, keep]) => { if (keep === false) s.delete(id); });
    return s;
  }, [keepDecisions]);

  const stats = AttData.computeStats(employees, included);
  const nextRef = React.useRef(0);

  const locate = (empId, day) => { setActiveCell({ empId, day }); setScrollTarget({ empId, day, _t: Date.now() }); };

  const reclassify = (empId, day, val) => {
    const c = employees.find(e => e.id === empId).cells[day];
    if (val === "pending") { c.status = "pending"; }
    else { c.status = val; }
    setActiveCell({ empId, day });
    bump();
    if (val !== "pending") showToast(`已归类为「${({miss:"缺卡",biz:"公出",absent:"未出勤"})[val]}」，已重算`);
  };
  const keepDecide = (empId, keep) => { setKeepDecisions(d => ({ ...d, [empId]: keep })); locate(empId, employees.find(e=>e.id===empId).leave); showToast(keep ? "已保留该员工" : "已从本月名单删除"); };
  const adoptAll = () => {
    let n = 0;
    pendingList.forEach(p => { const c = employees.find(e => e.id === p.empId).cells[p.day]; if (c.status === "pending") { c.status = p.suggest; n++; } });
    bump();
    if (n) showToast(`已按建议归类 ${n} 项，已重算`);
  };

  // anomaly cell list for "next issue"
  const anomalyCells = [];
  employees.forEach(e => { if (!included.has(e.id)) return; Object.entries(e.cells).forEach(([d, c]) => { if (c && ["pending","absent","miss","early","lateheavy","late"].includes(c.status)) anomalyCells.push({ empId: e.id, day: +d }); }); });
  const gotoNext = () => { if (!anomalyCells.length) return; const it = anomalyCells[nextRef.current % anomalyCells.length]; nextRef.current++; locate(it.empId, it.day); };

  const startReview = () => { setStep("review"); setMaxStep(2); };
  const goStep = (s) => { setStep(s); };

  const todos = { leaver: leavers.length, pending: pendingList.length };
  const peopleCount = included.size;

  // toolbar right content per step
  function ToolbarRight() {
    if (step === "ready") return <span style={{ fontSize: 11.5, color: "var(--ink-3)" }}>选择文件夹后自动就绪</span>;
    if (step === "review") {
      const done = leavers.filter(e => keepDecisions[e.id] !== undefined).length + pendingList.filter(p => employees.find(e=>e.id===p.empId).cells[p.day].status !== "pending").length;
      const total = leavers.length + pendingList.length;
      const allDone = done === total;
      return (<>
        <Chip2 icon="folder" text={AttData.dataDir} mono />
        <Chip2 text={`4 月 · ${peopleCount} 人`} />
        <Chip2 text={`待办 ${total - done}/${total}`} tone={allDone ? "ok" : "accent"} />
        <button onClick={() => { setStep("done"); }} style={{ ...primaryBtn, padding: "8px 16px", display: "inline-flex", alignItems: "center", gap: 7, opacity: 1 }}>
          完成并汇总 <Icon name="arrow-right" size={15} sw={2} />
        </button>
      </>);
    }
    return (<>
      <button onClick={() => setStep("review")} style={{ ...ghostBtn2, padding: "8px 14px", display: "inline-flex", alignItems: "center", gap: 6 }}><Icon name="undo" size={15} />返回工作台</button>
      <button onClick={() => setExportOpen(true)} style={{ ...primaryBtn, padding: "8px 16px", display: "inline-flex", alignItems: "center", gap: 7 }}><Icon name="download" size={15} />导出《考勤》</button>
    </>);
  }

  const accentVars = ACCENTS[t.accent] || ACCENTS.slate;
  const moodAttr = t.mood === "paper" ? "paper" : undefined;

  return (
    <div data-mood={moodAttr} data-theme={t.theme === "dark" ? "dark" : undefined}
      style={{ ...accentVars, height: "100%", display: "flex", flexDirection: "column", background: "var(--bg)", overflow: "hidden",
               borderRadius: t.showChrome ? 0 : 0 }}>
      {t.showChrome && <TitleBar />}
      <Toolbar step={step} onStep={goStep} maxStep={maxStep} right={<ToolbarRight />} />

      <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        {step === "ready" && <ReadyScreen variant={readyVariant} setVariant={setReadyVariant} todos={todos} people={peopleCount} onStart={startReview} onPick={() => { setReadyVariant("loading"); setTimeout(() => setReadyVariant("ok"), 2600); }} />}
        {step === "review" && <Workbench
          employees={employees} included={included} leavers={leavers} pendingList={pendingList} keepDecisions={keepDecisions}
          activeCell={activeCell} scrollTarget={scrollTarget} search={search} setSearch={setSearch} filter={filter} setFilter={setFilter}
          fullSet={stats.fullSet} mood={t.mood}
          onClassify={reclassify} onKeep={keepDecide} onLocate={locate} onSelectCell={(c) => setActiveCell(c)} onReclassify={reclassify}
          onNext={gotoNext} onAdvancedOpen={() => setAdvancedOpen(true)} onAdoptAll={adoptAll}
          anomalyCount={anomalyCells.length} pendingCount={stats.pending} />}
        {step === "done" && <Dashboard employees={employees} included={included} stats={stats} onExport={() => setExportOpen(true)} onSaveDecisions={() => showToast("本月决策已保存，下月可一键载入")} onBack={() => setStep("review")} />}
      </div>

      <AdvancedDrawer open={advancedOpen} onClose={() => setAdvancedOpen(false)} />
      {exportOpen && <ExportDialog onClose={() => setExportOpen(false)} onConfirm={() => { setExportOpen(false); showToast("已导出 考勤_2026-04.xlsx"); }} />}
      <Toast msg={toast} />

      <TweaksPanel title="Tweaks">
        <TweakSection label="视觉气质" />
        <TweakRadio label="界面气质" value={t.mood} options={[{value:"cool",label:"冷静"},{value:"paper",label:"暖白"},{value:"deep",label:"深栏"}]} onChange={(v) => setTweak("mood", v)} />
        <TweakSelect label="强调色" value={t.accent} options={[{value:"slate",label:"石板灰"},{value:"indigo",label:"靛蓝"},{value:"teal",label:"墨绿"},{value:"graphite",label:"石墨"}]} onChange={(v) => setTweak("accent", v)} />
        <TweakToggle label="深色主题" value={t.theme === "dark"} onChange={(v) => setTweak("theme", v ? "dark" : "light")} />
        <TweakSection label="窗口" />
        <TweakToggle label="显示 Windows 标题栏" value={t.showChrome} onChange={(v) => setTweak("showChrome", v)} />
      </TweaksPanel>
    </div>
  );
}

function Chip2({ icon, text, mono, tone }) {
  const col = tone === "ok" ? "var(--ok)" : tone === "accent" ? "var(--accent-strong)" : "var(--ink-2)";
  return (<span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 11.5, fontWeight: 600, color: col, background: "var(--surface-2)", border: "1px solid var(--line)", borderRadius: 7, padding: "5px 9px", maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
    {icon && <span style={{ color: "var(--ink-3)", lineHeight: 0 }}><Icon name={icon} size={13} /></span>}
    <span className={mono ? "tnum" : ""} style={{ overflow: "hidden", textOverflow: "ellipsis" }}>{text}</span></span>);
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
