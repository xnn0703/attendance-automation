/* grid.jsx — the colored attendance table (core component) + Legend + hover card */

const { useState, useRef, useEffect, useLayoutEffect, useCallback } = React;

// visual spec per status (color + icon + border/texture)
function getVisual(c) {
  if (!c) return { bg: "var(--surface)", fg: "var(--ink)", line: "var(--line)" };
  switch (c.status) {
    case "late":      return { bg: "var(--s-late-bg)", fg: "var(--s-late-fg)", line: "var(--s-late-line)", icon: "clock", strong: false };
    case "lateheavy": return { bg: "var(--s-lateheavy-bg)", fg: "var(--s-lateheavy-fg)", line: "var(--s-lateheavy-line)", icon: "clock2", strong: true };
    case "early":     return { bg: "var(--s-early-bg)", fg: "var(--s-early-fg)", line: "var(--s-early-line)", icon: "exit", strong: true };
    case "absent":    return { bg: "var(--s-absent-bg)", fg: "var(--s-absent-fg)", line: "var(--s-absent-line)", icon: "cross", strong: true, hatch: true };
    case "miss":      return { bg: "var(--s-miss-bg)", fg: "var(--s-miss-fg)", line: "var(--s-miss-line)", icon: "half", strong: true };
    case "biz":       return { bg: "var(--s-biz-bg)", fg: "var(--s-biz-fg)", line: "var(--s-biz-line)", icon: "bag", strong: true };
    case "field":     return { bg: "var(--s-field-bg)", fg: "var(--s-field-fg)", line: "var(--s-field-line)", icon: "pin", bar: "var(--s-field-bar)", stripe: true };
    case "rest":      return { bg: "var(--surface-3)", fg: "var(--ink-3)", line: "var(--line)", rest: true };
    case "holiday":   return { bg: "var(--surface-3)", fg: "var(--ink-3)", line: "var(--line)", rest: true, tag: "假" };
    case "pre": case "post": return { bg: "transparent", fg: "var(--ink-3)", line: "var(--line)", inactive: true };
    case "pending":   return { bg: "var(--surface)", fg: "var(--ink-2)", line: "var(--accent)", pending: true };
    default:          return { bg: "var(--surface)", fg: "var(--ink)", line: "var(--line)" };
  }
}

function tint(bg) {
  // OT-row faint version of a fill color
  if (bg === "var(--surface)" || bg === "transparent") return "var(--surface)";
  return `color-mix(in srgb, ${bg} 55%, var(--surface))`;
}

// ----- single day cell pair lives across two <td>; we render content here -----
function PunchContent({ c, v }) {
  if (!c) return null;
  if (c.status === "rest") return <span style={{ fontSize: 10, opacity: .5 }}>休</span>;
  if (c.status === "holiday") return <span style={{ fontSize: 10, opacity: .6 }}>假</span>;
  if (c.status === "pre" || c.status === "post") return null;
  if (c.status === "absent") return <span style={{ fontSize: 10, fontWeight: 700 }}>缺</span>;
  if (c.status === "biz") return <span style={{ fontSize: 10, fontWeight: 600 }}>公出</span>;
  if (c.status === "miss") {
    const p = (c.punches || [])[0];
    return (<div style={{ display: "flex", flexDirection: "column", lineHeight: 1.05, alignItems: "center" }}>
      <span className="tnum" style={{ fontSize: 9 }}>{p ? p.replace("(外勤)", "") : "—"}</span>
      <span style={{ fontSize: 8.5, fontWeight: 700 }}>缺卡</span></div>);
  }
  if (c.status === "pending") {
    const onlyOne = (c.punches || []).length === 1;
    return (
      <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.05, alignItems: "center" }}>
        {onlyOne
          ? <span className="tnum" style={{ fontSize: 9 }}>{c.punches[0].replace("(外勤)", "")}</span>
          : <span style={{ fontSize: 10, color: "var(--ink-3)" }}>—</span>}
        <span style={{ fontSize: 8.5, color: "var(--accent)", fontWeight: 700 }}>待定</span>
      </div>
    );
  }
  const inT = (c.in || "").replace("(外勤)", "");
  const isField = c.status === "field";
  return (
    <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.06, alignItems: "center" }}>
      <span className="tnum" style={{ fontSize: 9, fontWeight: c.status==="late"||c.status==="lateheavy"?700:500 }}>{inT || "—"}</span>
      <span className="tnum" style={{ fontSize: 9, fontWeight: c.status==="early"?700:500 }}>{(c.out || "—")}</span>
      {isField && <span style={{ fontSize: 7.5, color: "var(--s-field-fg)", marginTop: -1 }}>外勤</span>}
    </div>
  );
}

