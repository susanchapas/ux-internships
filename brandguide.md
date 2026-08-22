# Susan Chapas — Brand Guide

**This file is self-contained.** Paste it into any AI, coding agent, or new repository and it has everything
needed to produce on-brand software: the full token layer, exact component specifications, layout and motion
values, copy rules with an approved-string library, accessibility requirements, and page recipes. Nothing here
depends on reading another file.

- **Companions in this project:** `readme.md` (the 13-section system reference), `components/*/*.prompt.md`
  (per-component notes), `ui_kits/portfolio/` (a working click-through recreation of the real product).
- **If you have the design system available,** link `styles.css` and load `_ds_bundle.js`, then read components
  off `window.SusanChapasDesignSystem_006b36`. If you do **not**, §3 of this file is a complete, paste-ready
  token layer and §9 specifies every component precisely enough to rebuild from scratch.

---

## Table of contents

| § | Section |
| --- | --- |
| 1 | [The brand in 60 seconds](#1--the-brand-in-60-seconds) |
| 2 | [The twelve laws](#2--the-twelve-laws) |
| 3 | [Build tokens](#3--build-tokens) |
| 4 | [Colour in use](#4--colour-in-use) |
| 5 | [Typography spec](#5--typography-spec) |
| 6 | [Layout & responsive spec](#6--layout--responsive-spec) |
| 7 | [Motion spec](#7--motion-spec) |
| 8 | [Interaction state matrix](#8--interaction-state-matrix) |
| 9 | [Component specifications](#9--component-specifications) |
| 10 | [Page recipes](#10--page-recipes) |
| 11 | [Iconography](#11--iconography) |
| 12 | [Imagery](#12--imagery) |
| 13 | [Voice, language & copy library](#13--voice-language--copy-library) |
| 14 | [Disclosures & honesty rules](#14--disclosures--honesty-rules) |
| 15 | [Accessibility spec](#15--accessibility-spec) |
| 16 | [Anti-patterns](#16--anti-patterns) |
| 17 | [Extending the system](#17--extending-the-system) |
| 18 | [Known gaps](#18--known-gaps) |

---

## 1 · The brand in 60 seconds

**Who.** Susan Chapas — UX strategist, marketing professional, front-end developer and award-winning artist,
based in Jersey City, NJ. Bilingual English/Spanish. HCI at NJIT; full-stack at MIT xPRO.

**Self-description.** *"The Strategic Architect — bridging design, marketing strategy, and technical
implementation."*

**Positioning line.** *"I'm a designer who refuses to stop at the mockup."* Everything in this system serves
that claim: someone who researches, designs, builds and ships the same work.

**The product this system came from.** One five-route portfolio site — Home, About, Projects, Gallery, Contact —
plus four case-study pages. Next.js 16, Tailwind v4, Framer Motion, Lenis smooth scroll, Matter.js on the About
board. Self-described as *"neo-modern Swiss style with strong grids and negative space"* and *"cinematic motion
design."*

**What it feels like.** A dark gallery wall. Deep navy everywhere, generous negative space, one mint accent used
sparingly, warm human photography against the cool page, and motion that is smooth and slow rather than snappy.
Cool, futuristic, accessible — smoothness first.

**Audience.** Hiring managers, prospective clients (small businesses and nonprofits), collaborators, and gallery
visitors. The tone assumes an intelligent reader who is short on time.

---

## 2 · The twelve laws

Break any of these and the work stops looking like this brand.

1. **Dark only.** `--midnight` `#102f5d` is the page, top to bottom, every screen. There is no light mode.
2. **No gray.** Depth comes from translucent sky and paper over midnight, never from a neutral ramp.
3. **The accent is rationed.** One primary button, one kicker, one active state per view. Mint is never a
   background field or a large area of fill.
4. **Everything interactive is a pill.** Buttons, tabs, filters, tags, badges, icon circles — `border-radius:
   9999px`. Containers step 6/8/12/16/24px. Nothing in this system has square corners.
5. **Cards are borders, not shadows.** A 5% sky fill inside a 1px 10%-sky border. Shadow appears in exactly
   three places: paper tiles, overlays, and the active pill's glow.
6. **Hover brightens or fills. It never darkens.** Press is a uniform `scale(0.98)` with no colour change.
7. **Two easing curves, no others.** `--ease-smooth` for everything; `--ease-bounce` for rare overshoot.
8. **Focus is a 3px mint outline at 3px offset,** globally, never removed, never colour-only.
9. **Never put text on an image without `--gradient-protect`.** No flat scrims.
10. **Headlines are sentences with a turn,** and only the turn gets the gradient — never a whole headline.
11. **No emoji in product UI.** The one decorative glyph is the mint `•`.
12. **There is no logo.** Set `SC` or `Susan Chapas` in Instrument Sans Bold, mint on midnight. Never draw,
    reconstruct or approximate a mark.

---

## 3 · Build tokens

### 3.1 Paste-ready CSS

Everything below is the complete token layer. Drop it into one stylesheet, or split it back into the eight files
named in the comments. Load order matters: fonts → colors → typography → spacing → radius → elevation → motion →
base.

```css
/* ============================================================
   tokens/fonts.css
   ============================================================ */
/* Webfonts are served from Google Fonts. No binaries ship with this system —
   the upstream portfolio also loads its type over the network (next/font/google).
   Instrument Sans + Hanken Grotesk replace the upstream Space Grotesk / DM Sans pairing. */
@import url("https://fonts.googleapis.com/css2?family=Instrument+Sans:ital,wght@0,400..700;1,400..700&family=Hanken+Grotesk:ital,wght@0,300..800;1,300..800&family=Geist+Mono:wght@400;500&display=swap");

/* ============================================================
   tokens/colors.css
   ============================================================ */
:root{
  /* Base palette — lifted verbatim from src/app/globals.css */
  --midnight:#102f5d;        /* Midnight Carbon — the page */
  --midnight-deep:#091a35;   /* Deep panel: modals, tooltips, drawers */
  --paper:#f4f4f5;           /* Paper White */
  --mint:#6fcd9d;            /* Mint — the one accent color */
  --sky:#bbcdf3;             /* Soft Sky Blue — secondary accent */
  --clay:#e09f7d;            /* Soft Clay — tertiary accent, required-field marks */
  --danger:#f87171;          /* red-400, used for form error text */

  /* Alpha ramps. The whole system is built from mint / sky / paper over midnight.
     Upstream this accent is Electric Lime #ccff00; replaced here with a mint. */
  --sky-a05:rgba(187,205,243,0.05);
  --sky-a10:rgba(187,205,243,0.10);
  --sky-a15:rgba(187,205,243,0.15);
  --sky-a20:rgba(187,205,243,0.20);
  --sky-a30:rgba(187,205,243,0.30);
  --mint-a10:rgba(111,205,157,0.10);
  --mint-a20:rgba(111,205,157,0.20);
  --mint-a30:rgba(111,205,157,0.30);
  --mint-a50:rgba(111,205,157,0.50);
  --paper-a05:rgba(244,244,245,0.05);
  --paper-a40:rgba(244,244,245,0.40);
  --paper-a70:rgba(244,244,245,0.70);
  --paper-a80:rgba(244,244,245,0.80);
  --ink-a25:rgba(0,0,0,0.25);

  /* On-light variants. NOT new colours — darker siblings of mint / clay / sky, required because the
     accent is pale and the About tiles invert to Paper White. Use ONLY on --surface-tile or --paper. */
  --mint-ink:#2f7d5a;        /* 4.5:1 on paper */
  --clay-ink:#b56a3f;        /* 3.7:1 on paper */
  --sky-ink:#3f6ab5;         /* 4.8:1 on paper */

  /* Semantic surfaces */
  --surface-page:var(--midnight);
  --surface-card:var(--sky-a05);
  --surface-card-hover:var(--sky-a10);
  --surface-panel:var(--midnight-deep);
  --surface-sunken:var(--ink-a25);
  --surface-tile:var(--paper);
  --surface-glass:rgba(16,47,93,0.70);
  --surface-accent-soft:var(--mint-a10);

  /* Semantic text */
  --text-body:var(--paper);
  --text-muted:var(--paper-a70);
  --text-faint:var(--paper-a40);
  --text-accent:var(--mint);
  --text-secondary-accent:var(--sky);
  --text-on-accent:var(--midnight);
  --text-on-tile:var(--midnight);
  --text-danger:var(--danger);
  --text-link:var(--mint);
  --text-link-hover:rgba(111,205,157,0.80);

  /* Semantic borders */
  --border-subtle:var(--sky-a10);
  --border-default:var(--sky-a20);
  --border-hover:var(--mint-a30);
  --border-accent:var(--mint);
  --border-hairline:rgba(255,255,255,0.05);

  /* Studio-tile pin bars — the one place in the system where colour alone is the signal */
  --pin-work:var(--mint-ink);
  --pin-craft:var(--clay-ink);
  --pin-personal:var(--sky-ink);

  /* Interaction */
  --focus-ring:var(--mint);
  --selection-bg:var(--mint);
  --selection-fg:var(--midnight);

  /* Signature gradients */
  --gradient-text:linear-gradient(135deg,var(--mint) 0%,var(--clay) 100%);
  --gradient-mesh:radial-gradient(ellipse at 20% 80%,rgba(187,205,243,0.15) 0%,transparent 50%),radial-gradient(ellipse at 80% 20%,rgba(111,205,157,0.08) 0%,transparent 50%),radial-gradient(ellipse at 40% 40%,rgba(224,159,125,0.10) 0%,transparent 50%),var(--midnight);
  --gradient-protect:linear-gradient(to top,var(--midnight) 0%,rgba(16,47,93,0.55) 45%,transparent 100%);
}

/* ============================================================
   tokens/typography.css
   ============================================================ */
:root{
  --font-display:"Instrument Sans","Helvetica Neue",Arial,sans-serif;
  --font-body:"Hanken Grotesk",system-ui,-apple-system,sans-serif;
  --font-mono:"Geist Mono",ui-monospace,SFMono-Regular,monospace;

  /* Scale — Tailwind-derived, matching the upstream site's rem values */
  --text-xs:0.75rem;
  --text-sm:0.875rem;
  --text-base:1rem;
  --text-lg:1.125rem;
  --text-xl:1.25rem;
  --text-2xl:1.5rem;
  --text-3xl:1.875rem;
  --text-4xl:2.25rem;
  --text-5xl:3rem;
  --text-6xl:3.75rem;
  --text-7xl:4.5rem;

  --weight-regular:400;
  --weight-medium:500;
  --weight-semibold:600;
  --weight-bold:700;

  --leading-display:1.1;
  --leading-tight:1.25;
  --leading-normal:1.5;
  --leading-relaxed:1.625;

  /* The eyebrow/kicker treatment used on every section of the site */
  --tracking-kicker:0.1em;
  --tracking-widest:0.2em;
  --tracking-scroll:0.35em;
}

/* ============================================================
   tokens/spacing.css
   ============================================================ */
:root{
  /* 4px base step */
  --space-1:0.25rem;
  --space-2:0.5rem;
  --space-3:0.75rem;
  --space-4:1rem;
  --space-5:1.25rem;
  --space-6:1.5rem;
  --space-8:2rem;
  --space-10:2.5rem;
  --space-12:3rem;
  --space-16:4rem;
  --space-20:5rem;
  --space-24:6rem;
  --space-32:8rem;

  /* Layout constants read off the upstream site */
  --rail-width:5rem;        /* fixed desktop side navigation */
  --header-height:4rem;     /* fixed mobile header */
  --gutter:1.5rem;          /* px-6 mobile */
  --gutter-lg:3rem;         /* lg:px-12 desktop */
  --container-max:80rem;    /* max-w-7xl */
  --measure:42rem;          /* max-w-2xl — body copy measure */
  --section-y:6rem;         /* py-24 */
  --section-y-lg:8rem;      /* lg:py-32 */
  --grid-gap:0.75rem;       /* gallery bento gap (12px) */
}

/* ============================================================
   tokens/radius.css
   ============================================================ */
:root{
  --radius-sm:0.375rem;
  --radius-md:0.5rem;
  --radius-lg:0.75rem;   /* art tiles, role cards */
  --radius-xl:1rem;      /* project cards, form fields use 0.75rem */
  --radius-2xl:1.5rem;   /* studio board, large panels */
  --radius-pill:9999px;  /* every button, tab, tag and filter */
  --radius-field:0.75rem;/* inputs, selects, textareas */
}

/* ============================================================
   tokens/elevation.css
   ============================================================ */
:root{
  /* The site leans on borders and blur far more than shadow. These are the real ones in use. */
  --shadow-tile:0 20px 25px -5px rgba(0,0,0,0.3),0 8px 10px -6px rgba(0,0,0,0.3); /* shadow-xl on studio tiles */
  --shadow-panel:0 28px 55px -12px rgba(0,0,0,0.7);   /* drawers, modals */
  --shadow-tooltip:0 20px 45px -12px rgba(0,0,0,0.75);
  --shadow-sticky:0 12px 30px -12px rgba(0,0,0,0.6);  /* sticky tab bar */
  --shadow-mint:0 4px 14px -2px rgba(111,205,157,0.45); /* active pill glow */
  --ring-tile:inset 0 1px 0 rgba(187,205,243,0.08),inset 0 0 40px rgba(0,0,0,0.35); /* @kind shadow */

  --blur-glass:12px;
  --blur-soft:4px;
  --blur-bloom:48px;
}

/* ============================================================
   tokens/motion.css
   ============================================================ */
:root{
  /* Both easings are copied verbatim from the upstream globals.css / lib/motion.ts */
  --ease-smooth:cubic-bezier(0.22,1,0.36,1); /* @kind other */
  --ease-bounce:cubic-bezier(0.34,1.56,0.64,1); /* @kind other */

  --duration-fast:200ms; /* @kind other */
  --duration-base:300ms; /* @kind other */
  --duration-slow:500ms; /* @kind other */
  --duration-entrance:700ms; /* @kind other */
  --duration-marquee:60s; /* @kind other */

  --hover-lift:1.02; /* @kind other */   /* whileHover scale on buttons and links */
  --press-scale:0.98; /* @kind other */  /* whileTap / active:scale */
  --image-zoom:1.05; /* @kind other */   /* group-hover image scale inside cards */
}

@keyframes sc-marquee{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
@keyframes sc-fade-in{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@keyframes sc-modal-in{from{opacity:0;transform:scale(0.96) translateY(16px)}to{opacity:1;transform:scale(1) translateY(0)}}
@keyframes sc-fade-in-scale{from{opacity:0;transform:scale(0.95)}to{opacity:1;transform:scale(1)}}
@keyframes sc-float-slow{0%,100%{transform:translateY(0) translateX(0)}50%{transform:translateY(-20px) translateX(10px)}}
@keyframes sc-float-slow-reverse{0%,100%{transform:translateY(0) translateX(0)}50%{transform:translateY(15px) translateX(-15px)}}
@keyframes sc-bounce-slow{0%,100%{transform:translateY(0)}50%{transform:translateY(8px)}}
@keyframes sc-pulse{0%,100%{opacity:0.3}50%{opacity:0.95}}

/* ============================================================
   tokens/base.css  —  resets, defaults, signature utilities
   ============================================================ */
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--surface-page);color:var(--text-body);font-family:var(--font-body);font-size:var(--text-base);line-height:var(--leading-normal);-webkit-font-smoothing:antialiased;text-wrap:pretty}
h1,h2,h3,h4{font-family:var(--font-display);font-weight:var(--weight-bold);line-height:var(--leading-display);margin:0}
a{color:var(--text-link);text-decoration-color:var(--mint-a30);text-underline-offset:4px;transition:color var(--duration-fast) var(--ease-smooth),text-decoration-color var(--duration-fast) var(--ease-smooth)}
a:hover{color:var(--text-link-hover);text-decoration-color:var(--mint)}
::selection{background:var(--selection-bg);color:var(--selection-fg)}
:focus-visible{outline:3px solid var(--focus-ring);outline-offset:3px}
::-webkit-scrollbar{width:8px}
::-webkit-scrollbar-track{background:var(--surface-page)}
::-webkit-scrollbar-thumb{background:var(--sky);border-radius:4px}
::-webkit-scrollbar-thumb:hover{background:var(--mint)}

/* Signature utilities the site uses everywhere */
.sc-gradient-mesh{background:var(--gradient-mesh)}
.sc-glass{background:var(--surface-glass);backdrop-filter:blur(var(--blur-glass));-webkit-backdrop-filter:blur(var(--blur-glass));border:1px solid var(--border-subtle)}
.sc-text-gradient{background:var(--gradient-text);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent}
.sc-kicker{font-family:var(--font-body);font-size:var(--text-sm);letter-spacing:var(--tracking-kicker);text-transform:uppercase;color:var(--text-accent)}
.sc-grid-overlay{background-image:linear-gradient(rgba(244,244,245,0.5) 1px,transparent 1px),linear-gradient(90deg,rgba(244,244,245,0.5) 1px,transparent 1px);background-size:60px 60px;opacity:0.03}

@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation-duration:0.01ms !important;animation-iteration-count:1 !important;transition-duration:0.01ms !important}
}
```

### 3.2 Naming contract

- **Base tokens are descriptive:** `--midnight`, `--mint-a20`, `--space-6`, `--text-4xl`.
- **Semantic tokens are role-named** and alias the base ones: `--surface-card`, `--text-muted`,
  `--border-hover`, `--focus-ring`, `--pin-work`.
- **Always design against the semantic names.** Reach for a base token only when no alias fits.
- **Utilities are prefixed `sc-`:** `.sc-gradient-mesh`, `.sc-glass`, `.sc-text-gradient`, `.sc-kicker`,
  `.sc-grid-overlay`.
- **Keyframes are prefixed `sc-`:** `sc-marquee`, `sc-fade-in`, `sc-fade-in-scale`, `sc-modal-in`,
  `sc-float-slow`, `sc-float-slow-reverse`, `sc-bounce-slow`, `sc-pulse`.

### 3.3 Tailwind v4 mapping

The upstream product is Tailwind v4. If you build with Tailwind, map the tokens through `@theme inline` so
utility classes resolve to them:

```css
@import "tailwindcss";
@import "./tokens.css"; /* the block from 3.1 */

@theme inline {
  --color-page: var(--paper);
  --color-panel: var(--surface-panel);
  --color-paper: var(--paper-white);
  --color-midnight: var(--midnight);
  --color-accent: var(--mint);
  --color-sky: var(--sky);
  --color-clay: var(--clay);
  --color-danger: var(--danger);

  --font-display: var(--font-display);
  --font-body: var(--font-body);
  --font-mono: var(--font-mono);

  --radius-pill: 9999px;
  --ease-smooth: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

Then: `bg-page text-midnight`, `bg-accent text-white`, `border-sky/10`, `rounded-full`,
`ease-[var(--ease-smooth)]`.

> The real repository uses different names for the same values (`--color-primary`, `--color-secondary`,
> `--color-accent-lime`, `--color-accent-blue`, `--color-accent-clay`, `--font-display`, `--font-body`).
> If you are contributing back to it, edit `src/app/globals.css` and keep its names.

### 3.4 JSON tokens

For design-tool sync, native apps, or anything that can't read CSS:

```json
{
  "color": {
    "midnight": "#102f5d",
    "midnightDeep": "#091a35",
    "paper": "#f4f4f5",
    "mint": "#6fcd9d",
    "sky": "#bbcdf3",
    "clay": "#e09f7d",
    "danger": "#f87171",
    "mintInk": "#2f7d5a",
    "clayInk": "#b56a3f",
    "skyInk": "#3f6ab5"
  },
  "alpha": {
    "sky": { "a05": 0.05, "a10": 0.10, "a15": 0.15, "a20": 0.20, "a30": 0.30 },
    "mint": { "a10": 0.10, "a20": 0.20, "a30": 0.30, "a50": 0.50 },
    "paper": { "a05": 0.05, "a40": 0.40, "a70": 0.70, "a80": 0.80 },
    "ink": { "a25": 0.25 }
  },
  "font": {
    "display": "Instrument Sans",
    "body": "Hanken Grotesk",
    "mono": "Geist Mono"
  },
  "fontSize": {
    "xs": 12, "sm": 14, "base": 16, "lg": 18, "xl": 20,
    "2xl": 24, "3xl": 30, "4xl": 36, "5xl": 48, "6xl": 60, "7xl": 72
  },
  "fontWeight": { "regular": 400, "medium": 500, "semibold": 600, "bold": 700 },
  "lineHeight": { "display": 1.1, "tight": 1.25, "normal": 1.5, "relaxed": 1.625 },
  "letterSpacing": { "kicker": "0.1em", "widest": "0.2em", "scroll": "0.35em", "displayTight": "-0.02em" },
  "space": { "1": 4, "2": 8, "3": 12, "4": 16, "5": 20, "6": 24, "8": 32, "10": 40, "12": 48, "16": 64, "20": 80, "24": 96, "32": 128 },
  "radius": { "sm": 6, "md": 8, "lg": 12, "xl": 16, "2xl": 24, "field": 12, "pill": 9999 },
  "layout": {
    "railWidth": 80, "headerHeight": 64, "gutter": 24, "gutterLg": 48,
    "containerMax": 1280, "measure": 672, "sectionY": 96, "sectionYLg": 128, "gridGap": 12
  },
  "breakpoint": { "sm": 640, "md": 768, "lg": 1024, "xl": 1280 },
  "motion": {
    "easeSmooth": "cubic-bezier(0.22,1,0.36,1)",
    "easeBounce": "cubic-bezier(0.34,1.56,0.64,1)",
    "durationFast": 200, "durationBase": 300, "durationSlow": 500,
    "durationEntrance": 700, "durationMarquee": 60000,
    "hoverLift": 1.02, "pressScale": 0.98, "imageZoom": 1.05
  },
  "blur": { "glass": 12, "soft": 4, "bloom": 48 }
}
```

### 3.5 JS/TS constants

For React Native, canvas work, or anywhere CSS variables aren't available:

```js
export const sc = {
  color: {
    page: "#102f5d", panel: "#091a35", paper: "#f4f4f5",
    accent: "#6fcd9d", sky: "#bbcdf3", clay: "#e09f7d", danger: "#f87171",
    accentInk: "#2f7d5a", clayInk: "#b56a3f", skyInk: "#3f6ab5",
    surfaceCard: "rgba(187,205,243,0.05)",
    surfaceSunken: "rgba(0,0,0,0.25)",
    surfaceGlass: "rgba(16,47,93,0.70)",
    textMuted: "rgba(244,244,245,0.70)",
    textFaint: "rgba(244,244,245,0.40)",
    borderSubtle: "rgba(187,205,243,0.10)",
    borderDefault: "rgba(187,205,243,0.20)",
    borderHover: "rgba(111,205,157,0.30)",
  },
  font: {
    display: '"Instrument Sans", "Helvetica Neue", Arial, sans-serif',
    body: '"Hanken Grotesk", system-ui, -apple-system, sans-serif',
    mono: '"Geist Mono", ui-monospace, SFMono-Regular, monospace',
  },
  ease: { smooth: [0.22, 1, 0.36, 1], bounce: [0.34, 1.56, 0.64, 1] },
  radius: { sm: 6, md: 8, lg: 12, xl: 16, xxl: 24, pill: 9999 },
};
```

---

## 4 · Colour in use

### 4.1 The whole palette, and what each colour is for

| Token | Hex | Contrast on midnight | What it is for |
| --- | --- | --- | --- |
| `--midnight` | `#102f5d` | — | The page. Sections, heroes, the rail, the lightbox panel. |
| `--midnight-deep` | `#091a35` | — | Only for things floating *above* the page: tooltips, drawers, detail panels. |
| `--paper` | `#f4f4f5` | 12.4:1 | All body text. And the inverted About tiles, where it becomes a surface. |
| `--mint` | `#6fcd9d` | 6.8:1 | The accent. Kickers, primary fills, active states, focus, links, the status dot. |
| `--sky` | `#bbcdf3` | 8.9:1 | Company/secondary lines. Mostly used as alpha for fills and borders. |
| `--clay` | `#e09f7d` | 6.3:1 | Required-field asterisks, the About board's dot grid, the "craft" pin group. |
| `--danger` | `#f87171` | 5.1:1 | Error text and error borders. Nothing else. |

### 4.2 The alpha system is the depth system

There is no gray. Every surface, border and hover wash is translucent sky, mint or paper over midnight:

| Ramp | Where it appears |
| --- | --- |
| `--sky-a05` | Default card fill; alternating section backgrounds |
| `--sky-a10` | Default border; tag fill; card hover fill; icon-circle hover |
| `--sky-a15` | Tab-capsule fill; hairline rules inside panels |
| `--sky-a20` | Secondary button fill; stronger borders; filter hover |
| `--sky-a30` | Secondary button hover |
| `--mint-a10` | Accent wash: availability card, ghost hover, award pill, mono badge |
| `--mint-a20` | Accent borders on panels and pills |
| `--mint-a30` | Card hover border; overlay panel hairline; link underline at rest |
| `--mint-a50` | Art-tile hover border |
| `--paper-a70` | Body copy at muted weight (never go below this for prose) |
| `--paper-a40` | Placeholders, captions, disabled-ish labels |
| `--paper-a05` | Chip fill on busy or light backgrounds |
| `--ink-a25` | Recessed surfaces (role cards) — the only black in the system |

### 4.3 On light surfaces, the palette fails

Measured against `--paper` `#f4f4f5`: **mint 1.7:1 · clay 2.0:1 · sky 1.4:1.** None of them clear the 3:1
needed for a graphical mark. Whenever a colour lands on `--surface-tile` or `--paper`, use the ink variants:

| Token | Hex | On paper |
| --- | --- | --- |
| `--mint-ink` | `#2f7d5a` | 4.5:1 |
| `--clay-ink` | `#b56a3f` | 3.7:1 |
| `--sky-ink` | `#3f6ab5` | 4.8:1 |

These are darker siblings of existing colours, not new palette entries, and they never appear on midnight.

### 4.4 Gradients — three, and no others

| Token | Value | Rule |
| --- | --- | --- |
| `--gradient-text` | mint → clay, 135° | Only on the last one or two words of a headline. Never a whole headline, never body copy. |
| `--gradient-mesh` | three radial ellipses (sky 15%, mint 8%, clay 10%) over midnight | Hero and page-header backgrounds. |
| `--gradient-protect` | midnight → 55% midnight → transparent, bottom-up | Mandatory under any text sitting on an image. |

**Never** invent a gradient. No purple-to-blue, no three-stop rainbows, no gradient borders, no gradient fills
on buttons or cards.

### 4.5 Background rhythm

Below the fold, sections alternate between exactly **two** states: bare `--midnight`, or a `--sky-a05` wash.
Never a third. The About board is the single documented exception — a clay dot grid at 22px pitch.

Hero backgrounds stack three layers and never a flat fill:

```html
<section style="position:relative;overflow:hidden;padding:8rem 0">
  <div class="sc-gradient-mesh" style="position:absolute;inset:0">
    <div style="position:absolute;top:25%;left:20%;height:384px;width:384px;border-radius:50%;
                background:var(--mint-a10);filter:blur(48px);
                animation:sc-float-slow 15s ease-in-out infinite"></div>
    <div style="position:absolute;right:18%;bottom:18%;height:320px;width:320px;border-radius:50%;
                background:var(--sky-a15);filter:blur(48px);
                animation:sc-float-slow-reverse 18s ease-in-out infinite"></div>
  </div>
  <div class="sc-grid-overlay" style="position:absolute;inset:0" aria-hidden="true"></div>
  <!-- content -->
</section>
```

---

## 5 · Typography spec

### 5.1 The three faces

| Role | Family | Weights | Used for |
| --- | --- | --- | --- |
| Display | **Instrument Sans** | 400 / 500 / 600 / 700 | Headlines, buttons, card titles, tabs, monogram, tile titles, role years |
| Body | **Hanken Grotesk** | 400 / 500 / 600 | Paragraphs, labels, form fields, kickers, tags, captions |
| Mono | **Geist Mono** | 400 / 500 | Hex values, code badges (`< >`), technical labels. Never prose. |

Loaded from Google Fonts. No font binaries ship with this system.

> **Substitution note.** Upstream uses *Space Grotesk* (display) and *DM Sans* (body); its README also mentions
> *Syne*. Space Grotesk was deliberately replaced. Instrument Sans keeps the geometric confidence with smoother
> curves; Hanken Grotesk has notably open apertures at small sizes, which suits the accessibility posture.

### 5.2 Every text style, specified

| Style | Family | Size | Weight | Leading | Tracking | Colour |
| --- | --- | --- | --- | --- | --- | --- |
| Hero h1 | display | `4.5rem` (clamp 2.25→4.5) | 700 | 1.1 | -0.03em | `--text-body`, turn in gradient |
| Page h1 | display | `3.75rem` (clamp 2.25→3.75) | 700 | 1.1 | -0.02em | `--text-body`, turn in gradient |
| Section h2 | display | `2.25rem` | 700 | 1.1 | -0.02em | `--text-body` |
| Subsection h2 | display | `1.875rem` | 700 | 1.1 | normal | `--text-body` |
| Card h3 | display | `1.5rem` | 700 | 1.25 | normal | `--text-body` → `--text-accent` on hover |
| Tile title | display | `1.125rem` | 700 | 1.25 | normal | `--text-on-tile` |
| Kicker / eyebrow | body | `0.875rem` | 400 | 1.5 | `0.1em`, uppercase | `--text-accent` |
| Lead paragraph | body | `1.125rem`–`1.25rem` | 400 | 1.5 | normal | `--text-muted` |
| Body | body | `1rem` | 400 | 1.5 | normal | `--text-muted` |
| Long-form body | body | `1rem` | 400 | 1.625 | normal | `--paper-a80` |
| Label | body | `1rem` | 500 | 1.5 | normal | `--text-body` |
| Field text | body | `1rem` | 400 | 1.5 | normal | `--text-body`; placeholder `--text-faint` |
| Tab / filter | body | `0.875rem` | 600 / 400 | 1.5 | 0.01em | `--text-on-accent` active, `--paper-a70` rest |
| Tag | body | `0.75rem` | 500 | 1.5 | normal | `--sky` / `--mint` |
| Micro-badge | body | `0.6rem` | 500 | 1.5 | `0.2em`, uppercase | `--text-accent` |
| Tile kicker | body | `0.65rem` | 600 | 1.5 | `0.2em`, uppercase | `--text-faint` |
| Caption / meta | body | `0.875rem` | 400 | 1.5 | normal | `--text-faint` |
| Mono value | mono | `0.75rem`–`0.9375rem` | 400 | 1.5 | 0.01em | context |

**Measure.** Never let prose exceed `--measure` (42rem / 672px). Headlines may run wider.

**Numbers.** Year ranges and any stacked figures use `font-variant-numeric: tabular-nums`.

**Responsive headlines.** Scale with `clamp()` rather than breakpoint jumps, and keep `white-space: nowrap`
lines only where the clamp guarantees they fit:

```css
.hero-title { font-size: clamp(2.25rem, 4.6vw, 4.5rem); }
.page-title { font-size: clamp(2.25rem, 3.9vw, 3.75rem); }
```

### 5.3 The kicker + headline + lead block

This three-part block opens every section on the site. Always in this order, never with a part missing except
the lead:

```html
<span class="sc-kicker" style="display:block;margin-bottom:1rem">Portfolio</span>
<h2 style="font-family:var(--font-display);font-size:var(--text-4xl);font-weight:700;
           line-height:1.1;letter-spacing:-0.02em;margin-bottom:1.5rem">
  Selected <span class="sc-text-gradient">Case Studies</span>
</h2>
<p style="max-width:var(--measure);font-size:var(--text-lg);color:var(--text-muted);margin:0">
  A collection of projects where strategy meets execution.
</p>
```

---

## 6 · Layout & responsive spec

### 6.1 Fixed chrome

| Element | Size | Behaviour |
| --- | --- | --- |
| Side rail | `5rem` wide, full height, left edge | Desktop only (≥1024px). Content pads itself by `--rail-width`; the rail never overlaps. |
| Mobile header | `4rem` tall, full width, top | Below 1024px. Transparent over the hero; becomes `.sc-glass` once `scrollY > 50`. |
| Sticky bars | Tab rows, gallery filters | `top: 0` on desktop, `top: 4rem` on mobile. Carry `--shadow-sticky`. |

### 6.2 Spacing rhythm

| Constant | Value | Use |
| --- | --- | --- |
| `--section-y` / `--section-y-lg` | `6rem` / `8rem` | Vertical padding on every section |
| `--gutter` / `--gutter-lg` | `1.5rem` / `3rem` | Horizontal page padding |
| `--container-max` | `80rem` | Content container max width |
| `--measure` | `42rem` | Prose max width |
| `--grid-gap` | `0.75rem` | Gallery justified-row gaps |
| Card grid gap | `2rem` (`--space-8`) | Project/role card grids |
| Section header → content | `4rem`–`6rem` | Below the kicker block |

**Use flex/grid with `gap`,** never margins between siblings or whitespace-dependent inline flow.

### 6.3 Breakpoints and grid collapse

Breakpoints: **640 / 768 / 1024 / 1280**.

| Pattern | <768 | 768–1023 | 1024–1279 | ≥1280 |
| --- | --- | --- | --- | --- |
| Project cards | 1 col | 2 col | 2 col | 3 col |
| Role cards | 1 col | 1 col | 2 col | 2 col |
| Contact split | 1 col | 1 col | 2 col | 2 col |
| Footer | 1 col | 1.4fr 1fr 1fr | same | same |
| Hero + portrait | 1 col, portrait hidden | same | same | 2 col, portrait shown |
| About board tiles | 2 col | 3 col | 4 col | 5 col |
| Gallery rows | 1 full-width tile per row | justified rows, 300px target | justified rows, 340px target | same |

```css
.grid-3{display:grid;grid-template-columns:minmax(0,1fr);gap:2rem}
@media (min-width:768px){.grid-3{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (min-width:1280px){.grid-3{grid-template-columns:repeat(3,minmax(0,1fr))}}
```

### 6.4 The gallery is not a grid

It is a **justified-row** layout. Rows fill the container width at a target row height (340px desktop, 300px
below 1024px) with 12px gaps, and each tile's width is derived from its measured aspect ratio:

```js
const GAP = 12, TARGET = 340;
function justify(items, containerWidth) {
  const rows = []; let row = [], sum = 0;
  const flush = isLast => {
    if (!row.length) return;
    let h = (containerWidth - (row.length - 1) * GAP) / sum;
    if (isLast && h > TARGET) h = TARGET;          // don't blow up a short last row
    rows.push(row.map(a => ({ art: a, w: Math.round(h * (a.width / a.height)), h: Math.round(h) })));
    row = []; sum = 0;
  };
  for (const a of items) {
    row.push(a); sum += a.width / a.height;
    if (sum * TARGET + (row.length - 1) * GAP >= containerWidth) flush(false);
  }
  flush(true);
  return rows;
}
```

Below 640px, collapse to one full-width tile per row at its natural aspect ratio.

### 6.5 Radii by element

| Radius | Value | Elements |
| --- | --- | --- |
| `--radius-sm` | 6px | Images inside tiles |
| `--radius-md` | 8px | Small inner blocks, tooltips on labels |
| `--radius-lg` | 12px | Art tiles, role cards, availability card, studio tiles |
| `--radius-field` | 12px | Inputs, selects, textareas |
| `--radius-xl` | 16px | Project cards, the lightbox panel |
| `--radius-2xl` | 24px | The About board, large panels |
| `--radius-pill` | 9999px | Every button, tab, filter, tag, badge, icon circle |

### 6.6 Elevation

| Token | Value | Only for |
| --- | --- | --- |
| `--shadow-tile` | `0 20px 25px -5px rgba(0,0,0,.3), 0 8px 10px -6px rgba(0,0,0,.3)` | Paper studio tiles (they read as physical objects) |
| `--shadow-panel` | `0 28px 55px -12px rgba(0,0,0,.7)` | Modals, drawers |
| `--shadow-tooltip` | `0 20px 45px -12px rgba(0,0,0,.75)` | Tooltips |
| `--shadow-sticky` | `0 12px 30px -12px rgba(0,0,0,.6)` | Sticky bars |
| `--shadow-mint` | `0 4px 14px -2px rgba(111,205,157,.45)` | The active tab pill |

Everything else uses borders. **Never a drop shadow on a plain content card.**

### 6.7 Blur

`--blur-glass` 12px — scrolled header, award badges over artwork, lightbox controls.
`--blur-soft` 4px — lightbox scrim, recessed role cards.
`--blur-bloom` 48px — hero orbs.
Anything at page level is opaque.

---

## 7 · Motion spec

### 7.1 Curves

| Token | Value | Use |
| --- | --- | --- |
| `--ease-smooth` | `cubic-bezier(0.22, 1, 0.36, 1)` | Essentially everything: entrances, hovers, colour, layout, fades |
| `--ease-bounce` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Rare playful overshoot only |

Framer Motion equivalents: `EASE_SMOOTH = [0.22, 1, 0.36, 1]`, `EASE_BOUNCE = [0.34, 1.56, 0.64, 1]`.

### 7.2 Durations

| Token | Value | Applies to |
| --- | --- | --- |
| `--duration-fast` | 200ms | Colour, opacity, hover scale, focus |
| `--duration-base` | 300ms | Borders, transforms, disclosure open/close, header state |
| `--duration-slow` | 500ms | Image zoom inside cards |
| `--duration-entrance` | 700ms | Section and hero entrances |
| `--duration-marquee` | 60s | Ticker loop |

### 7.3 Named behaviours

| Behaviour | Spec |
| --- | --- |
| Section entrance | `opacity 0 → 1`, `translateY 30–40px → 0`, 600–800ms, `--ease-smooth`, once on scroll into view |
| Card stagger | 80–100ms per card, capped at ~400ms total |
| Gallery tile entrance | `opacity 0 → 1`, `blur(6px) → 0`, 550ms, staggered 40ms, capped 400ms |
| Lightbox open | scrim fades 250ms; panel `scale .96 → 1` + `translateY 16px → 0`, 320ms |
| Lightbox close | `opacity → 0`, `scale → .97`, `translateY → 8px` |
| Tab pill slide | spring, stiffness 420, damping 34 |
| Mobile menu | spring, stiffness 400, damping 40 |
| Marquee | `translateX 0 → -50%` over a **doubled** track, 60s linear infinite, paused on hover |
| Hero orbs | 15s and 18s ease-in-out infinite, second one delayed -5s |
| Status dot | 2.8s ease-in-out infinite opacity pulse |
| Scroll hint | 1.5s ease-in-out infinite 8px bounce |

### 7.4 Keyframes

```css
@keyframes sc-marquee{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
@keyframes sc-fade-in{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@keyframes sc-fade-in-scale{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}
@keyframes sc-modal-in{from{opacity:0;transform:scale(.96) translateY(16px)}to{opacity:1;transform:scale(1) translateY(0)}}
@keyframes sc-float-slow{0%,100%{transform:translateY(0) translateX(0)}50%{transform:translateY(-20px) translateX(10px)}}
@keyframes sc-float-slow-reverse{0%,100%{transform:translateY(0) translateX(0)}50%{transform:translateY(15px) translateX(-15px)}}
@keyframes sc-bounce-slow{0%,100%{transform:translateY(0)}50%{transform:translateY(8px)}}
@keyframes sc-pulse{0%,100%{opacity:.3}50%{opacity:.95}}
```

### 7.5 Never

Parallax on content · scroll-jacking · page-load spinners or skeleton shimmer · looping animation on anything
that must be read · animation on more than one property class at a time without reason · bounce on anything
functional.

**Reduced motion is handled at the token level** (see `tokens/base.css` in §3.1). Don't override it, and disable
JS-driven effects — custom cursor, physics, smooth scroll — when `prefers-reduced-motion` is set.

---

## 8 · Interaction state matrix

The single most important rule: **hover brightens or fills — it never darkens.**

| Element | Rest | Hover | Active/Press | Focus-visible | Disabled |
| --- | --- | --- | --- | --- | --- |
| Button primary | `--mint` fill, midnight label | `rgba(111,205,157,.9)`, `scale(1.02)` | `scale(0.98)` | 3px mint outline, 3px offset | `opacity .5`, no pointer events |
| Button secondary | `--sky-a20` fill, paper label | `--sky-a30`, `scale(1.02)` | `scale(0.98)` | same | same |
| Button outline | transparent, 2px mint border, mint label | mint **fill**, midnight label | `scale(0.98)` | same | same |
| Button ghost | transparent, paper label | `--mint-a10` wash, mint label | `scale(0.98)` | same | same |
| Text link | mint, underline `--mint-a30` | `rgba(111,205,157,.8)`, underline `--mint` | — | same | — |
| Arrow CTA | mint text + 16px arrow | `translateX(8px)` | — | same | — |
| "View all" link | mint, gap 12px | gap 20px | — | same | — |
| Project card | `--sky-a05` fill, `--border-subtle` | border `--border-hover`, image `scale(1.05)`, title → mint, CTA `translateX(8px)`, mint circle blooms `scale(0 → 1)` | — | ring on the `<a>` | — |
| Art tile | `--border-subtle` | border `--mint-a50`, image `scale(1.04)`; **all other tiles dim to 55% midnight** | — | ring, siblings undim | — |
| Tag | `--sky-a10` fill | none (not interactive) | — | — | — |
| Filter pill | `--sky-a10` fill, paper text | `--sky-a20` | — | ring | — |
| Filter pill active | `--mint` fill, midnight text | — | — | ring | — |
| Tab | transparent, `--paper-a70` | `--paper-a05` wash, paper text | — | ring | — |
| Tab active | `--mint` fill + `--shadow-mint`, midnight text | — | — | ring | — |
| Rail icon | transparent circle | `--sky-a20` circle + label tooltip 3.5rem right | — | ring | — |
| Rail icon active | `--mint` circle, glyph `filter: brightness(0)` | — | — | ring | — |
| Input / select / textarea | `--sky-a05` fill, `--border-subtle` | — | — | border transparent + 2px mint outline | — |
| Input error | `--danger` border | — | — | same | — |
| Studio tile | paper, `--shadow-tile` + 1px black/5 ring | mint 2px ring | — | mint ring + 2px offset | — |
| Lightbox close / chevrons | `rgba(16,47,93,.7)` + blur, paper glyph | `--mint` fill, midnight glyph | — | ring | — |
| Marquee | scrolling | animation paused | — | — | — |

---

## 9 · Component specifications

21 components in five groups. Each spec below is complete enough to rebuild the component from nothing. All of
them reference tokens through `var(--*)`; none import a CSS framework or a UI library.

If the compiled system is available:

```js
const {
  Button, TextLink, Tag, Badge, Card,
  Input, Select, Textarea,
  SideRail, MobileHeader, SectionTabs, FilterPill,
  SectionHeading, ProjectCard, ArtTile, RoleCard, Marquee, StudioTile, AvailabilityCard,
  Modal, Tooltip,
} = window.SusanChapasDesignSystem_006b36;
```

### 9.1 core / Button

The only button in the system. Pill, display font, semibold.

**Props** — `variant: "primary" | "secondary" | "outline" | "ghost"` (default `primary`) ·
`size: "sm" | "md" | "lg"` (default `md`) · `href` (renders an `<a>`) · `external` ·
`disabled` · `fullWidth` · `type` · `onClick` · `style`.

**Sizes** — `sm`: `0.5rem 1rem`, 14px, gap 8px · `md`: `0.75rem 1.5rem`, 16px, gap 8px ·
`lg`: `1rem 2rem`, 18px, gap 12px.

**Variants** — every variant carries `border: 2px solid transparent` so the outline variant doesn't shift layout.

| Variant | Rest | Hover |
| --- | --- | --- |
| primary | `--mint` / `--text-on-accent` | `rgba(111,205,157,.9)` |
| secondary | `--sky-a20` / `--text-body` | `--sky-a30` |
| outline | transparent / `--mint`, 2px `--mint` border | `--mint` fill, `--text-on-accent` |
| ghost | transparent / `--text-body` | `--mint-a10`, `--mint` text |

**Transform** — `scale(1.02)` hover, `scale(0.98)` press, transitioned at `--duration-fast` `--ease-smooth`.

**Content** — verb-first label; trailing `ArrowRight` for forward actions, as the last child.

```jsx
<Button size="lg">View My Work <ArrowRight size={20} /></Button>
<Button variant="outline" size="lg" href="/contact">Get in Touch</Button>
<Button type="submit" size="lg" fullWidth>Send Message <ArrowRight size={20} /></Button>
<Button variant="ghost" size="sm">Cancel</Button>
```

### 9.2 core / TextLink

Inline link for body copy. Mint, `text-decoration-color: --mint-a30` at rest → `--mint` on hover, colour
lifts to `rgba(111,205,157,.8)`, `text-underline-offset: 4px`.

**Props** — `href` · `external` (adds `target="_blank" rel="noopener noreferrer"` **and** a visually hidden
"(opens in new tab)") · `underline` (default true) · `style`.

```jsx
<TextLink href="https://linkedin.com/in/susan-chapas" external>LinkedIn</TextLink>
<TextLink href="mailto:susanchapas39@gmail.com" underline={false}>susanchapas39@gmail.com</TextLink>
```

### 9.3 core / Tag

Non-interactive metadata pill. `0.25rem 0.75rem`, 12px, weight 500, pill radius.

**Tones** — `sky` (`--sky-a10` / `--sky`) default · `mint` (`--mint-a10` / `--mint`) for emphasis ·
`outline` (`--paper-a05` fill, `--border-default`, `--paper-a80` text). `mono` switches to Geist Mono.

Use 2–3 tags per card. For a clickable filter use `FilterPill`; for state use `Badge`.

```jsx
<Tag>UX Research</Tag><Tag>Accessibility</Tag><Tag tone="mint" mono>&lt; &gt;</Tag>
```

### 9.4 core / Badge

Glassy uppercase state marker that floats over imagery. `0.25rem 0.5rem`, **0.6rem**, weight 500, tracking
`0.2em`, `rgba(16,47,93,.7)` + 12px blur, 1px `--mint-a30` border, mint text. Carries its own blur so it needs
no wrapper on an image.

**Props** — `icon` (11px glyph) · `dot` (adds a 6px mint dot on `sc-pulse`).

```jsx
<Badge icon={<Award size={11} />}>Award</Badge>
<Badge dot>Available</Badge>
```

### 9.5 core / Card

**Tones** — `card` (`--sky-a05` + 1px `--border-subtle`) · `sunken` (`--ink-a25` + 4px blur) ·
`panel` (`--midnight-deep` + 1px `--mint-a20`) · `accent` (`--mint-a10` + 1px `--mint-a20`).
**Props** — `radius: "lg" | "xl" | "2xl"` · `padding` (default `1.5rem`) · `interactive` (border → `--border-hover` on hover).

`panel` is reserved for things above the page. Never add a shadow to `card`.

### 9.6 forms / Input · Textarea · Select

One shared skin: `0.75rem 1rem` padding, `--radius-field` 12px, `--sky-a05` fill, 1px `--border-subtle`,
16px body text, `--text-faint` placeholder. **Focus:** border goes transparent and a 2px `--focus-ring` outline
appears. **Error:** `--danger` border, message below in `--danger` at 14px, wired via `aria-invalid` +
`aria-describedby`.

**Labels** sit above at 16px weight 500 in `--text-body`, with an 8px gap. **Required marks are `--clay`
asterisks, never red.** Textarea defaults to 6 rows, `resize: vertical`. Select keeps the **native** control
(accessibility posture) with `appearance: none` and `--text-faint` until a value is chosen.

```jsx
<Input id="email" label="Email" type="email" required placeholder="your@email.com"
       value={email} onChange={e => setEmail(e.target.value)} error={errors.email} />
<Select id="subject" label="Subject" required placeholder="Select a subject"
        options={[{value:"job",label:"Job Opportunity"},{value:"freelance",label:"Freelance Project"}]} />
<Textarea id="message" label="Message" required rows={6}
          placeholder="Tell me about your project or opportunity..." />
```

### 9.7 navigation / SideRail

Fixed `5rem` column on the left, desktop only. Vertically: monogram (top) · icon list (centre) · social (bottom),
`space-between`, `1.5rem 0` padding, `--surface-page` background, `z-index: 50`.

- **Monogram** — `SC`, display bold, 24px, `--text-accent`, tracking -0.02em.
- **Items** — 40px circles, 20px SVG. Active: `--mint` circle, glyph `filter: brightness(0)`.
  Inactive hover: `--sky-a20` circle. Label tooltip appears `3.5rem` to the right, `--surface-page`
  background, 14px, weight 500, fading at `--duration-fast`.
- **Social** — 18px lucide glyphs, `--text-body`, column with `1rem` gap.
- **Props** — `monogram` · `items: {name, href, icon}[]` · `activeHref` · `social: {label, href, icon}[]` ·
  `onNavigate(href)` for in-page prototypes.

Content areas must pad themselves by `--rail-width`; the rail never overlaps.

### 9.8 navigation / MobileHeader

`4rem` bar, monogram left, toggle right, `0 1.5rem`. Transparent with a transparent 1px bottom border until
`scrolled`, then `--surface-glass` + 12px blur + `--border-subtle`, transitioned over `--duration-base`.
The toggle is a 44px button whose three 2px bars **morph** into an X (top `translateY(7px) rotate(45deg)`,
middle `opacity 0`, bottom `translateY(-7px) rotate(-45deg)`) — it never swaps icons.

### 9.9 navigation / SectionTabs

Pill tabs inside a translucent capsule: `0.375rem` padding, pill radius, 1px `--sky-a15` border,
`--sky-a10` fill, `overflow-x: auto` (never wraps). Each tab `0.625rem 1.25rem`, 14px, weight 600.
Active tab: `--mint` fill, `--text-on-accent`, `--shadow-mint`. Rest: `--paper-a70`.

Proper `role="tablist"/"tab"`, `aria-selected`, `aria-controls`, roving `tabIndex`, and **left/right arrow
keys** move between tabs. On the real site the active pill springs between positions (stiffness 420, damping 34)
and the panel below cross-fades over 450ms.

### 9.10 navigation / FilterPill

`0.5rem 1rem`, 14px, pill. Rest `--sky-a10` / `--text-body`; hover `--sky-a20`; active `--mint` /
`--text-on-accent`. Uses **`aria-pressed`**, not a tab role — filters narrow a view, tabs switch one.
Lay out in a flex row with `gap: var(--space-3)`.

### 9.11 content / SectionHeading

The kicker + headline + lead block. **Props** — `kicker` · `title` · `gradientTitle` (last words, rendered in
`--gradient-text`) · `description` · `align: "left" | "center"` · `size: "md" | "lg" | "xl"`
(1.875 / 2.25 / 3rem).

Centre-align only for full-width interstitials. Put **only the last one or two words** in `gradientTitle`.

### 9.12 content / ProjectCard

The portfolio's primary content unit.

**Anatomy** — 16:10 image (`object-fit: cover`) under `--gradient-protect`; a hover overlay containing an
80px `--mint` circle with a 32px midnight arrow that blooms `scale(0 → 1)`; then a content block at
`1.5rem` padding: optional mono badge + 2–3 tags, `h3` at 24px, a **two-line-clamped** description, and a
mint arrow CTA pinned to the bottom with `margin-top: auto`.

**Container** — `--surface-card`, 1px `--border-subtle` → `--border-hover` on hover, `--radius-xl`,
`overflow: hidden`, full-height flex column so cards in a row match.

**Hover, all at once** — border → mint 30%, image `scale(1.05)` over 500ms, circle blooms, title → mint,
CTA slides 8px right.

**Props** — `title` · `description` · `image` · `href` · `tags[]` · `badge` · `cta` (default
"View Case Study") · `onClick`.

> Write descriptions to two sentences. The third line is clipped and you will not see it.

### 9.13 content / ArtTile

Gallery tile. Sizes are **passed in**, not intrinsic — the parent computes them from aspect ratio (§6.4).

**Anatomy** — full-bleed image; optional glassy "Award" badge at `top/left: 0.75rem`; a dim layer
(`--surface-page` at 55%) shown when `dimmed`; a bottom caption block over `--gradient-protect` with
`padding: 1rem`, `padding-top: 2.5rem`, holding a 0.65rem uppercase mint category and a 16px display title.

**Border** — `--border-subtle` → `--mint-a50` on hover. Image `scale(1.04)` over 500ms.

**The signature grid behaviour:** hovering one tile dims *every other* tile. Track hover in the grid and pass
`dimmed={hovered !== null && hovered !== id}`.

**Props** — `title` · `category` · `image` · `award` (boolean) · `dimmed` · `width` · `height` · `onClick`.

### 9.14 content / RoleCard

Experience entry on `--surface-sunken` (25% black + 4px blur) — recessed, because the section it sits in
already has a wash. `--radius-lg`, `1.5rem` padding, flex column.

**Order** — mint 14px semibold **tabular-nums** year with `0.1em` tracking · 20px display role ·
`--text-secondary-accent` (sky) company line at weight 500 · `--text-muted` description · optional
disclosure.

**Disclosure** — a display-font 14px button with a `ChevronDown` that rotates 180°; the panel animates
`max-height` + `opacity` over `--duration-base`, with a `--sky-a20` top rule and `1.25rem` padding.

### 9.15 content / Marquee

Full-bleed infinite ticker. `2rem 0` padding, `--surface-card` background, `--border-subtle` top and bottom.
Track: `display: flex`, `gap: 2rem`, `width: max-content`, `animation: sc-marquee {speed}s linear infinite`,
paused on hover.

**The track must contain exactly two copies of the content** (the `sc-marquee` keyframe translates -50%). The
`items` prop doubles them for you; if you pass `children`, double them yourself.

Items render as 18px display text in `--paper-a80` separated by a 24px mint `•`.

**Always** provide the same list as real text elsewhere for screen readers (the upstream site ships a
`sr-only` `<ul>`).

### 9.16 content / StudioTile

The one place the palette inverts: a paper-white index card. `11rem` wide (or `width: 100%` in a grid),
`1rem` padding, `--radius-lg`, `--surface-tile` background, `--text-on-tile` text, `--shadow-tile` plus a
1px `rgba(0,0,0,.05)` ring → 2px `--mint` ring on hover or when selected.

**Order** — a 4px full-width pin bar · optional 4:3 image at `--radius-sm` · a 0.65rem uppercase kicker with
`0.2em` tracking in `rgba(16,47,93,.5)` and a 14px leading icon · an 18px display bold title.

**Pin bars use the on-light ink variants** — `pin: "work" | "craft" | "personal"` → `--pin-work` /
`--pin-craft` / `--pin-personal`. The palette colours themselves are 1.4–2.0:1 on paper and effectively
invisible. This is the only spot where colour alone is the signal, so it must clear 3:1.

**`rotate`** tilts the card a few degrees. Only use it if something resolves collisions — a static scatter of
fixed-width tiles will overlap. For a static layout use a grid (2 → 3 → 4 → 5 columns) with `rotate={0}`.

### 9.17 content / AvailabilityCard

Status callout: `--mint-a10` fill, 1px `--mint-a20`, `--radius-lg`, `1.5rem` padding. A 12px mint dot on
`sc-pulse` (2.8s) sits beside a display-font semibold title; a 14px `--text-muted` line sits below.
**One per page maximum.** The pulsing dot is the only looping animation permitted in a static block.

### 9.18 feedback / Modal

The artwork lightbox, and any dialog.

**Scrim** — `rgba(16,47,93,0.80)` + `--blur-soft` 4px, fading in over 250ms. **Never black.**

**Panel** — `--surface-page` (plain midnight, *not* the deep panel, because the media bed behind it is 30%
black), 1px `--mint-a30`, `--radius-xl` **16px**, `max-height: 90vh`, `--shadow-panel`, entering on
`sc-modal-in` (`scale .96` + `translateY 16px`, 320ms).

**Two panes** — media on a `rgba(0,0,0,.3)` bed at `flex: 0 0 33.333%` with `min-height: 60vh`; content
scrolling at `2rem` padding with `overscroll-behavior: contain`. When the piece is landscape
(`width / height >= 1.3`) pass `stacked`: media goes on top at `38vh` and `max-width` drops from
`min(92vw, 64rem)` to `min(92vw, 56rem)`.

**Controls** — 36px close button at `top/right: 12px`; 44px chevrons at the media pane's vertical centre,
`left/right: 12px`. All three are `rgba(16,47,93,.7)` + 12px blur, and all three fill `--mint` with a
midnight glyph on hover.

**Behaviour** — `role="dialog"` `aria-modal="true"`; **Esc** closes; **←/→** navigate; **Tab and Shift+Tab
are contained inside the panel**; focus moves to the close button on open and **returns to the trigger on
close**; body scroll is locked while open. Clicking the scrim closes.

**Content-pane order in the real product** — `Category • Year` kicker (12px uppercase mint) · title (24px
display) · award pill (`--mint-a10` fill, `--mint-a30` border, 13px `Award` icon, self-start) · description
paragraphs (16px, leading 1.625, `--paper-a80`, 12px gaps) · a `Medium` definition list above a
`--sky-a15` rule (0.65rem uppercase mint `<dt>`, 14px `--paper-a70` `<dd>`) · link pills (first `--mint`
filled, rest `rgba(187,205,243,.25)` outlined, `min-height: 44px`, 14px, with a 14px `ExternalLink`).

```jsx
<Modal open={!!active} stacked={active.width / active.height >= 1.3}
       onClose={close} onPrev={prev} onNext={next}
       media={<img src={active.src} alt={active.title}
                   style={{position:"absolute",inset:0,width:"100%",height:"100%",objectFit:"contain"}} />}>
  <ArtworkDetail art={active} />
</Modal>
```

### 9.19 feedback / Tooltip

`16rem` wide, `--surface-panel` background, 1px `--mint-a20`, `--radius-lg`, `1rem` padding,
`--shadow-tooltip`, 14px `--paper-a80` at leading 1.625, with a 12px rotated-45° diamond pointer in the same
colour. Opens on **hover and keyboard focus**, fades at `--duration-fast`, `pointer-events: none`.
Placement `top` or `bottom`, offset `0.6rem`.

It carries **real prose**, one or two sentences — not a label.

### 9.20 Components deliberately absent

`CustomCursor` (a mint mix-blend-difference cursor — a page-level effect, not a component) ·
`SmoothScrollProvider` / `MorphTransitionWrapper` / `useMagneticTilt` (behaviour with no visual surface) ·
`Footer` (layout, composed per product — see §10.5).

**Do not add primitives this brand does not define.** No Avatar, Accordion, Breadcrumb, Pagination, Toast,
Popover, Table, or Stepper — none exist in the source. If you genuinely need one, build it from the tokens and
the state matrix in §8, and note the addition.

---

## 10 · Page recipes

Five archetypes, in the structure the real product uses. Build new pages by composing these rather than
inventing new layouts.

### 10.1 Shell (every page)

```
<Shell>
  ├─ SideRail            fixed left, 5rem, ≥1024px   (MobileHeader below that)
  ├─ <main id="main">    padding-left: var(--rail-width)
  │    └─ page content
  └─ SiteFooter
```

Plus a skip link as the first focusable element in the body:

```html
<a href="#main" style="position:absolute;top:-100%;left:50%;transform:translateX(-50%);
   background:var(--mint);color:var(--text-on-accent);padding:1rem 2rem;z-index:9999;
   font-family:var(--font-body);font-weight:600;border-radius:0 0 8px 8px;text-decoration:none">
  Skip to main content
</a>
```

### 10.2 Home

1. **Hero** — three-layer background (§4.5), `padding: 8rem 0`. Two columns at ≥1280px
   (`minmax(0,1fr) auto`), one column below with the portrait hidden. Left column: uppercase mint kicker
   (16px) → `h1` at `clamp(2.25rem, 4.6vw, 4.5rem)` in three `nowrap` lines with the last line in
   `--gradient-text` → 20px `--text-muted` lead at `--measure` → two buttons (`primary` + `outline`, both
   `lg`) in a `flex` row with `gap: 1rem`. Right column: portrait at `20rem`, `--radius-2xl`,
   `justify-self: end`.
2. **Selected Work** — `SectionHeading` (kicker "Portfolio") with `4rem` below, then a 1/2/3-column
   `ProjectCard` grid at `gap: 2rem`, then a centred "View All Projects" arrow link.
3. **Currently** — `--surface-card` section, container narrowed to `64rem`, `SectionHeading` size `md`
   (kicker "Currently", title "Where I am now"), then a 2-column `RoleCard` grid with `align-items: start`.
4. **Skills ticker** — full-bleed `Marquee`.
5. **Beyond the Code** — `--border-hairline` top rule, centred `SectionHeading` (kicker "Creative Side"),
   then a `Marquee` of `ArtTile`s at 384×256 with the section chrome stripped
   (`background: transparent; border: none; padding: 0`).

### 10.3 Index page (Projects / Gallery)

1. **PageHero** — `.sc-gradient-mesh`, `padding: 8rem 0 6rem`, content capped at `48rem`: kicker → `h1` at
   `clamp(2.25rem, 3.9vw, 3.75rem)` with a `<br>` and the second line in `--gradient-text` → optional lead.
2. **Sticky control bar** *(Gallery only)* — `--surface-page`, `--border-subtle` bottom, `padding: 1.5rem 0`,
   `position: sticky; top: 0; z-index: 30`, holding a `flex` row of `FilterPill`s at `gap: 0.75rem`.
3. **Content** — project card grid, or justified `ArtTile` rows (§6.4) with cross-tile dimming.
4. **Closing CTA** *(Projects only)* — `--surface-card` section, centred `SectionHeading` size `md`
   ("Have a project in mind?") and one `lg` primary button.
5. **Modal** — mounted at page level for the gallery lightbox.

### 10.4 Contact

1. **PageHero** — kicker "Get in Touch", title "Let's Create / **Something Great**".
2. **Two-column split** at `gap: 6rem`, collapsing below 1024px.
   - **Left:** a 30px display "Contact Information" heading, then a `2rem`-gap column of labelled blocks
     (label = 14px uppercase mint at `0.1em`; value = 20px). Email as a `TextLink`, location as plain text,
     social as 48px `--sky-a10` circles. Then `AvailabilityCard` with `3rem` above.
   - **Right:** the form — `Input` name, `Input` email, `Select` subject, `Textarea` message, full-width
     `lg` submit — in a `1.5rem`-gap column, `noValidate`, validating on submit.
3. **Success state** replaces the form in place: a `card` at `2rem` padding, centred, with a 64px mint circle
   holding a 32px midnight check, a 24px display "Message Sent!", a `--text-muted` line, and an `outline`
   button to send another.

Validation copy, verbatim: `"Name is required"` · `"Email is required"` ·
`"Please enter a valid email address"` · `"Subject is required"` · `"Message is required"` ·
`"Message must be at least 10 characters"`.

### 10.5 Footer

`--border-default` top rule, `padding: 6rem 0 2rem`. Three columns (`1.4fr 1fr 1fr`, collapsing to one below
768px) at `gap: 3rem`:

1. **Brand** — 30px display mint "Susan Chapas", then the positioning line at `--text-muted` capped to `20rem`.
2. **Quick Links** — 18px display semibold heading, then a `0.75rem`-gap list of `--text-muted` links.
3. **Let's Connect** — same heading, the email as a `TextLink`, then 44px `--sky-a10` social circles.

Then a `--border-subtle` rule with `3rem` above and `2rem` below, holding the copyright left and a
`MapPin` + "Jersey City" right, both 14px `--text-muted`.

### 10.6 Case study (structure only)

The real detail pages weren't recreated in this system, but their structure is: a full-bleed hero with the
project's cover image under `--gradient-protect`, a sticky `SectionTabs` bar pinned under the header, and one
cross-fading panel per section (Problem · Research · Design · Outcome). Panels are prose at `--measure` with
full-width imagery between, and pull-quotes set in display type.

---

## 11 · Iconography

**Two systems, deliberately.**

### 11.1 The five custom nav glyphs

`assets/icons/nav/{home,about,projects,gallery,contact}.svg` ship with the brand. They render at **20px** inside
the rail's 40px circles. When active, the circle fills `--mint` and the glyph is knocked to black with
`filter: brightness(0)` — **the SVGs are inverted, not recoloured.**

### 11.2 lucide for everything else

The upstream product imports `lucide-react` directly. **This is the real icon set, not a substitution.**

```html
<script src="https://unpkg.com/lucide@0.454.0/dist/umd/lucide.js"></script>
```

Glyphs actually used: `Menu` `X` `ChevronDown` `ChevronLeft` `ChevronRight` `ArrowRight`
`ExternalLink` `MapPin` `Award` `Brush` `Code2` `Coffee` `Compass` `Gamepad2` `GraduationCap`
`HeartHandshake` `Languages` `Layers` `MousePointer2` `Palette` `PenTool` `RotateCcw` `Rocket`
`Utensils` `Check` `Linkedin` `Github`.

**Sizes** — 11px badge · 13px award pill · 14px tile kicker and link pill · 16px inline and the modal close ·
18px social · 20px buttons and rail · 22px lightbox chevrons · 24px mobile toggle. Stroke width **2** always
(2.5 only on the scroll-hint chevron).

### 11.3 Rules

- No icon font. No custom-drawn SVG icons. If lucide doesn't have it, reconsider the need.
- Icons in buttons are the **last** child for forward actions, first for meta labels.
- Every standalone icon button needs an `aria-label`; every decorative icon needs `aria-hidden="true"`.
- Social marks: lucide `Linkedin` / `Github` at 18–20px (upstream hand-inlines 24×24 filled paths; these read
  identically).
- **No emoji in product UI.** The only decorative glyph is the mint `•` between marquee items. The `< >` on
  the Schematic Marketing card is a mono **text badge**, not an icon.

---

## 12 · Imagery

**Real work only.** Paintings, event and portrait photography, branding mockups, product screens, one portrait
of Susan. **No stock photography, no illustration-as-decoration, no generated imagery, no 3D renders, no
hand-drawn SVG scenes.** If you don't have a real asset, leave the space empty and say so.

**Colour temperature.** The imagery runs **warm and human** — clay, skin, brick, summer light — against the cool
midnight page. That contrast is what makes the page read as a gallery wall. Don't apply cool filters, duotones,
or heavy grain.

**Treatment rules.**

| Context | Crop | Radius | Overlay | Hover |
| --- | --- | --- | --- | --- |
| Project card cover | 16:10, `cover` | inherits 16px | `--gradient-protect` | `scale(1.05)` / 500ms |
| Gallery tile | native ratio, `cover` | 12px | `--gradient-protect` on the caption | `scale(1.04)` / 500ms |
| Lightbox media | `contain` on `rgba(0,0,0,.3)` | panel-clipped | none | none |
| Studio tile | 4:3, `cover` | 6px | none | none |
| Hero portrait | native, `cover` | 24px | none | none |

**Text on imagery always gets `--gradient-protect`** — never a flat scrim, never text directly on a photo.

**Metadata.** Artwork carries category, year, medium, an optional award string, a 2–4 paragraph description and
optional link pills. Never show a piece without at least its category and year.

**Alt text.** Decorative → `alt="" aria-hidden="true"`. Meaningful → describe the work
(`"ArchLog project preview"`, not `"screenshot"`).

---

## 13 · Voice, language & copy library

### 13.1 Voice

**First person, plainspoken, confident without swagger.** Susan writes as *I*, and addresses the reader as *you*
only in invitations. She states what she does and moves on.

> "I figure out what people actually need, design it to work for everyone, then build and ship it myself."

> "I build the front end myself, so the design that ships is the design I drew. The handoff is just me handing
> it to me."

> "Accessibility is my starting point. If it works for someone using a screen reader, a keyboard, or a second
> language, it's ready to ship."

### 13.2 Two registers — know which one you're in

| Register | Where | Example |
| --- | --- | --- |
| **Measured** | Case studies, role descriptions, contact page, capability copy | *"Leading website redesign, copywriting, translations, and UX improvements informed by user flow analysis."* |
| **Relaxed** | The About board, personal detail | *"It counts as water, right?"* · *"No picky eaters allowed"* · *"Chasing Korok seeds"* · *"Did the scary thing"* |

Never blend them. A case study does not wink; a personal tile does not read like a résumé.

### 13.3 Headlines

The pattern is **a plain claim followed by a small pivot**, with the pivot in `--gradient-text`:

- *"I'm a designer who refuses to stop at the **mockup**."*
- *"Designer, developer, artist — **and a few more hats**."*
- *"Paint, Pixels **& Motion**."*
- *"Selected **Case Studies**"*
- *"Let's Create **Something Great**"*

Never a label-headline ("UX Designer & Developer"). Never all-caps a headline. Never gradient the whole thing.

### 13.4 Language rules

**Casing** — sentence case for headlines and body; Title Case for section headings, nav labels and buttons;
ALL CAPS only for mint kickers and micro-badges.

**Kickers** name the section in one or two words: *Portfolio · Currently · Creative Side · About Me ·
Selected Work · Get in Touch*.

**Buttons and links are verb-first and specific.** Approved: *View My Work · Get in Touch · View Case Study ·
Start a Conversation · Send Message · Send Another Message · See the gallery · Read the feature · Watch the
full explainer · View All Projects · Previous role · Hide previous role · Skip to main content*.
Banned: *Learn more · Submit · Click here · Read more · Get started · Explore*.

**Length** — project descriptions: two sentences, clamped to two lines, "what it is, then what it did."
Leads: one to three sentences at `--measure`. Artwork descriptions: 2–4 paragraphs, the one place the brand
writes at length. Tooltips: one or two real sentences, never a label.

**Punctuation** — em dashes for the appositive turn ("Susan Chapas — UX strategist, front-end developer, and
award-winning artist"). Ampersands in headings and role titles. `•` as separator in tickers and
`Category • Year`. Curly apostrophes. Oxford comma. Date ranges with a spaced en dash: *2025 — Present*.

**Numbers** — always numerals. Years and stacked figures in `tabular-nums`.

**Terminology**

| Use | Not |
| --- | --- |
| case study | project write-up |
| piece / artwork | image |
| board (About) | wall, canvas |
| rail (navigation) | sidebar |
| accessible | a11y-friendly, inclusive-ish |

**Spanish** is genuine, not decorative — real sentences, same faces and weights, `lang="es"` on the container.

**Banned words and habits** — synergy · leverage (as a verb) · passionate about · seamless · cutting-edge ·
revolutionary · game-changing · "in today's fast-paced world" · third-person self-description · hedging ("I try
to…") · exclamation marks beyond genuine warmth (*"Drop me a message!"* is the ceiling) · emoji.

### 13.5 Approved string library

Reuse these verbatim where they fit rather than paraphrasing.

**Positioning** — *"The Strategic Architect — bridging design, marketing strategy, and technical
implementation."*

**Hero** — *"UX Strategist & Marketing Professional"* / *"I'm a designer who refuses to stop at the mockup."* /
*"Susan Chapas — UX strategist, front-end developer, and award-winning artist. I figure out what people actually
need, design it to work for everyone, then build and ship it myself."*

**Selected Work lead** — *"A collection of projects where strategy meets execution. Each case study demonstrates
the intersection of design thinking, marketing expertise, and technical implementation."*

**Creative Side lead** — *"Exploring the intersection of humanity and technology through visual art."*

**About lead** — *"Everything that shapes how I work, laid out on the board below."*

**Contact lead** — *"I'm always open to discussing new opportunities, creative projects, or ways we can
collaborate. Drop me a message!"*

**Availability** — *"Available for opportunities"* / *"Currently open to full-time roles, freelance projects, and
creative collaborations."*

**Projects CTA** — *"Have a project in mind?"* / *"I'm always open to discussing new opportunities and creative
challenges. Let's create something meaningful together."*

**Success** — *"Message Sent!"* / *"Thank you for reaching out. I'll get back to you as soon as possible."*

**Footer** — *"© {year} Susan Chapas. All rights reserved."* / *"Jersey City"*

**Facts you can rely on** — Jersey City, NJ · susanchapas39@gmail.com · linkedin.com/in/susan-chapas ·
github.com/susanchapas · susanchapas.com · BS in Human-Computer Interaction at NJIT · MIT xPRO full-stack ·
fluent English and Spanish · founder of Schematic Marketing (2024–) · Marketing & UX Strategist at Spring Bank
(2025–, previously Marketing Coordinator 2022–2024) · Research Assistant in UX/accessibility at NJIT (2026–) ·
Marketing & Business Development Manager at All Executive Clean (2025–) · "Mindless Mirth" won the HCCC
Foundation Art Award, 2025.

---

## 14 · Disclosures & honesty rules

The source carries no legal or regulatory disclosure copy — it's a personal portfolio. What it does carry, and
what you should reproduce:

- **Link destinations.** Every external link gets `target="_blank" rel="noopener noreferrer"` **plus** a
  visually hidden *"(opens in new tab)"*. In-page anchors never open new tabs.
- **Availability is scoped and current.** If the status changes, change the sentence — never leave a stale
  pulsing dot.
- **Form honesty.** Required fields are marked **before** submission, not discovered after. Errors say what to
  do. If you mock a form, don't imply data is stored anywhere it isn't. (Upstream posts to Web3Forms and uses a
  hidden honeypot field for spam.)
- **Attribution.** Collaborative work says so (*"Built as a team effort"*). Third-party contributions are named
  (*"shot by Spring Bank's videography partner and edited by me"*). Client work names the client. Awards state
  issuer and year.
- **Decorative vs meaningful imagery** is a disclosure, not just markup — it tells assistive tech what matters.
- **Copyright.** `© {year} Susan Chapas. All rights reserved.` The repository is MIT licensed; **the work shown
  in it is not.** Never imply portfolio imagery, client work or artwork is reusable.

> **Gap:** there is no privacy policy, cookie notice or terms page anywhere in the source. If a design needs
> one, **ask for real copy** — do not draft placeholder legal language.

---

## 15 · Accessibility spec

Accessibility is the brand's stated starting point, not a QA pass. WCAG 2.1 AA is the floor.

| Requirement | Spec |
| --- | --- |
| Focus indicator | `:focus-visible { outline: 3px solid var(--focus-ring); outline-offset: 3px }` — global, never removed, never colour-only |
| Hit targets | 44×44px minimum, including lightbox chevrons and link pills |
| Skip link | Mint, drops in from above the viewport on focus; `<main>` carries `tabIndex={-1}` |
| Reduced motion | Handled at the token level; also disable cursor, physics and smooth scroll |
| Text contrast | Midnight on paper 14.5:1 · `--ink-a70` on paper ~7:1. Never below 50% opacity for prose |
| Graphical contrast | Any mark carrying meaning clears 3:1 — hence the ink variants (§4.3) |
| Forms | `aria-invalid` + `aria-describedby`; clay required marks; `noValidate` with real messages |
| Dialogs | `role="dialog"` + `aria-modal`; Esc; arrows; focus to the dialog on open; **Tab contained**; focus restored to the trigger on close; body scroll locked |
| Tabs | `role="tablist"/"tab"/"tabpanel"`, `aria-selected`, `aria-controls`, roving `tabIndex`, ←/→ keys |
| Toggles/filters | `aria-pressed` (not tab roles) |
| Motion-only content | Marquees ship an `sr-only` list of the same items |
| Images | Decorative `alt="" aria-hidden`; meaningful describes the work |
| Language | `lang="en"` at the root; `lang="es"` on Spanish containers |
| Headings | One `h1` per page; never skip levels for styling — use the size tokens |
| Colour alone | Never the only signal. Pair with fill, weight, size, icon or text |

### QA checklist before shipping anything

- [ ] Tab through the whole page: every interactive element gets a visible mint ring, in a sensible order
- [ ] Open every dialog with the keyboard; Tab stays inside; Esc closes; focus lands back on the trigger
- [ ] Zoom to 200%: nothing clips, no horizontal scroll
- [ ] `prefers-reduced-motion: reduce`: nothing animates, nothing breaks
- [ ] Every image has intentional alt text (or is explicitly decorative)
- [ ] Every icon-only button has an `aria-label`
- [ ] No text sits on an image without `--gradient-protect`
- [ ] No accent colour is used at an opacity too pale to read on white
- [ ] Contrast-check any new colour pairing on white/paper surfaces
- [ ] Headline `nowrap` lines still fit at the smallest supported width
- [ ] The accent appears once or twice on the page — not five times

---

## 16 · Anti-patterns

Things that instantly make work look like it isn't this brand:

**Colour** — a light mode · a gray ramp · a third background state in one page · the accent as a large fill ·
an invented gradient (especially blue→purple) · gradient buttons or borders · a flat black scrim · the accent
on paper without an ink variant.

**Shape** — square corners anywhere · a drop shadow on a plain card · a card with a coloured left border only ·
inconsistent radii inside one component.

**Type** — all-caps headlines · a gradient across a whole headline · prose wider than `--measure` · mono for
body copy · a fourth typeface · letterspaced display type.

**Motion** — a third easing curve · parallax on content · scroll-jacking · loading spinners · looping animation
behind text · bounce on functional UI.

**Content** — emoji · placeholder lorem · stock photography · hand-drawn SVG illustration · AI-generated
imagery · a fabricated logo · dummy sections added to fill space · stats or numbers invented for visual rhythm.

**Copy** — "Learn more" · "Submit" · third-person self-description · buzzwords · a case study written in the
relaxed register · a personal tile written like a résumé.

**Structure** — adding component families the brand doesn't define · re-implementing a primitive inside a
screen · a storybook masquerading as a product view.

---

## 17 · Extending the system

**Adding a colour.** Don't, unless a real need exists. If it does: define the base token, then the alpha steps
you actually use, then a semantic alias — and contrast-check it against `--midnight` **and** `--paper` before
using it. If it lands on a light surface, it needs an ink variant.

**Adding a component.** First check whether composing existing primitives covers it. If not: build it from the
tokens, follow the state matrix in §8 (brighten on hover, `scale(0.98)` on press, mint focus ring), give it a
pill radius if it's interactive, and document it — name, purpose, props, states, and *why* it was needed.

**Adding a page type.** Start from the closest recipe in §10. Keep the kicker + headline + lead opening, keep
the two-state background rhythm, and keep sections at `6rem`/`8rem`.

**Porting to another platform.** Use the JSON in §3.4 or the JS constants in §3.5. Native equivalents:
`--radius-pill` → `height / 2`; `backdrop-filter` → a platform blur view; `--ease-smooth` → a cubic
timing curve with the same control points; the marquee → a looping horizontal scroll with a doubled track.

**Checking your work.** Screenshot it next to the real site. If the accent shows up more than twice, if
anything has a square corner, if any card has a shadow, or if the page has a third background colour, it isn't
there yet.

---

## 18 · Known gaps

Be honest about these rather than papering over them:

- **Fonts are substituted.** Upstream loads Space Grotesk + DM Sans (its README also mentions Syne). This system
  uses Instrument Sans + Hanken Grotesk + Geist Mono, from Google Fonts. No `@font-face` binaries ship.
- **The accent is substituted and darkened for light mode.** Upstream is Electric Lime `#ccff00` under the name `--accent-lime`. This
  system uses Mint `#2a9d6e` — darkened from the original `#6fcd9d` to achieve 4.5:1 contrast on white surfaces. Green now carries "success" semantics — if you build anything stateful, pair the
  accent with an icon or label rather than letting green alone mean "done."
- **No logo file exists.** The identity is typographic. Never invent a mark.
- **No privacy policy, terms or cookie copy** exists in the source.
- **Not implemented, only documented:** the About board's Matter.js drag-and-sling physics, the custom mint
  mix-blend-difference cursor, Lenis smooth scroll, the magnetic tilt on gallery tiles, and the four case-study
  detail pages.
- **Two gallery pieces are video** ("EOP Explainer", "ATM Home Screen") and their `.mp4` sources are absent
  from the repository, so the `Motion` category is dropped from the filter row here — five categories instead of
  the upstream six.

---

*Source of truth: [github.com/susanchapas/susanchapas](https://github.com/susanchapas/susanchapas) (branch
`master`) — `src/app/globals.css`, `src/lib/motion.ts`, `src/components/*`, `src/app/gallery/*`. Read it
directly when you can; it carries more than any guide can.*
