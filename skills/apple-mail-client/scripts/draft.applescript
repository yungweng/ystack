-- Creates and saves ONE plain-text draft. It never sends.
-- Arguments: configured sender, subject, UTF-8 body file, one or more To addresses.
on run argv
    if (count argv) < 4 then error "Usage: draft.applescript SENDER SUBJECT BODY_FILE TO [TO ...]"
    set senderAddress to item 1 of argv
    set subjectText to item 2 of argv
    set bodyPath to item 3 of argv
    set bodyText to read (POSIX file bodyPath) as «class utf8»
    if senderAddress contains return or senderAddress contains linefeed then error "Invalid sender"
    if subjectText contains return or subjectText contains linefeed then error "Invalid subject"
    repeat with recipientAddress in items 4 thru -1 of argv
        if recipientAddress does not contain "@" or recipientAddress contains return or recipientAddress contains linefeed then error "Use concrete To email addresses"
    end repeat
    with timeout of 30 seconds
        tell application "Mail"
            set senderFound to false
            repeat with a in accounts
                if enabled of a then
                    set accountAddresses to get email addresses of a
                    repeat with configuredAddress in accountAddresses
                        ignoring case
                            if (configuredAddress as text) is senderAddress then set senderFound to true
                        end ignoring
                    end repeat
                end if
            end repeat
            if not senderFound then error "Sender is not an enabled configured account address"
            set draftMessage to make new outgoing message with properties {sender:senderAddress, subject:subjectText, content:bodyText, visible:false}
            tell draftMessage
                repeat with recipientAddress in items 4 thru -1 of argv
                    make new to recipient at end of to recipients with properties {address:(recipientAddress as text)}
                end repeat
            end tell
            save draftMessage
            return "saved outgoing_id=" & (id of draftMessage as text) & linefeed & "sender=" & (sender of draftMessage) & linefeed & "to=" & (address of to recipients of draftMessage as text) & linefeed & "subject=" & (subject of draftMessage)
        end tell
    end timeout
end run
