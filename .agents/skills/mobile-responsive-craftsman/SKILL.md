---
name: mobile-responsive-craftsman
description: >-
  Specialized mobile-first responsive frontend development skill.
  Activate when writing CSS, layout wrappers, grid/flex containers, viewport handling,
  touch gestures, or responsive media queries.
---

# Mobile Responsive Craftsman Standard

Ensures web applications feel like native mobile apps while scaling seamlessly up to ultra-wide desktop displays.

## 1. Viewport & Dynamic Sizing Rules
- Use `dvh` (Dynamic Viewport Height) instead of `vh` to prevent jumping when mobile address bars expand/collapse.
- Use CSS `clamp()` for fluid typography and spacing:
  `font-size: clamp(0.875rem, 0.8rem + 0.5vw, 1.125rem);`
- Always respect iOS/Android safe area insets:
  `padding-bottom: max(16px, env(safe-area-inset-bottom));`

## 2. Flexible Layout Mechanics
- Mobile: Single-column vertical flow with full-width action cards.
- Tablet (>= 768px): 2-column balanced split (Editor on left, Waveform/Studio on right).
- Desktop (>= 1024px): 3-column / sidebar-driven cockpit with persistent navigation.
- No Horizontal Overflow: Always enforce `overflow-x: hidden` and `box-sizing: border-box` across all containers.

## 3. Touch Gestures & Mobile Scrolling
- Momentum Scrolling: `-webkit-overflow-scrolling: touch;` on all scrollable containers.
- Disable Unwanted Mobile Zoom: Use `touch-action: manipulation;` on buttons and interactive canvases.
- Pull-to-refresh & Overscroll: Set `overscroll-behavior-y: contain;` on modals and sheets.
