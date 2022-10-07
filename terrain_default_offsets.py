import os
import ntpath

import jbeam
from file_manager import FileManager


def main():
    p = r'C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive\content\levels'

    terrain_offsets = {}

    f = FileManager()

    for file in os.listdir(p):
        f.reset()

        if not file.endswith('.zip'):
            print('{} is not zip'.format(file))
            continue

        f.load_zip(os.path.join(p, file))

        objects_path = ('main', 'MissionGroup')

        map_name = file[:-4]

        map_str = os.path.join('levels', map_name + os.sep)

        mission_group_str = os.path.join(map_str, *objects_path) + os.sep

        for filename in f.files.keys():
            norm_filename = ntpath.normpath(filename)
            if norm_filename.startswith(mission_group_str):
                j = jbeam.load(f.read_file(filename).decode('utf-8'))
                for line in j.lines:
                    if line['class'] == 'TerrainBlock':
                        terrain_offsets[map_name] = line['position']

    jb = jbeam.Jbeam([
        terrain_offsets
    ])

    with open('terrains.json', 'w') as f:
        f.write(jb.tostring(2))


if __name__ == '__main__':
    main()
