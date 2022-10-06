import os

import jbeam
from file_manager import FileManager
from terrain import Terrain
import ntpath
import cv2
import numpy as np

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
    import shutil

    for p in [
        r'C:\Users\jack-\AppData\Local\BeamNG.drive\0.26\mods\unpacked\allmap\levels\allmap\main\MissionGroup',
        r'C:\Users\jack-\AppData\Local\BeamNG.drive\0.26\mods\unpacked\allmap\levels\allmap\forest',
        r'C:\Users\jack-\AppData\Local\BeamNG.drive\0.26\mods\unpacked\allmap\levels\allmap\art',
    ]:
        shutil.rmtree(p, ignore_errors=True)

    base_map_path = r'C:\Users\jack-\AppData\Local\BeamNG.drive\0.26\mods\unpacked\allmap'
    base_map_name = 'allmap'

    base_file_path = r'C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive\content\levels'

    objects_path = ('main', 'MissionGroup')

    merge_maps = [
        # {
        #     'name': 'automation_test_track',
        #     'pos': [-0.25, -0.25, -1],
        # },
        # {
        #     'name': 'Cliff',
        #     'pos': [0, 2048, 0],
        # },
        # {
        #     'name': 'derby',
        #     'pos': [0, 0, 0],
        # },
        # {
        #     'name': 'driver_training',
        #     'pos': [-0.5, -0.5, 0],
        # },
        {
            'name': 'east_coast_usa',
            'pos': [4096, 0, 71],
        },
        # {
        #     'name': 'gridmap_v2',
        #     'pos': [2047.5, -0.5, 0],
        # },
        # {
        #     'name': 'hirochi_raceway',
        #     'pos': [-0.375, -0.375, 0],
        # },
        # {
        #     'name': 'Industrial',
        #     'pos': [0, 0, 0],
        # },
        # {
        #     'name': 'italy',
        #     'pos': [0, 0, 0],
        # },
        # {
        #     'name': 'jungle_rock_island',
        #     'pos': [0, 0, 0],
        # },
        # {
        #     'name': 'small_island',
        #     'pos': [0, 0, 0],
        # },
        # {
        #     'name': 'Utah',
        #     'pos': [0, 0, 0],
        # },
        {
            'name': 'west_coast_usa',
            'pos': [-0.5, -0.5, 0],
        },
    ]

    base_tex_size = [2048, 2048]

    build_new_terrain = True

    main_json = jbeam.Jbeam()

    terrain = None

    f = FileManager()
    for merge_map in merge_maps:
        f.reset()

        if 'file' not in merge_map:
            merge_map['file'] = os.path.join(base_file_path, merge_map['name'] + '.zip')

        keep_terrain_textures = []
        switch_terrain_textures = []

        map_prefix = merge_map['name'] + '_'
        main_name = map_prefix + 'map'

        print('merging', merge_map['name'], '...')

        main_json.lines.append({
            "name": main_name,
            "class": "SimGroup",
            "persistentId": jbeam.create_persistent_id(),
            "__parent": objects_path[-1],
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
            mission_group_str = os.path.join(map_str, *objects_path) + os.sep

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

                    if line['class'] not in ['SimGroup', 'WaterPlane'] and 'position' not in line:
                        line['position'] = [0, 0, 0]
                    if 'position' in line:
                        line['position'][0] += merge_map['pos'][0]
                        line['position'][1] += merge_map['pos'][1]
                        line['position'][2] += merge_map['pos'][2]

                    if build_new_terrain and line['class'] == 'TerrainBlock':
                        tf = line['terrainFile']
                        if tf[0] == '/':
                            tf = tf[1:]

                        kwargs = {'layer_names_prefix': map_prefix}
                        if 'position' in line:
                            kwargs['position'] = line['position']
                        if 'squareSize' in line:
                            kwargs['square_size'] = line['squareSize']
                        if 'maxHeight' in line:
                            kwargs['max_height'] = line['maxHeight']
                        if terrain is None:
                            terrain = Terrain().load(
                                f.get_file_content(tf),
                                **kwargs
                            )
                        else:
                            terrain = Terrain.merge(
                                terrain,
                                Terrain().load(
                                    f.get_file_content(tf),
                                    **kwargs
                                ),
                                downscale=True,
                            )

                        del j.lines[i]

                    if 'nodes' in line:
                        for i2 in range(len(line['nodes'])):
                            line['nodes'][i2][0] += merge_map['pos'][0]
                            line['nodes'][i2][1] += merge_map['pos'][1]
                            line['nodes'][i2][2] += merge_map['pos'][2]

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
                    os.path.join(base_map_path, 'levels', base_map_name, *objects_path, main_name),
                    new_filepath,
                )

            # is materials file
            elif norm_filename.endswith(material_str):
                j = jbeam.load(f.read_file(filename).decode('utf-8'))
                fix_absolute_paths(j.lines, norm_filename)
                for i in range(len(j.lines)):
                    if build_new_terrain:
                        for k, v in j.lines[i].items():
                            if 'class' in v and v['class'] == 'TerrainMaterialTextureSet':
                                print(v)
                            for base_tex_name in [
                                'aoBaseTex',
                                'baseColorBaseTex',
                                'heightBaseTex',
                                'normalBaseTex',
                                'roughnessBaseTex',
                            ]:
                                if base_tex_name in v:
                                    tf = v[base_tex_name]
                                    if tf[0] == '/':
                                        tf = tf[1:]

                                    if tf not in keep_terrain_textures:

                                        new_tf = tf[len(map_str):]
                                        if new_tf[0] == '/':
                                            new_tf = new_tf[1:]

                                        if tf not in switch_terrain_textures:
                                            img = cv2.imdecode(np.frombuffer(f.read_file(tf), np.uint8), 1)
                                            if img.shape[0] == base_tex_size[0] and img.shape[1] == base_tex_size[1]:
                                                keep_terrain_textures.append(tf)
                                            else:
                                                switch_terrain_textures.append(tf)
                                                res = cv2.resize(img,
                                                                 dsize=(base_tex_size[0], base_tex_size[1]),
                                                                 interpolation=cv2.INTER_AREA)
                                                f.write_file(new_tf, cv2.imencode(new_tf, res)[1])
                                                f.save_file(
                                                    new_tf,
                                                    new_art_folder,
                                                    new_tf,
                                                )
                                                print('changing size:', new_tf)

                                        # change path
                                        j.lines[i][k][base_tex_name] = '/levels/' + base_map_name + '/art/' \
                                                                       + merge_map['name'] + '/' + new_tf

                            for name_value in [
                                # 'name',
                                'internalName',
                                'annotation',
                                # 'groundmodelName',
                                # 'groundType',
                            ]:
                                if name_value in v:
                                    j.lines[i][k][name_value] = map_prefix + v[name_value]
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

    if build_new_terrain:
        terrain_texture_set_name = base_map_name + 'TerrainTextureSet'

        terrain_texture_set_json = jbeam.Jbeam()
        terrain_texture_set_json.lines.append({
                terrain_texture_set_name: {
                    "name": terrain_texture_set_name,
                    "class": "TerrainMaterialTextureSet",
                    "persistentId": jbeam.create_persistent_id(),
                    "baseTexSize": base_tex_size,
                    "detailTexSize": [
                        1024,
                        1024,
                    ],
                    "macroTexSize": [
                        1024,
                        1024,
                    ]
                },
        })

        terrain_texture_set_json_path = 'art/main.materials.json'

        f.write_file(terrain_texture_set_json_path, terrain_texture_set_json.tostring().encode('utf-8'))
        f.save_file(
            terrain_texture_set_json_path,
            os.path.join(base_map_path, 'levels', base_map_name),
            terrain_texture_set_json_path,
        )

        terrain_path = 'levels/' + base_map_name + '/theTerrain.ter'

        main_json.lines.append({
            "name": "theTerrain",
            "class": "TerrainBlock",
            "persistentId": jbeam.create_persistent_id(),
            "__parent": objects_path[-1],
            "materialTextureSet": terrain_texture_set_name,
            "position": terrain.position,
            "squareSize": terrain.square_size,
            "maxHeight": terrain.max_height,
            "baseTexSize": terrain.max_height,
            "terrainFile": '/' + terrain_path,
        })

        terrain.save()

        f.write_file(terrain_path, terrain.data)
        f.save_file(
            terrain_path,
            base_map_path,
            terrain_path
        )

    main_path = os.path.join(*objects_path, 'items.level.json')

    f.write_file(main_path, main_json.tostring().encode('utf-8'))
    f.save_file(
        main_path,
        os.path.join(base_map_path, 'levels', base_map_name),
        main_path,
    )


if __name__ == '__main__':
    main()
