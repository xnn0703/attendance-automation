/* inspector.jsx — right column: detail / inspector for the selected cell + person */

function Stat({ label, value, accent }) {
  return (
    <div style={{ background: "var(--surface-2)", border: "1px solid var(--line)", borderRadius: 9, padding: "8px 10px" }}>
      <div className="tnum" style={{ fontSize: 18, fontWeight: 700, color: accent || "var(--ink)", lineHeight: 1.1 }}>{value}</div>
      <div style={{ fontSize: 10.5, color: "var(--ink-3)", marginTop: 1 }}>{label}</div>
    </div>
  );
}

function DefRow({ k, v, mono }) {
  return (
    <div style={{ display: "flex", gap: 10, fontSize: 12.5, lineHeight: 1.5 }}>
      <span style={{ color: "var(--ink-3)", flex: "0 0 60px" }}>{k}</span>
      <span className={mono ? "tnum" : ""} style={{ color: "var(--ink)", flex: 1 }}>{v}</span>
    </div>
  );
}

function InspectorEmpty() {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 28, textAlign: "center", color: "var(--ink-3)", gap: 12 }}>
      <span style={{ width: 46, height: 46, borderRadius: 12, background: "var(--surface-3)", display: "grid", placeItems: "center", color: "var(--ink-3)" }}><Icon name="grid" size={22} /></span>
      <div style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-2)" }}>检查器</div>
      <div style={{ fontSize: 12, lineHeight: 1.6, maxWidth: 200 }}>点击网格中任意单元格，这里会显示<b style={{ color: "var(--ink-2)" }}>原始打卡、判定原因、加班算式</b>，以及该员工本月小结。</div>
    </div>
  );
}

function Inspector({ employees, activeCell, included }) {
  const emp = activeCell ? employees.find(e => e.id === activeCell.empId) : null;
  const cell = emp ? emp.cells[activeCell.day] : null;
  const sum = emp ? AttData.personSummary(emp, included) : null;

  if (!emp || !cell) {
    return <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0, background: "var(--surface)", borderLeft: "1px solid var(--line)" }}><InspectorEmpty /></div>;
  }

  const [title, sub] = AttData.reasonFor(cell);
  const otF = AttData.otFormula(cell);
  const cal = AttData.calendar[activeCell.day - 1];
  const swatchKind = cell.status === "pending" ? (cell.suggest || "miss") : cell.status;
  const showSwatch = !["normal", "rest", "holiday", "pre", "post"].includes(cell.status) || cell.swap;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0, background: "var(--surface)", borderLeft: "1px solid var(--line)" }}>
      {/* person header */}
      <div style={{ flex: "0 0 auto", padding: "14px 16px", borderBottom: "1px solid var(--line)", background: "var(--surface-2)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ width: 34, height: 34, borderRadius: 9, background: sum.full ? "var(--s-full-bg)" : "var(--accent-soft)", color: sum.full ? "var(--s-full-fg)" : "var(--accent-strong)", display: "grid", placeItems: "center", fontSize: 14, fontWeight: 700 }}>{emp.name[0]}</span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14.5, fontWeight: 700, color: "var(--ink)", display: "flex", alignItems: "center", gap: 6 }}>
              {emp.name}
              {sum.full && <span style={{ display: "inline-flex", alignItems: "center", gap: 3, fontSize: 10, fontWeight: 700, color: "var(--s-full-fg)", background: "var(--s-full-bg)", border: "1px solid var(--s-full-line)", borderRadius: 5, padding: "1px 6px" }}><SIcon name="star" size={9} />全勤</span>}
            </div>
            <div className="tnum" style={{ fontSize: 11, color: "var(--ink-3)" }}>{emp.id} · {emp.pos} · {emp.type}</div>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, minHeight: 0, overflow: "auto", padding: "14px 16px", display: "flex", flexDirection: "column", gap: 16 }}>
        {/* selected day */}
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--ink-3)", letterSpacing: ".04em", marginBottom: 8 }}>选中：{AttData.month} 月 {activeCell.day} 日 · 周{cal.wk}</div>
          <div style={{ border: "1px solid var(--line)", borderRadius: 11, overflow: "hidden" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 9, padding: "10px 12px", background: "var(--surface-2)", borderBottom: "1px solid var(--line)" }}>
              {showSwatch ? <Swatch kind={swatchKind} bar={cell.status === "field"} /> : <span style={{ width: 26, height: 18, borderRadius: 4, border: "1px solid var(--line-2)", background: "var(--surface)" }} />}
              <span style={{ fontSize: 14, fontWeight: 700, color: "var(--ink)" }}>{title}</span>
              {cell.swap && <span style={{ marginLeft: "auto", display: "inline-flex", alignItems: "center", gap: 3, fontSize: 10, fontWeight: 700, color: "var(--s-swap-fg)", background: "var(--s-swap-bg)", border: "1px solid var(--s-swap-line)", borderRadius: 5, padding: "1px 6px" }}><SIcon name="swap" size={9} />调班</span>}
            </div>
            <div style={{ padding: "11px 12px", display: "flex", flexDirection: "column", gap: 9 }}>
              <DefRow k="判定原因" v={sub} />
              <DefRow k="原始打卡" v={(cell.punches && cell.punches.length) ? cell.punches.join("    ") : "无任何打卡记录"} mono />
              {otF && <DefRow k="加班算式" v={otF} mono />}
              {cell.status === "pending" && <div style={{ marginTop: 2, fontSize: 11.5, color: "var(--accent-strong)", background: "var(--accent-soft)", borderRadius: 8, padding: "7px 9px", lineHeight: 1.5 }}>需在左侧待办或点击此格归类为 缺卡 / 公出 / 未出勤。工具建议：<b>{({miss:"缺卡",biz:"公出",absent:"未出勤"})[cell.suggest]}</b>。</div>}
            </div>
          </div>
        </div>

        {/* person summary */}
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--ink-3)", letterSpacing: ".04em", marginBottom: 8 }}>本月小结</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <Stat label="出勤天数" value={sum.workDays} />
            <Stat label="加班合计 (h)" value={sum.ot} accent="var(--s-ot-fg)" />
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 7, marginTop: 10 }}>
            <Chip label="迟到" n={sum.late} kind="lateheavy" />
            <Chip label="早退" n={sum.early} kind="early" />
            <Chip label="缺卡" n={sum.miss} kind="miss" />
            <Chip label="未出勤" n={sum.absent} kind="absent" />
            <Chip label="公出" n={sum.biz} kind="biz" />
            <Chip label="外勤" n={sum.field} kind="field" />
            {sum.pend > 0 && <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 11.5, fontWeight: 600, color: "var(--accent-strong)", background: "var(--accent-soft)", borderRadius: 7, padding: "4px 9px" }}>待归类 {sum.pend}</span>}
          </div>
        </div>

        {/* anomaly list for the person */}
        <PersonAnomalies emp={emp} />
      </div>
    </div>
  );
}

