# Specify the path to the folder
$folderPath = "Z:\Photo\Life.Montreal\20140424.Landing Montreal"


# Specify the character or substring to find
$substringToFind = "-IMG_"
$prefixLong = 2
$dryrun = 0

# Get all files in the folder
$files = Get-ChildItem -Path $folderPath -File

# Iterate through each file and find the index of the substring
foreach ($file in $files) {
    $index = $file.Name.IndexOf($substringToFind)
    
    if ($index -ne -1) {
        #Write-Host "Substring found in $($file.Name) at index $index"
        $newName = $file.Name.Substring($prefixLong)

         $newPath = Join-Path -Path $folderPath -ChildPath $newName
         if (Test-Path $newPath) {
                Write-Host "The file $($newPath) exists."
            } else {
                Write-Host "Rename $($file.Name) to $($newName)."
                if ($dryrun -eq 0){
                    Rename-Item -Path $file.FullName -NewName $newName -Force
                }
                
            }
        
    } else {
        #Write-Host "Substring not found in $($file.Name)"
    }
}