import ntpath
import zipfile
import os


class FileManager:
    files = {}
    changed_files = {}

    def reset(self):
        self.files = {}
        self.changed_files = {}

    def load_zip(self, file):
        zip_file = zipfile.ZipFile(file, 'r')
        for file in zip_file.infolist():
            if not file.is_dir():
                self.files[file.filename] = (zip_file, file)

    def load_dir(self, directory):
        for current_path, folders, files in os.walk(directory):
            for file in files:
                rel_path = os.path.join(current_path[len(directory)+1:], file)
                self.files[rel_path] = (directory, rel_path)

    def load_file(self, base_path, file):
        self.files[file] = (base_path, file)

    def read_file(self, filename):
        f = self.files[filename]
        if isinstance(f[0], str):
            with open(os.path.join(f[0], f[1]), 'rb') as fh:
                return fh.read()
        elif isinstance(f[0], zipfile.ZipFile):
            return f[0].read(f[1].filename)

    def get_file_content(self, filename):
        if filename in self.changed_files:
            return self.changed_files[filename]
        return self.read_file(filename)

    def write_file(self, filename, content):
        self.changed_files[filename] = content

    def save_file(self, filename, directory, as_filename):
        file = ntpath.normpath(os.path.join(directory, as_filename))
        dir_name = os.path.dirname(file)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with open(file, 'wb') as f:
            f.write(self.get_file_content(filename))

    def save_dir(self, directory, progress=False):
        n = len(self.files)
        for i, filename in enumerate(self.files.keys()):
            if progress:
                print(i, '/', n)
            self.save_file(filename, directory, filename)

    def save_zip(self, file, compression_level=9, progress=False):
        with zipfile.ZipFile(file, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zf:
            n = len(self.files)
            for i, filename in enumerate(self.files.keys()):
                if progress:
                    print(i, '/', n)
                zf.writestr(filename, self.get_file_content(filename))

    def delete_file(self, filename):
        del self.files[filename]
