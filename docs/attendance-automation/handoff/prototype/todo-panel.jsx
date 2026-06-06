/* todo-panel.jsx — left column: To-Do (leaver keep/drop + classification queue) */

const LABELS = { miss: "缺卡", biz: "公出", absent: "未出勤" };
const LABEL_COLOR = { miss: "var(--s-miss-fg)", biz: "var(--s-biz-fg)", absent: "var(--s-absent-bg)" };

function ProgressRing({ done, total }) {
  const pct = total ? done / total : 0;
  const R = 15, C = 2 * Math.PI * R;
  return (
    <svg width="38" height="38" viewBox="0 0 38 38" style={{ flex: "0 0 auto" }}>
      <circle cx="19" cy="19" r={R} fill="none" stroke="var(--line)" strokeWidth="4" />
      <circle cx="19" cy="19" r={R} fill="none" stroke="var(--accent)" strokeWidth="4" strokeLinecap="round"
        strokeDasharray={`${C * pct} ${C}`} transform="rotate(-90 19 19)" style={{ transition: "stroke-dasharray .4s ease" }} />
      <text x="19" y="22.5" textAnchor="middle" fontSize="11" fontWeight="700" fill="var(--ink)" className="tnum">{total - done}</text>
    </svg>
  );
}

function ClassifyRow({ item, emp, cell, onClassify, onLocate, active }) {
  const [open, setOpen] = React.useState(false);
  const done = cell.status !== "pending";
  const cur = done ? cell.status : null;
  const suggest = item.suggest;
  const suspectBiz = suggest === "biz";
  return (
    <div onClick={() => onLocate(emp.id, item.day)} style={{
      border: "1px solid", borderColor: active ? "var(--accent)" : "var(--line)", borderRadius: 10,
      background: active ? "var(--accent-soft)" : "var(--surface)", padding: "9px 10px", cursor: "pointer",
      boxShadow: active ? "0 0 0 3px var(--accent-ring)" : "none", transition: "border-color .15s, box-shadow .15s",
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 5 }}>
        <span style={{ display: "flex", alignItems: "center", gap: 6, minWidth: 0 }}>
          <span style={{ fontSize: 12.5, fontWeight: 650, color: "var(--ink)" }}>{emp.name}</span>
          <span className="tnum" style={{ fontSize: 11, color: "var(--ink-3)" }}>· 4/{item.day}（周{AttData.calendar[item.day-1].wk}）</span>
        </span>
        {done
          ? <span style={{ display: "inline-flex", alignItems: "center", gap: 3, fontSize: 10.5, fontWeight: 700, color: "var(--ok)" }}><Icon name="check" size={12} sw={2.4} />已定</span>
          : suspectBiz && <span style={{ fontSize: 9.5, fontWeight: 700, color: "var(--s-biz-fg)", background: "var(--s-biz-bg)", border: "1px solid var(--s-biz-line)", borderRadius: 5, padding: "1px 5px" }}>疑似公出</span>}
      </div>
      <div className="tnum" style={{ fontSize: 11, color: "var(--ink-2)", marginBottom: 8, lineHeight: 1.45 }}>
        当天打卡：{(cell.punches && cell.punches.length) ? cell.punches.join("  ·  ") : "无记录"}
        <span style={{ display: "block", color: "var(--ink-3)", fontSize: 10.5 }}>{item.reason}</span>
      </div>

      {done ? (
        <div style={{ display: "flex", alignItems: "center", gap: 8 }} onClick={(e) => e.stopPropagation()}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "3px 9px", borderRadius: 7, background: "var(--surface-3)" }}>
            <Swatch kind={cur} /><span style={{ fontSize: 12, fontWeight: 600, color: "var(--ink)" }}>{LABELS[cur]}</span>
          </span>
          <button onClick={() => onClassify(emp.id, item.day, "pending")} style={ghostBtn}>改判</button>
        </div>
      ) : (
        <div style={{ display: "flex", alignItems: "center", gap: 7, position: "relative" }} onClick={(e) => e.stopPropagation()}>
          <button onClick={() => onClassify(emp.id, item.day, suggest)} style={{
            flex: 1, display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 6, padding: "7px 10px",
            border: "none", borderRadius: 8, background: "var(--accent)", color: "#fff", fontSize: 12, fontWeight: 600,
          }}>
            <Icon name="check" size={13} sw={2.2} /> 采纳建议：{LABELS[suggest]}
          </button>
          <button onClick={() => setOpen(o => !o)} style={{ ...ghostBtn, padding: "7px 9px" }}>改<Icon name="chevron-down" size={12} /></button>
          {open && (
            <div style={{ position: "absolute", top: "100%", right: 0, marginTop: 4, zIndex: 30, width: 150,
              background: "var(--surface)", border: "1px solid var(--line-2)", borderRadius: 9, boxShadow: "var(--shadow-2)", padding: 5 }}>
              {["miss", "biz", "absent"].map((k) => (
                <button key={k} onClick={() => { onClassify(emp.id, item.day, k); setOpen(false); }} style={{
                  width: "100%", display: "flex", alignItems: "center", gap: 8, padding: "6px 7px", border: "none",
                  borderRadius: 7, background: "transparent", textAlign: "left",
                }} onMouseEnter={e=>e.currentTarget.style.background="var(--surface-3)"} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                  <Swatch kind={k} /><span style={{ fontSize: 12.5, color: "var(--ink)" }}>{LABELS[k]}</span>
                  {k === suggest && <span style={{ marginLeft: "auto", fontSize: 9, fontWeight: 700, color: "var(--accent-strong)" }}>建议</span>}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const ghostBtn = {
  display: "inline-flex", alignItems: "center", gap: 2, padding: "6px 9px", borderRadius: 8,
  border: "1px solid var(--line-2)", background: "var(--surface)", color: "var(--ink-2)", fontSize: 12, fontWeight: 600,
};

function LeaverRow({ emp, decision, onKeep, onLocate, active }) {
  const decided = decision !== undefined;
  return (
    <div onClick={() => onLocate(emp.id, emp.leave)} style={{
      border: "1px solid", borderColor: active ? "var(--accent)" : "var(--line)", borderRadius: 10,
      background: active ? "var(--accent-soft)" : "var(--surface)", padding: "9px 10px", cursor: "pointer",
      boxShadow: active ? "0 0 0 3px var(--accent-ring)" : "none",
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 12.5, fontWeight: 650, color: "var(--ink)" }}>{emp.name}</span>
          <span style={{ fontSize: 9.5, fontWeight: 600, color: "var(--ink-2)", background: "var(--surface-3)", borderRadius: 3, padding: "0 4px" }}>{emp.type}</span>
        </span>
        {decided && <span style={{ display: "inline-flex", alignItems: "center", gap: 3, fontSize: 10.5, fontWeight: 700, color: "var(--ok)" }}><Icon name="check" size={12} sw={2.4} />{decision ? "保留" : "删除"}</span>}
      </div>
      <div className="tnum" style={{ fontSize: 11, color: "var(--ink-2)", marginBottom: 8, lineHeight: 1.45 }}>
        本月离职（4/{emp.leave}），仅打卡 <b style={{ color: "var(--warn)" }}>{emp.punchDays}</b> 天（&lt;7 天）
        <span style={{ display: "block", color: "var(--ink-3)", fontSize: 10.5 }}>打卡天数过少，是否纳入本月《考勤》？</span>
      </div>
      <div style={{ display: "flex", gap: 7 }} onClick={(e) => e.stopPropagation()}>
        <button onClick={() => onKeep(emp.id, true)} style={segBtn(decision === true)}>保留</button>
        <button onClick={() => onKeep(emp.id, false)} style={segBtn(decision === false)}>删除</button>
      </div>
    </div>
  );
}
function segBtn(on) {
  return {
    flex: 1, padding: "7px 0", borderRadius: 8, fontSize: 12.5, fontWeight: 600,
    border: on ? "none" : "1px solid var(--line-2)",
    background: on ? "var(--accent)" : "var(--surface)", color: on ? "#fff" : "var(--ink-2)",
  };
}

function SectionHead({ title, count, total, icon }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 7, padding: "2px 2px 0" }}>
      <span style={{ color: "var(--ink-2)", lineHeight: 0 }}><Icon name={icon} size={14} /></span>
      <span style={{ fontSize: 12, fontWeight: 700, color: "var(--ink)" }}>{title}</span>
      <span className="tnum" style={{ fontSize: 11, color: "var(--ink-3)", marginLeft: "auto" }}>{count}/{total}</span>
    </div>
  );
}

function TodoPanel({ employees, leavers, pendingList, decisions, keepDecisions, activeCell,
                     onClassify, onKeep, onLocate, onAdvancedOpen, onAdoptAll }) {
  const byId = Object.fromEntries(employees.map(e => [e.id, e]));

  const leaverDone = leavers.filter(e => keepDecisions[e.id] !== undefined).length;
  const classDone = pendingList.filter(p => byId[p.empId].cells[p.day].status !== "pending").length;
  const total = leavers.length + pendingList.length;
  const done = leaverDone + classDone;
  const allDone = done === total;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0, background: "var(--surface-2)", borderRight: "1px solid var(--line)" }}>
      {/* header */}
      <div style={{ flex: "0 0 auto", padding: "13px 14px", borderBottom: "1px solid var(--line)", display: "flex", alignItems: "center", gap: 12, background: "var(--surface)" }}>
        <ProgressRing done={done} total={total} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13.5, fontWeight: 700, color: "var(--ink)" }}>待办清单</div>
          <div style={{ fontSize: 11.5, color: "var(--ink-2)" }} className="tnum">
            {allDone ? <span style={{ color: "var(--ok)", fontWeight: 600 }}>全部处理完成 ✓</span> : <>剩 <b style={{ color: "var(--accent-strong)" }}>{total - done}</b> 项待定 · 已处理 {done}/{total}</>}
          </div>
        </div>
      </div>

      <div style={{ flex: 1, minHeight: 0, overflow: "auto", padding: "12px 12px 16px", display: "flex", flexDirection: "column", gap: 16 }}>
        {/* leaver decisions */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <SectionHead title="离职取舍" count={leaverDone} total={leavers.length} icon="user" />
          {leavers.map((e) => (
            <LeaverRow key={e.id} emp={e} decision={keepDecisions[e.id]} onKeep={onKeep} onLocate={onLocate}
              active={activeCell && activeCell.empId === e.id && activeCell.day === e.leave} />
          ))}
        </div>

        {/* classification queue */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ flex: 1, minWidth: 0 }}><SectionHead title="逐条归类（打卡 < 2 次）" count={classDone} total={pendingList.length} icon="list" /></div>
            {classDone < pendingList.length && (
              <button onClick={onAdoptAll} title="把所有待定项一次性按工具建议归类" style={{
                display: "inline-flex", alignItems: "center", gap: 4, padding: "4px 9px", borderRadius: 7,
                border: "1px solid var(--accent)", background: "var(--accent-soft)", color: "var(--accent-strong)",
                fontSize: 11, fontWeight: 700, flex: "0 0 auto", whiteSpace: "nowrap",
              }}>
                <Icon name="check" size={12} sw={2.4} /> 全部采纳建议
              </button>
            )}
          </div>
          {pendingList.map((p) => (
            <ClassifyRow key={p.empId + "-" + p.day} item={p} emp={byId[p.empId]} cell={byId[p.empId].cells[p.day]}
              onClassify={onClassify} onLocate={onLocate}
              active={activeCell && activeCell.empId === p.empId && activeCell.day === p.day} />
          ))}
        </div>
      </div>

      {/* advanced settings entry */}
      <button onClick={onAdvancedOpen} style={{
        flex: "0 0 auto", display: "flex", alignItems: "center", gap: 8, padding: "11px 14px",
        border: "none", borderTop: "1px solid var(--line)", background: "var(--surface)", color: "var(--ink-2)",
        fontSize: 12.5, fontWeight: 600, textAlign: "left",
      }} onMouseEnter={e=>e.currentTarget.style.background="var(--surface-3)"} onMouseLeave={e=>e.currentTarget.style.background="var(--surface)"}>
        <Icon name="settings" size={15} /> 高级设置
        <span style={{ marginLeft: "auto", color: "var(--ink-3)" }}><Icon name="chevron-right" size={14} /></span>
      </button>
    </div>
  );
}

Object.assign(window, { TodoPanel });
