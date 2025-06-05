[Setup]
AppName=PremediaApp
AppVersion=1.0.0
DefaultDirName={pf}\PremediaApp
DefaultGroupName=PremediaApp
OutputBaseFilename=PremediaApp_Setup_1.0.0
SetupIconFile=pm.ico
UninstallDisplayIcon={app}\PremediaApp.exe
Compression=lzma
SolidCompression=yes
SignedUninstaller=yes

# Publisher info
Publisher=Your Company Name
URL=https://yourcompany.com

# Terms and conditions dialog
LicenseFile=TERMS.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\PremediaApp.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\PremediaApp.exe"

[Run]
Filename: "{app}\PremediaApp.exe"; Description: "Launch PremediaApp"; Flags: nowait postinstall skipifsilent
