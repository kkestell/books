#define SourceDir "C:\Users\Kyle\Source\thoth"

[Setup]
AppId={{762af19c-af88-4f0e-92d8-7d18fe6b2e1d}}
AppName=Thoth
AppVersion=0.4.0
AppVerName=Thoth
AppPublisher=Kyle Kestell
AppPublisherURL=https://github.com/kkestell/thoth
AppSupportURL=https://github.com/kkestell/thoth
AppUpdatesURL=https://github.com/kkestell/thoth
DefaultDirName={autopf}\Thoth
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
LicenseFile={#SourceDir}\LICENSE
PrivilegesRequired=lowest
OutputDir={#SourceDir}\publish
OutputBaseFilename=Thoth_0.5.0_Setup
SetupIconFile={#SourceDir}\assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Thoth.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\Thoth"; Filename: "{app}\Thoth.exe"; IconFilename: "{app}\Thoth.exe"
Name: "{userdesktop}\Thoth"; Filename: "{app}\Thoth.exe"; Tasks: desktopicon; IconFilename: "{app}\Thoth.exe"

[Run]
Filename: "{app}\Thoth.exe"; Description: "{cm:LaunchProgram,Thoth}"; Flags: nowait postinstall skipifsilent