function Chip({ label, n, kind }) {
  const dim = n === 0;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 11.5, fontWeight: 600,
      color: dim ? "var(--ink-3)" : "var(--ink)",
      background: dim ? "var(--surface-2)" : "var(--surface-3)",
      border: "1px solid var(--line)", borderRadius: 7, padding: "4px 9px", opacity: dim ? .65 : 1 }}>
      {!dim && <Swatch kind={kind} bar={kind === "field"} />}
      {label} <b className="tnum" style={{ fontWeight: 700 }}>{n}</b>
    </span>
  );
}

function PersonAnomalies({ emp }) {
  const items = [];
  Object.entries(emp.cells).forEach(([d, c]) => {
    if (c && ["late","lateheavy","early","absent","miss","pending"].includes(c.status)) {
      const [t] = AttData.reasonFor(c);
      items.push({ day: +d, label: c.status === "pending" ? "待归类" : t, kind: c.status === "pending" ? (c.suggest||"miss") : c.status });
    }
  });
  if (!items.length) return (
    <div style={{ fontSize: 12, color: "var(--ink-3)", background: "var(--surface-2)", border: "1px dashed var(--line-2)", borderRadius: 9, padding: "12px", textAlign: "center" }}>本月无异常记录 🎉</div>
  );
  items.sort((a, b) => a.day - b.day);
  return (
    <div>
      <div style={{ fontSize: 11, fontWeight: 700, color: "var(--ink-3)", letterSpacing: ".04em", marginBottom: 8 }}>异常明细（{items.length}）</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {items.map((it, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, padding: "5px 8px", borderRadius: 7, background: "var(--surface-2)" }}>
            <Swatch kind={it.kind} bar={it.kind === "field"} />
            <span className="tnum" style={{ color: "var(--ink-2)", flex: "0 0 40px" }}>4/{it.day}</span>
            <span style={{ color: "var(--ink)" }}>{it.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { Inspector });
