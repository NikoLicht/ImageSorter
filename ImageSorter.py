import re
import os
import shutil
from pathlib import Path, PureWindowsPath
from PIL import Image, ExifTags
import datetime

image_formats = ["BMP", "EXR", "GIF", "ICO", "JPEG", "JPEG2000", "JPG", "PNG", "PSD", "TIF","TGA", "TIFF", "TIFF/EP", "TIFF/IT", "WBMP", "WebP"]
months_strings = ["Januar", "Februar", "Marts", "April", "Maj", "Juni", "Juli", "August", "September", "Oktober", "November", "December"]
temp_folder = None
sorted_folder = None
sorted_folders = {}
debug_messages = []
options = {
    "DELETE_EMPTY_FOLDERS": True,
    "PRINT_STATUS": True,
    }

def status(status):
    if options["PRINT_STATUS"]:
        print("ACTION | " + status)

def main():
    make_temp_folder()
    os.chdir(".\\images\\test\\")
    delete_empty_folders(os.getcwd())
    move_images_to_temp_folder()
    delete_empty_folders(os.getcwd())
    sort_into_folders()
    print_debug_messages()



def delete_empty_folders(path):
    folders = [f.path for f in os.scandir(path) if f.is_dir()]
    for folder in folders:
        content = os.listdir(folder)
        if len(content) == 0:
            if options["DELETE_EMPTY_FOLDERS"]:
                shutil.rmtree(folder)
                status("DELETED EMPTY FOLDER - " + folder)

def make_temp_folder():
    global temp_folder
    global sorted_folder
    temp_folder_name = "TEMP_images"
    sorted_folder_name = "sorted_images"
    sorted_folder = Path(os.getcwd() + "/" + sorted_folder_name) 
    temp_folder = Path(os.getcwd() + "/" + temp_folder_name)
    try:
        os.mkdir(temp_folder)
    except:
        debug_messages.append("DEBUG | Temp folder aldredy exist")

    try:
        os.mkdir(sorted_folder)
    except:
        print("DEBUG | sorted folder aldredy exist")
    
    print("this is the temp folder: " + str(temp_folder))
    print("this is the sorted folder: " + str(sorted_folder))
    status("Created Temporary folder " + str(temp_folder))



def move_images_to_temp_folder():
    folders_to_fix = []
    for path in Path(".").iterdir():
        if path.is_dir and should_fix(path.stem):
            folders_to_fix.append(path)
            status('Added folder {} to fixing stack'.format(path.name))

    for folder in folders_to_fix:
        for picture in Path(folder).iterdir():
            if picture.is_file():
                picture = Path(PureWindowsPath(picture))
                try_move_picture(picture)


def try_move_picture(pic):
    new_picture = None
    if os.path.exists(Path(os.path.join(str(temp_folder), pic.name))):        
        i = 0
        while os.path.exists(Path(os.path.join(str(temp_folder), pic.stem + "_" + str(i) + pic.suffix))):
            i += 1
        new_picture = Path(os.path.join(str(temp_folder), pic.stem + "_" + str(i) + pic.suffix))
    else:
        new_picture = Path(os.path.join(str(temp_folder), pic.name))

    try:
        pic.rename(new_picture)
        status('Moved picture {} to temp_folder'.format(new_picture.name))

    except FileExistsError:
        debug_messages.append("The file {} already exists at the location. You should really do something about that.".format(pic.name))

def should_fix(folder_name):
    regex = r"\d{2,4}-\d{2}"
    if re.search(regex, folder_name) != None:
        return True
        status('Folder {} should be fixed'.format(folder_name))

    else:
        return False

def sort_into_folders():
    for picture in Path(temp_folder).iterdir():
        if picture.is_file():
            pic_format = picture.suffix.upper()[1:]
            if  pic_format in image_formats:
                img = Image.open(str(picture))
                try:
                    exif = { ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS }
                    #print("picture taken at " + exif["DateTimeOriginal"])
                    img.close()
                    if "DateTimeOriginal" in exif:
                        create_folder_and_move(picture, exif["DateTimeOriginal"])
                except AttributeError:
                    print("picture {} did not have any exif information".format(picture.name))
            elif pic_format in ["MOV", "MP4", "AVI", "WEBM"]:
                video_path = Path(os.path.join(str(sorted_folder), "videos"))
                if not os.path.exists(video_path):
                    os.mkdir(video_path)
                complete_video_path = os.path.join(video_path, picture.name)

                if os.path.exists(complete_video_path):
                    i = 0
                    while os.path.exists(complete_video_path.stem + "_" + str(i) + complete_video_path.suffix):
                        i += 1
                    complete_video_path = Path(complete_video_path.stem + "_" + str(i) + complete_video_path.suffix)

                picture.rename(complete_video_path)
                status("Moved video {} to video folder".format(picture.name))
            else:
                debug_messages.append("DEBUG  | could not find {} in image or video formats".format( picture.suffix.upper() ))

def create_folder_and_move(picture, date):
    global sorted_folder
    global sorted_folders
    count = 0
    for symbol in date:
        if symbol.isspace():
            count += 1
    if count == 1:

        date = datetime.datetime.strptime(date, '%Y:%m:%d %H:%M:%S')
        year = str(date.year)
        month = months_strings[date.month -1 ]

        new_folder = Path(os.path.join(str(sorted_folder), year))
        print(new_folder)
        if not os.path.exists(new_folder):
            os.mkdir(new_folder)
            status("Created new year sorting folder " + str(new_folder))

        new_sub_folder = Path(os.path.join(str(sorted_folder), year, month))
        if not os.path.exists(new_sub_folder):
            os.mkdir(new_sub_folder)
            status("Created new month sorting folder " + year + " / " + month)

        sub_folder_path = Path(os.path.join(new_sub_folder, picture.name))

        if os.path.exists(sub_folder_path):
            i = 0
            while os.path.exists(os.path.join(new_sub_folder, picture.stem + "_" + str(i) + picture.suffix)):
                i += 1
            sub_folder_path = Path(os.path.join(new_sub_folder, picture.stem + "_" + str(i) + picture.suffix))

        picture.rename(sub_folder_path)
        status("Moved picture {} into folder {} / {}".format(picture.name, year, month))
    else:
        debug_messages.append("DEBUG | too many spaces in date " + str(picture))

def print_debug_messages():
    for message in debug_messages:
        print(message)

main()
