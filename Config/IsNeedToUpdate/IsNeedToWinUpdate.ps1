$session = New-Object -ComObject Microsoft.Update.Session
$searcher = $session.CreateUpdateSearcher()
$result = $searcher.Search("IsInstalled=0")
$result.Updates | Out-File -FilePath E:\MonitorSystem\Source\OnionScraper\Config\IsNeedToUpdate\ResultChkWinUpdate.txt