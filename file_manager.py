import ntpath
import zipfile
import os


class FileManager:
    files = {}
    changed_files = {}

    def reset(self):
        self.files = {}
        self.changed_files = {}

    def filenames(self):
        return self.files.keys() | self.changed_files.keys()

    def load_zip(self, file, allow_override=True, throw_error=True):
        success_files = set()
        duplicate_files = set()
        zip_file = zipfile.ZipFile(file, 'r')
        for file in zip_file.infolist():
            if not file.is_dir():
                if (not allow_override) and (file.filename in self.files):
                    if throw_error:
                        raise FileExistsError('duplicate file: "{}"'.format(file.filename))
                    duplicate_files.add(file.filename)
                else:
                    success_files.add(file.filename)
                    self.files[file.filename] = (zip_file, file)
        if duplicate_files:
            return False, success_files, duplicate_files
        return True, success_files, duplicate_files

    def load_dir(self, directory):
        for current_path, folders, files in os.walk(directory):
            for file in files:
                rel_path = os.path.join(current_path[len(directory)+1:], file)
                self.files[rel_path] = (directory, rel_path)

    def load_file(self, base_path, file):
        self.files[file] = (base_path, file)

    def read_file(self, filename):
        f = None
        if filename in self.files:
            f = self.files[filename]
        else:
            filename_lower = filename.lower()
            for s_filename in self.files.keys():
                if s_filename.lower() == filename_lower:
                    f = self.files[s_filename]
            if f is None:
                raise FileNotFoundError('{} not found'.format(filename))
        if isinstance(f[0], str):
            with open(os.path.join(f[0], f[1]), 'rb') as fh:
                return fh.read()
        elif isinstance(f[0], zipfile.ZipFile):
            return f[0].read(f[1].filename)

    def exists_file(self, filename):
        return filename in self.filenames()

    def get_file_content(self, filename):
        if filename in self.changed_files:
            return self.changed_files[filename]
        return self.read_file(filename)

    def write_file(self, filename, content):
        self.changed_files[filename] = content

    def save_file(self, filename, directory='', as_filename=''):
        file = ntpath.normpath(os.path.join(directory, as_filename)
                               if as_filename else
                               os.path.join(directory, filename))
        dir_name = os.path.dirname(file)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with open(file, 'wb') as f:
            f.write(self.get_file_content(filename))

    def save_dir(self, directory, progress=False):
        n = len(self.files)
        for i, filename in enumerate(self.filenames()):
            if progress:
                print(i, '/', n)
            self.save_file(filename, directory, filename)

    def save_zip(self, file, compression=zipfile.ZIP_DEFLATED, compression_level=9, progress=False):
        with zipfile.ZipFile(file, 'w', compression=compression, compresslevel=compression_level) as zf:
            n = len(self.files)
            for i, filename in enumerate(self.filenames()):
                if progress:
                    print(i, '/', n)
                zf.writestr(filename, self.get_file_content(filename))

    def delete_file(self, filename):
        del self.files[filename]
