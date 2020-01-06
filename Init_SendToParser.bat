powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\AppData\Roaming\Microsoft\Windows\SendTo\run_StructParser.bat.lnk');$s.WorkingDirectory='%~dp0';$s.TargetPath='%~dp0\run_StructParser.bat';$s.Save()"

start SendTotutorial.png

