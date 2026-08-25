## Waybill design system — build conventions

A "shipping manifest / logistics" visual language: kraft-paper cards, freight crates, tracking waybills, a status timeline. Dark ground by default (`--ink`), amber accent (`--amber`).

**No provider or wrapper needed.** Every component is self-contained — there is no `ThemeProvider`/context to wrap your app in. Just import and use components directly from `window.AditfDesignSystem.*`.

**Load the Google Fonts link tag, or type falls back to system fonts.** The three font tokens (`--font-display`, `--font-body`, `--font-mono`) are NOT shipped as `@font-face` files — they resolve at runtime from Google Fonts, the same way the source site loads them. Include this in your page `<head>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```
Skip this and every heading/label silently renders in a fallback sans-serif — not broken, just off-brand.

**Styling idiom: CSS custom-property tokens, not utility classes.** Each component owns its own internal class names (e.g. `.btn--stamp`, `.project-card__badge`) — never write new CSS targeting those classes; treat components as opaque and style around them with the token set below in your own layout glue:

| Token | Value | Use for |
|---|---|---|
| `--ink` | `#14181B` | page/section background |
| `--ink-soft` | `#1B2023` | raised surface (hover states, mobile nav) |
| `--ink-line` | `#2B3236` | hairline borders, dividers |
| `--paper` | `#EDE6D6` | primary text on `--ink` |
| `--paper-dim` | `#9CA3A0` | secondary/muted text |
| `--kraft` | `#D9C8A8` | kraft-paper surfaces (LabelCard, seals) |
| `--kraft-line` | `#B8A47D` | kraft borders, dashed rules |
| `--kraft-ink` | `#2A2116` | text on kraft surfaces |
| `--amber` | `#E8871E` | accent, CTAs, active/live states |
| `--amber-soft` | `rgba(232,135,30,.14)` | tag/chip backgrounds |
| `--steel` | `#7FA9C4` | secondary accent (subtitles, labels) |
| `--stamp-red` | `#C24B3B` | reserved accent |
| `--font-display` | Oswald stack | headings, large numerals |
| `--font-body` | Inter stack | running prose |
| `--font-mono` | IBM Plex Mono stack | labels, tags, dates, nav links — this system's "data" voice |
| `--max` | `1080px` | page content max-width |
| `--edge` | `clamp(20px, 6vw, 64px)` | page horizontal padding |

Also importable directly as typed JS constants — `colors`, `fonts`, `layout` — from `window.AditfDesignSystem` (e.g. `colors.amber`, `fonts.mono`), for anywhere you need the value in JS rather than CSS.

**Where the truth lives.** `styles.css` (in this bundle) is the full compiled stylesheet — read it before styling anything custom. Each component's own `.d.ts` is its prop contract; each `.prompt.md` is its usage doc.

**One idiomatic composition** (adapted from a verified preview — `Hero` composing the tracking-waybill badge, name, route line, and action buttons):

```tsx
<Hero
  trackingLabel="TRACKING NO."
  trackingValue="AF-2011–2026"
  status="IN TRANSIT"
  name="Aditya"
  nameAccent="Firmansyah"
  role="Senior Software Engineer — Full-Stack Developer"
  origin="SURAKARTA, ID"
  dest="WORLDWIDE"
  lede="Thirteen-plus years shipping web, backend, and mobile software."
  actions={
    <>
      <Button variant="stamp" href="/cv.pdf" download>Download CV</Button>
      <Button variant="ghost" href="#contact">Get in touch</Button>
    </>
  }
/>
```

Twenty components ship: `Button`, `Nav`, `RouteProgress`, `SectionHead`, `Hero`, `Waybill`, `LabelCard`, `StatRow`/`StatChip`, `CrateGrid`/`Crate`, `ProjectCard`, `Timeline`/`TimelineItem`, `Seal`, `LangChip`, `ContactGrid`/`ContactRow`, `Barcode`, `Reveal`. `Reveal` wraps any children in a scroll-triggered fade-in (respects `prefers-reduced-motion`); compose it around a section, not inside one.
