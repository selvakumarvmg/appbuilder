[Setup]
AppId={{9ca9316f-48ec-47dd-ab0e-dbbb86de0a9f}}
AppName=PremediaApp
AppVersion=1.1.2
AppVerName=PremediaApp 1.1.2
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
AppPublisher=VMG Digital Pvt Ltd
AppPublisherURL=https://vmgdigital.com
AppSupportURL=https://vmgdigital.com/support
AppUpdatesURL=https://vmgdigital.com/downloads
LicenseFile=..\license.txt
WizardImageFile=..\installer-assets\dmg-background.bmp
WizardSmallImageFile=..\icons\premedia-logo.bmp
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=no
DisableReadyPage=no
DisableFinishedPage=no
ShowLanguageDialog=no
CreateUninstallRegKey=yes
Uninstallable=yes

[Tasks]
Name: autostart; Description: "Launch PremediaApp automatically on startup"; Flags: unchecked

[Files]
; Entire app output folder
Source: "..\dist\PremediaApp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Other resources
; Explicitly include additional resources (optional, since already covered by wildcard)
Source: "..\terms.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\icons\cache_icon.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\cache_icon.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\cache_icon.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\clear_cache_icon.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\clear_cache_icon.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\clear_cache_icon.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\default_icon.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\default_icon.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\download_icon.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\download_icon.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\download_icon.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\folder.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\login_icon.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\login_icon.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\login_icon.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\logout_icon.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\logout_icon.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\logout_icon.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\log_icon.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\log_icon.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\log_icon.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\photoshop.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\premedia-logo.bmp"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\premedia.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\premedia.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\premedia.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\quit_icon.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\quit_icon.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\quit_icon.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\report.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\report.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\upload_icon.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\upload_icon.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\upload_icon.png"; DestDir: "{app}\icons"; Flags: ignoreversion

Source: "..\icons\copy_icon.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\copy_icon.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\copy_icon.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\retry.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\retry.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\retry.png"; DestDir: "{app}\icons"; Flags: ignoreversion

Source: "..\icons\user_icon.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\user_icon.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\user_icon.png"; DestDir: "{app}\icons"; Flags: ignoreversion

Source: "..\icons\version_icon.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\version_icon.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\version_icon.icns"; DestDir: "{app}\icons"; Flags: ignoreversion

Source: "..\icons\login-logo.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\login-logo.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\login-logo.png"; DestDir: "{app}\icons"; Flags: ignoreversion

Source: "..\icons\logout-logo.icns"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\logout-logo.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\logout-logo.png"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "..\icons\vmg-premedia-logo.png"; DestDir: "{app}\icons"; Flags: ignoreversion

[Icons]
Name: "{group}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"
Name: "{commondesktop}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"
Name: "{userstartup}\PremediaApp (Auto Start)"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\icons\premedia.ico"; Tasks: autostart

[Run]
Filename: "{app}\PremediaApp.exe"; Description: "Launch PremediaApp"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\*.*"
Type: dirifempty; Name: "{app}"

[Registry]
Root: HKCU; Subkey: "Software\PremediaApp"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekeyifempty

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  // During installation
  if CurStep = ssInstall then
  begin
    if IsTaskSelected('autostart') then
    begin
      // Optional: Add logic for registry or task scheduler autostart if needed
      // Currently handled by the [Icons] section
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Attempt to terminate PremediaApp.exe if running
    Exec('taskkill', '/F /IM "PremediaApp.exe"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

    // Remove autostart shortcut from Startup folder
    if DirExists(ExpandConstant('{userstartup}')) then
    begin
      DeleteFile(ExpandConstant('{userstartup}\PremediaApp (Auto Start).lnk'));
    end;
  end;
end;

// Correct InitializeUninstall function prototype
function InitializeUninstall(): Boolean;
begin
  Result := True; // default allow uninstall

  // Warn the user if app is running (optional)
  if FileExists(ExpandConstant('{app}\PremediaApp.exe')) then
  begin
    if MsgBox('PremediaApp is currently running. It will be closed automatically during uninstall. Continue?', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False; // cancel uninstall
    end;
  end;
end;

