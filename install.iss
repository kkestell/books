#define SourceDir "C:\Users\Kyle\source\books"

[Setup]
AppId={{15B0BFB2-7A36-43D3-90C7-B714DCDC1F19}
AppName=Books
AppVersion=0.2.0
AppVerName=Books
AppPublisher=Kyle Kestell
AppPublisherURL=https://github.com/kkestell/books
AppSupportURL=https://github.com/kkestell/books
AppUpdatesURL=https://github.com/kkestell/books
DefaultDirName={autopf}\Books
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
LicenseFile={#SourceDir}\LICENSE
PrivilegesRequired=lowest
OutputDir={#SourceDir}\publish
OutputBaseFilename=Books_0.2.0_Setup
SetupIconFile={#SourceDir}\assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Books.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\publish\Books.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Books"; Filename: "{app}\Books.exe"; IconFilename: "{app}\Books.exe"
Name: "{userdesktop}\Books"; Filename: "{app}\Books.exe"; Tasks: desktopicon; IconFilename: "{app}\Books.exe"

[Run]
Filename: "{app}\Books.exe"; Description: "{cm:LaunchProgram,Books}"; Flags: nowait postinstall skipifsilent
