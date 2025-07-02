[Setup]
AppId={{9ca9316f-48ec-47dd-ab0e-dbbb86de0a9f}}
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
PrivilegesRequired=admin
UninstallDisplayIcon={app}\icons\premedia.ico
WizardImageFile=..\installer-assets\dmg-background.bmp
WizardSmallImageFile=..\icons\premedia-logo.bmp
AppPublisher=VMG Digital Pvt Ltd
AppPublisherURL=https://vmgdigital.com
AppSupportURL=https://vmgdigital.com/support
AppUpdatesURL=https://vmgdigital.com/downloads
LicenseFile=..\terms.txt

[Files]
Source: "..\dist\PremediaApp\PremediaApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\terms.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\icons\premedia.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\photoshop.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\folder.png"; DestDir: "{app}\icons"; Flags: ignoreversion

; Only include these if you need them at runtime (UI/Dev)
Source: "..\login.ui"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\premediaapp.ui"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\icons.qrc"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\icons_rc.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\login.py"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"
Name: "{commondesktop}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"
Name: "{userstartup}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"

[Run]
Filename: "{app}\PremediaApp.exe"; Description: "Launch PremediaApp"; Flags: nowait postinstall skipifsilent
