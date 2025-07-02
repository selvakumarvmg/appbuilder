[Setup]
AppName=PremediaApp
AppVersion=1.0.0
DefaultDirName={autopf}\PremediaApp
DefaultGroupName=PremediaApp
OutputBaseFilename=PremediaApp-Setup
OutputDir=Output
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=icons\premedia.ico

[Files]
Source: "dist\PremediaApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "terms.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "icons\premedia.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "icons\photoshop.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "icons\folder.png"; DestDir: "{app}\icons"; Flags: ignoreversion

[Icons]
Name: "{group}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\premedia.ico"
Name: "{commondesktop}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\premedia.ico"

[Run]
Filename: "{app}\PremediaApp.exe"; Description: "Launch PremediaApp"; Flags: nowait postinstall skipifsilent