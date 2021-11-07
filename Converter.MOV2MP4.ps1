
$path = "Z:\Photo\Life.Montreal\20210919.SaintEsprit-摘葡萄"
#$path =  "C:\Workspace\ffmpeg-4.4.1-essentials_build"


Get-ChildItem -Path $path -File -Recurse | % {

    ## iPhone
    if ($_.Extension -eq ".MOV") {
       
        $inputFile = $_.FullName
        $outputFile = $_.Directory.FullName + "\" + $_.BaseName+"_1080p.mp4"

        #If the file does not exist, create it.
        if (-not(Test-Path -Path $outputFile)) {
            Write-Host "Outputing: [$outputFile]"
            ## 1920=1080p, 1280=720p.
            ## trunc to avoid height cannot be divisible.
            .\bin\ffmpeg.exe -i $inputFile -filter:v scale="1920:trunc(ow/a/2)*2" -vcodec h264 -acodec aac $outputFile -v quiet -stats
        }
        #If the file already exists, show the message and do nothing.
        else {
            Write-Host "Already exists: [$outputFile]"
        }
    }
}


