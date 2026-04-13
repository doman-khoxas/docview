; DocSetup — Combined installer for DocView + DocNotes
; Build: python build.py --onedir && python build_docnotes.py --onedir && ISCC installer_setup.iss

#define MyAppVersion "2.2.0"
#define MyAppPublisher "Operator Systems"
#define MyAppURL "https://github.com/doman-khoxas/docview"

[Setup]
AppId={{F7A3E1D2-4B8C-4F6E-9D0A-3C5B7E8F1A2D}
AppName=DocSuite
AppVersion={#MyAppVersion}
AppVerName=DocSuite {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\DocSuite
DefaultGroupName=DocSuite
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename=DocSetup_{#MyAppVersion}
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\DocView\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoProductName=DocSuite
MinVersion=10.0
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Types]
Name: "full"; Description: "Full installation (DocView + DocNotes)"
Name: "docview"; Description: "DocView only"
Name: "docnotes"; Description: "DocNotes only"
Name: "custom"; Description: "Custom"; Flags: iscustom

[Components]
Name: "docview"; Description: "DocView — PDF Viewer & Markdown Editor"; Types: full docview custom
Name: "docnotes"; Description: "DocNotes — Note-taking with Vault hierarchy"; Types: full docnotes custom

[Tasks]
Name: "desktopicon_docview"; Description: "DocView desktop shortcut"; GroupDescription: "Desktop Shortcuts:"; Components: docview
Name: "desktopicon_docnotes"; Description: "DocNotes desktop shortcut"; GroupDescription: "Desktop Shortcuts:"; Components: docnotes
Name: "fileassoc_pdf"; Description: "Associate .pdf files with DocView"; GroupDescription: "File Associations:"; Components: docview; Flags: unchecked
Name: "fileassoc_md_docview"; Description: "Associate .md files with DocView"; GroupDescription: "File Associations:"; Components: docview; Flags: unchecked
Name: "fileassoc_md_docnotes"; Description: "Associate .md files with DocNotes"; GroupDescription: "File Associations:"; Components: docnotes; Flags: unchecked

[Files]
; DocView
Source: "dist\DocView\*"; DestDir: "{app}\DocView"; Components: docview; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\icon.ico"; DestDir: "{app}\DocView\assets"; Components: docview; Flags: ignoreversion
Source: "assets\filetype_pdf.ico"; DestDir: "{app}\DocView\assets"; Components: docview; Flags: ignoreversion
Source: "assets\filetype_md.ico"; DestDir: "{app}\DocView\assets"; Components: docview; Flags: ignoreversion

; DocNotes
Source: "dist\DocNotes\*"; DestDir: "{app}\DocNotes"; Components: docnotes; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\docnotes_icon.ico"; DestDir: "{app}\DocNotes\assets"; Components: docnotes; Flags: ignoreversion
Source: "assets\filetype_md.ico"; DestDir: "{app}\DocNotes\assets"; Components: docnotes; Flags: ignoreversion

[Icons]
; DocView
Name: "{group}\DocView"; Filename: "{app}\DocView\DocView.exe"; IconFilename: "{app}\DocView\assets\icon.ico"; Components: docview
Name: "{autodesktop}\DocView"; Filename: "{app}\DocView\DocView.exe"; IconFilename: "{app}\DocView\assets\icon.ico"; Tasks: desktopicon_docview

; DocNotes
Name: "{group}\DocNotes"; Filename: "{app}\DocNotes\DocNotes.exe"; IconFilename: "{app}\DocNotes\assets\docnotes_icon.ico"; Components: docnotes
Name: "{autodesktop}\DocNotes"; Filename: "{app}\DocNotes\DocNotes.exe"; IconFilename: "{app}\DocNotes\assets\docnotes_icon.ico"; Tasks: desktopicon_docnotes

; Uninstall
Name: "{group}\Uninstall DocSuite"; Filename: "{uninstallexe}"

[Registry]
; === DocView PDF association ===
Root: HKA; Subkey: "Software\Classes\DocView.PDF"; ValueType: string; ValueName: ""; ValueData: "PDF Document - DocView"; Flags: uninsdeletekey; Tasks: fileassoc_pdf
Root: HKA; Subkey: "Software\Classes\DocView.PDF\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\DocView\assets\filetype_pdf.ico,0"; Tasks: fileassoc_pdf
Root: HKA; Subkey: "Software\Classes\DocView.PDF\shell"; ValueType: string; ValueName: ""; ValueData: "open"; Tasks: fileassoc_pdf
Root: HKA; Subkey: "Software\Classes\DocView.PDF\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\DocView\DocView.exe"" ""%1"""; Tasks: fileassoc_pdf
Root: HKA; Subkey: "Software\Classes\.pdf"; ValueType: string; ValueName: ""; ValueData: "DocView.PDF"; Flags: uninsdeletevalue; Tasks: fileassoc_pdf
Root: HKA; Subkey: "Software\Classes\.pdf\OpenWithProgids"; ValueType: string; ValueName: "DocView.PDF"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc_pdf

; === DocView Markdown association ===
Root: HKA; Subkey: "Software\Classes\DocView.Markdown"; ValueType: string; ValueName: ""; ValueData: "Markdown Document - DocView"; Flags: uninsdeletekey; Tasks: fileassoc_md_docview
Root: HKA; Subkey: "Software\Classes\DocView.Markdown\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\DocView\assets\filetype_md.ico,0"; Tasks: fileassoc_md_docview
Root: HKA; Subkey: "Software\Classes\DocView.Markdown\shell"; ValueType: string; ValueName: ""; ValueData: "open"; Tasks: fileassoc_md_docview
Root: HKA; Subkey: "Software\Classes\DocView.Markdown\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\DocView\DocView.exe"" ""%1"""; Tasks: fileassoc_md_docview
Root: HKA; Subkey: "Software\Classes\.md"; ValueType: string; ValueName: ""; ValueData: "DocView.Markdown"; Flags: uninsdeletevalue; Tasks: fileassoc_md_docview
Root: HKA; Subkey: "Software\Classes\.md\OpenWithProgids"; ValueType: string; ValueName: "DocView.Markdown"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc_md_docview

; === DocNotes Markdown association ===
Root: HKA; Subkey: "Software\Classes\DocNotes.Markdown"; ValueType: string; ValueName: ""; ValueData: "Markdown Note - DocNotes"; Flags: uninsdeletekey; Tasks: fileassoc_md_docnotes
Root: HKA; Subkey: "Software\Classes\DocNotes.Markdown\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\DocNotes\assets\filetype_md.ico,0"; Tasks: fileassoc_md_docnotes
Root: HKA; Subkey: "Software\Classes\DocNotes.Markdown\shell"; ValueType: string; ValueName: ""; ValueData: "open"; Tasks: fileassoc_md_docnotes
Root: HKA; Subkey: "Software\Classes\DocNotes.Markdown\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\DocNotes\DocNotes.exe"" ""%1"""; Tasks: fileassoc_md_docnotes
Root: HKA; Subkey: "Software\Classes\.md"; ValueType: string; ValueName: ""; ValueData: "DocNotes.Markdown"; Flags: uninsdeletevalue; Tasks: fileassoc_md_docnotes
Root: HKA; Subkey: "Software\Classes\.md\OpenWithProgids"; ValueType: string; ValueName: "DocNotes.Markdown"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc_md_docnotes

; === DocView App Registration ===
Root: HKA; Subkey: "Software\Classes\Applications\DocView.exe"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "DocView"; Flags: uninsdeletekey; Components: docview
Root: HKA; Subkey: "Software\Classes\Applications\DocView.exe\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\DocView\assets\icon.ico,0"; Components: docview
Root: HKA; Subkey: "Software\Classes\Applications\DocView.exe\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\DocView\DocView.exe"" ""%1"""; Components: docview
Root: HKA; Subkey: "Software\Classes\Applications\DocView.exe\SupportedTypes"; ValueType: string; ValueName: ".pdf"; ValueData: ""; Components: docview
Root: HKA; Subkey: "Software\Classes\Applications\DocView.exe\SupportedTypes"; ValueType: string; ValueName: ".md"; ValueData: ""; Components: docview

; === DocNotes App Registration ===
Root: HKA; Subkey: "Software\Classes\Applications\DocNotes.exe"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "DocNotes"; Flags: uninsdeletekey; Components: docnotes
Root: HKA; Subkey: "Software\Classes\Applications\DocNotes.exe\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\DocNotes\assets\docnotes_icon.ico,0"; Components: docnotes
Root: HKA; Subkey: "Software\Classes\Applications\DocNotes.exe\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\DocNotes\DocNotes.exe"" ""%1"""; Components: docnotes
Root: HKA; Subkey: "Software\Classes\Applications\DocNotes.exe\SupportedTypes"; ValueType: string; ValueName: ".md"; ValueData: ""; Components: docnotes

; === Registered Applications for Default Programs ===
Root: HKA; Subkey: "Software\DocView\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "DocView"; Flags: uninsdeletekey; Components: docview
Root: HKA; Subkey: "Software\DocView\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Document Viewer and Editor"
Root: HKA; Subkey: "Software\DocView\Capabilities\FileAssociations"; ValueType: string; ValueName: ".pdf"; ValueData: "DocView.PDF"; Components: docview
Root: HKA; Subkey: "Software\DocView\Capabilities\FileAssociations"; ValueType: string; ValueName: ".md"; ValueData: "DocView.Markdown"; Components: docview
Root: HKA; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "DocView"; ValueData: "Software\DocView\Capabilities"; Flags: uninsdeletevalue; Components: docview

Root: HKA; Subkey: "Software\DocNotes\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "DocNotes"; Flags: uninsdeletekey; Components: docnotes
Root: HKA; Subkey: "Software\DocNotes\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Note-taking with Vault hierarchy"
Root: HKA; Subkey: "Software\DocNotes\Capabilities\FileAssociations"; ValueType: string; ValueName: ".md"; ValueData: "DocNotes.Markdown"; Components: docnotes
Root: HKA; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "DocNotes"; ValueData: "Software\DocNotes\Capabilities"; Flags: uninsdeletevalue; Components: docnotes

[Run]
Filename: "{app}\DocView\DocView.exe"; Description: "Launch DocView"; Flags: nowait postinstall skipifsilent unchecked; Components: docview
Filename: "{app}\DocNotes\DocNotes.exe"; Description: "Launch DocNotes"; Flags: nowait postinstall skipifsilent unchecked; Components: docnotes

[UninstallDelete]
Type: filesandordirs; Name: "{app}\DocView\assets"
Type: filesandordirs; Name: "{app}\DocNotes\assets"
