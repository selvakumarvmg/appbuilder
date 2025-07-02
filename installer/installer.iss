[Setup]
AppId={{9ca9316f-48ec-47dd-ab0e-dbbb86de0a9f}}
AppName=PremediaApp
AppVersion=1.0.0
AppVerName=PremediaApp 1.0.0
DefaultDirName={autopf}\PremediaApp
DefaultGroupName=PremediaApp
AllowNoIcons=yes
OutputBaseFilename=PremediaApp-Setup
OutputDir=..\Output
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
SetupIconFile=..\icons\premedia.ico
UninstallDisplayIcon={app}\icons\premedia.ico
WizardImageFile=..\installer-assets\dmg-background.bmp
WizardSmallImageFile=..\icons\premedia-logo.bmp
AppPublisher=VMG Digital Pvt Ltd
AppPublisherURL=https://vmgdigital.com
AppSupportURL=https://vmgdigital.com/support
AppUpdatesURL=https://vmgdigital.com/downloads
LicenseFile=..\terms.txt
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=no
DisableReadyPage=no
DisableFinishedPage=no
ShowLanguageDialog=no
CreateUninstallRegKey=yes
Uninstallable=yes

[Files]
Source: "..\dist\app.exe"; DestDir: "{app}"; DestName: "PremediaApp.exe"; Flags: ignoreversion
Source: "..\terms.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\icons\premedia.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\photoshop.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\folder.png"; DestDir: "{app}\icons"; Flags: ignoreversion

[Icons]
Name: "{group}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"
Name: "{commondesktop}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"
Name: "{userstartup}\PremediaApp (Auto Start)"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"

[Run]
Filename: "{app}\PremediaApp.exe"; Description: "Launch PremediaApp"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\*.*"
Type: dirifempty; Name: "{app}"

[Registry]
Root: HKCU; Subkey: "Software\PremediaApp"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekeyifempty

[Code]
// Optional: Add custom uninstall behavior or validations here.
