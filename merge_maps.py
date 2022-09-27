import os

import jbeam
from file_manager import FileManager
import ntpath

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
    '.wav',
]


def is_map_path(p):
    if p[0] != 'l':
        p = p[1:]
    return ntpath.normpath(p).startswith('levels' + os.sep)


def fix_absolute_paths(j, norm_filename):
    def fix_absolute_paths_rec(d):
        it = None
        if isinstance(d, dict):
            it = d.items()
        elif isinstance(d, list):
            it = enumerate(d)
        for k, v in it:
            if isinstance(v, dict) or isinstance(v, list):
                fix_absolute_paths_rec(v)
            else:
                file_base, file_extension = os.path.splitext(str(v))
                file_extension = file_extension.lower()
                if file_extension in ALLOWED_EXTENSIONS and not is_map_path(v):
                    d[k] = os.path.join(os.path.dirname(norm_filename), v).replace(os.sep, '/')

    fix_absolute_paths_rec(j)


def main():
    base_map_path = r'C:\Users\jack-\AppData\Local\BeamNG.drive\0.26\mods\unpacked\allmap'
    base_map_name = 'allmap'

    merge_maps = [
        # {
        #     'file': r'C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive\content\levels\automation_test_track.zip',
        #     'name': 'automation_test_track',
        #     'pos': [0, 0, 0],
        # },
        {
            'file': r'C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive\content\levels\west_coast_usa.zip',
            'name': 'west_coast_usa',
            'pos': [0, 2000, 0],
        },
        {
            'file': r'C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive\content\levels\Cliff.zip',
            'name': 'Cliff',
            'pos': [0, 4000, 0],
        },
    ]

    has_terrain = False

    main_json = jbeam.Jbeam()

    f = FileManager()
    for merge_map in merge_maps:
        f.reset()

        map_prefix = merge_map['name'] + '_'
        main_name = map_prefix + 'map'

        main_json.lines.append({
            "name": main_name,
            "class": "SimGroup",
            "persistentId": jbeam.create_persistent_id(),
            "__parent": "maps",
        })

        if 'file' in merge_map:
            f.load_zip(merge_map['file'])

        material_str = 'materials.json'

        forest_str = 'forest4.json'
        forestbrushes_str = 'forestbrushes4.json'

        new_art_folder = os.path.join(base_map_path, 'levels', base_map_name, 'art', merge_map['name'])
        new_forest_folder = os.path.join(base_map_path, 'levels', base_map_name, 'forest', merge_map['name'])

        for filename in f.files.keys():
            norm_filename = ntpath.normpath(filename)

            map_str = os.path.join('levels', merge_map['name'] + os.sep)
            mission_group_str = os.path.join(map_str, 'main', 'MissionGroup' + os.sep)

            forest_managed_data_str = os.path.join(map_str, 'art', 'forest', 'managedItemData.cs')

            # is main object
            if norm_filename.startswith(mission_group_str):

                new_filepath = norm_filename[len(mission_group_str):]
                new_dir_path = os.path.dirname(new_filepath)
                if new_dir_path != '':
                    new_dir_path = os.sep.join(map(lambda x: map_prefix + x, new_dir_path.split(os.sep)))
                    new_filepath = os.path.join(new_dir_path, os.path.basename(new_filepath))

                j = jbeam.load(f.read_file(filename).decode('utf-8'))
                for i in reversed(range(len(j.lines))):
                    line = j.lines[i]

                    if line['class'] == 'TerrainBlock':
                        if has_terrain:
                            j.lines.pop(i)
                            continue
                        else:
                            has_terrain = True

                    if line['class'] not in ['SimGroup', 'WaterPlane'] and 'position' not in line:
                        line['position'] = [0, 0, 0]
                    if 'position' in line:
                        line['position'][0] += merge_map['pos'][0]
                        line['position'][1] += merge_map['pos'][1]
                        line['position'][2] += merge_map['pos'][2]

                    if 'nodes' in line:
                        for i in range(len(line['nodes'])):
                            line['nodes'][i][0] += merge_map['pos'][0]
                            line['nodes'][i][1] += merge_map['pos'][1]
                            line['nodes'][i][2] += merge_map['pos'][2]

                    if '__parent' in line:
                        if line['__parent'] == 'MissionGroup':
                            line['__parent'] = main_name
                        else:
                            line['__parent'] = map_prefix + line['__parent']
                    if 'name' in line:
                        line['name'] = map_prefix + line['name']

                f.write_file(filename, j.tostring().encode('utf-8'))

                f.save_file(
                    filename,
                    os.path.join(base_map_path, 'levels', base_map_name, 'main', 'MissionGroup', 'maps', main_name),
                    new_filepath,
                )

            # is materials file
            elif norm_filename.endswith(material_str):
                j = jbeam.load(f.read_file(filename).decode('utf-8'))
                fix_absolute_paths(j.lines, norm_filename)
                f.write_file(filename, j.tostring().encode('utf-8'))
                f.save_file(
                    filename,
                    new_art_folder,
                    norm_filename[len(map_str):],
                )

            # is forest managed data
            elif norm_filename == forest_managed_data_str:
                f.save_file(
                    filename,
                    new_art_folder,
                    norm_filename[len(map_str):],
                )

            # forest data
            elif norm_filename.endswith(forest_str) or norm_filename.endswith(forestbrushes_str):
                j = jbeam.load(f.read_file(filename).decode('utf-8'))
                for line in j.lines:
                    if 'pos' in line:
                        line['pos'][0] += merge_map['pos'][0]
                        line['pos'][1] += merge_map['pos'][1]
                        line['pos'][2] += merge_map['pos'][2]
                f.write_file(filename, j.tostring().encode('utf-8'))
                f.save_file(
                    filename,
                    new_forest_folder,
                    norm_filename[len(map_str):],
                )

    f.reset()
    main_path = os.path.join('main', 'MissionGroup', 'maps', 'items.level.json')
    f.write_file(main_path, main_json.tostring().encode('utf-8'))

    f.save_file(
        main_path,
        os.path.join(base_map_path, 'levels', base_map_name),
        main_path,
    )


if __name__ == '__main__':
    main()
