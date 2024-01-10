
$path = "C:\Users\Camel\Pictures\photos_iPhone7.Nightcat\Longfile - MP4 - Copy"
$dryrun = 0

Set-Location -Path $PSScriptRoot

Get-ChildItem -Path $path -File | ForEach-Object {
   
    $substringToFind = "_IMG"
    $index = $_.Name.IndexOf($substringToFind)
    if ($index -eq -1){
        Write-Host $_.Name "not contains" $substringToFind
        return
    }

    $dateInNameString = $_.Name.Substring(0, $index)
    $newName = $_.Name.Substring($index+1)

    if ($_.Extension -eq ".MP4" -and $_.BaseName -Like "*_1080p") {
    
        $nameArray = $dateInNameString -split '_'
        $mediaCreatedDateString = $nameArray[0]+'-'+$nameArray[1]+'-'+$nameArray[2]+ 'T'+ $nameArray[3]+":"+$nameArray[4]+":00"
        $mediaCreatedDate = Get-Date $mediaCreatedDateString
        $mediaCreatedDateFormat = $mediaCreatedDate.ToUniversalTime().ToString("yyyy:MM:dd HH:mm:ss")
        
        Write-Host "Set Media Created Date: $mediaCreatedDateFormat"
        try {
            if ($dryrun -eq 0) {
                .\bin\exiftool.exe -QuickTime:CreateDate="$mediaCreatedDateFormat" $_.FullName -overwrite_original 
            }
          
            $newFullName = Join-Path -Path $path -ChildPath $newName
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
        catch {
            # Handle the error
            Write-Host "Error: $_"
            # Break out of a loop or exit the script
            break
        }
   


    }

    if ($_.Extension -eq ".JPG") {

        try {
            $newFullName = Join-Path -Path $path -ChildPath $newName
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
        catch {
            # Handle the error
            Write-Host "Error: $_"
            
            # Break out of a loop or exit the script
            break
        }
   


    }
}

