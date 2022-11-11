On Error Resume Next

ReDim args(WScript.Arguments.Count-1)

For i = 0 To WScript.Arguments.Count-1
    If InStr(WScript.Arguments(i), " ") > 0 Then
        args(i) = Chr(34) & WScript.Arguments(i) & Chr(34)
    Else
        args(i) = WScript.Arguments(i)
        End If

Next

CreateObject("WScript.Shell").Run Join(args, " "), 0, False