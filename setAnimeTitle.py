#!/usr/bin/env python
import sys
import subprocess
import os
import re
import tempfile
from shutil import which

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def get_video_files(directory):
    return sorted(
        [f for f in os.listdir(directory) if f.lower().endswith((".mp4", ".mkv"))],
        key=natural_sort_key
    )

def find_tool(tool_name):
    path = which(tool_name)
    if not path:
        print(f"Warning: {tool_name} not found in PATH. Some files may fail to update.")
    return path

def generate_mkv_tags_xml(title, album):
    """Generate a temporary MKV tags XML file"""
    xml_content = f"""<?xml version="1.0"?>
<Tags>
  <Tag>
    <Targets>
      <TargetTypeValue>50</TargetTypeValue>
    </Targets>
    <Simple>
      <Name>TITLE</Name>
      <String>{title}</String>
    </Simple>
    <Simple>
      <Name>ALBUM</Name>
      <String>{album}</String>
    </Simple>
  </Tag>
</Tags>"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xml", mode='w', encoding='utf-8')
    temp_file.write(xml_content)
    temp_file.close()
    return temp_file.name

def set_metadata(file_path, episode_idx, anime_title, exiftool_path, mkvpropedit_path, dry_run=False):
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == ".mp4":
        if not exiftool_path:
            print(f"Skipping MP4 (ExifTool not found): {file_path}")
            return
        command = [
            exiftool_path,
            '-overwrite_original',
            f'-Album={anime_title}',
            f'-Title={episode_idx}',
            file_path,
        ]
    elif file_ext == ".mkv":
        if not mkvpropedit_path:
            print(f"Skipping MKV (mkvpropedit not found): {file_path}")
            return
        xml_file = generate_mkv_tags_xml(episode_idx, anime_title)
        command = [
            mkvpropedit_path,
            file_path,
            "--tags", f"all:{xml_file}"
        ]
    else:
        print(f"Skipping unsupported file type: {file_path}")
        return

    if dry_run:
        print(f"[DRY-RUN] Would run: {' '.join(command)}")
    else:
        try:
            subprocess.run(command, check=True, text=True, encoding='utf-8', errors='replace')
            print(f"Updated '{file_path}' -> Title: '{episode_idx}', Album: '{anime_title}'")
        except subprocess.CalledProcessError as e:
            print(f"Error updating '{file_path}': {e.stderr}")
        finally:
            if file_ext == ".mkv" and not dry_run:
                os.remove(xml_file)  # cleanup temp XML

def main():
    if len(sys.argv) < 2:
        print("Usage:setAnimeTitle <Anime Title> [--dry-run]")
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv
    anime_title = " ".join(arg for arg in sys.argv[1:] if not arg.startswith("--"))

    if not anime_title:
        print("Error: Anime title cannot be empty.")
        sys.exit(1)

    if dry_run:
        print("[DRY-RUN] Dry run mode active. No files will be modified.")

    exiftool_path = find_tool("exiftool")
    mkvpropedit_path = find_tool("mkvpropedit")

    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    print(f"Setting Album name as: '{anime_title}'")

    video_files = get_video_files(current_dir)
    if not video_files:
        print("No MP4 or MKV files found in this directory この馬鹿. Nothing to do.")
        sys.exit(0)

    confirmation = input(f"\nProceed to update {len(video_files)} files? (Y/N): ").strip().upper()
    if confirmation not in ("Y", "YES"):
        print("Operation Cancelled.")
        sys.exit(0)

    print("\nUpdating metadata...")
    for idx, file in enumerate(video_files, start=1):
        episode_idx = f"Ep{idx:02d}"
        set_metadata(file, episode_idx, anime_title, exiftool_path, mkvpropedit_path, dry_run=dry_run)

    print("\nDone.")

if __name__ == "__main__":
    main()
