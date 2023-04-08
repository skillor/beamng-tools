import glob
import zipfile
import fnmatch
from file_manager import FileManager


def find_duplicate_mod(files=iter([]), allow_wildcards=()):
    fm = FileManager()
    file_files = {}
    results = []
    for f in files:
        try:
            valid, unique, duplicates = fm.load_zip(f, allow_override=False, throw_error=False)
            file_files[f] = unique
            if not valid:
                filtered_duplicates = [dup for dup in duplicates
                                       if (True not in [fnmatch.fnmatch(dup, w) for w in allow_wildcards])]
                if filtered_duplicates:
                    duplicate_files = {}
                    for dup in filtered_duplicates:
                        dup_filename = fm.files[dup][0]
                        if issubclass(type(dup_filename), zipfile.ZipFile):
                            dup_filename = dup_filename.filename
                        if dup_filename in duplicate_files:
                            duplicate_files[dup_filename].append(dup)
                        else:
                            duplicate_files[dup_filename] = [dup]
                    for df, d_files in duplicate_files.items():
                        p = len(d_files) * 100 / (len(d_files) + len(unique))
                        results.append((p, '{:3.0f}% {:4}/{:4} "{}" "{}"'.format(
                            p,
                            len(d_files),
                            len(d_files) + len(unique),
                            f,
                            df
                        )))
        except zipfile.BadZipFile:
            print('bad zip: "{}"'.format(f))
    print('\n'.join([x[1] for x in sorted(results, key=lambda x: -x[0])]))


def main(args):
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('mods', nargs='+', type=str)
    parser.add_argument('-a', '--allow-wildcard', nargs='+', action='append', type=str, default=[])
    parsed_args = parser.parse_args(args)

    files = set()
    for x in parsed_args.mods:
        for y in glob.glob(x):
            files.add(y)
    find_duplicate_mod(
        iter(files),
        allow_wildcards=tuple(set([y for x in parsed_args.allow_wildcard for y in x])),
    )


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
