#!/usr/bin/osascript
-- AppleScript to open Share menu for a file
-- Usage: osascript share_file.applescript "/path/to/file"

on run argv
    set filePath to item 1 of argv
    
    tell application "Finder"
        -- First reveal and select the file
        set theFile to POSIX file filePath as alias
        reveal theFile
        
        -- Make sure the file is selected
        set selection to theFile
        
        -- Bring Finder to front
        activate
    end tell
    
    delay 0.2
    
    -- Try to use System Events to click the Share menu
    try
        tell application "System Events"
            tell process "Finder"
                set frontmost to true
                delay 0.3
                
                -- Click Share in the File menu (with ellipsis)
                click menu item "Share…" of menu "File" of menu bar 1
                delay 0.5
                
                -- The Share dialog should now be open
                -- Try to find and click AirDrop button if available
                try
                    -- Look for AirDrop button in the share sheet
                    click button "AirDrop" of sheet 1 of window 1
                on error
                    -- Share sheet is open but user needs to select AirDrop manually
                end try
            end tell
        end tell
    on error errMsg
        -- Log the actual error for debugging
        log "Error: " & errMsg
        
        -- If it's specifically an assistive access error
        if errMsg contains "not allowed assistive access" then
            display dialog "Accessibility permissions issue detected." & return & return & "Please ensure iTerm2 has accessibility permissions in:" & return & "System Settings > Privacy & Security > Accessibility" & return & return & "You may need to remove and re-add iTerm2 to the list." buttons {"OK"} default button "OK" with title "Permission Required"
        else
            -- Some other error occurred
            display dialog "Error accessing Share menu: " & errMsg buttons {"OK"} default button "OK"
        end if
    end try
end run