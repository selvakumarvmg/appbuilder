; Inno Setup Script for PremediaApp (Windows)
[Setup]
AppName=PremediaApp
AppVersion=1.0.0
AppPublisher=xAI
AppPublisherURL=https://x.ai
AppSupportURL=https://x.ai
AppUpdatesURL=https://x.ai
DefaultDirName={autopf}\PremediaApp
DefaultGroupName=PremediaApp
OutputDir=Output
OutputBaseFilename=PremediaApp_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=icons\premedia.ico
UninstallDisplayIcon={app}\icons\premedia.ico
LicenseFile=license.txt
InfoAfterFile=terms.txt
PrivilegesRequired=admin

[Files]
Source: "dist\PremediaApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icons\premedia.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "icons\photoshop.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "icons\folder.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "terms.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "license.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"
Name: "{group}\Uninstall PremediaApp"; Filename: "{uninstallexe}"
Name: "{autodesktop}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"; Tasks: desktopicon
Name: "{group}\View Terms"; Filename: "{app}\terms.txt"
Name: "{group}\View License"; Filename: "{app}\license.txt"

[Tasks]
Name: desktopicon; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Run]
Filename: "{app}\PremediaApp.exe"; Description: "{cm:LaunchProgram,PremediaApp}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\terms.txt"; Description: "View Terms of Service"; Flags: shellexec postinstall unchecked
Filename: "{app}\license.txt"; Description: "View License"; Flags: shellexec postinstall unchecked

[Dirs]
Name: "{app}\log"; Permissions: users-modify
Name: "{app}\icons"
Name: "{userdocs}\PremediaApp\Nas"; Permissions: users-modify

[Registry]
Root: HKCR; Subkey: "premediaapp"; ValueType: string; ValueName: ""; ValueData: "URL:PremediaApp Protocol"; Flags: uninsdeletekey
Root: HKCR; Subkey: "premediaapp"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""
Root: HKCR; Subkey: "premediaapp\shell"; ValueType: string; ValueName: ""; ValueData: ""
Root: HKCR; Subkey: "premediaapp\shell\open"; ValueType: string; ValueName: ""; ValueData: ""
Root: HKCR; Subkey: "premediaapp\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\PremediaApp.exe"" ""%1"""