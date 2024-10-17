import os
import re
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define base folder and subfolder paths
base_folder = os.getenv('BASE_FOLDER')
# Define subfolders
t_folder = os.path.join(base_folder, '_t')
pics_folder = os.path.join(base_folder, '_')
vids_folder = os.path.join(base_folder, '_o')
old_folder = os.path.join(base_folder, '_old')
special_folders = os.getenv('SPECIAL_FOLDERS').split(',')

# Regex pattern to match iOS asset filenames
ios_filename_pattern = re.compile(r'^((s)+-)+\d{8}_\d{9}_iOS\.\w+$')


# Function to get file creation timestamp
def get_file_creation_time(file_path):
    try:
        # On Windows, this returns the creation time. On Unix, it returns the last modification time.
        creation_time = os.path.getctime(file_path)
        return datetime.fromtimestamp(creation_time)
    except Exception as e:
        print(f"Error retrieving creation time: {e}")
        return None


# Function to convert datetime to milliseconds
def convert_to_ms(dt_obj):
    try:
        ms = int(dt_obj.timestamp() / 10)
        return ms
    except Exception as e:
        print(f"Error converting timestamp: {e}")
        return None


# Function to count files
def count_files(folder):
    pics_count = 0
    vids_count = 0
    specials_count = 0
    for root, dirs, files in os.walk(folder):
        if os.path.basename(root) in special_folders:
            for file in files:
                if file.startswith("."):
                    continue  # ignore .DS_Store files
                specials_count += 1

        for file in files:
            file_path = os.path.join(root, file)
            if file_path.startswith("."):
                continue  # ignore .DS_Store files

            # Check if the file is an image
            try:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.heic')):
                    pics_count += 1
                elif file.lower().endswith(('.mov', '.mp4')):
                    vids_count += 1
                else:
                    continue
            except Exception as e:
                print(f"Error processing image: {e}")

    print(f"Total images: {pics_count}")
    print(f"Total videos: {vids_count}")
    print(f"Total specials: {specials_count}")


# Function to rename files
def process_files(folder):
    for root, dirs, files in os.walk(folder):
        # if os.path.basename(root) in special_folders:
        #     continue  # ignore special folders

        for file in files:
            if file.startswith("."):
                continue  # ignore .DS_Store files

            # Skip if file already matches iOS filename pattern
            if ios_filename_pattern.match(file):
                continue

            # Skip if file already has the folder name as prefix
            if file.startswith(f"{os.path.basename(root)}-"):
                continue

            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1]
            parent_folder = os.path.basename(root)

            # Get file creation time
            creation_time = get_file_creation_time(file_path)
            ms = convert_to_ms(creation_time) if creation_time else "000000000"

            new_filename = f"{datetime.now().strftime('%Y%m%d')}_{ms}_iOS{file_ext}"

            # Append parent folder name to the file
            new_filename = f"{parent_folder}-{new_filename}"

            # Rename the file
            new_file_path = os.path.join(root, new_filename)

            # if file exists, add a number to the filename
            if os.path.exists(new_file_path):
                i = 1
                while True:
                    new_filename = f"{parent_folder}-{datetime.now().strftime('%Y%m%d')}_{ms}_iOS_{i}{file_ext}"
                    new_file_path = os.path.join(root, new_filename)
                    if not os.path.exists(new_file_path):
                        break
                    i += 1

            os.rename(file_path, new_file_path)
            print(f"Renamed {file} to {new_filename}")


# Move files to base folder
def move_files(folder):
    # Move to the base folder
    # 1. pics to base_folder + "/_"
    # 2. vids to base_folder + "/_o"

    # Create subfolders if they don't exist
    if not os.path.exists(pics_folder):
        os.makedirs(pics_folder)
    if not os.path.exists(vids_folder):
        os.makedirs(vids_folder)

    # Move files to the respective subfolders
    for root, dirs, files in os.walk(folder):
        if os.path.basename(root) in special_folders:
            move_special_folder_files(root, files)
            continue

        for file in files:
            file_path = os.path.join(root, file)
            if file.startswith("."):
                continue  # ignore .DS_Store files

            # Check if the file is an image
            try:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.heic')):
                    img = Image.open(file_path)
                    img.close()
                    new_path = os.path.join(pics_folder, file)
                elif file.lower().endswith(('.mov', '.mp4')):
                    new_path = os.path.join(vids_folder, file)
                else:
                    continue

                os.rename(file_path, new_path)
                print(f"Moved {file} to {new_path}")
            except Exception as e:
                print(f"Error processing image: {e}")


# Move special folder files
def move_special_folder_files(root, files):
    special_folder = os.path.basename(root)
    if special_folder not in special_folders:
        return  # ignore non special folders

    for file in files:
        if file.startswith("."):
            continue  # ignore .DS_Store files

        file_path = os.path.join(root, file)
        new_path = os.path.join(base_folder, "_" + special_folder, file)
        os.rename(file_path, new_path)
        print(f"Moved special {file} to {new_path}")


def move_old_files():
    # Move old files to old folder.
    # Files older than 7 days will be moved to a folder named "_old"
    # 1. pics to old_folder + "/_"
    # 2. vids to old_folder + "/_o"

    # TODO: Include 2024/2024q3 folder

    # Define oldfolder subfolders
    old_pics_folder = os.path.join(old_folder, '_')
    old_vids_folder = os.path.join(old_folder, '_o')

    # Create subfolders if they don't exist
    if not os.path.exists(old_pics_folder):
        os.makedirs(old_pics_folder)
    if not os.path.exists(old_vids_folder):
        os.makedirs(old_vids_folder)

    # List files in the pics and vids folders older than 7 days
    for folder in [pics_folder, vids_folder]:
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                if file.startswith("."):
                    continue  # ignore .DS_Store files

                # Get file creation time
                # creation_time = get_file_creation_time(file_path)
                try:
                    # Get creation time from filename date part
                    creation_time = datetime.strptime(file.split('-')[1][:8], '%Y%m%d')

                    if creation_time:
                        # Calculate the difference in days
                        diff = datetime.now() - creation_time
                        if diff.days > 7:
                            # Move the file to the old folder
                            if folder == pics_folder:
                                new_path = os.path.join(old_pics_folder, file)
                            else:
                                new_path = os.path.join(old_vids_folder, file)

                            os.rename(file_path, new_path)
                            print(f"Moved {file} to {new_path}")
                except Exception as e:
                    print(f"Error processing file: {file} -> {e}")


if __name__ == "__main__":
    while True:
        # Ask for which option to run and execute per module
        option = input(
            "Which option do you want to run?\n"
            "1: Count files\n"
            "2: Process files\n"
            "3: Move files\n"
            "4: Move old files\n"
            "0: Exit\n"
        )

        if option == "1":
            count_files(t_folder)
        elif option == "2":
            # Start processing files in the subfolder
            process_files(t_folder)
        elif option == "3":
            # Move files to base folder
            move_files(t_folder)
        elif option == "4":
            # Move old files
            move_old_files()
        elif option == "0":
            # Exit the program
            break
        else:
            print("Invalid option. Please try again.")
