{
  "brand": {
    "name": "DagzFlix",
    "attributes": [
      "premium",
      "cinematic",
      "ultra-fluid",
      "trustworthy",
      "French-first",
      "glassmorphism",
      "dark-only"
    ],
    "north_star": "Netflix browsing speed + Apple TV polish, with a power-user player (audio/subtitles/quality) that still feels effortless."
  },
  "visual_style": {
    "fusion_inspiration": {
      "layout_principle": "Netflix rows + Apple TV vertical posters + bento utility panels (Continue Watching / Requests / Favorites)",
      "surface_language": "Liquid-glass overlays (frosted, subtle borders, inner highlights) on deep charcoal",
      "motion_language": "fast, damped spring; controls fade/slide; hover tilt on posters; player controls auto-hide"
    },
    "do_not": [
      "No purple for AI/chat-like accents (use ocean/teal/ice-blue + warm amber for warnings)",
      "No heavy gradients; keep gradients decorative and under 20% viewport",
      "No centered app container text alignment"
    ]
  },
  "design_tokens": {
    "css_custom_properties": {
      "instructions": "Define these in /app/frontend/src/index.css under :root and [data-theme='dark'] (dark-only is fine). Use Tailwind for layout but keep these tokens for consistency.",
      "tokens": {
        "--bg": "#050607",
        "--bg-elev-1": "#0A0C0F",
        "--bg-elev-2": "#0E1116",
        "--fg": "#F4F6FB",
        "--fg-muted": "rgba(244,246,251,0.72)",
        "--fg-subtle": "rgba(244,246,251,0.56)",

        "--card": "rgba(255,255,255,0.04)",
        "--card-strong": "rgba(255,255,255,0.06)",
        "--stroke": "rgba(255,255,255,0.08)",
        "--stroke-strong": "rgba(255,255,255,0.12)",

        "--primary": "#E11D48",
        "--primary-2": "#FB7185",
        "--accent": "#2DD4BF",
        "--accent-2": "#38BDF8",

        "--success": "#22C55E",
        "--warning": "#F59E0B",
        "--danger": "#EF4444",
        "--info": "#38BDF8",

        "--ring": "rgba(45,212,191,0.55)",
        "--shadow": "0 18px 60px rgba(0,0,0,0.55)",
        "--shadow-soft": "0 10px 30px rgba(0,0,0,0.35)",

        "--radius-sm": "10px",
        "--radius-md": "14px",
        "--radius-lg": "18px",

        "--blur-sm": "10px",
        "--blur-md": "18px",
        "--blur-lg": "28px",

        "--space-1": "4px",
        "--space-2": "8px",
        "--space-3": "12px",
        "--space-4": "16px",
        "--space-5": "24px",
        "--space-6": "32px",
        "--space-7": "48px",
        "--space-8": "64px"
      }
    },
    "tailwind_usage_notes": {
      "backgrounds": "Use bg-[color:var(--bg)] for app shell; use glass utility classes from App.css for panels.",
      "borders": "Prefer border-white/10 or border-[color:var(--stroke)]",
      "shadows": "Use shadow-[var(--shadow-soft)] for cards; shadow-[var(--shadow)] for modals/player overlays",
      "radius": "Use rounded-[var(--radius-md)] for most cards; rounded-[var(--radius-lg)] for hero panels"
    },
    "gradients": {
      "allowed_decorative_gradients": [
        "radial-gradient(900px circle at 20% 10%, rgba(45,212,191,0.14), transparent 55%)",
        "radial-gradient(700px circle at 80% 20%, rgba(56,189,248,0.12), transparent 60%)",
        "radial-gradient(800px circle at 60% 90%, rgba(225,29,72,0.10), transparent 55%)"
      ],
      "usage": "Only as section background overlays (hero/top of page) and never behind long text blocks. Keep total gradient coverage under 20% viewport height."
    }
  },
  "typography": {
    "font_pairing": {
      "display": "Brockmann (fallback: Space Grotesk)",
      "body": "Figtree (fallback: Inter)",
      "mono": "IBM Plex Mono (for technical labels like codecs, bitrates, debug)"
    },
    "google_fonts_import": {
      "instructions": "Add to /app/frontend/public/index.html <head> (CRA) or import in index.css via @import url(...).",
      "urls": [
        "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Figtree:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap"
      ],
      "note": "If Brockmann is not available via Google Fonts, use Space Grotesk as the display font."
    },
    "text_size_hierarchy": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
      "h2": "text-base md:text-lg text-[color:var(--fg-muted)]",
      "section_title": "text-lg md:text-xl font-semibold",
      "body": "text-sm md:text-base text-[color:var(--fg)]/90",
      "meta": "text-xs text-[color:var(--fg-subtle)]",
      "chip": "text-[11px] uppercase tracking-widest"
    },
    "type_rules": [
      "Use tighter tracking for big titles (tracking-tight) and wider tracking for chips/badges (tracking-widest).",
      "Never use pure white for long paragraphs; use --fg-muted for readability on dark backgrounds."
    ]
  },
  "layout": {
    "grid_system": {
      "container": "px-4 sm:px-6 lg:px-10 max-w-[1400px]",
      "page_gutters": "Mobile-first: 16px; Tablet: 24px; Desktop: 40px",
      "library_grid": {
        "mobile": "grid-cols-2 gap-3",
        "tablet": "sm:grid-cols-3 sm:gap-4",
        "desktop": "lg:grid-cols-6 lg:gap-5",
        "poster_aspect": "2/3 (use AspectRatio component)"
      },
      "rows": "Home uses horizontal ScrollArea rows with snap + hover lift; keep row titles left-aligned."
    },
    "navigation": {
      "pattern": "Left rail on desktop (glass), bottom nav on mobile (glass).",
      "desktop_rail": "72px collapsed icons; expands to 240px on hover/focus-within.",
      "mobile_bottom_nav": "5 items max: Home, Movies, Series, Search, Profile",
      "data_testids": {
        "desktop_nav": "app-desktop-nav",
        "mobile_nav": "app-mobile-bottom-nav",
        "search_trigger": "nav-search-button"
      }
    }
  },
  "components": {
    "component_path": {
      "shadcn_primary": [
        "/app/frontend/src/components/ui/button.jsx",
        "/app/frontend/src/components/ui/card.jsx",
        "/app/frontend/src/components/ui/input.jsx",
        "/app/frontend/src/components/ui/label.jsx",
        "/app/frontend/src/components/ui/dialog.jsx",
        "/app/frontend/src/components/ui/drawer.jsx",
        "/app/frontend/src/components/ui/sheet.jsx",
        "/app/frontend/src/components/ui/tabs.jsx",
        "/app/frontend/src/components/ui/select.jsx",
        "/app/frontend/src/components/ui/dropdown-menu.jsx",
        "/app/frontend/src/components/ui/slider.jsx",
        "/app/frontend/src/components/ui/progress.jsx",
        "/app/frontend/src/components/ui/scroll-area.jsx",
        "/app/frontend/src/components/ui/tooltip.jsx",
        "/app/frontend/src/components/ui/hover-card.jsx",
        "/app/frontend/src/components/ui/badge.jsx",
        "/app/frontend/src/components/ui/skeleton.jsx",
        "/app/frontend/src/components/ui/sonner.jsx"
      ],
      "notes": "Prefer Dialog for desktop modals and Drawer/Sheet for mobile. Use ScrollArea for Netflix-like rows."
    },
    "core_patterns": {
      "glass_panel": {
        "use": "Setup cards, login panel, filters bar, player settings overlay",
        "class": "glass rounded-[var(--radius-lg)] shadow-[var(--shadow-soft)] border border-white/10"
      },
      "poster_card": {
        "structure": "AspectRatio -> img -> overlay gradient (very subtle) -> meta row",
        "class": "group relative overflow-hidden rounded-[var(--radius-md)] border border-white/10 bg-white/5",
        "hover": "hover:shadow-[0_18px_60px_rgba(0,0,0,0.55)] hover:-translate-y-1 (transition-transform only)",
        "micro": "On hover: show quick actions (Play, Details, Favorite) in a glass mini-toolbar."
      },
      "chips_badges": {
        "use": "VF/VFQ/VO/VOSTFR, Direct Play/HLS, 4K/HDR",
        "class": "inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] tracking-widest uppercase"
      },
      "filters_bar": {
        "use": "Movies/Series library filters",
        "class": "sticky top-0 z-30 glass-strong rounded-[var(--radius-lg)] px-3 py-2",
        "components": "Select, Tabs, Input (search within library), ToggleGroup"
      }
    },
    "forms": {
      "setup_page": {
        "layout": "Wizard-like: left progress rail + right form panel. On mobile: single column with Collapsible sections.",
        "sections": [
          "Jellyfin server URL + API key/login",
          "TMDB API key",
          "Radarr config",
          "Sonarr config",
          "Test connections + Save"
        ],
        "components": ["Form", "Input", "Button", "Alert", "Progress", "Accordion", "Tooltip"],
        "data_testids": [
          "setup-jellyfin-url-input",
          "setup-jellyfin-login-button",
          "setup-tmdb-key-input",
          "setup-radarr-url-input",
          "setup-sonarr-url-input",
          "setup-test-connections-button",
          "setup-save-button"
        ]
      },
      "login_page": {
        "pattern": "Centered panel but left-aligned text; background uses subtle cinematic gradients + noise.",
        "components": ["Card", "Input", "Button", "Separator"],
        "data_testids": ["login-username-input", "login-password-input", "login-submit-button"]
      }
    },
    "search": {
      "tmdb_command_palette": {
        "pattern": "Use Command component as a spotlight search (Cmd+K).",
        "components": ["Command", "Dialog", "Badge"],
        "data_testids": ["search-open-command", "search-command-input", "search-result-item"]
      }
    },
    "player": {
      "player_shell": {
        "layout": "Fullscreen video with top-left back button + title; bottom controls glass overlay; right-side settings drawer.",
        "controls": [
          "Play/Pause",
          "Seek bar (Slider)",
          "Time elapsed/remaining",
          "Volume",
          "Quality (Auto/1080p/4K)",
          "Audio track selector (FR/VFQ/VO)",
          "Subtitle selector (Off/FR forced/FR full)",
          "Playback speed",
          "Direct Play vs HLS badge"
        ],
        "micro_interactions": [
          "Controls fade in on mouse move; fade out after 2.5s idle.",
          "Keyboard: Space play/pause, arrows seek, M mute, F fullscreen, S subtitles.",
          "On track change: show toast (sonner) with selected audio/subtitle."
        ],
        "components": ["Slider", "Tooltip", "DropdownMenu", "Sheet", "Badge", "Sonner"],
        "data_testids": [
          "player-play-toggle",
          "player-seek-slider",
          "player-volume-slider",
          "player-quality-menu",
          "player-audio-menu",
          "player-subtitle-menu",
          "player-back-button"
        ]
      },
      "subtitle_style": {
        "note": "Existing App.css has video::cue and .player-subtitle. Keep it; ensure subtitle background opacity adapts to bright scenes.",
        "recommended": "Use a subtle rounded rectangle with strong shadow; avoid huge font sizes on mobile."
      }
    },
    "admin_future": {
      "pattern": "Data-dense but premium: Table + Tabs + Cards; use IBM Plex Mono for IDs/codec stats.",
      "components": ["Table", "Tabs", "Card", "Badge", "Pagination"],
      "charts": "Use Recharts for telemetry (transcode time, bitrate, errors)."
    }
  },
  "motion": {
    "library": {
      "recommended": "framer-motion",
      "install": "npm i framer-motion",
      "usage": "Use for page transitions, poster hover lift, and player control fade. Respect prefers-reduced-motion."
    },
    "principles": [
      "Use spring transitions for transforms only (no transition: all).",
      "Hover: translateY(-4px) + slight scale(1.02) on posters; keep duration 180–240ms.",
      "Focus-visible: ring uses --ring; never remove outlines.",
      "Scrolling: rows use momentum + snap; add subtle parallax on hero backdrop (translateY 12px max)."
    ],
    "micro_interaction_specs": {
      "buttons": {
        "default": "bg-[color:var(--primary)] text-white rounded-[12px]",
        "hover": "hover:brightness-110",
        "press": "active:scale-[0.98]",
        "transition": "transition-[filter,background-color,box-shadow] duration-200"
      },
      "glass_controls": {
        "hover": "hover:bg-white/10 hover:border-white/15",
        "transition": "transition-[background-color,border-color,box-shadow,opacity] duration-200"
      }
    }
  },
  "accessibility": {
    "requirements": [
      "WCAG AA contrast: use --fg-muted for paragraphs; ensure buttons meet contrast on glass surfaces.",
      "Keyboard navigation for all menus, player controls, and carousels.",
      "ARIA labels for icon-only buttons (e.g., aria-label='Play').",
      "Respect prefers-reduced-motion: disable parallax and reduce hover transforms."
    ],
    "focus": "Keep existing focus-visible outline but change to --ring for non-danger actions; reserve red outline for destructive actions."
  },
  "performance": {
    "notes": [
      "Prefer CSS blur only on small surfaces; avoid full-screen backdrop-filter layers.",
      "Poster images: lazy-load, use low-quality placeholders (Skeleton).",
      "Player: keep overlays lightweight; avoid re-rendering video element on menu changes."
    ]
  },
  "image_urls": {
    "hero_backgrounds": [
      {
        "url": "https://images.unsplash.com/photo-1708497351913-71254998ed1a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHw0fHxjaW5lbWF0aWMlMjBkYXJrJTIwbW92aWUlMjB0aGVhdGVyJTIwYWJzdHJhY3QlMjBiYWNrZ3JvdW5kfGVufDB8fHxibGFja3wxNzc1MDY5MjQzfDA&ixlib=rb-4.1.0&q=85",
        "description": "Cinematic theater ambience for Setup/Login hero backdrop (apply heavy blur + dark overlay)."
      },
      {
        "url": "https://images.pexels.com/photos/7234386/pexels-photo-7234386.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "description": "Bokeh popcorn background for empty states / onboarding panels (blurred)."
      }
    ],
    "textures": [
      {
        "url": "https://images.unsplash.com/photo-1554356391-8bbd5018add1?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2OTV8MHwxfHNlYXJjaHw0fHxkYXJrJTIwYmx1ZSUyMGNpbmVtYXRpYyUyMGdyYWRpZW50JTIwdGV4dHVyZXxlbnwwfHx8Ymx1ZXwxNzc1MDY5MjQzfDA&ixlib=rb-4.1.0&q=85",
        "description": "Soft blue blur texture for subtle section overlays (keep under 20% viewport)."
      }
    ],
    "avatars": [
      {
        "url": "https://images.unsplash.com/photo-1561820009-8bef03ebf8e5?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2ODl8MHwxfHNlYXJjaHwzfHxkYXJrJTIwbWluaW1hbCUyMHBvcnRyYWl0JTIwYXZhdGFyJTIwc3R1ZGlvfGVufDB8fHxibGFja3wxNzc1MDY5MjQzfDA&ixlib=rb-4.1.0&q=85",
        "description": "Profile avatar placeholder (use Avatar component; crop circle)."
      }
    ]
  },
  "instructions_to_main_agent": {
    "global_css_updates": [
      "Keep existing /app/frontend/src/App.css glass classes; extend with token-based colors in index.css.",
      "Do NOT add transition: all anywhere. Use transition-[background-color,border-color,opacity,filter,box-shadow] and transition-transform separately.",
      "Add a subtle noise overlay utility (pseudo-element) for hero sections only (max 20% viewport)."
    ],
    "component_build_plan": [
      "Create a reusable <PosterCard /> (JS) using AspectRatio + HoverCard/Tooltip + Button variants; include data-testid on card and actions.",
      "Create <MediaRow /> using ScrollArea horizontal with snap; skeleton placeholders while loading.",
      "Create <PlayerControls /> overlay using Slider + DropdownMenu + Sheet; auto-hide logic; keyboard shortcuts.",
      "Setup page as wizard: Accordion sections + Progress; test connection buttons show Sonner toasts."
    ],
    "data_testid_policy": "All buttons/inputs/menus and key info labels must include data-testid in kebab-case describing role (e.g., data-testid='media-detail-play-button').",
    "js_only_note": "All components are .jsx; follow named exports for components and default exports for pages."
  }
}

