[Setup]
AppName=PremediaApp
AppVersion=1.0.0
DefaultDirName={autopf}\PremediaApp
DefaultGroupName=PremediaApp
OutputBaseFilename=PremediaApp-Setup
OutputDir=installer\Output
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=icons\premedia.ico

[Files]
Source: "dist\PremediaApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "terms.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "icons\premedia.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\premedia.ico"
Name: "{commondesktop}\PremediaApp"; Filename: "{app}\PremediaApp.exe"; IconFilename: "{app}\premedia.ico"

[Run]
Filename: "{app}\PremediaApp.exe"; Description: "Launch PremediaApp"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  if not FileExists(ExpandConstant('{src}\dist\PremediaApp.exe')) then begin
    MsgBox('Error: dist\PremediaApp.exe not found.', mbError, MB_OK);
    Result := False;
    exit;
  end;
  Result := True;
end;
