Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "C:\driver-zkteco-service\run_zkteco.bat", 0, False
Set WshShell = Nothing
