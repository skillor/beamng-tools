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
    f = FileManager()
    f.load_zip(input_file)

    for filename in list(f.files.keys()):
        file_base, file_extension = os.path.splitext(filename)
        file_extension = file_extension.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            print("removing file", filename)
            f.delete_file(filename)

    f.save_zip(output_file, compression_level=compression_level)


def main(args):
    import argparse
    import pathlib

    parser = argparse.ArgumentParser()
    parser.add_argument('input_path', type=pathlib.Path)
    parser.add_argument('output_path', type=pathlib.Path)
    parser.add_argument('-c', '--compression', type=int, default=9)
    parsed_args = parser.parse_args(args)

    if os.path.isfile(parsed_args.input_path):
        cleanup_mod(parsed_args.input_path, parsed_args.output_path, parsed_args.compression)
    else:
        if not os.path.isdir(parsed_args.output_path):
            os.mkdir(parsed_args.output_path)
        for filename in os.listdir(parsed_args.input_path):
            # print(os.path.join(args.input_path, filename))
            cleanup_mod(os.path.join(parsed_args.input_path, filename),
                        os.path.join(parsed_args.output_path, filename),
                        parsed_args.compression)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
