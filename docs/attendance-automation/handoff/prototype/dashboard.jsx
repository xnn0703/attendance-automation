/* dashboard.jsx — phase ③ 完成：summary dashboard + export dialog */

function BigStat({ value, label, sub, accent }) {
  return (
    <div style={{ flex: 1, background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 13, padding: "16px 18px" }}>
      <div className="tnum" style={{ fontSize: 30, fontWeight: 800, color: accent || "var(--ink)", lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 12.5, fontWeight: 600, color: "var(--ink)", marginTop: 6 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: "var(--ink-3)", marginTop: 1 }}>{sub}</div>}
    </div>
  );
}

function CountCard({ kind, label, n }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "11px 13px", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 11 }}>
      <Swatch kind={kind} bar={kind === "field"} />
      <span style={{ fontSize: 12.5, color: "var(--ink-2)", flex: 1 }}>{label}</span>
      <span className="tnum" style={{ fontSize: 18, fontWeight: 700, color: "var(--ink)" }}>{n}</span>
    </div>
  );
}

function ExportDialog({ onClose, onConfirm }) {
  const [legend, setLegend] = React.useState(true);
  const [purple, setPurple] = React.useState(true);
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 300, background: "rgba(15,23,42,.42)", display: "grid", placeItems: "center" }} onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: 440, maxWidth: "92%", background: "var(--surface)", borderRadius: 16, boxShadow: "var(--shadow-3)", overflow: "hidden" }}>
        <div style={{ padding: "18px 20px", borderBottom: "1px solid var(--line)", display: "flex", alignItems: "center", gap: 11 }}>
          <span style={{ width: 36, height: 36, borderRadius: 10, background: "var(--accent-soft)", color: "var(--accent-strong)", display: "grid", placeItems: "center" }}><Icon name="download" size={18} /></span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: "var(--ink)" }}>导出《考勤》</div>
            <div style={{ fontSize: 11.5, color: "var(--ink-3)" }}>生成与界面配色一致的 Excel 表</div>
          </div>
          <button onClick={onClose} style={{ border: "none", background: "transparent", color: "var(--ink-3)" }}><Icon name="x" size={18} /></button>
        </div>
        <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 12 }}>
          <DefRow2 k="文件名" v="考勤_2026-04.xlsx" />
          <DefRow2 k="保存到" v={AttData.dataDir} />
          <div style={{ display: "flex", flexDirection: "column", gap: 9, marginTop: 4 }}>
            <CheckLine on={legend} set={setLegend} label="在表内附颜色图例" />
            <CheckLine on={purple} set={setPurple} label="全勤者姓名格使用浅紫底色" />
          </div>
        </div>
        <div style={{ padding: "14px 20px", borderTop: "1px solid var(--line)", background: "var(--surface-2)", display: "flex", justifyContent: "flex-end", gap: 9 }}>
          <button onClick={onClose} style={{ ...ghostBtn2 }}>取消</button>
          <button onClick={onConfirm} style={{ ...primaryBtn, display: "inline-flex", alignItems: "center", gap: 7 }}><Icon name="download" size={15} />导出</button>
        </div>
      </div>
    </div>
  );
}
function DefRow2({ k, v }) {
  return (<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "9px 12px", background: "var(--surface-2)", borderRadius: 9, border: "1px solid var(--line)" }}>
    <span style={{ fontSize: 12, color: "var(--ink-3)" }}>{k}</span><span className="tnum" style={{ fontSize: 12.5, color: "var(--ink)", fontWeight: 600 }}>{v}</span></div>);
}
function CheckLine({ on, set, label }) {
  return (<button onClick={() => set(!on)} style={{ display: "flex", alignItems: "center", gap: 9, border: "none", background: "transparent", padding: 0 }}>
    <span style={{ width: 19, height: 19, borderRadius: 6, border: on ? "none" : "1.5px solid var(--line-2)", background: on ? "var(--accent)" : "var(--surface)", color: "#fff", display: "grid", placeItems: "center" }}>{on && <Icon name="check" size={13} sw={2.6} />}</span>
    <span style={{ fontSize: 12.5, color: "var(--ink)" }}>{label}</span></button>);
}
const ghostBtn2 = { padding: "9px 16px", borderRadius: 9, border: "1px solid var(--line-2)", background: "var(--surface)", color: "var(--ink-2)", fontSize: 13, fontWeight: 600 };

