[Setup]
AppName=PremediaApp
AppVersion=1.0.0
DefaultDirName={autopf}\PremediaApp
DefaultGroupName=PremediaApp
OutputBaseFilename=PremediaApp-Setup
OutputDir=..\Output
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=..\icons\premedia.ico
UninstallDisplayIcon={app}\PremediaApp.exe
Publisher=VMG Digital Pvt Ltd

[Files]
; Copy all app runtime files from onedir PyInstaller output
Source: "..\dist\PremediaApp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Terms and license
Source: "..\terms.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\license.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu and Desktop icons
Name: "{group}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"
Name: "{commondesktop}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"

[Run]
Filename: "{app}\PremediaApp.exe"; Description: "Launch PremediaApp"; Flags: nowait postinstall skipifsilent
