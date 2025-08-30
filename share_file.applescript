#!/usr/bin/osascript
-- AppleScript to open Share menu for a file
-- Usage: osascript share_file.applescript "/path/to/file"

on run argv
    set filePath to item 1 of argv
    
    tell application "Finder"
        activate
        set theFile to POSIX file filePath as alias
        reveal theFile
        delay 0.5
    end tell
    
    -- Try to open the Share menu using the toolbar button
    tell application "System Events"
        tell process "Finder"
            set frontmost to true
            delay 0.5
            
            -- Try to click the Share button in the toolbar
            try
                click (first button of toolbar 1 of window 1 whose description contains "Share")
            on error
                -- If toolbar button not found, try keyboard shortcut
                -- Note: There's no standard keyboard shortcut for Share menu
                -- User will need to right-click manually
                display notification "Right-click the file and select Share > AirDrop" with title "Ready to Share"
            end try
        end tell
    end tell
end run