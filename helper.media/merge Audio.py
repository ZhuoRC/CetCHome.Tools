import os
from pydub import AudioSegment
from tqdm import tqdm

# Specify the folder containing the MP4 files
folder_path = "C:\Clouds\Dropbox\Music\Game\轩辕剑\轩辕剑黄金纪念版CD"

# Get all MP4 files in the folder, sorted alphabetically
video_files = sorted([os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith(".mp4")])
# Get all MP3 files in the folder, sorted alphabetically
audio_files = sorted([os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith(".mp3")])


# Get the folder name to use as the output file name
output_filename = os.path.basename(folder_path) + ".mp3"

# Define the path to the parent directory
parent_folder_path = os.path.dirname(folder_path)
output_path = os.path.join(parent_folder_path, output_filename)

# Check if there are MP4 files in the folder
if not video_files:
    print("No MP4 files found in the folder.")
else:
    # Convert the first MP4 file to MP3 and load it as the initial audio segment
    merged_audio = AudioSegment.from_file(video_files[0], format="mp4").export("temp_0.mp3", format="mp3")
    merged_audio = AudioSegment.from_file("temp_0.mp3")

    # Convert and append the rest of the MP4 files with a progress bar
    for i, file in enumerate(tqdm(video_files[1:], desc="Converting and merging files")):
        # Convert MP4 to MP3
        temp_mp3_path = f"temp_{i+1}.mp3"
        AudioSegment.from_file(file, format="mp4").export(temp_mp3_path, format="mp3")
        
        # Load the converted MP3 file and append to merged_audio
        next_audio = AudioSegment.from_file(temp_mp3_path)
        merged_audio += next_audio
        
        # Clean up the temporary MP3 file
        os.remove(temp_mp3_path)

    # Export the final merged audio to the parent folder
    merged_audio.export(output_path, format="mp3")

    print(f"Files have been converted and merged successfully into {output_path}!")


# Check if there are MP3 files in the folder
if not audio_files:
    print("No MP3 files found in the folder.")
else:
    # Load the first MP3 file
    merged_audio = AudioSegment.from_file(audio_files[0])

    # Append the rest of the MP3 files with a progress bar
    for file in tqdm(audio_files[1:], desc="Merging files"):
        next_audio = AudioSegment.from_file(file)
        merged_audio += next_audio

    # Export the merged audio to the parent folder
    merged_audio.export(output_path, format="mp3")

    print(f"Files have been merged successfully into {output_path}!")