<General UI UX Design Guidelines>  
    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms
    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text
   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json

 **GRADIENT RESTRICTION RULE**
NEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc
NEVER use dark gradients for logo, testimonial, footer etc
NEVER let gradients cover more than 20% of the viewport.
NEVER apply gradients to text-heavy content or reading areas.
NEVER use gradients on small UI elements (<100px width).
NEVER stack multiple gradient layers in the same viewport.

**ENFORCEMENT RULE:**
    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors

**How and where to use:**
   • Section backgrounds (not content backgrounds)
   • Hero section header content. Eg: dark to light to dark color
   • Decorative overlays and accent elements only
   • Hero section with 2-3 mild color
   • Gradients creation can be done for any angle say horizontal, vertical or diagonal

- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**

</Font Guidelines>

- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. 
   
- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.

- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.
   
- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly
    Eg: - if it implies playful/energetic, choose a colorful scheme
           - if it implies monochrome/minimal, choose a black–white/neutral scheme

**Component Reuse:**
	- Prioritize using pre-existing components from src/components/ui when applicable
	- Create new components that match the style and conventions of existing components when needed
	- Examine existing components to understand the project's component patterns before creating new ones

**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component

**Best Practices:**
	- Use Shadcn/UI as the primary component library for consistency and accessibility
	- Import path: ./components/[component-name]

**Export Conventions:**
	- Components MUST use named exports (export const ComponentName = ...)
	- Pages MUST use default exports (export default function PageName() {...})

**Toasts:**
  - Use `sonner` for toasts"
  - Sonner component are located in `/app/src/components/ui/sonner.tsx`

Use 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.
</General UI UX Design Guidelines>
