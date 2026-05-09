---
name: Assistant Design System
colors:
  surface: '#13131b'
  surface-dim: '#13131b'
  surface-bright: '#393841'
  surface-container-lowest: '#0d0d15'
  surface-container-low: '#1b1b23'
  surface-container: '#1f1f27'
  surface-container-high: '#292932'
  surface-container-highest: '#34343d'
  on-surface: '#e4e1ed'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#e4e1ed'
  inverse-on-surface: '#303038'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#d0bcff'
  on-secondary: '#3c0091'
  secondary-container: '#571bc1'
  on-secondary-container: '#c4abff'
  tertiary: '#ffb783'
  on-tertiary: '#4f2500'
  tertiary-container: '#d97721'
  on-tertiary-container: '#452000'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#e9ddff'
  secondary-fixed-dim: '#d0bcff'
  on-secondary-fixed: '#23005c'
  on-secondary-fixed-variant: '#5516be'
  tertiary-fixed: '#ffdcc5'
  tertiary-fixed-dim: '#ffb783'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#703700'
  background: '#13131b'
  on-background: '#e4e1ed'
  surface-variant: '#34343d'
typography:
  display-lg:
    fontFamily: Geist
    fontSize: 40px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.04em
  headline-md:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-sm:
    fontFamily: Geist
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  label-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  container-max: 1200px
  gutter: 16px
---

## Brand & Style
This design system is engineered for a "facts-first" fintech environment. The brand personality is authoritative yet accessible, balancing the technical rigor of mutual fund data with the conversational ease of an AI assistant. 

The aesthetic leverages **Modern Glassmorphism** with a focus on depth and legibility. By utilizing a deep navy-black foundation, we create a high-contrast environment where critical financial data stands out. The style avoids unnecessary decoration, instead using subtle translucent layers, crisp 1px borders, and soft gradients to guide the user's eye toward actionable insights and clarity in response.

## Colors
The palette is rooted in a deep "Midnight Navy" to reduce eye strain during long reading sessions.
- **Primary Indigo (#6366f1):** Used for primary actions, active states, and brand-driven highlights.
- **Secondary Violet (#8b5cf6):** Used for AI-generated content accents and differentiating assistant messages from user messages.
- **Functional Colors:** Emerald Green handles the "Send" action and success confirmations; Amber is reserved for regulatory warnings or data disclaimers; Rose is used for refusal states or system errors.
- **Borders:** All UI boundaries use a consistent Slate (#334155) to maintain structure without creating visual noise.

## Typography
This design system utilizes a dual-font strategy to maximize readability and technical feel.
- **Geist** is employed for headings and labels. Its monolinear, technical construction fits the fintech narrative. Headings must use **Semibold** weights with tight tracking (-0.02em to -0.04em) to feel impactful and modern.
- **Inter** is used for all body text and chat bubbles. Its high x-height ensures that complex financial explanations remain legible at smaller sizes.
- **Scale:** On mobile devices, `display-lg` should scale down to 32px to maintain visual balance.

## Layout & Spacing
The system follows a strict 4px soft-grid. 
- **Chat Interface:** Uses a centered fixed-width column (max 800px) on desktop to keep the conversation focused. 
- **Dashboards:** Utilize a 12-column fluid grid with 24px gutters.
- **Margins:** Standard mobile padding is 16px, scaling to 24px or 40px on desktop to allow the glassmorphic cards room to "breathe."
- **Rhythm:** Use `md` (16px) for internal card padding and `lg` (24px) for vertical separation between message clusters.

## Elevation & Depth
Depth is achieved through **Tonal Layering** and **Backdrop Blurs** rather than traditional heavy shadows.
- **Layer 0 (Background):** Solid #0b0f19.
- **Layer 1 (Cards/Bubbles):** Surface #151b2b with a 1px border (#334155). 
- **Layer 2 (Popovers/Modals):** Surface #151b2b with 80% opacity and a 12px `backdrop-filter: blur()`. These should have a subtle outer glow using the Primary Indigo at 10% opacity.
- **Focus States:** Elements receive a 2px offset ring of Primary Indigo (#6366f1) to ensure high visibility for keyboard navigation.

## Shapes
The shape language is friendly but professional, utilizing distinct corner radii to categorize information:
- **Chat Bubbles:** Use `rounded-2xl` (1.5rem) to create a soft, approachable container for conversation.
- **Inputs:** Use `rounded-xl` (0.75rem) to differentiate interactive fields from static content.
- **Data Cards:** Use `rounded-lg` (1rem) for a more structured, organized feel in the FAQ and portfolio sections.
- **Buttons:** Small buttons use `rounded-md`, while primary "Send" or "Action" buttons may use the pill shape for maximum prominence.

## Components
- **Buttons:** Primary buttons use a linear gradient from Primary Indigo to Secondary Violet. Hover states should increase the gradient intensity.
- **Chat Bubbles:** Assistant bubbles feature a subtle 1px border (#334155) and the Surface background. User bubbles should have a slightly lighter tint or a very subtle Indigo glow to distinguish authorship.
- **Input Fields:** The search/chat input is a large `xl` rounded bar. It uses a 1px border that transitions from Slate to Primary Indigo on focus.
- **Chips/Filters:** Used for "Quick Questions" (e.g., "What is an Expense Ratio?"). These are ghost-style buttons with a Slate border and no fill until hovered.
- **Progress Indicators:** For loading AI responses, use a pulse animation rather than a spinner, utilizing the Primary Indigo color.
- **Success States:** "Send" buttons and success alerts utilize the Emerald Green (#10b981) to signify completion and safety.
