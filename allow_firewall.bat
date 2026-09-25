@echo off
echo Requesting Administrator privileges to allow port 8000 through Windows Firewall...
powershell -Command "Start-Process cmd -ArgumentList '/c netsh advfirewall firewall add rule name=\"OmniGrab Backend 8000\" dir=in action=allow protocol=TCP localport=8000 & pause' -Verb RunAs"
echo Done. Please click "Yes" on the Windows UAC prompt.
