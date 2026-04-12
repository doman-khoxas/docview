; DocNotes Installer Script for Inno Setup 6
; Build: python build_docnotes.py --installer

#define MyAppName "DocNotes"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Operator Systems"
#define MyAppURL "https://github.com/doman-khoxas/docview"
#define MyAppExeName "DocNotes.exe"

[Setup]
AppId={{C4E8F2A1-9D3B-4A7C-B6E5-1F0D8A2C5E9B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename=DocNotes_{#MyAppVersion}_Setup
SetupIconFile=assets\docnotes_icon.ico
UninstallDisplayIcon={app}\assets\docnotes_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoProductName={#MyAppName}
MinVersion=10.0
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "fileassoc_md"; Description: "Associate .md files with {#MyAppName}"; GroupDescription: "File Associations:"; Flags: unchecked

[Files]
Source: "dist\DocNotes\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\docnotes_icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "assets\filetype_md.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\docnotes_icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\docnotes_icon.ico"; Tasks: desktopicon

[Registry]
; === Markdown file association ===
Root: HKA; Subkey: "Software\Classes\DocNotes.Markdown"; ValueType: string; ValueName: ""; ValueData: "Markdown Note - DocNotes"; Flags: uninsdeletekey; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\DocNotes.Markdown\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\assets\filetype_md.ico,0"; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\DocNotes.Markdown\shell"; ValueType: string; ValueName: ""; ValueData: "open"; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\DocNotes.Markdown\shell\open"; ValueType: string; ValueName: ""; ValueData: "Open with DocNotes"; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\DocNotes.Markdown\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\.md"; ValueType: string; ValueName: ""; ValueData: "DocNotes.Markdown"; Flags: uninsdeletevalue; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\.md\OpenWithProgids"; ValueType: string; ValueName: "DocNotes.Markdown"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\.markdown"; ValueType: string; ValueName: ""; ValueData: "DocNotes.Markdown"; Flags: uninsdeletevalue; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\.markdown\OpenWithProgids"; ValueType: string; ValueName: "DocNotes.Markdown"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc_md

; === App registration ===
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#MyAppName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\assets\docnotes_icon.ico,0"
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".md"; ValueData: ""
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".markdown"; ValueData: ""

; === Capabilities for Default Programs ===
Root: HKA; Subkey: "Software\{#MyAppName}\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "{#MyAppName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\{#MyAppName}\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Note-taking with Vault/Notebook/Section hierarchy"
Root: HKA; Subkey: "Software\{#MyAppName}\Capabilities\FileAssociations"; ValueType: string; ValueName: ".md"; ValueData: "DocNotes.Markdown"
Root: HKA; Subkey: "Software\{#MyAppName}\Capabilities\FileAssociations"; ValueType: string; ValueName: ".markdown"; ValueData: "DocNotes.Markdown"
Root: HKA; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: "Software\{#MyAppName}\Capabilities"; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\assets"
