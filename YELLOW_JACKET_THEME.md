# 🐝 Buzz Sort - Yellow Jacket Theme

## Georgia Tech Official Colors Applied

This application uses the official Georgia Tech color palette to create a stunning, professional interface that represents Yellow Jacket pride.

### Primary Colors Used

#### Tech Gold (#B3A369)
- Used for: Secondary accents, accessible text
- PMS: 4515 Metallic / 8383
- RGB: 179, 163, 105

#### Buzz Gold (#EAAA00)
- Used for: Primary buttons, highlights, status bar text, folder names
- PMS: 124
- RGB: 234, 170, 0
- **Most prominent color** - vibrant and eye-catching

#### Navy Blue (#003057)
- Used for: Headers, primary text, button backgrounds, status bar background
- PMS: 540
- RGB: 0, 48, 87
- **Primary brand color**

### Secondary Colors Used

#### Tech Medium Gold (#A4925A)
- Used for: Arrows, accessible large text
- RGB: 164, 146, 90

#### Tech Dark Gold (#857437)
- Used for: Subheaders, accessible small text
- RGB: 133, 116, 55

#### Gray Matter (#54585A)
- Used for: File names, muted text
- PMS: 425
- RGB: 84, 88, 90

#### Pi Mile (#D6DBD4)
- Used for: Progress bar trough
- PMS: 427
- RGB: 214, 219, 212

#### Diploma (#F9F6E5)
- Used for: Window background, card backgrounds
- PMS: 7499
- RGB: 249, 246, 229

## UI Elements

### Header
- **Navy Blue background** (#003057) with raised border
- **Buzz Gold title** (#EAAA00) in large, bold font
- **Tech Gold subtitle** (#B3A369) for branding
- **Yellow Jacket emoji** (🐝) as the icon

### Buttons
- **Primary buttons**: Navy Blue background with Buzz Gold text
- **Warning buttons**: Buzz Gold background with Navy Blue text
- **Hover effects**: Transitions through Tech Gold shades
- **Larger padding** (10px) for prominence

### Text Areas
- **Headers**: Navy Blue (#003057)
- **Highlights**: Buzz Gold (#EAAA00)
- **Folders**: Buzz Gold (#EAAA00) - stands out
- **Files**: Gray Matter (#54585A)
- **Warnings**: Tech Gold (#B3A369)
- **Errors**: Dark red (#8B0000)

### Progress Bar
- **Bar color**: Buzz Gold (#EAAA00)
- **Trough color**: Pi Mile (#D6DBD4)
- **Thicker bar** (24px) for visibility
- **Raised relief** for 3D effect

### Status Bar
- **Background**: Navy Blue (#003057)
- **Text**: Buzz Gold (#EAAA00)
- **Bold font** for readability
- **Yellow Jacket emoji** (🐝) prefix

### Tooltips
- **Background**: Navy Blue (#003057)
- **Text**: Buzz Gold (#EAAA00)
- **Solid border** (2px) for definition
- **Bold font** for emphasis

### Cards/Frames
- **Background**: Diploma (#F9F6E5)
- **Border**: 2px solid
- **Labels**: Navy Blue (#003057)

## Accessibility

All color combinations meet WCAG AA standards:
- **Navy Blue on Buzz Gold**: High contrast
- **Buzz Gold on Navy Blue**: High contrast
- **Navy Blue on Diploma**: Excellent contrast
- **Tech Dark Gold on white**: Accessible for small text

## Branding Elements

1. **Application Title**: "BUZZ SORT" in all caps
2. **Subtitle**: "AI-Powered File Organization • Georgia Tech"
3. **Icon**: Yellow Jacket emoji (🐝) throughout
4. **Window Title**: "🐝 Buzz Sort - AI File Organization"
5. **Status Messages**: Prefixed with 🐝

## Visual Impact

The Yellow Jacket theme creates:
- **Immediate brand recognition** with GT colors
- **Professional appearance** suitable for judges
- **High contrast** for excellent readability
- **Vibrant energy** from Buzz Gold accents
- **Cohesive design** across all UI elements
- **School spirit** that stands out

## Technical Implementation

- **Tkinter ttk.Style** for button and widget styling
- **tk.Label** for colored backgrounds (header, status bar)
- **Text widget tags** for syntax highlighting
- **Consistent color constants** defined at setup
- **Hover effects** using style.map()

---

**Go Jackets! 🐝💛💙**