function AttGrid({ employees, calendar, included, filter, search, activeCell, scrollTarget,
                   onSelectCell, onReclassify, fullSet }) {
  const wrapRef = useRef(null);
  const [hover, setHover] = useState(null); // {c, emp, day, x, y}
  const [menu, setMenu] = useState(null);   // {empId, day, x, y, suggest, c}

  const NAME_W = 152, CELL_W = 48;

  // filter rows
  const rows = employees.filter((e) => {
    if (search && !(e.name.includes(search) || e.id.includes(search) || (e.pos||"").includes(search))) return false;
    if (filter === "anomaly") {
      return Object.values(e.cells).some(c => c && ["late","lateheavy","early","absent","miss","pending"].includes(c.status));
    }
    if (filter === "pending") {
      return Object.values(e.cells).some(c => c && c.status === "pending");
    }
    return true;
  });

  // scroll to target cell when a todo is clicked
  useEffect(() => {
    if (!scrollTarget || !wrapRef.current) return;
    const el = wrapRef.current.querySelector(`[data-cell="${scrollTarget.empId}-${scrollTarget.day}"]`);
    if (!el) return;
    const wrap = wrapRef.current;
    const left = el.offsetLeft - wrap.clientWidth / 2 + CELL_W;
    const top = el.offsetTop - wrap.clientHeight / 2;
    wrap.scrollTo({ left: Math.max(0, left), top: Math.max(0, top), behavior: "smooth" });
  }, [scrollTarget]);

  const headBg = "var(--surface-2)";
  const stickyShadow = "2px 0 0 0 var(--line), 3px 0 8px -2px rgba(15,23,42,.10)";

  function cornerBadge(v, c) {
    if (c.status === "pending") {
      return <span style={{ position: "absolute", top: 1, right: 1, width: 13, height: 13, borderRadius: 4, background: "var(--accent)", color: "#fff", fontSize: 9, fontWeight: 800, display: "grid", placeItems: "center", lineHeight: 1 }}>?</span>;
    }
    if (!v.icon) return null;
    return (
      <span style={{ position: "absolute", top: 1.5, right: 1.5, color: v.fg, opacity: v.strong ? .95 : .85, lineHeight: 0 }}>
        <SIcon name={v.icon} size={9.5} />
      </span>
    );
  }

  function renderPunchCell(emp, day) {
    const c = emp.cells[day];
    const v = getVisual(c);
    const cal = calendar[day - 1];
    const active = activeCell && activeCell.empId === emp.id && activeCell.day === day;
    const isPending = c && c.status === "pending";
    const bg = v.bg;
    return (
      <td key={"p" + day}
        data-cell={`${emp.id}-${day}`}
        onMouseEnter={(e) => { if (c && !["pre","post"].includes(c.status)) { const r = e.currentTarget.getBoundingClientRect(); setHover({ c, emp, day, cal, x: r.left + r.width / 2, y: r.top }); } }}
        onMouseLeave={() => setHover(null)}
        onClick={(e) => {
          if (c && !["pre","post","rest","holiday"].includes(c.status)) onSelectCell({ empId: emp.id, day });
          if (isPending) { const r = e.currentTarget.getBoundingClientRect(); setHover(null); setMenu({ empId: emp.id, day, x: r.left + r.width / 2, y: r.bottom, suggest: c.suggest, c }); }
        }}
        style={{
          position: "relative", width: CELL_W, minWidth: CELL_W, maxWidth: CELL_W, height: 34,
          padding: 0, textAlign: "center", verticalAlign: "middle",
          color: v.fg, background: bg,
          borderRight: "1px solid var(--line)", borderBottom: "1px solid var(--line)",
          borderLeft: v.bar ? `3px solid ${v.bar}` : undefined,
          outline: active ? "2px solid var(--accent)" : isPending ? "1.5px dashed var(--accent)" : "none",
          outlineOffset: active ? "-2px" : "-1.5px",
          boxShadow: active ? "0 0 0 3px var(--accent-ring)" : undefined,
          cursor: c && !["pre","post","rest","holiday"].includes(c.status) ? "pointer" : "default",
          zIndex: active ? 3 : isPending ? 2 : "auto",
        }}>
        {v.stripe && <span style={{ position: "absolute", inset: 0, pointerEvents: "none", background: "repeating-linear-gradient(45deg, transparent, transparent 5px, color-mix(in srgb, var(--s-field-bar) 10%, transparent) 5px, color-mix(in srgb, var(--s-field-bar) 10%, transparent) 6px)" }} />}
        {v.hatch && <span style={{ position: "absolute", inset: 0, pointerEvents: "none", background: "repeating-linear-gradient(45deg, transparent, transparent 5px, rgba(255,255,255,.18) 5px, rgba(255,255,255,.18) 6px)" }} />}
        {v.inactive && <span style={{ position: "absolute", inset: 0, pointerEvents: "none", background: "repeating-linear-gradient(45deg, transparent, transparent 4px, color-mix(in srgb, var(--ink-3) 9%, transparent) 4px, color-mix(in srgb, var(--ink-3) 9%, transparent) 5px)" }} />}
        {c && c.swap && <span title="个人调班来的班" style={{ position: "absolute", left: 0, top: 0, width: 0, height: 0, borderTop: "8px solid var(--s-swap-line)", borderRight: "8px solid transparent" }} />}
        <PunchContent c={c} v={v} />
        {c && cornerBadge(v, c)}
      </td>
    );
  }

  function renderOtCell(emp, day) {
    const c = emp.cells[day];
    const v = getVisual(c);
    const show = c && c.ot ? c.ot : null;
    return (
      <td key={"o" + day} style={{
        width: CELL_W, minWidth: CELL_W, maxWidth: CELL_W, height: 18, padding: 0, textAlign: "center",
        background: v.rest || v.inactive ? v.bg : tint(v.bg),
        color: "var(--s-ot-fg)", fontSize: 9,
        borderRight: "1px solid var(--line)", borderBottom: "1px solid var(--line-2)",
        borderLeft: v.bar ? `3px solid color-mix(in srgb, ${v.bar} 45%, transparent)` : undefined,
      }} className="tnum">
        {show ? <span style={{ fontWeight: 600 }}>{show}</span> : <span style={{ opacity: .25 }}>·</span>}
      </td>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      <div ref={wrapRef} style={{ flex: 1, minHeight: 0, overflow: "auto", position: "relative", background: "var(--surface)" }}>
        <table style={{ borderCollapse: "separate", borderSpacing: 0, tableLayout: "fixed" }}>
          <thead>
            <tr>
              <th style={{
                position: "sticky", top: 0, left: 0, zIndex: 6, width: NAME_W, minWidth: NAME_W,
                background: headBg, borderRight: "1px solid var(--line-2)", borderBottom: "1px solid var(--line-2)",
                boxShadow: stickyShadow, padding: "0 10px", textAlign: "left",
                fontSize: 11, fontWeight: 600, color: "var(--ink-2)", height: 44,
              }}>姓名 · 工号</th>
              {calendar.map((cal) => {
                const wknd = cal.type === "rest", hol = cal.type === "holiday";
                return (
                  <th key={cal.d} style={{
                    position: "sticky", top: 0, zIndex: 4, width: CELL_W, minWidth: CELL_W,
                    background: wknd || hol ? "color-mix(in srgb, var(--surface-3) 78%, var(--surface-2))" : headBg,
                    borderRight: "1px solid var(--line)", borderBottom: "1px solid var(--line-2)",
                    padding: "3px 0", height: 44,
                  }}>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", lineHeight: 1.1, gap: 1 }}>
                      <span className="tnum" style={{ fontSize: 12.5, fontWeight: 700, color: wknd || hol ? "var(--ink-3)" : "var(--ink)" }}>{cal.d}</span>
                      <span style={{ fontSize: 9, color: "var(--ink-3)" }}>周{cal.wk}</span>
                      <span style={{
                        fontSize: 8, fontWeight: 700, padding: "0 4px", borderRadius: 3, lineHeight: "12px",
                        background: hol ? "color-mix(in srgb, var(--s-swap-bg) 80%, transparent)" : wknd ? "color-mix(in srgb, var(--ink-3) 14%, transparent)" : "color-mix(in srgb, var(--ok) 14%, transparent)",
                        color: hol ? "var(--s-swap-fg)" : wknd ? "var(--ink-2)" : "var(--ok)",
                      }}>{hol ? "假" : wknd ? "休" : "班"}</span>
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {rows.map((emp) => {
              const isFull = fullSet && fullSet.has(emp.id);
              const dropped = included && !included.has(emp.id);
              return (
                <React.Fragment key={emp.id}>
                  <tr>
                    <th rowSpan={2} style={{
                      position: "sticky", left: 0, zIndex: 2, width: NAME_W, minWidth: NAME_W,
                      background: dropped ? "var(--surface-3)" : isFull ? "var(--s-full-bg)" : "var(--surface)",
                      borderRight: "1px solid var(--line-2)", borderBottom: "1px solid var(--line)",
                      boxShadow: stickyShadow, padding: "0 10px", textAlign: "left", verticalAlign: "middle",
                      opacity: dropped ? .5 : 1,
                    }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
                        {isFull && <span style={{ color: "var(--s-full-fg)", lineHeight: 0 }} title="全勤"><SIcon name="star" size={12} /></span>}
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontSize: 12.5, fontWeight: 600, color: dropped ? "var(--ink-3)" : "var(--ink)", textDecoration: dropped ? "line-through" : "none", display: "flex", alignItems: "center", gap: 5 }}>
                            {emp.name}
                            {emp.type !== "正式" && <span style={{ fontSize: 9, fontWeight: 600, color: "var(--ink-2)", background: "var(--surface-3)", borderRadius: 3, padding: "0 4px" }}>{emp.type}</span>}
                          </div>
                          <div className="tnum" style={{ fontSize: 9.5, color: "var(--ink-3)" }}>{emp.id} · {emp.pos}</div>
                        </div>
                      </div>
                    </th>
                    {calendar.map((cal) => renderPunchCell(emp, cal.d))}
                  </tr>
                  <tr>
                    {calendar.map((cal) => renderOtCell(emp, cal.d))}
                  </tr>
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
        {rows.length === 0 && (
          <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", color: "var(--ink-3)", fontSize: 13 }}>没有符合条件的人员</div>
        )}
      </div>

      <Legend />

      {hover && <HoverCard {...hover} />}
      {menu && <ReclassMenu menu={menu} onClose={() => setMenu(null)} onPick={(val) => { onReclassify(menu.empId, menu.day, val); setMenu(null); }} />}
    </div>
  );
}

// ---- floating explain card ----
function HoverCard({ c, emp, day, cal, x, y }) {
  const ref = useRef(null);
  const [pos, setPos] = useState({ left: x, top: y, place: "above" });
  useLayoutEffect(() => {
    const el = ref.current; if (!el) return;
    const w = el.offsetWidth, h = el.offsetHeight;
    let left = x - w / 2; left = Math.max(8, Math.min(left, window.innerWidth - w - 8));
    let top = y - h - 10, place = "above";
    if (top < 8) { top = y + 40; place = "below"; }
    setPos({ left, top, place });
  }, [x, y]);
  const [title, sub] = AttData.reasonFor(c);
  const otF = AttData.otFormula(c);
  return (
    <div ref={ref} style={{
      position: "fixed", left: pos.left, top: pos.top, zIndex: 200, width: 232,
      background: "var(--surface)", border: "1px solid var(--line-2)", borderRadius: 10,
      boxShadow: "var(--shadow-3)", padding: 11, pointerEvents: "none", fontSize: 12,
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontWeight: 700, color: "var(--ink)" }}>{emp.name} · {day} 日</span>
        <span style={{ fontSize: 10, color: "var(--ink-3)" }}>周{cal.wk} · {cal.type === "work" ? "上班" : cal.type === "rest" ? "休息" : "假"}</span>
      </div>
      <div style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "2px 8px", borderRadius: 6, background: "var(--surface-3)", marginBottom: 7 }}>
        <Swatch kind={c.status === "pending" ? (c.suggest||"miss") : c.status} bar={c.status==="field"} />
        <span style={{ fontWeight: 600, color: "var(--ink)" }}>{title}</span>
      </div>
      <div style={{ color: "var(--ink-2)", lineHeight: 1.5, marginBottom: 8 }}>{sub}</div>
      <div style={{ borderTop: "1px solid var(--line)", paddingTop: 7, display: "grid", gap: 4 }}>
        <Row k="当天打卡" v={(c.punches && c.punches.length) ? c.punches.join("  ·  ") : "无记录"} />
        {otF && <Row k="加班" v={otF} />}
      </div>
    </div>
  );
}
function Row({ k, v }) {
  return (<div style={{ display: "flex", gap: 8, fontSize: 11.5 }}>
    <span style={{ color: "var(--ink-3)", flex: "0 0 52px" }}>{k}</span>
    <span className="tnum" style={{ color: "var(--ink-2)", flex: 1 }}>{v}</span>
  </div>);
}

// ---- reclassify popover ----
function ReclassMenu({ menu, onClose, onPick }) {
  const ref = useRef(null);
  const [pos, setPos] = useState({ left: menu.x, top: menu.y });
  useLayoutEffect(() => {
    const el = ref.current; if (!el) return;
    const w = el.offsetWidth, h = el.offsetHeight;
    let left = menu.x - w / 2; left = Math.max(8, Math.min(left, window.innerWidth - w - 8));
    let top = menu.y + 8; if (top + h > window.innerHeight - 8) top = menu.y - h - 40;
    setPos({ left, top });
  }, [menu]);
  useEffect(() => {
    const h = (e) => { if (ref.current && !ref.current.contains(e.target)) onClose(); };
    const k = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("mousedown", h); document.addEventListener("keydown", k);
    return () => { document.removeEventListener("mousedown", h); document.removeEventListener("keydown", k); };
  }, []);
  const opts = [
    { k: "miss", label: "缺卡", desc: "当天仅 1 次打卡", color: "var(--s-miss-fg)" },
    { k: "biz", label: "公出", desc: "外出公干，计出勤", color: "var(--s-biz-fg)" },
    { k: "absent", label: "未出勤", desc: "当天确实没来", color: "var(--s-absent-bg)" },
  ];
  return (
    <div ref={ref} style={{ position: "fixed", left: pos.left, top: pos.top, zIndex: 250, width: 216,
      background: "var(--surface)", border: "1px solid var(--line-2)", borderRadius: 11, boxShadow: "var(--shadow-3)", padding: 7 }}>
      <div style={{ fontSize: 11, color: "var(--ink-3)", padding: "3px 6px 6px" }}>归类为</div>
      {opts.map((o) => {
        const isSuggest = o.k === menu.suggest;
        return (
          <button key={o.k} onClick={() => onPick(o.k)} style={{
            width: "100%", display: "flex", alignItems: "center", gap: 9, padding: "8px 8px", border: "none",
            borderRadius: 8, background: "transparent", textAlign: "left",
          }} onMouseEnter={e=>e.currentTarget.style.background="var(--surface-3)"} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
            <Swatch kind={o.k} />
            <span style={{ flex: 1 }}>
              <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--ink)" }}>{o.label}</span>
                {isSuggest && <span style={{ fontSize: 9, fontWeight: 700, color: "var(--accent-strong)", background: "var(--accent-soft)", borderRadius: 4, padding: "1px 5px" }}>建议</span>}
              </span>
              <span style={{ display: "block", fontSize: 10.5, color: "var(--ink-3)" }}>{o.desc}</span>
            </span>
          </button>
        );
      })}
    </div>
  );
}

// ---- legend (always visible under the grid) ----
function Legend() {
  return (
    <div style={{ flex: "0 0 auto", display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap",
      padding: "8px 14px", background: "var(--surface-2)", borderTop: "1px solid var(--line)", fontSize: 11 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: "var(--ink-2)", letterSpacing: ".02em" }}>图例</span>
      {AttData.legend.map((l) => (
        <span key={l.key} style={{ display: "inline-flex", alignItems: "center", gap: 5, color: "var(--ink-2)" }}>
          <Swatch kind={l.swatch} bar={l.bar} />
          <span style={{ fontWeight: 600, color: "var(--ink)" }}>{l.label}</span>
          <span style={{ color: "var(--ink-3)", fontSize: 10.5 }}>{l.desc}</span>
        </span>
      ))}
    </div>
  );
}

Object.assign(window, { AttGrid, Legend, getVisual });
