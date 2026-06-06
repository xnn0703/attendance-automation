/* ui.jsx — shared primitives: status icons, generic icons, small helpers */

// tiny semantic glyphs that ride along with color (colorblind-friendly)
function SIcon({ name, size = 11 }) {
  const s = { width: size, height: size, display: "block" };
  const sw = 1.7;
  switch (name) {
    case "clock": // late
      return (<svg style={s} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth={sw} strokeLinecap="round"><circle cx="8" cy="8" r="6"/><path d="M8 5v3.2L10.2 10"/></svg>);
    case "clock2": // late-heavy (filled clock)
      return (<svg style={s} viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.2" fill="currentColor"/><path d="M8 4.4v3.9l2.4 1.6" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" fill="none"/></svg>);
    case "exit": // early-leave (door + out arrow)
      return (<svg style={s} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round"><path d="M9.5 2.5h-6v11h6"/><path d="M7 8h7m0 0-2.4-2.4M14 8l-2.4 2.4"/></svg>);
    case "cross": // absent
      return (<svg style={s} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><path d="M4 4l8 8M12 4l-8 8"/></svg>);
    case "half": // missing punch (half-filled)
      return (<svg style={s} viewBox="0 0 16 16"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" strokeWidth={sw}/><path d="M8 2a6 6 0 0 1 0 12z" fill="currentColor"/></svg>);
    case "bag": // business trip
      return (<svg style={s} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth={sw} strokeLinejoin="round"><rect x="2.5" y="5" width="11" height="8.5" rx="1.4"/><path d="M6 5V3.6c0-.6.4-1 1-1h2c.6 0 1 .4 1 1V5"/></svg>);
    case "pin": // field work
      return (<svg style={s} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth={sw} strokeLinejoin="round"><path d="M8 14.5c2.8-3 4.3-5.3 4.3-7.3a4.3 4.3 0 1 0-8.6 0c0 2 1.5 4.3 4.3 7.3Z"/><circle cx="8" cy="7" r="1.5"/></svg>);
    case "star": // full attendance
      return (<svg style={s} viewBox="0 0 16 16"><path d="M8 1.5l1.9 3.9 4.3.6-3.1 3 .7 4.3L8 11.3 4.2 13.3l.7-4.3-3.1-3 4.3-.6z" fill="currentColor"/></svg>);
    case "swap":
      return (<svg style={s} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round"><path d="M3 5.5h8m0 0L8.5 3M11 5.5 8.5 8M13 10.5H5m0 0L7.5 8M5 10.5 7.5 13"/></svg>);
    default: return null;
  }
}

// generic UI icons
function Icon({ name, size = 16, sw = 1.7 }) {
  const s = { width: size, height: size, display: "block", flex: "0 0 auto" };
  const p = { fill: "none", stroke: "currentColor", strokeWidth: sw, strokeLinecap: "round", strokeLinejoin: "round" };
  switch (name) {
    case "search": return (<svg style={s} viewBox="0 0 20 20" {...p}><circle cx="9" cy="9" r="6"/><path d="M14 14l3.5 3.5"/></svg>);
    case "check": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M4 10.5l4 4 8-9"/></svg>);
    case "chevron-right": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M7.5 4l6 6-6 6"/></svg>);
    case "chevron-down": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M4 7.5l6 6 6-6"/></svg>);
    case "arrow-right": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M3.5 10h13m0 0-5-5M16.5 10l-5 5"/></svg>);
    case "alert": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M10 2.5 18.5 17H1.5L10 2.5Z"/><path d="M10 8v4"/><circle cx="10" cy="14.6" r=".4" fill="currentColor" stroke="none"/></svg>);
    case "info": return (<svg style={s} viewBox="0 0 20 20" {...p}><circle cx="10" cy="10" r="7.5"/><path d="M10 9v4.5"/><circle cx="10" cy="6.4" r=".5" fill="currentColor" stroke="none"/></svg>);
    case "folder": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M2.5 5.5c0-.6.4-1 1-1h4l1.5 2h6.5c.6 0 1 .4 1 1v6c0 .6-.4 1-1 1h-12c-.6 0-1-.4-1-1z"/></svg>);
    case "file": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M5 2.5h7l4 4v11H5z"/><path d="M12 2.5v4h4"/></svg>);
    case "download": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M10 3v9m0 0 4-4M10 12 6 8"/><path d="M3.5 15.5h13"/></svg>);
    case "x": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M5 5l10 10M15 5L5 15"/></svg>);
    case "undo": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M7 8H4V5"/><path d="M4 8a8 8 0 1 1-1.5 4.6"/></svg>);
    case "settings": return (<svg style={s} viewBox="0 0 20 20" {...p}><circle cx="10" cy="10" r="2.6"/><path d="M10 1.5v2.2M10 16.3v2.2M3.5 3.5l1.6 1.6M14.9 14.9l1.6 1.6M1.5 10h2.2M16.3 10h2.2M3.5 16.5l1.6-1.6M14.9 5.1l1.6-1.6"/></svg>);
    case "user": return (<svg style={s} viewBox="0 0 20 20" {...p}><circle cx="10" cy="7" r="3.2"/><path d="M4 16.5c1-3 3.2-4.2 6-4.2s5 1.2 6 4.2"/></svg>);
    case "filter": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M3 5h14l-5.5 6.5V16l-3 1.5v-6z"/></svg>);
    case "next-issue": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M5 4v12M10 4l6 6-6 6"/></svg>);
    case "list": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M7 5.5h10M7 10h10M7 14.5h10"/><circle cx="3.5" cy="5.5" r=".6" fill="currentColor" stroke="none"/><circle cx="3.5" cy="10" r=".6" fill="currentColor" stroke="none"/><circle cx="3.5" cy="14.5" r=".6" fill="currentColor" stroke="none"/></svg>);
    case "grid": return (<svg style={s} viewBox="0 0 20 20" {...p}><rect x="3" y="3" width="14" height="14" rx="1.5"/><path d="M3 8h14M8 3v14"/></svg>);
    case "spark": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M10 2v4M10 14v4M2 10h4M14 10h4"/></svg>);
    case "clock": return (<svg style={s} viewBox="0 0 20 20" {...p}><circle cx="10" cy="10" r="7.5"/><path d="M10 6v4.3l2.8 1.7"/></svg>);
    case "refresh": return (<svg style={s} viewBox="0 0 20 20" {...p}><path d="M16.5 4.5v3.5H13"/><path d="M16 8a6.5 6.5 0 1 0 .3 3.6"/></svg>);
    default: return null;
  }
}

// swatch chip used in legend + grid demos
function Swatch({ kind, fill, bar, withIcon }) {
  const m = {
    late: ["--s-late-bg","--s-late-line","--s-late-fg","clock"],
    lateheavy: ["--s-lateheavy-bg","--s-lateheavy-line","--s-lateheavy-fg","clock2"],
    early: ["--s-early-bg","--s-early-line","--s-early-fg","exit"],
    absent: ["--s-absent-bg","--s-absent-line","--s-absent-fg","cross"],
    miss: ["--s-miss-bg","--s-miss-line","--s-miss-fg","half"],
    biz: ["--s-biz-bg","--s-biz-line","--s-biz-fg","bag"],
    field: ["--s-field-bg","--s-field-line","--s-field-fg","pin"],
    full: ["--s-full-bg","--s-full-line","--s-full-fg","star"],
    swap: ["--s-swap-bg","--s-swap-line","--s-swap-fg","swap"],
  }[kind];
  if (!m) return null;
  const [bg, line, fg, icon] = m;
  return (
    <span style={{
      width: 26, height: 18, borderRadius: 4, flex: "0 0 auto",
      background: kind === "field" ? "var(--s-field-bg)" : `var(${bg})`,
      border: `1px solid var(${line})`,
      borderLeft: bar ? `3px solid var(--s-field-bar)` : `1px solid var(${line})`,
      color: `var(${fg})`,
      display: "inline-flex", alignItems: "center", justifyContent: "center",
      position: "relative",
    }}>
      {withIcon !== false && <SIcon name={icon} size={10} />}
      {kind === "field" && <span style={{position:"absolute",inset:0,borderRadius:3,
        background:"repeating-linear-gradient(45deg, transparent, transparent 3px, color-mix(in srgb, var(--s-field-bar) 18%, transparent) 3px, color-mix(in srgb, var(--s-field-bar) 18%, transparent) 4px)"}}/>}
    </span>
  );
}

Object.assign(window, { SIcon, Icon, Swatch });
