/* ============================================================
   data.js — mock data + recompute engine for the attendance tool
   Exposes window.AttData
   Month: 2026-04 (the brief's validated real-data month)
   ============================================================ */
(function () {
  const YEAR = 2026, MONTH = 4;
  const DAYS_IN = new Date(YEAR, MONTH, 0).getDate(); // 30
  const WK = ["日", "一", "二", "三", "四", "五", "六"];

  // ---- calendar: workday / rest / holiday ----
  // base rule: Sat+Sun = rest; 2026-04-06 (Mon) = 清明 holiday
  const HOLIDAYS = { 6: "清明节" };
  function baseType(day) {
    if (HOLIDAYS[day]) return "holiday";
    const w = new Date(YEAR, MONTH - 1, day).getDay();
    return (w === 0 || w === 6) ? "rest" : "work";
  }
  const calendar = [];
  for (let d = 1; d <= DAYS_IN; d++) {
    const w = new Date(YEAR, MONTH - 1, d).getDay();
    calendar.push({ d, w, wk: WK[w], type: baseType(d), holidayName: HOLIDAYS[d] || null });
  }

  // ---- helpers to fabricate punch times deterministically ----
  function pad(n) { return String(n).padStart(2, "0"); }
  function t(h, m) { return pad(h) + ":" + pad(m); }
  function jitter(seed, lo, hi) { // deterministic pseudo-random int in [lo,hi]
    const x = Math.sin(seed * 999.7) * 10000;
    const f = x - Math.floor(x);
    return lo + Math.floor(f * (hi - lo + 1));
  }
  // overtime from out-time (minutes past 18:30), rounded to 0.5h, min 1.0 to count
  function calcOT(outH, outM) {
    const mins = (outH * 60 + outM) - (18 * 60 + 30);
    if (mins < 50) return 0;
    return Math.max(1, Math.round((mins / 60) * 2) / 2);
  }

  // build a normal present cell for emp #i on day d
  function normalCell(i, d) {
    const inM = jitter(i * 31 + d, 44, 59);                 // 08:44–08:59
    const outBaseH = 18, outM = jitter(i * 53 + d * 7, 30, 58);
    let outH = outBaseH, om = outM;
    // a few people work later → overtime
    const lateWorker = (i === 10 || i === 2 || i === 16); // 吴昊 / 王芳 / 林峰
    if (lateWorker) { outH = 19 + jitter(i + d, 0, 1); om = jitter(d, 0, 55); }
    const ot = calcOT(outH, om);
    return {
      status: "normal",
      punches: [t(8, inM), t(outH, om)],
      in: t(8, inM), out: t(outH, om),
      ot,
    };
  }

  const NO_OT = new Set(["E01"]); // 经理 不计加班名单

  // ---- employees ----
  const ROSTER = [
    { id: "E01", name: "张伟", pos: "部门经理", type: "正式" },
    { id: "E02", name: "王芳", pos: "项目主管", type: "正式" },
    { id: "E03", name: "李娜", pos: "运营专员", type: "正式" },
    { id: "E04", name: "刘洋", pos: "运营专员", type: "正式" },
    { id: "E05", name: "陈静", pos: "行政助理", type: "正式" },
    { id: "E06", name: "杨磊", pos: "市场专员", type: "正式" },
    { id: "E07", name: "赵敏", pos: "财务", type: "正式" },
    { id: "E08", name: "黄强", pos: "销售", type: "正式" },
    { id: "E09", name: "周婷", pos: "行政", type: "正式" },
    { id: "E10", name: "吴昊", pos: "技术", type: "正式" },
    { id: "E11", name: "徐丽", pos: "客服", type: "正式" },
    { id: "E12", name: "孙鹏", pos: "销售", type: "正式" },
    { id: "E13", name: "马超", pos: "运营实习", type: "实习", join: 8 },
    { id: "E14", name: "朱琳", pos: "运营专员", type: "正式", leave: 9 },
    { id: "E15", name: "胡军", pos: "驻场支持", type: "外包" },
    { id: "E16", name: "林峰", pos: "市场实习", type: "实习", leave: 6 },
  ];

  // individual shift-swaps:  E01 works Sat 11, rests Mon 13
  const SWAPS = {
    E01: { 11: "work", 13: "rest" },
  };
  function effType(empId, day) {
    const sw = SWAPS[empId];
    if (sw && sw[day]) return { type: sw[day], swapped: true };
    const c = calendar[day - 1];
    return { type: c.type, swapped: false };
  }

  // event overrides keyed by empId -> day -> patch
  // status set here is FINAL for non-pending; pending carries `suggest`
  function lateCell(i, d, hh, mm, heavy) {
    const base = normalCell(i, d);
    base.in = t(hh, mm); base.punches[0] = t(hh, mm);
    base.status = heavy ? "lateheavy" : "late";
    base.note = "上午 " + t(hh, mm) + " 打卡，迟于 09:00";
    return base;
  }
  function earlyCell(i, d, hh, mm) {
    const base = normalCell(i, d);
    base.out = t(hh, mm); base.punches[1] = t(hh, mm); base.ot = 0;
    base.status = "early";
    base.note = "下午 " + t(hh, mm) + " 离开，早于 18:30";
    return base;
  }
  function fieldCell(i, d) {
    const base = normalCell(i, d);
    base.status = "field";
    base.punches = [base.in + "(外勤)", base.out];
    base.field = true;
    base.note = "当天含外勤打卡标记";
    return base;
  }
  function pendingCell(i, d, suggest, punches, reason) {
    return {
      status: "pending", suggest, punches,
      in: punches[0] || null, out: punches[1] || null, ot: 0,
      reason,
    };
  }

  const EVENTS = {
    E03: { 7:  lateCell(3, 7, 9, 18, false), 15: earlyCell(3, 15, 17, 42) },
    E04: { 9:  lateCell(4, 9, 9, 47, true) },
    E05: { 14: pendingCell(5, 14, "miss", ["08:55"], "当天仅 1 次打卡（上午），下午无记录") },
    E06: { 8:  fieldCell(6, 8), 10: fieldCell(6, 10) },
    E08: {
      20: pendingCell(8, 20, "biz", ["08:51(外勤)"], "外勤单卡 · 与 21、22 连续 → 疑似公出"),
      21: pendingCell(8, 21, "biz", [], "全天无打卡 · 处于连续空白段 → 疑似公出"),
      22: pendingCell(8, 22, "biz", [], "全天无打卡 · 处于连续空白段 → 疑似公出"),
    },
    E09: { 16: pendingCell(9, 16, "absent", [], "全天无任何打卡，前后均正常出勤") },
    E11: { 23: lateCell(11, 23, 9, 12, false),
           30: pendingCell(11, 30, "miss", ["09:02"], "当天仅 1 次打卡（上午），下午无记录") },
    E12: { 17: fieldCell(12, 17), 28: earlyCell(12, 28, 18, 5) },
  };

  // ---- build per-employee cells ----
  const employees = ROSTER.map((r, idx) => {
    const i = idx + 1;
    const cells = {};
    const ev = EVENTS[r.id] || {};
    let punchDays = 0;
    for (let d = 1; d <= DAYS_IN; d++) {
      // out of active range
      if (r.join && d < r.join) { cells[d] = { status: "pre" }; continue; }
      if (r.leave && d > r.leave) { cells[d] = { status: "post" }; continue; }

      const et = effType(r.id, d);
      if (ev[d]) { cells[d] = ev[d]; if ((ev[d].punches || []).length) punchDays++; if (et.swapped) cells[d].swap = true; continue; }

      if (et.type === "rest")    { cells[d] = { status: "rest" }; continue; }
      if (et.type === "holiday") { cells[d] = { status: "holiday", holidayName: calendar[d-1].holidayName }; continue; }

      // working day → normal punches
      const c = normalCell(i, d);
      if (et.swapped) { c.swap = true; c.note = "个人调班：休息日调为上班"; }
      if (NO_OT.has(r.id)) c.ot = 0;
      cells[d] = c;
      punchDays++;
    }
    const leaver = !!r.leave;
    return {
      ...r, idx, cells, punchDays,
      leaver,
      // leavers with <7 punch days need the keep/drop decision
      needsKeepDecision: leaver && punchDays < 7,
    };
  });

  // ---- semantic legend (resolved color system) ----
  const legend = [
    { key: "late",      label: "迟到", desc: "09:00–09:30 到", icon: "clock", swatch: "late",  fill: false },
    { key: "lateheavy", label: "迟到较重", desc: "晚于 09:30", icon: "clock2", swatch: "lateheavy", fill: true },
    { key: "early",     label: "早退", desc: "早于 18:30 离开", icon: "exit", swatch: "early", fill: true },
    { key: "absent",    label: "未出勤", desc: "全天无打卡", icon: "cross", swatch: "absent", fill: true },
    { key: "miss",      label: "缺卡", desc: "当天仅 1 次打卡", icon: "half", swatch: "miss", fill: true },
    { key: "biz",       label: "公出", desc: "外出公干", icon: "bag", swatch: "biz", fill: true },
    { key: "field",     label: "外勤日", desc: "当天含外勤打卡", icon: "pin", swatch: "field", bar: true },
    { key: "full",      label: "全勤", desc: "整月无异常（姓名底色）", icon: "star", swatch: "full", fill: true },
    { key: "swap",      label: "调班上班", desc: "个人调班调来的班", icon: "swap", swatch: "swap", fill: true },
  ];

  // statuses that count as an "anomaly" (break full-attendance)
  const ANOMALY = new Set(["late", "lateheavy", "early", "absent", "miss", "pending"]);

  // ---- stats / recompute (pure) ----
  // `included` : Set of empIds to include (leaver decisions). default: all kept.
  function computeStats(emps, included) {
    const counts = { late: 0, lateheavy: 0, early: 0, absent: 0, miss: 0, biz: 0, field: 0 };
    let otTotal = 0, pending = 0;
    const fullList = [];
    const anomalyPeople = new Set();
    emps.forEach((e) => {
      if (included && !included.has(e.id)) return;
      let hasAnomaly = false, anyWork = false;
      Object.values(e.cells).forEach((c) => {
        if (!c || c.status === "rest" || c.status === "holiday" || c.status === "pre" || c.status === "post") return;
        anyWork = true;
        if (c.status === "pending") { pending++; hasAnomaly = true; }
        if (counts[c.status] !== undefined) counts[c.status]++;
        if (ANOMALY.has(c.status)) hasAnomaly = true;
        if (c.ot) otTotal += c.ot;
      });
      if (anyWork && !hasAnomaly) fullList.push(e);
      if (hasAnomaly) anomalyPeople.add(e.id);
    });
    return {
      counts, otTotal: Math.round(otTotal * 10) / 10, pending,
      fullList, fullSet: new Set(fullList.map(e => e.id)),
      anomalyPeople,
    };
  }

  // person-level overtime + flags (for inspector / dashboard)
  function personSummary(e, included) {
    let ot = 0, late = 0, early = 0, miss = 0, absent = 0, biz = 0, field = 0, pend = 0, workDays = 0;
    Object.values(e.cells).forEach((c) => {
      if (!c) return;
      if (["rest","holiday","pre","post"].includes(c.status)) return;
      workDays++;
      if (c.ot) ot += c.ot;
      if (c.status === "late" || c.status === "lateheavy") late++;
      if (c.status === "early") early++;
      if (c.status === "miss") miss++;
      if (c.status === "absent") absent++;
      if (c.status === "biz") biz++;
      if (c.status === "field") field++;
      if (c.status === "pending") pend++;
    });
    const included_ = !included || included.has(e.id);
    const full = included_ && workDays > 0 && !late && !early && !miss && !absent && !pend;
    return { ot: Math.round(ot * 10) / 10, late, early, miss, absent, biz, field, pend, workDays, full };
  }

  // human reason text for a cell (for hover card + inspector)
  function reasonFor(c) {
    switch (c.status) {
      case "normal": return ["正常出勤", c.swap ? "（个人调班调来的班）" : "上午按时到岗、下午按时离开"];
      case "late": return ["迟到", (c.note || "09:00–09:30 之间到岗")];
      case "lateheavy": return ["迟到较重", (c.note || "晚于 09:30 到岗")];
      case "early": return ["早退", (c.note || "早于 18:30 离开")];
      case "absent": return ["未出勤", "当天没有任何打卡记录"];
      case "miss": return ["缺卡", "当天仅 1 次打卡，缺少另一次"];
      case "biz": return ["公出", "外出公干，按出勤计"];
      case "field": return ["外勤日", "当天含外勤打卡标记"];
      case "pending": return ["待归类", (c.reason || "当天打卡少于 2 次，需人工判定")];
      case "rest": return ["休息日", "本日按调班表为休息"];
      case "holiday": return ["法定节假日", c.holidayName || ""];
      case "pre": return ["未入职", "该员工本日尚未入职"];
      case "post": return ["已离职", "该员工本日已离职"];
      default: return ["—", ""];
    }
  }

  // how OT was derived (string)
  function otFormula(c) {
    if (!c || !c.out || c.status === "rest" || c.status === "holiday") return null;
    if (NO_OT_NOTE(c)) return "在「不计加班名单」中，本月不计加班";
    if (!c.ot) return "下班 " + (c.out || "—") + "，未达加班起算（18:30 + ≥50 分钟）";
    return "(" + c.out + " − 18:30) ≈ " + c.ot + " 小时（按 0.5h 取整）";
  }
  function NO_OT_NOTE() { return false; } // simplified; manager handled at build

  window.AttData = {
    year: YEAR, month: MONTH, daysIn: DAYS_IN, calendar, employees,
    legend, computeStats, personSummary, reasonFor, otFormula,
    noOtList: ["张伟"], strictLateList: [], redOnlyList: [],
    dataDir: "D:\\考勤\\2026-04",
    files: [
      { role: "打卡原表", name: "钉钉打卡_2026-04.xlsx", month: "2026-04", ok: true },
      { role: "员工花名册", name: "员工花名册.xlsx", month: "—", ok: true },
      { role: "调班表", name: "调班表_2026-04.xlsx", month: "2026-04", ok: true },
    ],
  };
})();
