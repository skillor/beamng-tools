import zipfile

from file_manager import FileManager
import os

ALLOWED_EXTENSIONS = [
    '.cs',
    '.css',
    '.dae',
    '.dds',
    '.html',
    '.jbeam',
    '.jpg',
    '.js',
    '.json',
    '.lua',
    '.mp3',
    '.ogg',
    '.otf',
    '.pc',
    '.prefab',
    '.png',
    '.sbeam',
    '.svg',
    '.ter',
    '.ttf',
    '.wav',
]


def cleanup_mod(input_file, output_file, compression_level=9):
    try:
        f = FileManager()
        f.load_zip(input_file)

        removed_files = []
        for filename in list(f.files.keys()):
            file_base, file_extension = os.path.splitext(filename)
            file_extension = file_extension.lower()
            if file_extension not in ALLOWED_EXTENSIONS:
                f.delete_file(filename)
                removed_files.append(filename)

        f.save_zip(output_file, compression_level=compression_level)
        print('\n'.join(['copied "{}" to "{}"'.format(input_file, output_file)] +
                        ['  -"{}"'.format(x) for x in removed_files]))
    except zipfile.BadZipfile:
        print('bad zip: "{}"'.format(input_file))


def main(args):
    import argparse
    import glob

    parser = argparse.ArgumentParser()
    parser.add_argument('input_path', type=str)
    parser.add_argument('output_path', type=str)
    parser.add_argument('-c', '--compression', type=int, default=9)
    parsed_args = parser.parse_args(args)

    if os.path.isfile(parsed_args.input_path):
        cleanup_mod(parsed_args.input_path, parsed_args.output_path, parsed_args.compression)
    else:
        os.makedirs(parsed_args.output_path, exist_ok=True)
        for filename in glob.glob(parsed_args.input_path):
            if os.path.isfile(filename):
                cleanup_mod(filename,
                            os.path.join(parsed_args.output_path, os.path.basename(filename)),
                            parsed_args.compression)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