function Dashboard({ employees, included, stats, onExport, onSaveDecisions, onBack }) {
  const c = stats.counts;
  const otTotal = stats.otTotal;
  const includedCount = included.size;
  const anomalyCount = stats.anomalyPeople.size;
  return (
    <div style={{ flex: 1, minHeight: 0, overflow: "auto", background: "var(--bg)" }}>
      <div style={{ maxWidth: 1080, margin: "0 auto", padding: "26px 28px 40px" }}>
        {/* title row */}
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 18, flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ fontSize: 22, fontWeight: 800, color: "var(--ink)" }}>2026 年 4 月 · 考勤汇总</div>
            <div style={{ fontSize: 13, color: "var(--ink-2)", marginTop: 3 }}>所有待办已处理完成，下面是本月概览与导出。</div>
          </div>
          <div style={{ display: "flex", gap: 9 }}>
            <button onClick={onSaveDecisions} style={{ ...ghostBtn2, display: "inline-flex", alignItems: "center", gap: 6 }}><Icon name="download" size={15} />保存本月决策</button>
            <button onClick={onExport} style={{ ...primaryBtn, display: "inline-flex", alignItems: "center", gap: 7 }}><Icon name="file" size={15} />导出《考勤》</button>
          </div>
        </div>

        {/* big stats */}
        <div style={{ display: "flex", gap: 12, marginBottom: 14, flexWrap: "wrap" }}>
          <BigStat value={includedCount} label="纳入人数" sub={`共识别 ${employees.length} 人`} />
          <BigStat value={otTotal} label="加班合计 (h)" sub="不计名单已排除" accent="var(--s-ot-fg)" />
          <BigStat value={stats.fullList.length} label="全勤人数" accent="var(--s-full-fg)" />
          <BigStat value={anomalyCount} label="有异常人数" sub={`${includedCount - anomalyCount} 人本月正常`} accent={anomalyCount ? "var(--warn)" : "var(--ink)"} />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 14 }}>
          {/* counts */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <Panel title="异常计数">
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 9 }}>
                <CountCard kind="lateheavy" label="迟到（含较重）" n={c.late + c.lateheavy} />
                <CountCard kind="early" label="早退" n={c.early} />
                <CountCard kind="miss" label="缺卡" n={c.miss} />
                <CountCard kind="absent" label="未出勤" n={c.absent} />
                <CountCard kind="biz" label="公出" n={c.biz} />
                <CountCard kind="field" label="外勤日" n={c.field} />
              </div>
            </Panel>
            <Panel title={`全勤名单（${stats.fullList.length}）`}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {stats.fullList.length ? stats.fullList.map((e) => (
                  <span key={e.id} style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 12.5, fontWeight: 600, color: "var(--s-full-fg)", background: "var(--s-full-bg)", border: "1px solid var(--s-full-line)", borderRadius: 999, padding: "4px 11px" }}><SIcon name="star" size={10} />{e.name}</span>
                )) : <span style={{ fontSize: 12, color: "var(--ink-3)" }}>本月无全勤</span>}
              </div>
            </Panel>
          </div>

          {/* anomaly list */}
          <Panel title="异常清单">
            <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 320, overflow: "auto" }}>
              {employees.filter(e => included.has(e.id) && stats.anomalyPeople.has(e.id)).map((e) => {
                const ps = AttData.personSummary(e, included);
                const tags = [];
                if (ps.late) tags.push(["迟到", "lateheavy", ps.late]);
                if (ps.early) tags.push(["早退", "early", ps.early]);
                if (ps.miss) tags.push(["缺卡", "miss", ps.miss]);
                if (ps.absent) tags.push(["未出勤", "absent", ps.absent]);
                return (
                  <div key={e.id} style={{ display: "flex", alignItems: "center", gap: 9, padding: "8px 10px", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 9 }}>
                    <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--ink)", flex: "0 0 52px" }}>{e.name}</span>
                    <span style={{ display: "flex", flexWrap: "wrap", gap: 5, flex: 1 }}>
                      {tags.map(([l, k, n], i) => <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11, color: "var(--ink-2)" }}><Swatch kind={k} />{l}×{n}</span>)}
                    </span>
                  </div>
                );
              })}
            </div>
          </Panel>
        </div>

        {/* full preview */}
        <div style={{ marginTop: 16 }}>
          <Panel title="完整预览 · 《考勤》表" right={<span style={{ fontSize: 11, color: "var(--ink-3)" }}>与导出 Excel 配色一致</span>}>
            <div style={{ height: 300, border: "1px solid var(--line)", borderRadius: 10, overflow: "hidden" }}>
              <AttGrid employees={employees} calendar={AttData.calendar} included={included} filter="all" search="" activeCell={null} scrollTarget={null} onSelectCell={() => {}} onReclassify={() => {}} fullSet={stats.fullSet} />
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function Panel({ title, right, children }) {
  return (
    <div style={{ background: "var(--surface-2)", border: "1px solid var(--line)", borderRadius: 14, padding: 16 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: "var(--ink)" }}>{title}</span>
        {right}
      </div>
      {children}
    </div>
  );
}

Object.assign(window, { Dashboard, ExportDialog });
