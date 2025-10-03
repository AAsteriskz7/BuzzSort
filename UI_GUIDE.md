# User Interface Guide

This guide explains the visual elements and layout of the Intelligent File Janitor application.

## Main Window Layout

The application window is organized into clear, card-based sections:

### 1. Header Section
```
🧹 Intelligent File Janitor
   AI-powered file organization
─────────────────────────────────
```
- **Large icon** for brand recognition
- **Title** in blue, bold text
- **Subtitle** explaining the purpose
- **Separator line** for visual clarity

### 2. Folder Selection Card
```
┌─ 📁 Select Folder ──────────────────┐
│                                      │
│  [📂 Browse Folder]  No folder sel… │
│                                      │
└──────────────────────────────────────┘
```
- **Card with icon** (📁) in the title
- **Browse button** with folder icon
- **Path display** showing selected folder
- **Tooltip** on hover with keyboard shortcut

### 3. Analysis Results Card
```
┌─ 🔍 Analysis Results ───────────────┐
│                                      │
│  📊 Scan Summary                     │
│  • Found 150 files                   │
│  • 3 clusters identified             │
│                                      │
│  📁 Cluster 1: Documents (45 files)  │
│  📁 Cluster 2: Images (80 files)     │
│  📁 Cluster 3: Code (25 files)       │
│                                      │
└──────────────────────────────────────┘
```
- **Scrollable text area** with light background
- **Color-coded content**:
  - Blue for headers
  - Green for success/highlights
  - Orange for warnings
  - Red for errors
- **Monospace font** for file paths

### 4. Organization Plan Card
```
┌─ 📋 Organization Plan ──────────────┐
│                                      │
│  📂 Folders to Create:               │
│  • Documents/                        │
│  • Images/                           │
│  • Code/                             │
│                                      │
│  📄 File Operations:                 │
│  • report.txt → Documents/           │
│  • photo.jpg → Images/               │
│                                      │
└──────────────────────────────────────┘
```
- **Scrollable text area** with light background
- **Color-coded operations**:
  - Blue for folders
  - Gray for files
  - Orange for warnings
- **Clear operation descriptions**

### 5. Action Buttons
```
[🔍 Analyze Files]  [⚡ Execute Plan]
```
- **Icon-enhanced buttons** for quick recognition
- **Color-coded**:
  - Blue for analysis (safe operation)
  - Orange for execution (warning)
- **Hover effects** with light background
- **Tooltips** with keyboard shortcuts

### 6. Progress Indicator
```
Processing files... (45/150)
████████████░░░░░░░░░░░░░░░░░░ 30%
```
- **Status text** in blue
- **Green progress bar** with gray background
- **Percentage display**
- **Smooth animation**

### 7. Status Bar
```
┌──────────────────────────────────────┐
│ ✨ Ready - Select a folder to begin  │
└──────────────────────────────────────┘
```
- **Light blue background** (#E3F2FD)
- **Blue text** for consistency
- **Emoji prefix** for friendliness
- **Full-width** display

## Color Coding System

### Text Areas

#### Analysis Results
- **Headers** (🔵 Blue): Section titles
- **Highlights** (🟢 Green): Success messages, file counts
- **Warnings** (🟠 Orange): Cautions, suggestions
- **Errors** (🔴 Red): Problems, failures
- **Info** (🔵 Blue): General information
- **Muted** (⚪ Gray): Less important details

#### Organization Plan
- **Headers** (🟠 Orange): Section titles
- **Folders** (🔵 Blue): Directory names
- **Files** (⚪ Gray): File names
- **Success** (🟢 Green): Completed operations
- **Warnings** (🟠 Orange): Potential issues
- **Errors** (🔴 Red): Failed operations

## Interactive Elements

### Buttons

#### Primary Button (Analyze)
- **Color**: Blue text
- **Icon**: 🔍
- **Hover**: Light blue background
- **State**: Enabled after folder selection

#### Warning Button (Execute)
- **Color**: Orange text
- **Icon**: ⚡
- **Hover**: Light orange background
- **State**: Enabled after plan generation

### Tooltips
- **Dark background** with white text
- **Appear on hover** after 0.5 seconds
- **Show keyboard shortcuts** and warnings
- **95% opacity** for modern look

### Scrollbars
- **Thin, modern style**
- **Auto-hide** when not needed
- **Smooth scrolling**

## Keyboard Shortcuts

All shortcuts are shown in tooltips and menus:

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open folder browser |
| `Ctrl+A` | Analyze files |
| `F5` | Analyze files (alternative) |
| `Ctrl+E` | Execute plan |
| `Ctrl+H` | View operation history |
| `Ctrl+L` | Open log file |

## Menu Bar

### File Menu
- **Select Folder...** (Ctrl+O)
- **Exit**

### View Menu
- **Operation History** (Ctrl+H)
- **Open Log File** (Ctrl+L)

### Help Menu
- **About**

## Responsive Behavior

### Window Resizing
- **Minimum size**: 750×550 pixels
- **Default size**: 950×750 pixels
- **Text areas expand** with window
- **Buttons maintain** fixed size
- **Proper spacing** at all sizes

### Content Overflow
- **Scrollbars appear** automatically
- **Text wraps** in display areas
- **Long paths** are fully visible with scrolling

## Visual States

### Idle State
- **Status**: "✨ Ready - Select a folder to begin"
- **Analyze button**: Disabled (gray)
- **Execute button**: Disabled (gray)
- **Text areas**: Empty with light background

### Folder Selected
- **Status**: "📁 Folder selected: [path]"
- **Analyze button**: Enabled (blue)
- **Execute button**: Disabled (gray)
- **Folder path**: Displayed in black

### Analyzing
- **Status**: "🔍 Analyzing files..."
- **Progress bar**: Visible and animating
- **Buttons**: Disabled during operation
- **Text area**: Updating with results

### Plan Ready
- **Status**: "✅ Plan ready for review"
- **Analyze button**: Enabled (blue)
- **Execute button**: Enabled (orange)
- **Both text areas**: Populated with results

### Executing
- **Status**: "⚡ Executing plan..."
- **Progress bar**: Visible and animating
- **Buttons**: Disabled during operation
- **Plan area**: Updating with results

### Complete
- **Status**: "✅ Organization complete!"
- **Results**: Displayed in plan area
- **Summary**: Shows success/failure counts
- **Buttons**: Re-enabled for new operation

## Accessibility Features

### Visual Clarity
- **High contrast** text and backgrounds
- **Large, readable fonts** (9-16pt)
- **Clear visual hierarchy**
- **Consistent spacing**

### Color Independence
- **Icons supplement** color coding
- **Text descriptions** for all operations
- **Status messages** provide context

### Keyboard Navigation
- **Tab order** follows logical flow
- **Keyboard shortcuts** for all actions
- **Focus indicators** on active elements

## Tips for Best Experience

1. **Maximize window** for best view of results
2. **Read tooltips** for helpful information
3. **Check status bar** for current state
4. **Review plan carefully** before executing
5. **Watch progress bar** during operations
6. **Check logs** for detailed information

---

**The modern, intuitive interface makes file organization a pleasant experience!** ✨
