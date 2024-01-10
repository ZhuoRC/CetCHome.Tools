$path =  "C:\Users\Camel\Pictures\photos_iPhone7.Nightcat\Longfile - MP4 - Copy"

$dryrun = 0

Set-Location -Path $PSScriptRoot
   
Get-ChildItem -Path $path -File -Recurse | ForEach-Object {


    $newFullName = $_.FullName.Replace("_1080p.mp4",".MOV")
    $newName = $_.Name.Replace("_1080p.mp4",".MOV")
    #If the file does not exist, create it.
    if (-not(Test-Path -Path $newFullName)) {
        Write-Host $_.Name "--->" $newName
        if ($dryrun -eq 0) {
            Rename-Item -Path $_.FullName -NewName $newName -Force
        }
    }
    #If the file already exists, show the message and do nothing.
    else {
        Write-Host "Already exists: [$outputFile]"
    }  

}

