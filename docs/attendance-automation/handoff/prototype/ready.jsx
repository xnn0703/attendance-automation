/* ready.jsx — phase ① 准备：drop zone + ready card + states (empty/loading/ok/warn/error) */

function StateTabs({ variant, setVariant }) {
  const opts = [["empty", "空态"], ["loading", "解析中"], ["ok", "校验通过"], ["warning", "有警告"], ["error", "缺表"]];
  return (
    <div style={{ position: "absolute", top: 14, right: 16, display: "flex", alignItems: "center", gap: 8, zIndex: 5 }}>
      <span style={{ fontSize: 10.5, color: "var(--ink-3)", fontWeight: 600 }}>演示状态</span>
      <div style={{ display: "flex", background: "var(--surface-2)", border: "1px solid var(--line)", borderRadius: 8, padding: 2 }}>
        {opts.map(([k, l]) => (
          <button key={k} onClick={() => setVariant(k)} style={{
            padding: "4px 9px", border: "none", borderRadius: 6, fontSize: 11, fontWeight: 600,
            background: variant === k ? "var(--surface)" : "transparent", color: variant === k ? "var(--ink)" : "var(--ink-3)",
            boxShadow: variant === k ? "var(--shadow-1)" : "none",
          }}>{l}</button>
        ))}
      </div>
    </div>
  );
}

function DropZone({ onPick }) {
  const [over, setOver] = React.useState(false);
  return (
    <div style={{ flex: 1, display: "grid", placeItems: "center", padding: 32 }}>
      <div onClick={onPick} onDragOver={(e) => { e.preventDefault(); setOver(true); }} onDragLeave={() => setOver(false)} onDrop={(e) => { e.preventDefault(); setOver(false); onPick(); }}
        style={{
          width: 560, maxWidth: "90%", padding: "56px 40px", borderRadius: 18, textAlign: "center", cursor: "pointer",
          border: `2px dashed ${over ? "var(--accent)" : "var(--line-2)"}`, background: over ? "var(--accent-soft)" : "var(--surface)",
          transition: "all .18s",
        }}>
        <div style={{ width: 64, height: 64, borderRadius: 16, background: "var(--accent-soft)", color: "var(--accent-strong)", display: "grid", placeItems: "center", margin: "0 auto 18px" }}>
          <Icon name="folder" size={30} />
        </div>
        <div style={{ fontSize: 18, fontWeight: 700, color: "var(--ink)", marginBottom: 7 }}>选择或拖入本月数据文件夹</div>
        <div style={{ fontSize: 13, color: "var(--ink-2)", lineHeight: 1.6, maxWidth: 380, margin: "0 auto 22px" }}>
          文件夹里应包含三张表：<b>打卡原表</b>、<b>员工花名册</b>、<b>调班表</b>。<br />工具会自动识别、校验，并把能算的全部算完。
        </div>
        <button style={primaryBtn}>选择文件夹…</button>
      </div>
    </div>
  );
}

