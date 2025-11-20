#!/usr/bin/osascript
-- Debug script to list menu items

tell application "Finder"
    activate
end tell

delay 0.5

tell application "System Events"
    tell process "Finder"
        set menuItems to name of every menu item of menu "File" of menu bar 1
        repeat with itemName in menuItems
            log itemName
        end repeat
    end tell
end tell