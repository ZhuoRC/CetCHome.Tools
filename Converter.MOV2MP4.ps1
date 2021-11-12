
$path = "X:\Video.Tech\Building Dynamic Websites"
#$path =  "C:\Workspace\ffmpeg-4.4.1-essentials_build"


Get-ChildItem -Path $path -File -Recurse | Sort-Object -Property {$_.Name}  | % {

    # ## iPhone Record
    # if (($_.Extension -eq ".MOV") -or ($_.Extension -eq ".MP4" -and $_.BaseName -NotLike "_1080p.mp4")) {
       
    #     $inputFile = $_.FullName
    #     $outputFile = $_.Directory.FullName + "\" + $_.BaseName+"_1080p.mp4"
    # }

    ## Others
    if (($_.Extension -eq ".MOV") -or ($_.Extension -eq ".avi") -or ($_.Extension -eq ".flv"))
    {
        
        $inputFile = $_.FullName
        $outputFile = $_.Directory.FullName + "\" + $_.BaseName+"_480p.mp4"
    }    

    #If the file does not exist, create it.
    if (-not(Test-Path -Path $outputFile)) {
        Write-Host "Outputing: [$outputFile]"
        ## 1920=1080p, 1280=720p, 858=480p
        ## trunc to avoid height cannot be divisible.
        .\bin\ffmpeg.exe -i $inputFile -filter:v scale="858:trunc(ow/a/2)*2" -vcodec h264 -acodec aac $outputFile -v quiet -stats
    }
    #If the file already exists, show the message and do nothing.
    else {
        Write-Host "Already exists: [$outputFile]"
    }
}


