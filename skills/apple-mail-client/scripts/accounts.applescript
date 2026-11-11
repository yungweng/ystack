on run
    set rows to {"account_id" & tab & "name" & tab & "addresses" & tab & "enabled" & tab & "type" & tab & "directory"}
    with timeout of 20 seconds
        tell application "Mail"
            repeat with a in accounts
                set addressesText to ""
                set accountAddresses to get email addresses of a
                repeat with addr in accountAddresses
                    if addressesText is not "" then set addressesText to addressesText & ", "
                    set addressesText to addressesText & (addr as text)
                end repeat
                set accountDirectory to get account directory of a
                set directoryPath to POSIX path of (accountDirectory as text)
                set end of rows to (id of a as text) & tab & (name of a as text) & tab & addressesText & tab & (enabled of a as text) & tab & (account type of a as text) & tab & directoryPath
            end repeat
        end tell
    end timeout
    set savedDelimiters to AppleScript's text item delimiters
    set AppleScript's text item delimiters to linefeed
    set resultText to rows as text
    set AppleScript's text item delimiters to savedDelimiters
    return resultText
end run
