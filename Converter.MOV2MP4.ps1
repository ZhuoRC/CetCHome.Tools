$formats = @(
    @{ number = 0; quality = "1080p"; width = "1920"},
    @{ number = 1; quality = "720p"; width = "1280"},
    @{ number = 2; quality = "480p"; width = "858"}
)


$path = "Z:\Photo\Angelo\2020.Age 2+"
#$path =  "C:\Workspace\ffmpeg-4.4.1-essentials_build"

$format = $formats[0]


Get-ChildItem -Path $path -File -Recurse | Sort-Object -Property {$_.Name} |  Where-Object {".mov",".mp4",".avi",".flv",".mkv" -eq $_.extension} | % {

     if ($_.BaseName -NotLike "*_"+$format.quality) {
        $inputFile = $_.FullName
        $outputFile = $_.Directory.FullName + "\" + $_.BaseName+"_"+$format.quality+".mp4"

        if (-not(Test-Path -Path $outputFile)) {
            Write-Host "Outputing: [$outputFile]"
            ## 1920=1080p, 1280=720p, 858=480p
            ## trunc to avoid height cannot be divisible.
            $scale = $format.width + ":trunc(ow/a/2)*2"
            .\bin\ffmpeg.exe -i $inputFile -filter:v scale=$scale -vcodec h264 -acodec aac $outputFile -v quiet -stats
        }

        #If the file already exists, show the message and do nothing.
        else {
            Write-Host "Already exists: [$outputFile]"
        }
    }
}
