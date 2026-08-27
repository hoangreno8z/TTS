---
name: zero-lag-frontend-architecture
description: >-
  High-performance, zero-lag frontend engineering guidelines.
  Activate when writing JavaScript logic, DOM updates, event listeners, state stores,
  audio playback visualizers, or performance profiling.
---

# Zero-Lag Frontend Architecture Standard

Guarantees 60fps/120fps ultra-smooth performance without stutter, garbage collection spikes, or memory leaks.

## 1. DOM & Rendering Optimization
- Hardware-Accelerated Animations: Only animate `transform` and `opacity`. NEVER animate `height`, `top`, `margin`, or `padding`.
- Batch DOM Mutations: Avoid Layout Thrashing. Read layout measurements first (`getBoundingClientRect`), then write batch updates in `requestAnimationFrame`.
- Virtualization & Lazy Loading: For long lists of voice models or audio files, render only visible items in DOM.

## 2. Event Handling & Memory Discipline
- Debounce & Throttle: Debounce text input handlers (300ms) and throttle canvas resize/scroll events (16ms).
- Event Delegation: Attach event listeners to parent containers rather than hundreds of individual child nodes.
- Cleanup & Garbage Collection: Always remove listeners, disconnect `ResizeObserver`/`IntersectionObserver`, and close `AudioContext` on component unmount.

## 3. Audio & Canvas Zero-Lag Execution
- Canvas Waveform Rendering: Use `OffscreenCanvas` or double-buffered canvas rendering for audio waveforms.
- Web Audio Lifecycle: Suspend `AudioContext` when inactive to save mobile CPU and battery.
