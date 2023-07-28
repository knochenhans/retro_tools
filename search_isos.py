import os
import tempfile
import zipfile
import re
import subprocess

# Searches zipped iso files in directory for string

def extract_paths_from_ls_output(ls_output):
    path_pattern = r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\s\.\.\.\.\.\s+\d+\s+\d+\s+(.*)'
    return [match.group(1) for match in re.finditer(path_pattern, ls_output)]


def list_iso_content(filename):
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


def search_strings_by_regex(string_list, regex_pattern):
    matching_strings = []
    regex = re.compile(regex_pattern, re.IGNORECASE)

    for string in string_list:
        if regex.search(string):
            matching_strings.append(string)

    return matching_strings


# filename = '/mnt/Daten/Emulation/ROMs/Commodore/Amiga/CD/Coverdiscs/[ISO]/Amiga Games CD-ROM 1995-01 (1995)(CompuTec)(DE)[!].zip'
directory_path = '/mnt/Daten/Emulation/ROMs/Commodore/Amiga/CD/Coverdiscs/[ISO]/'

pattern = 'Hanger'


def check_iso_zip(filename):
    print(f'Checking {filename}')
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(filename, 'r') as zip_archive:
            for zip_filename in zip_archive.namelist():
                if zip_filename.lower().endswith('.iso'):
                    # Extract the ISO file to the temporary directory
                    extracted_path = os.path.join(temp_dir, os.path.basename(zip_filename))
                    with zip_archive.open(zip_filename) as iso_file, open(extracted_path, 'wb') as temp_iso:
                        temp_iso.write(iso_file.read())

                    # command = "/tmp/Amiga Games CD-ROM 1995-01 (1995)(CompuTec)(DE)[!].iso"
                    output = list_iso_content(extracted_path)

                    if output:
                        paths = extract_paths_from_ls_output(output)
                        matching_strings = search_strings_by_regex(paths, pattern)

                        if matching_strings:
                            print(f'Found matches in {filename}')
                            for match in matching_strings:
                                print(match)


for root, _, files in os.walk(directory_path):
    for file in sorted(files):
        if file.lower().endswith('.zip'):
            check_iso_zip(os.path.join(root, file))
