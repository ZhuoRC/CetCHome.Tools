


Get-ChildItem -Path  "\\mtlinas\iCore\Photo"  -Recurse -Directory -Force | Where-Object { $_.Name -eq ".@__thumb" } | Foreach-Object { 
Write-Host $_.FullName

if ((Get-ChildItem -Path $_.FullName -File).Count -lt 10) {
    Write-Host "The folder is empty."
} else { 
    Remove-Item -Path $_.FullName -Confirm:$false -Force
}

}
