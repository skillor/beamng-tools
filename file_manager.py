import zipfile


class FileManager:
    files = None
    zip_file = None

    def reset(self):
        self.zip_file = None
        self.files = {}

    def load_zip(self, file):
        self.reset()
        self.zip_file = zipfile.ZipFile(file, 'r')
        for file in self.zip_file.infolist():
            if not file.is_dir():
                self.files[file.filename] = file

    def save_zip(self, file, compression_level=9, progress=False):
        with zipfile.ZipFile(file, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zf:
            n = len(self.files)
            for i, file in enumerate(self.files.values()):
                if progress:
                    print(i, '/', n)
                if isinstance(file, zipfile.ZipInfo):
                    zf.writestr(file.filename, self.zip_file.read(file.filename))

    def delete_file(self, filename):
        del self.files[filename]
