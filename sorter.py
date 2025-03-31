import os
import shutil
import time
import subprocess

# Path to Downloads and Trash
DOWNLOADS_PATH = os.path.expanduser("~/Downloads")
TRASH_PATH = os.path.expanduser("~/.Trash")

# Unique folder names with emojis
TIME_CATEGORIES = {
    "📌 Today": 1,
    "📆 Week": 7,
    "🌙 Month": 30,
    "🗑 Old": 90,
}

CATEGORY_MAP = {
    "🖼 Images": [],
    "🎞 Videos": [],
    "🎵 Music": [],
    "📄 Documents": [],
    "📦 Archives": [],
    "💻 Code": [],
    "🌱 Torrents": [],
    "🖼 Screenshots": [],
    "📁 Other": [],
}

EXTENSION_MAP = {
    "📄 Documents": [".pdf", ".docx", ".txt", ".rtf", ".md", ".xls", ".xlsx"],
    "🖼 Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    "🖼 Screenshots": [".screenshot", "_screenshot", "screenshot"],
    "🎞 Videos": [".mp4", ".mov", ".avi", ".mkv"],
    "🎵 Music": [".mp3", ".wav", ".flac"],
    "📦 Archives": [".zip", ".rar", ".tar.gz", ".tar", ".dmg"],
    "💻 Code": [".py", ".js", ".html", ".css", ".java", ".go", ".json"],
    "🌱 Torrents": [".torrent"],
    "📁 Other": [],
}

now = time.time()


def get_file_category(file_path):
    """Determine the category of a file based on extension only."""
    ext = os.path.splitext(file_path)[1].lower()
    for category, extensions in EXTENSION_MAP.items():
        if ext in extensions:
            return category
    return "📁 Other"


def get_time_category(file_path):
    """Determine the time category of a file based on modification time."""
    try:
        created_time = os.path.getmtime(file_path)
        days_old = (now - created_time) / 86400
    except Exception as e:
        print(f"⚠️ Error getting time for {file_path}: {e}")
        return None

    for category, max_days in TIME_CATEGORIES.items():
        if days_old <= max_days:
            return category

    return "Old" if days_old > TIME_CATEGORIES["🗑 Old"] else None


def move_to_trash(file_path):
    """Move old files to Trash instead of deleting them."""
    try:
        trash_destination = os.path.join(TRASH_PATH, os.path.basename(file_path))
        counter = 1
        while os.path.exists(trash_destination):
            base, ext = os.path.splitext(os.path.basename(file_path))
            trash_destination = os.path.join(TRASH_PATH, f"{base}_{counter}{ext}")
            counter += 1
        shutil.move(file_path, trash_destination)
        print(f"🗑 Moved to Trash: {file_path} → {trash_destination}")
    except Exception as e:
        print(f"⚠️ Error moving to Trash {file_path}: {e}")


def move_file(file_path, time_category):
    """Move a file to the appropriate category folder."""
    file_category = get_file_category(file_path)
    destination_folder = os.path.join(DOWNLOADS_PATH, time_category, file_category)
    os.makedirs(destination_folder, exist_ok=True)
    try:
        shutil.move(file_path, destination_folder)
        print(f"📄 Moved file: {file_path} → {destination_folder}")
    except Exception as e:
        print(f"⚠️ Error moving file {file_path}: {e}")


def move_folder(folder_path, time_category):
    """Move a folder to the appropriate time category."""
    destination_folder = os.path.join(
        DOWNLOADS_PATH, time_category, os.path.basename(folder_path)
    )
    if os.path.exists(destination_folder):
        print(f"⚠️ Skipping {folder_path}, destination already exists")
        return
    try:
        os.makedirs(os.path.dirname(destination_folder), exist_ok=True)
        shutil.move(folder_path, destination_folder)
        print(f"📁 Moved folder: {folder_path} → {destination_folder}")
    except Exception as e:
        print(f"⚠️ Error moving folder {folder_path}: {e}")


def remove_empty_folders(directory):
    """Recursively remove empty folders in a directory."""
    for root, dirs, files in os.walk(directory, topdown=False):
        for d in dirs:
            folder_path = os.path.join(root, d)
            if not os.listdir(folder_path):
                os.rmdir(folder_path)
                print(f"🗑 Removed empty folder: {folder_path}")


def sort_downloads():
    """Main function to sort files in Downloads."""
    for item in os.listdir(DOWNLOADS_PATH):
        item_path = os.path.join(DOWNLOADS_PATH, item)
        if item in [".DS_Store", "desktop.ini"] or item in TIME_CATEGORIES:
            continue
        time_category = get_time_category(item_path)
        if not time_category:
            continue
        if time_category == "Old":
            move_to_trash(item_path)
            continue
        if os.path.isdir(item_path):
            move_folder(item_path, time_category)
        else:
            move_file(item_path, time_category)
    remove_empty_folders(DOWNLOADS_PATH)


def reset_sorted_downloads():
    """Reset sorted files/folders by moving them back to Downloads and removing time/category folders."""
    for time_cat in TIME_CATEGORIES:
        time_cat_path = os.path.join(DOWNLOADS_PATH, time_cat)
        if not os.path.isdir(time_cat_path):
            continue

        moved_items = set()

        for category in CATEGORY_MAP:
            category_path = os.path.join(time_cat_path, category)
            if not os.path.isdir(category_path):
                continue
            for item in os.listdir(category_path):
                src = os.path.join(category_path, item)
                dst = os.path.join(DOWNLOADS_PATH, item)
                counter = 1
                while os.path.exists(dst):
                    dst = os.path.join(DOWNLOADS_PATH, f"{item}_{counter}")
                    counter += 1
                shutil.move(src, dst)
                moved_items.add(src)
                print(f"📁 Moved folder/file: {src} → {dst}")

        for item in os.listdir(time_cat_path):
            item_path = os.path.join(time_cat_path, item)
            if item_path in moved_items:
                continue
            dst = os.path.join(DOWNLOADS_PATH, item)
            counter = 1
            while os.path.exists(dst):
                dst = os.path.join(DOWNLOADS_PATH, f"{item}_{counter}")
                counter += 1
            shutil.move(item_path, dst)
            print(f"📦 Moved uncategorized item: {item_path} → {dst}")

        try:
            shutil.rmtree(time_cat_path)
            print(f"🧹 Removed folder: {time_cat_path}")
        except Exception as e:
            print(f"⚠️ Could not remove {time_cat_path}: {e}")


if __name__ == "__main__":
    reset_sorted_downloads()
    sort_downloads()
