
import pathlib
import imageio
import rawpy
from rich.progress import track
from PIL import Image
import shutil
import os
import pillow_heif

path = r'Z:\Photo\Life.Montreal\!杂七杂八'
#ext = 'RAF'
ext = 'HEIC'

FROM = pathlib.Path(path)  # Folder to read from.
TO = pathlib.Path(FROM.joinpath(ext))  # Folder to save images into.
if not os.path.exists(TO):
    os.makedirs(TO)

images = list(FROM.glob(f'*.{ext}'))

for img in track(images):
    new_location = (TO / img.name).with_suffix(".jpg")

    if ext=='RAF':
        with rawpy.imread(str(img)) as raw:
            rgb = raw.postprocess(rawpy.Params(
                use_camera_wb=True,  # 是否使用拍摄时的白平衡值
                use_auto_wb=False,
                exp_shift=0.25  # 修改后光线会下降，所以需要手动提亮，线性比例的曝光偏移。可用范围从0.25（变暗2级）到8.0（变浅3级）。
                ))
        
        imageio.imsave(new_location, rgb)
    
    if ext=='HEIC':
        heif_file = pillow_heif.read_heif(str(img))
        image = Image.frombytes(
            heif_file.mode,
            heif_file.size,
            heif_file.data,
            "raw",
        )

    image.save(new_location, "JPEG", quality=100)

    #clone exif        
    import subprocess
    command = f'.\\helper.photo\\bin\\exiftool -overwrite_original -TagsFromFile \"{img._str}\" \"{new_location._str}\"'
    print(command)
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("Command executed successfully.")
    print("Output:", result.stdout)
    
    shutil.move(img, TO) 
    
subprocess.Popen(r'explorer /select,"'+str(TO)+'\"')