# 바탕화면에 "주식분석 플랫폼" 단축키를 생성합니다
# 이 스크립트를 한 번만 실행하면 됩니다

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$batPath = Join-Path $projectDir "start_all.bat"

$result = C:\ProgramData\anaconda3\python.exe -u -c @"
import sys, io, win32com.client, shutil, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
shell   = win32com.client.Dispatch('WScript.Shell')
tmp     = r'C:\Users\Public\stockapp_tmp.lnk'
sc      = shell.CreateShortCut(tmp)
sc.Targetpath        = r'$batPath'
sc.WorkingDirectory  = r'$projectDir'
sc.Description       = 'Stock Analysis Platform'
sc.IconLocation      = r'C:\Windows\System32\shell32.dll,13'
sc.save()
desktop = shell.SpecialFolders('Desktop')
dest    = os.path.join(desktop, 'stockapp.lnk')
shutil.move(tmp, dest)
print('OK:' + dest)
"@

if ($result -like "OK:*") {
    $dest = $result.Substring(3)
    Write-Host ""
    Write-Host "  ✅ 바탕화면 단축키 생성 완료!" -ForegroundColor Green
    Write-Host "  📍 $dest" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  앞으로는 바탕화면의 [stockapp] 아이콘을" -ForegroundColor White
    Write-Host "  더블클릭하면 모든 서버가 자동 시작됩니다." -ForegroundColor White
} else {
    Write-Host "오류: $result" -ForegroundColor Red
}
Write-Host ""
pause
