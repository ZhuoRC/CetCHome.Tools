
import pathlib
import imageio
import rawpy
from rich.progress import track
from PIL import Image
import shutil
import os
import pillow_heif
from PIL import Image
from datetime import datetime


def get_date_taken(image_path):
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if 36867 in exif_data:  # 36867 corresponds to the DateTimeOriginal tag
                date_taken_str = exif_data[36867]
                date_taken = datetime.strptime(date_taken_str, "%Y:%m:%d %H:%M:%S")
                return date_taken
            else:
                return "Date taken information not found in metadata."
    except Exception as e:
        return f"Error: {e}"
    
    
from datetime import datetime, timedelta  

def add_days_to_datetime(input_datetime, days_to_add):
    try:
        # Add the specified number of days
        result_datetime = input_datetime + timedelta(days=days_to_add)

        return result_datetime
    except ValueError as e:
        return f"Error: {e}"
    
pathArray = [
             r'Z:\Photo\Angelo\2020.Age 2+\2012']
             
for path in pathArray:
    print(path)
    #path = r'Z:\Photo\Life.Montreal\20151018.Part nature du Bois-de-ile-Bizard'
    ext = 'JPG'
    #ext = 'HEIC'

    FROM = pathlib.Path(path)  # Folder to read from.
    TO = pathlib.Path(FROM.joinpath(ext))  # Folder to save images into.
    if not os.path.exists(TO):
        os.makedirs(TO)

    images = list(FROM.glob(f'*.{ext}'))

    for img in track(images):
        new_location = (TO / img.name).with_suffix(".JPG")
        shutil.copy(img, new_location)

        date_taken  = get_date_taken(img)
        new_date_taken = add_days_to_datetime(date_taken,2659)
        print("change date:{0} to {1}",date_taken, new_date_taken)

        #change exif        
        import subprocess
        command = f'.\\helper.photo\\bin\\exiftool -overwrite_original -AllDates=\"{new_date_taken}\" \"{new_location._str}\"'
        print(command)
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Command executed successfully.")
        print("Output:", result.stdout)
        
        #shutil.move(img, TO) 
        
    #subprocess.Popen(r'explorer /select,"'+str(TO)+'\"')