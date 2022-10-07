import math

import cv2
import numpy as np

MAX_HEIGHT_BYTES = 65535
DEBUG = True


class Terrain:
    byte_read_offset = 0
    position = (0, 0, 0)
    square_size = 1
    max_height = 1
    version = 0
    size = 0
    layers = [
        np.array([], dtype=np.ushort),  # height map
        np.array([], dtype=np.ubyte),  # layer map
        np.array([], dtype=np.ubyte),  # layer texture map
        np.array([], dtype=np.ubyte),
        np.array([], dtype=np.ubyte),
        np.array([], dtype=np.ubyte),
    ]
    layer_names = []

    def load(self,
             data,
             position=(0, 0, 0),
             square_size=1,
             max_height=None,
             layer_names_prefix=''):
        if position[0] % 1 != 0 or position[1] % 1 != 0:
            raise RuntimeError('uneven position not possible: {}'.format(position))

        self.position = position
        self.square_size = square_size
        self.byte_read_offset = 0
        self.version = self.load_byte(data)
        self.size = self.load_uint(data)
        if max_height is None:
            self.max_height = self.size
        else:
            self.max_height = max_height

        print(position, square_size, max_height, self.size)

        square = self.size * self.size
        self.layers = [
            self.load_ushort_array(data, square).reshape(-1, self.size),  # height map
            self.load_byte_array(data, square).reshape(-1, self.size),  # layer map
            self.load_byte_array(data, square).reshape(-1, self.size),  # layer texture map
            self.load_byte_array(data, square).reshape(-1, self.size),
            self.load_byte_array(data, square).reshape(-1, self.size),
            self.load_byte_array(data, square).reshape(-1, self.size),
        ]
        self.layer_names = [layer_names_prefix + x for x in self.load_string_list(data)]
        return self

    def save(self):
        data = np.array(self.version, dtype=np.uint8).tobytes() + np.array(self.size, dtype=np.uint32).tobytes()
        for layer in self.layers:
            data += layer.reshape(-1).tobytes()
        data += np.array(len(self.layer_names), dtype=np.int32).tobytes()
        for name in self.layer_names:
            data += np.array(len(name), dtype=np.uint8).tobytes()
            data += np.array(name.encode('utf-8'), dtype='S'+str(len(name))).tobytes()
        return data

    def set_square_size(self, square_size):
        if square_size <= 0:
            return self
        self.size = int(self.size * self.square_size / square_size)
        self.square_size = square_size
        for i in range(6):
            self.layers[i] = cv2.resize(self.layers[i], (self.size, self.size), interpolation=cv2.INTER_AREA)
        return self

    @staticmethod
    def merge(terrain1: 'Terrain', terrain2: 'Terrain', scale=1) -> 'Terrain':
        t = Terrain()
        t.position = [min(terrain1.position[i], terrain2.position[i]) for i in range(3)]

        if scale > 0:
            t.square_size = scale
        else:
            t.square_size = min(terrain1.square_size, terrain2.square_size)
        t_square_size_rep = 1 / t.square_size

        terrain1_new_position = [int(terrain1.position[i] - t.position[i]) for i in range(3)]
        terrain2_new_position = [int(terrain2.position[i] - t.position[i]) for i in range(3)]

        for i in range(2):
            terrain1_new_position[i] = int(terrain1_new_position[i] * t_square_size_rep)
            terrain2_new_position[i] = int(terrain2_new_position[i] * t_square_size_rep)

        terrain1_norm_size = int(terrain1.size * terrain1.square_size)
        terrain2_norm_size = int(terrain2.size * terrain2.square_size)

        t.version = terrain1.version
        t.size = math.ceil(max(
            terrain1_new_position[0] + terrain1_norm_size,
            terrain1_new_position[1] + terrain1_norm_size,
            terrain2_new_position[0] + terrain2_norm_size,
            terrain2_new_position[1] + terrain2_norm_size,
        ) * t_square_size_rep)

        t.size = 1 << (t.size - 1).bit_length()

        for i in range(len(t.layers)):
            t.layers[i].resize((t.size, t.size), refcheck=False)

        t.max_height = max(
            terrain1_new_position[2] + terrain1.max_height,
            terrain2_new_position[2] + terrain2.max_height,
        )
        # t.max_height = t.size

        t.layer_names = terrain1.layer_names + terrain2.layer_names

        terrain1_new_size = int(terrain1_norm_size * t_square_size_rep)
        terrain2_new_size = int(terrain2_norm_size * t_square_size_rep)

        new_terrain1_layers = []
        new_terrain2_layers = []
        for i in range(6):
            new_terrain1_layers.append(
                cv2.resize(terrain1.layers[i], (terrain1_new_size, terrain1_new_size), interpolation=cv2.INTER_AREA)
            )
            new_terrain2_layers.append(
                cv2.resize(terrain2.layers[i], (terrain2_new_size, terrain2_new_size), interpolation=cv2.INTER_AREA)
            )

        terrain1_height_adjust = terrain1.max_height / t.max_height
        terrain1_height_offset = (terrain1_new_position[2] / t.max_height) * MAX_HEIGHT_BYTES

        terrain2_height_adjust = terrain2.max_height / t.max_height
        terrain2_height_offset = (terrain2_new_position[2] / t.max_height) * MAX_HEIGHT_BYTES

        new_terrain1_layers[0] = new_terrain1_layers[0] * terrain1_height_adjust + terrain1_height_offset
        new_terrain2_layers[0] = new_terrain2_layers[0] * terrain2_height_adjust + terrain2_height_offset

        for i in range(1, 6):
            new_terrain2_layers[i] += len(terrain1.layer_names)

        overlap_lx = max(terrain1_new_position[0], terrain2_new_position[0])
        overlap_ly = max(terrain1_new_position[1], terrain2_new_position[1])
        overlap_rx = min(terrain1_new_position[0] + terrain1_new_size, terrain2_new_position[0] + terrain2_new_size)
        overlap_ry = min(terrain1_new_position[1] + terrain1_new_size, terrain2_new_position[1] + terrain2_new_size)

        picked = np.full((t.size, t.size), 0, dtype=np.ubyte)
        picked[
            terrain1_new_position[1]:terrain1_new_position[1] + terrain1_new_size,
            terrain1_new_position[0]:terrain1_new_position[0] + terrain1_new_size,
        ] = 1
        picked[
            terrain2_new_position[1]:terrain2_new_position[1] + terrain1_new_size,
            terrain2_new_position[0]:terrain2_new_position[0] + terrain1_new_size,
        ] = 2
        picked[overlap_ly:overlap_ry, overlap_lx:overlap_rx][
            new_terrain1_layers[0][
                overlap_ly - terrain1_new_position[1]:overlap_ry - terrain1_new_position[1],
                overlap_lx - terrain1_new_position[0]:overlap_rx - terrain1_new_position[0],
            ] >
            new_terrain2_layers[0][
                overlap_ly - terrain2_new_position[1]:overlap_ry - terrain2_new_position[1],
                overlap_lx - terrain2_new_position[0]:overlap_rx - terrain2_new_position[0],
            ]
        ] = 1

        for i in range(6):
            t.layers[i][
                terrain1_new_position[1]:terrain1_new_position[1] + terrain1_new_size,
                terrain1_new_position[0]:terrain1_new_position[0] + terrain1_new_size,
            ] = np.where(
                picked[
                      terrain1_new_position[1]:terrain1_new_position[1] + terrain1_new_size,
                      terrain1_new_position[0]:terrain1_new_position[0] + terrain1_new_size
                ] == 1,
                new_terrain1_layers[i],
                t.layers[i][
                    terrain1_new_position[1]:terrain1_new_position[1] + terrain1_new_size,
                    terrain1_new_position[0]:terrain1_new_position[0] + terrain1_new_size,
                ]
            )

            t.layers[i][
                terrain2_new_position[1]:terrain2_new_position[1] + terrain2_new_size,
                terrain2_new_position[0]:terrain2_new_position[0] + terrain2_new_size,
            ] = np.where(
                picked[
                    terrain2_new_position[1]:terrain2_new_position[1] + terrain2_new_size,
                    terrain2_new_position[0]:terrain2_new_position[0] + terrain2_new_size
                ] == 2,
                new_terrain2_layers[i],
                t.layers[i][
                    terrain2_new_position[1]:terrain2_new_position[1] + terrain2_new_size,
                    terrain2_new_position[0]:terrain2_new_position[0] + terrain2_new_size,
                ]
            )

        if DEBUG:
            debug = np.full((t.size, t.size, 3), (0, 0, 0), dtype=np.uint8)

            debug[picked == 1] = (255, 0, 0)
            debug[picked == 2] = (0, 0, 255)

            cv2.imshow('picked', cv2.resize(debug, (512, 512)))

            debug = t.layers[0] / MAX_HEIGHT_BYTES

            cv2.imshow('heights', cv2.resize(debug, (512, 512)))
            cv2.waitKey(0)

        return t

    def load_byte(self, data):
        t = np.frombuffer(data, dtype=np.uint8, count=1, offset=self.byte_read_offset)[0]
        self.byte_read_offset += 1
        return t

    def load_uint(self, data):
        t = np.frombuffer(data, dtype=np.uint32, count=1, offset=self.byte_read_offset)[0]
        self.byte_read_offset += 4
        return t

    def load_string_list(self, data):
        layer_names_len = np.frombuffer(data, dtype=np.int32, count=1, offset=self.byte_read_offset)[0]
        self.byte_read_offset += 4
        layer_names = []
        for i in range(layer_names_len):
            string_len = np.frombuffer(data, dtype=np.uint8, count=1, offset=self.byte_read_offset)[0]
            self.byte_read_offset += 1
            layer_names.append(
                np.frombuffer(
                    data,
                    dtype='S'+str(string_len),
                    count=1,
                    offset=self.byte_read_offset)[0].decode('utf-8')
            )
            self.byte_read_offset += string_len
        return layer_names

    def load_ushort_array(self, data, size):
        t = np.frombuffer(data, dtype=np.uint16, count=size, offset=self.byte_read_offset)
        self.byte_read_offset += 2 * size
        return t

    def load_byte_array(self, data, size):
        t = np.frombuffer(data, dtype=np.uint8, count=size, offset=self.byte_read_offset)
        self.byte_read_offset += 1 * size
        return t


def main():
    t = Terrain()
    with open(
            r'F:\BeamModding\test\west_coast_usa\west_coast_usa2.ter',
            'rb'
    ) as f:
        t.load(f.read())
    with open(
            r'F:\BeamModding\test\west_coast_usa\west_coast_usa.ter',
            'wb'
    ) as f:
        f.write(t.save())


if __name__ == '__main__':
    main()