function Loading() {
  const steps = ["识别三张输入表", "解析打卡原表（钉钉导出）", "整理《初表》：删无关人 · 补工号职位", "计算工作日 / 加班 / 迟到 / 外勤"];
  const [n, setN] = React.useState(0);
  React.useEffect(() => { const id = setInterval(() => setN(v => (v + 1) % (steps.length + 1)), 700); return () => clearInterval(id); }, []);
  return (
    <div style={{ flex: 1, display: "grid", placeItems: "center" }}>
      <div style={{ width: 420, textAlign: "center" }}>
        <div style={{ width: 52, height: 52, margin: "0 auto 20px", position: "relative" }}>
          <svg width="52" height="52" viewBox="0 0 52 52" style={{ animation: "spin 1s linear infinite" }}>
            <circle cx="26" cy="26" r="21" fill="none" stroke="var(--line)" strokeWidth="5" />
            <circle cx="26" cy="26" r="21" fill="none" stroke="var(--accent)" strokeWidth="5" strokeLinecap="round" strokeDasharray="40 200" />
          </svg>
        </div>
        <div style={{ fontSize: 15, fontWeight: 700, color: "var(--ink)", marginBottom: 18 }}>正在解析与计算…</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 9, textAlign: "left", maxWidth: 320, margin: "0 auto" }}>
          {steps.map((s, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 9, fontSize: 12.5, color: i < n ? "var(--ink)" : i === n ? "var(--ink-2)" : "var(--ink-3)" }}>
              <span style={{ width: 18, height: 18, borderRadius: 999, display: "grid", placeItems: "center", flex: "0 0 auto",
                background: i < n ? "var(--ok)" : "var(--surface-3)", color: "#fff" }}>
                {i < n ? <Icon name="check" size={11} sw={2.6} /> : i === n ? <span style={{ width: 6, height: 6, borderRadius: 999, background: "var(--accent)", animation: "pulse 1s infinite" }} /> : ""}
              </span>
              {s}
            </div>
          ))}
        </div>
      </div>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}@keyframes pulse{50%{opacity:.3}}`}</style>
    </div>
  );
}

function FileTable({ files }) {
  return (
    <div style={{ border: "1px solid var(--line)", borderRadius: 11, overflow: "hidden" }}>
      {files.map((f, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "11px 14px", borderBottom: i < files.length - 1 ? "1px solid var(--line)" : "none", background: f.ok ? "var(--surface)" : "var(--s-lateheavy-bg)" }}>
          <span style={{ color: f.ok ? "var(--ink-2)" : "var(--err)", lineHeight: 0 }}><Icon name="file" size={18} /></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12.5, fontWeight: 600, color: "var(--ink)" }}>{f.role}</div>
            <div className="tnum" style={{ fontSize: 11, color: "var(--ink-3)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{f.name}</div>
          </div>
          <span className="tnum" style={{ fontSize: 11, color: "var(--ink-2)" }}>{f.month}</span>
          {f.ok
            ? <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11, fontWeight: 700, color: "var(--ok)" }}><Icon name="check" size={13} sw={2.4} />识别</span>
            : <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11, fontWeight: 700, color: "var(--err)" }}><Icon name="alert" size={13} />{f.err}</span>}
        </div>
      ))}
    </div>
  );
}

function Banner({ tone, title, body }) {
  const map = { warn: ["var(--s-late-bg)", "var(--s-late-line)", "var(--warn)", "alert"], err: ["var(--s-lateheavy-bg)", "var(--s-lateheavy-line)", "var(--err)", "alert"], ok: ["var(--s-miss-bg)", "var(--s-miss-line)", "var(--ok)", "check"] };
  const [bg, line, fg, icon] = map[tone];
  return (
    <div style={{ display: "flex", gap: 11, padding: "12px 14px", borderRadius: 11, background: bg, border: `1px solid ${line}` }}>
      <span style={{ color: fg, lineHeight: 0, flex: "0 0 auto", marginTop: 1 }}><Icon name={icon} size={18} /></span>
      <div>
        <div style={{ fontSize: 13, fontWeight: 700, color: "var(--ink)", marginBottom: 2 }}>{title}</div>
        <div style={{ fontSize: 12, color: "var(--ink-2)", lineHeight: 1.55 }}>{body}</div>
      </div>
    </div>
  );
}

function ReadyCard({ variant, todos, people, onStart }) {
  const warn = variant === "warning", err = variant === "error";
  const files = warn
    ? [{ role: "打卡原表", name: "钉钉打卡_2026-03.xlsx", month: "2026-03", ok: false, err: "月份不一致" }, ...AttData.files.slice(1)]
    : err
    ? [AttData.files[0], AttData.files[1], { role: "调班表", name: "—— 未找到 ——", month: "—", ok: false, err: "缺少此表" }]
    : AttData.files;
  return (
    <div style={{ flex: 1, overflow: "auto", display: "grid", placeItems: "center", padding: "32px 24px" }}>
      <div style={{ width: 620, maxWidth: "100%", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 18, boxShadow: "var(--shadow-2)", overflow: "hidden" }}>
        {/* head */}
        <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--line)", display: "flex", alignItems: "center", gap: 14, background: "var(--surface-2)" }}>
          <span style={{ width: 46, height: 46, borderRadius: 13, background: "var(--accent)", color: "#fff", display: "grid", placeItems: "center", fontSize: 18, fontWeight: 800 }}>4<span style={{ fontSize: 10, fontWeight: 600, marginLeft: 1, alignSelf: "flex-end", marginBottom: 7 }}>月</span></span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 16.5, fontWeight: 700, color: "var(--ink)" }}>2026 年 4 月 · 考勤已就绪</div>
            <div className="tnum" style={{ fontSize: 12, color: "var(--ink-3)", display: "flex", alignItems: "center", gap: 6 }}><Icon name="folder" size={13} />{AttData.dataDir}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div className="tnum" style={{ fontSize: 26, fontWeight: 800, color: "var(--ink)", lineHeight: 1 }}>{people}</div>
            <div style={{ fontSize: 11, color: "var(--ink-3)" }}>纳入人数</div>
          </div>
        </div>

        <div style={{ padding: "18px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
          {warn && <Banner tone="warn" title="月份不一致 — 请先更换文件" body="打卡原表识别为 2026-03，与调班表（2026-04）不一致。请把打卡原表换成 4 月的导出文件后重试（这正是上次真实数据出错的原因）。" />}
          {err && <Banner tone="err" title="缺少「调班表」" body="未在所选文件夹找到调班表。调班表决定工作日/休息日与个人调班，缺失将无法判断当月班休。请补齐后重新选择文件夹。" />}
          {!warn && !err && <Banner tone="ok" title="三张表均已识别，月份一致（2026-04）" body="《初表》已整理：删除无关人员、补全工号与职位、按部门排序；能自动算的（工作日 / 加班 / 迟到 / 外勤 / 全勤）已全部算完。" />}

          <div>
            <div style={{ fontSize: 11.5, fontWeight: 700, color: "var(--ink-3)", letterSpacing: ".04em", marginBottom: 8 }}>识别到的输入表</div>
            <FileTable files={files} />
          </div>

          {!warn && !err && (
            <div>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: "var(--ink-3)", letterSpacing: ".04em", marginBottom: 8 }}>待你处理</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <TodoBig n={todos.leaver} label="离职取舍" sub="离职且打卡 < 7 天" icon="user" />
                <TodoBig n={todos.pending} label="逐条归类" sub="当天打卡 < 2 次" icon="list" />
              </div>
            </div>
          )}
        </div>

        <div style={{ padding: "16px 24px", borderTop: "1px solid var(--line)", display: "flex", alignItems: "center", justifyContent: "space-between", background: "var(--surface-2)" }}>
          <span style={{ fontSize: 12, color: "var(--ink-3)" }}>{warn || err ? "解决上述问题后即可开始" : <>共 <b className="tnum" style={{ color: "var(--ink-2)" }}>{todos.leaver + todos.pending}</b> 项需要你判断，其余已自动完成</>}</span>
          <button onClick={onStart} disabled={warn || err} style={{ ...primaryBtn, opacity: warn || err ? .45 : 1, cursor: warn || err ? "not-allowed" : "pointer", display: "inline-flex", alignItems: "center", gap: 7 }}>
            开始复核 <Icon name="arrow-right" size={16} sw={2} />
          </button>
        </div>
      </div>
    </div>
  );
}

function TodoBig({ n, label, sub, icon }) {
  return (
    <div style={{ border: "1px solid var(--line)", borderRadius: 11, padding: "13px 14px", display: "flex", alignItems: "center", gap: 12, background: "var(--surface)" }}>
      <span style={{ width: 38, height: 38, borderRadius: 10, background: "var(--accent-soft)", color: "var(--accent-strong)", display: "grid", placeItems: "center" }}><Icon name={icon} size={18} /></span>
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
          <span className="tnum" style={{ fontSize: 22, fontWeight: 800, color: "var(--ink)" }}>{n}</span>
          <span style={{ fontSize: 13, fontWeight: 600, color: "var(--ink)" }}>{label}</span>
        </div>
        <div style={{ fontSize: 11, color: "var(--ink-3)" }}>{sub}</div>
      </div>
    </div>
  );
}

const primaryBtn = {
  padding: "10px 20px", borderRadius: 9, border: "none", background: "var(--accent)", color: "#fff",
  fontSize: 13.5, fontWeight: 600, boxShadow: "var(--shadow-1)",
};

function ReadyScreen({ variant, setVariant, todos, people, onStart, onPick }) {
  return (
    <div style={{ position: "relative", flex: 1, minHeight: 0, display: "flex", flexDirection: "column", background: "var(--bg)" }}>
      <StateTabs variant={variant} setVariant={setVariant} />
      {variant === "empty" && <DropZone onPick={onPick} />}
      {variant === "loading" && <Loading />}
      {(variant === "ok" || variant === "warning" || variant === "error") && <ReadyCard variant={variant} todos={todos} people={people} onStart={onStart} />}
    </div>
  );
}

Object.assign(window, { ReadyScreen, primaryBtn });
