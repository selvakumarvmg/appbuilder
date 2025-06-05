[Setup]
AppName=PremediaApp
AppVersion=1.0.0
DefaultDirName={pf}\PremediaApp
DefaultGroupName=PremediaApp
UninstallDisplayIcon={app}\PremediaApp.exe
LicenseFile=LICENSE.txt
InfoBeforeFile=TERMS.txt
OutputDir=dist
OutputBaseFilename=PremediaApp_Setup_1.0.0
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist\PremediaApp.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PremediaApp"; Filename: "{app}\PremediaApp.exe"
Name: "{group}\Uninstall PremediaApp"; Filename: "{uninstallexe}"
