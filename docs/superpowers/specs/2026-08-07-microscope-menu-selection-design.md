# Microscope Menu Selection Design

## Goal

Make the active microscope immediately legible in Navigate's **Microscope
Configuration** menu on Windows while preserving clear behavior on macOS and
Linux.

## Background

Microscope and zoom choices are Tk menu radiobuttons backed by the shared
`resolution_value` variable. The controller already keeps that variable aligned
with the active microscope and zoom. On Windows, however, Tk draws the selected
entry using the menu's `selectcolor`. Navigate applies dark menu background and
foreground colors globally but does not currently provide a themed selection
color, so the Windows system default can have poor contrast.

## Design

### Global menu colors

The global theme will set `*Menu.SelectColor` to the theme's `text` color. This
keeps the selected checkmark visible against both the dark menu background and
the active-entry background. The option will apply to all Tk menus rather than
introducing Windows-only branches or styling only the microscope menu.

The global theme will also set `*Menu.DisabledForeground` to the existing
`muted_text` color. This keeps the disabled status row readable and makes other
disabled menu entries consistent with Navigate's theme instead of inheriting a
platform system color.

### Current-microscope status row

The first entry in **Microscope Configuration** will be a disabled status row
with the label `Current microscope: <name>`, followed by a separator. It will be
informational rather than actionable and will remain visible before the user
navigates into any microscope-specific zoom submenu.

The status row will initialize from the configured microscope name. Whenever
`resolution_value` changes, the existing trace path will update the status row
before forwarding the resolution change to the parent controller. The displayed
name will be derived from the full resolution value without changing the
existing microscope-selection or zoom-selection semantics.

## Error Handling and Compatibility

If the resolution value is empty during startup, the status row will retain the
configured microscope name. No platform detection is required: macOS may ignore
the Tk selection-color option while Windows and X11 can use it. The existing
radiobutton state remains the authority for selection.

## Testing

Focused tests will verify that:

1. Global theme application registers the menu selection color using the theme
   text color and the disabled foreground using the muted-text color.
2. Menu initialization adds the current-microscope status row and separator
   before microscope choices.
3. A resolution-variable update refreshes the displayed microscope name and
   still dispatches the existing resolution command.

Native Windows smoke testing remains the final visual check because macOS Tk
cannot reproduce Windows menu rendering.

## Out of Scope

- Changing microscope or zoom selection behavior.
- Adding platform-specific menu implementations.
- Renaming the top-level menubar item.
- Introducing new palette colors or changing existing theme tokens.
