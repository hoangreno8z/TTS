---
name: ui-ux-pro-max
description: >-
  Expert UI/UX design intelligence for both mobile and desktop interfaces.
  Activate when designing, writing, or refining UI components, layouts, styling,
  color systems, touch targets, modals, drawers, or user interaction flows.
---

# UI/UX Pro Max: Design & Interaction Standard

Provides design intelligence to build ultra-sleek, ergonomic, and high-performance interfaces for mobile devices and desktop browsers.

## 1. Zero-Emoji Design System
- NEVER use Unicode emojis (e.g. 🎙️, 🚀, 💡, 📱, ✨) in web UI components, buttons, or labels.
- ALWAYS use crisp SVG icons, CSS-rendered glyphs, or semantic typographic badges.
- All icons must have `aria-hidden="true"` and explicit viewBox/dimensions (e.g., 16x16, 20x20, 24x24).

## 2. Ergonomics & Touch-Target Architecture (Mobile-First)
- Minimum Touch Target: 44px x 44px (Apple HIG & Material Design 3 standard) for all tappable buttons, sliders, and controls.
- Thumb-Zone Placement: Place primary actions (Play, Stop, Record, Submit) in the bottom 40% of the mobile screen.
- Active Feedback: Every button must provide instant tactile visual feedback on tap (`:active { transform: scale(0.97); opacity: 0.9; }`).

## 3. Screen Space Optimization & Information Density
- High Information Density with Clean Breathing Room: Avoid bloated paddings (>24px on mobile is forbidden). Use compact 8px/12px/16px rhythm.
- Collapsible Accordions & Floating Drawers: Hide secondary controls (DSP fine-tuning, advanced parameters) inside smooth bottom sheets or accordions to keep the main view clean.
- Sticky Header & Control Bar: Keep essential playback/status controls accessible without requiring endless scrolling.

## 4. Visual Hierarchy & Color System
- High-Contrast Semantic Palette:
  - Background: Deep Dark (`#0b0f19`, `#111827`) or Crisp Slate (`#0f172a`).
  - Card/Surface: Elevated Glass (`rgba(30, 41, 59, 0.7)` with `backdrop-filter: blur(12px)`).
  - Primary Accent: Electric Cyan (`#06b6d4`), Neon Indigo (`#6366f1`), or Emerald (`#10b981`).
  - Text Hierarchy: Primary (`#f8fafc`), Secondary (`#94a3b8`), Muted/Helper (`#64748b`).
- Borders & Dividers: Subtle 1px borders (`border: 1px solid rgba(255, 255, 255, 0.08)`).
