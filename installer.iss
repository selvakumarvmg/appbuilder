; installer.iss
[Setup]
AppName=PremediaApp
AppVersion=1.0.0
DefaultDirName={autopf}\PremediaApp
DefaultGroupName=PremediaApp
OutputDir=Output
OutputBaseFilename=PremediaApp-Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=icons\premedia.ico

[Files]
Source: "dist\PremediaApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion recursesubdirs
Source: "dist\terms.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\license.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"
Name: "{group}\Uninstall PremediaApp"; Filename: "{uninstallexe}"