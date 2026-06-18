Set objShell = CreateObject("WScript.Shell")

' Load User env vars that VBScript doesn't inherit automatically
Dim groqKey, voyageKey, anthropicKey, dbUrl
groqKey     = objShell.RegRead("HKEY_CURRENT_USER\Environment\GROQ_API_KEY")
voyageKey   = objShell.RegRead("HKEY_CURRENT_USER\Environment\VOYAGE_API_KEY")
anthropicKey = objShell.RegRead("HKEY_CURRENT_USER\Environment\ANTHROPIC_API_KEY")
dbUrl       = objShell.RegRead("HKEY_CURRENT_USER\Environment\DATABASE_URL")

Dim env
Set env = objShell.Environment("Process")
If groqKey <> ""     Then env("GROQ_API_KEY")     = groqKey
If voyageKey <> ""   Then env("VOYAGE_API_KEY")   = voyageKey
If anthropicKey <> "" Then env("ANTHROPIC_API_KEY") = anthropicKey
If dbUrl <> ""       Then env("DATABASE_URL")      = dbUrl
env("GBRAIN_POOL_SIZE") = "2"

' Resolve USERPROFILE at runtime so this works on any machine
Dim streamlitExe, cmd
streamlitExe = objShell.ExpandEnvironmentStrings("%USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\Scripts\streamlit.exe")

' Fall back to 'streamlit' from PATH if the specific install path doesn't exist
Dim fso
Set fso = CreateObject("Scripting.FileSystemObject")
If Not fso.FileExists(streamlitExe) Then
    streamlitExe = "streamlit"
End If

cmd = """" & streamlitExe & """ run ""C:\brain\gbrain_app.py"" --server.headless true"
objShell.Run cmd, 0, False
