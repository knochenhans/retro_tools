import ntpath
import os
import sys
import tempfile
import zipfile
import re
import subprocess

# Searches zipped iso files in directory for matching filenames and optionally extracts them
# Example: search_isos.py x ^med\. \.med$ ^mod\. \.mod$

directory_path = '/mnt/Daten/Emulation/ROMs/Commodore/Amiga/CD/'


def extract_paths_from_ls_output(ls_output: str) -> list[str]:
    path_pattern = r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\s\.\.\.\.\.\s+\d+\s+\d+\s+(.*)'
    return [match.group(1) for match in re.finditer(path_pattern, ls_output)]


def list_iso_content(filename: str) -> str|None:
    try:
        result = subprocess.run(
            ['7z',
             'l',
             filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        return None


def extract_iso_content(archive_filename: str, filename: str, output_path: str) -> str|None:
    # folder_path = os.path.join(output_path, os.path.dirname(filename))
    # os.makedirs(folder_path, exist_ok=True)
    folder_path = output_path
    try:
        result=subprocess.run(
            ['7z',
             'e',
             archive_filename,
             filename,
             '-o' + folder_path,
             '-spf',
             '-aoa'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        return None


def search_strings_by_regex(string_list: list, regex_pattern: str) -> list[str]:
    matching_strings=[]
    regex=re.compile(regex_pattern, re.IGNORECASE)

    for string in string_list:
        if regex.search(string):
            matching_strings.append(string)

    return matching_strings


def check_iso_zip(filename: str, pattern: str, extract: bool):
    print(f'Checking {filename}')
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(filename, 'r') as zip_archive:
            for zip_filename in zip_archive.namelist():
                if zip_filename.lower().endswith('.iso'):
                    # Extract the ISO file to the temporary directory
                    extracted_path=os.path.join(temp_dir, os.path.basename(zip_filename))
                    with zip_archive.open(zip_filename) as iso_file, open(extracted_path, 'wb') as temp_iso:
                        temp_iso.write(iso_file.read())

                    output=list_iso_content(extracted_path)

                    if output:
                        paths=extract_paths_from_ls_output(output)
                        matching_strings=search_strings_by_regex(paths, pattern)

                        if matching_strings:
                            if extract:
                                print(f'Found matches in {filename}, and extracting')
                                for match in matching_strings:
                                    extract_iso_content(extracted_path, match, '/tmp/test')
                            else:
                                print(f'Found matches in {filename}')
                                for match in matching_strings:
                                    print(match)


def main():
    if len(sys.argv) < 3:
        print('Usage: search_isos.py [s | x] [pattern1 pattern2 ...]')
        return

    option=sys.argv[1].lower()
    arguments=sys.argv[2:]

    extract = False

    if option == 's':
        pass
    elif option == 'x':
        extract = True
    else:
        print("Invalid option. Use 's' for searching or 'x' for extracting.")

    for root, _, files in os.walk(directory_path):
        for file in sorted(files):
            if file.lower().endswith('.zip'):
                for argument in arguments:
                    check_iso_zip(os.path.join(root, file), argument, extract)


if __name__ == "__main__":
    main()
