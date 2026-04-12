; DocView Installer Script for Inno Setup 6
; Build: python build.py --installer

#define MyAppName "DocView"
#define MyAppVersion "2.2.0"
#define MyAppPublisher "Operator Systems"
#define MyAppURL "https://github.com/doman-khoxas/docview"
#define MyAppExeName "DocView.exe"

[Setup]
AppId={{8A2F4E3D-B7C1-4D9E-A5F0-2E8C6B9D1A3F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename=DocView_{#MyAppVersion}_Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\assets\icon.ico
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
Name: "fileassoc_pdf"; Description: "Associate .pdf files with {#MyAppName}"; GroupDescription: "File Associations:"; Flags: unchecked
Name: "fileassoc_md"; Description: "Associate .md files with {#MyAppName}"; GroupDescription: "File Associations:"; Flags: unchecked

[Files]
Source: "dist\DocView\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "assets\filetype_pdf.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "assets\filetype_md.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Registry]
; === PDF file association ===
; Register ProgID with icon and open command
Root: HKA; Subkey: "Software\Classes\DocView.PDF"; ValueType: string; ValueName: ""; ValueData: "PDF Document - DocView"; Flags: uninsdeletekey; Tasks: fileassoc_pdf
Root: HKA; Subkey: "Software\Classes\DocView.PDF\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\assets\filetype_pdf.ico,0"; Tasks: fileassoc_pdf
Root: HKA; Subkey: "Software\Classes\DocView.PDF\shell"; ValueType: string; ValueName: ""; ValueData: "open"; Tasks: fileassoc_pdf
Root: HKA; Subkey: "Software\Classes\DocView.PDF\shell\open"; ValueType: string; ValueName: ""; ValueData: "Open with DocView"; Tasks: fileassoc_pdf
Root: HKA; Subkey: "Software\Classes\DocView.PDF\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: fileassoc_pdf
; Set as default handler for .pdf
Root: HKA; Subkey: "Software\Classes\.pdf"; ValueType: string; ValueName: ""; ValueData: "DocView.PDF"; Flags: uninsdeletevalue; Tasks: fileassoc_pdf
; Also register in OpenWithProgids so it shows in "Open With" even if not default
Root: HKA; Subkey: "Software\Classes\.pdf\OpenWithProgids"; ValueType: string; ValueName: "DocView.PDF"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc_pdf

; === Markdown file association ===
Root: HKA; Subkey: "Software\Classes\DocView.Markdown"; ValueType: string; ValueName: ""; ValueData: "Markdown Document - DocView"; Flags: uninsdeletekey; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\DocView.Markdown\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\assets\filetype_md.ico,0"; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\DocView.Markdown\shell"; ValueType: string; ValueName: ""; ValueData: "open"; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\DocView.Markdown\shell\open"; ValueType: string; ValueName: ""; ValueData: "Open with DocView"; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\DocView.Markdown\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: fileassoc_md
; Set as default handler for .md
Root: HKA; Subkey: "Software\Classes\.md"; ValueType: string; ValueName: ""; ValueData: "DocView.Markdown"; Flags: uninsdeletevalue; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\.md\OpenWithProgids"; ValueType: string; ValueName: "DocView.Markdown"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc_md
; Also handle .markdown extension
Root: HKA; Subkey: "Software\Classes\.markdown"; ValueType: string; ValueName: ""; ValueData: "DocView.Markdown"; Flags: uninsdeletevalue; Tasks: fileassoc_md
Root: HKA; Subkey: "Software\Classes\.markdown\OpenWithProgids"; ValueType: string; ValueName: "DocView.Markdown"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc_md

; === App registration for "Open With" menu (always, not task-gated) ===
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#MyAppName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\assets\icon.ico,0"
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".pdf"; ValueData: ""
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".md"; ValueData: ""
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".markdown"; ValueData: ""

; === Capabilities for Default Programs / Settings ===
Root: HKA; Subkey: "Software\{#MyAppName}\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "{#MyAppName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\{#MyAppName}\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Document Viewer and Editor"
Root: HKA; Subkey: "Software\{#MyAppName}\Capabilities\FileAssociations"; ValueType: string; ValueName: ".pdf"; ValueData: "DocView.PDF"
Root: HKA; Subkey: "Software\{#MyAppName}\Capabilities\FileAssociations"; ValueType: string; ValueName: ".md"; ValueData: "DocView.Markdown"
Root: HKA; Subkey: "Software\{#MyAppName}\Capabilities\FileAssociations"; ValueType: string; ValueName: ".markdown"; ValueData: "DocView.Markdown"
Root: HKA; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: "Software\{#MyAppName}\Capabilities"; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\assets"
