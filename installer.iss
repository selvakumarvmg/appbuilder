[Setup]
AppName=PremediaApp
AppVersion=1.0.0
AppPublisher=VMG Digital
AppPublisherURL=https://www.vmgdigital.com
AppSupportURL=https://www.vmgdigital.com/support
AppUpdatesURL=https://www.vmgdigital.com/update
DefaultDirName={pf}\PremediaApp
DefaultGroupName=PremediaApp
UninstallDisplayIcon={app}\PremediaApp.exe
OutputDir=dist
OutputBaseFilename=PremediaApp_Setup_1.0.0
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
LicenseFile=LICENSE.txt
InfoBeforeFile=TERMS.txt
DisableDirPage=no
DisableProgramGroupPage=no
ShowLanguageDialog=yes

[Files]
Source: "dist\PremediaApp.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; WorkingDir: "{app}"
Name: "{group}\Uninstall PremediaApp"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\PremediaApp.exe"; Description: "Launch PremediaApp"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\PremediaApp.exe"

[Registry]
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\PremediaApp"; ValueType: string; ValueName: "DisplayName"; ValueData: "PremediaApp"
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\PremediaApp"; ValueType: string; ValueName: "UninstallString"; ValueData: "{uninstallexe}"
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\PremediaApp"; ValueType: string; ValueName: "Publisher"; ValueData: "VMG Digital"
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\PremediaApp"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "1.0.0"
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\PremediaApp"; ValueType: string; ValueName: "URLInfoAbout"; ValueData: "https://www.vmgdigital.com"
