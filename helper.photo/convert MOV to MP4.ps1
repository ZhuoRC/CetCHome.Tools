
$path = "C:\Clouds\Dropbox\Photo"
$dryrun = 0

Set-Location -Path $PSScriptRoot
# get file media created, date taken or LastWriteTime:
function entGetMediaCreatedOrLastWriteTime($objFile) {
    $idxMediaCreated = 208
  
    $objShell = New-Object -COMObject Shell.Application
    $objShellFolder = $objShell.NameSpace($objFile.DirectoryName)
  
    $iState = [System.Runtime.Interopservices.Marshal]::ReleaseComObject($objShell)
  
    $objShellFile = $objShellFolder.ParseName($objFile.Name)
    $mediaCreated = $objShellFolder.GetDetailsOf($objShellFile, $idxMediaCreated)
  
  
    #
    # if media created is empty, we check if we have Date taken:
    #
    if($mediaCreated -eq "") {
      #
      # canon cameras set Date taken for photos:
      #
      $idxDateTaken = 12
      $dateTaken = $objShellFolder.GetDetailsOf($objShellFile, $idxDateTaken)
      
      #
      # return LastWriteTime if neither media created, nor Date taken:
      #
      if($dateTaken -eq "") {
          return $objFile.LastWriteTime
      }
      #
      # otherwise return Date taken, removing non-ascii before:
      #
      else
      {   
          return [DateTime]($dateTaken -replace '\P{IsBasicLatin}')
      }
    }
    #
    # otherwise return valid media created, removing non-ascii before:
    #
    else {
      return [DateTime]($mediaCreated -replace '\P{IsBasicLatin}')
    }
}



Get-ChildItem -Path $path -File | Sort-Object -Property {$_.Name} |  Where-Object {".mov",".mp4",".avi",".flv",".mkv" -eq $_.extension} | ForEach-Object {

    ## iPhone
    if (($_.Extension -eq ".MOV") -or ($_.Extension -eq ".MP4" -and $_.BaseName -NotLike "*_1080p")) {
       
        $inputFile = $_.FullName
        $outputFile = $_.Directory.FullName + "\" + $_.BaseName+"_1080p.mp4"

        $mediaCreatedDateTime = entGetMediaCreatedOrLastWriteTime $_
        $mediaCreatedDateTimeFormat = $mediaCreatedDateTime.ToUniversalTime().ToString("yyyy:MM:dd HH:mm:ss")
        Write-Host "Media Created: $mediaCreatedDateTimeFormat"
 
        #If the file does not exist, create it.
        if (-not(Test-Path -Path $outputFile)) {
            Write-Host "Outputing: [$outputFile]"
            ## 1920=1080p, 1280=720p.
            ## trunc to avoid height cannot be divisible.
            if ($dryrun -eq 0) {
                .\bin\ffmpeg.exe -i $inputFile -filter:v scale="1920:trunc(ow/a/2)*2" -vcodec h264 -acodec aac $outputFile -v quiet -stats
                #.\exiftool.exe -QuickTime:CreateDate="$mediaCreatedDateTimeFormat" -overwrite_original $outputFile 
                .\bin\exiftool.exe  -overwrite_original -TagsFromFile $inputFile $outputFile 
               
            }
        }
        #If the file already exists, show the message and do nothing.
        else {
            Write-Host "Already exists: [$outputFile]"
        }
    }
}

