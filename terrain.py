import math
import struct

MAX_HEIGHT_BYTES = 65535


class Terrain:
    byte_read_offset = 0
    data = b''
    position = (0, 0, 0)
    square_size = 1
    max_height = 1
    version = 0
    size = 0
    layers = [
        [],  # height map
        [],  # layer map
        [],  # layer texture map
        [],
        [],
        [],
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

        self.data = data
        self.position = position
        self.square_size = square_size
        self.byte_read_offset = 0
        self.version = self.load_byte()
        self.size = self.load_uint()
        if max_height is None:
            self.max_height = self.size
        else:
            self.max_height = max_height

        print(position, square_size, max_height, self.size)

        square = self.size * self.size
        self.layers = [
            self.load_ushort_array(square),  # height map
            self.load_byte_array(square),  # layer map
            self.load_byte_array(square),  # layer texture map
            self.load_byte_array(square),
            self.load_byte_array(square),
            self.load_byte_array(square),
        ]
        self.layer_names = [layer_names_prefix + x for x in self.load_string_list()]
        return self

    def save(self):
        square = self.size * self.size
        data_struct = '=BI' + ('H' * square) + ('B' * square * 5) + 'i'
        data = [
                   self.version,
                   self.size
               ] + [
                   x for x in self.layers[0]
               ] + [
                   x for layer in self.layers[1:] for x in layer
               ] + [len(self.layer_names)]
        for name in self.layer_names:
            data_struct += 'B' + ('B' * len(name))
            data.append(len(name))
            data += [x for x in name.encode('utf-8')]
        self.data = struct.pack(data_struct, *data)
        return self.data

    @staticmethod
    def merge(terrain1: 'Terrain', terrain2: 'Terrain', downscale=1) -> 'Terrain':
        t = Terrain()
        t.position = [min(terrain1.position[i], terrain2.position[i]) for i in range(3)]
        terrain1_new_position = [terrain1.position[i] - t.position[i] for i in range(3)]
        terrain2_new_position = [terrain2.position[i] - t.position[i] for i in range(3)]

        if downscale > 0:
            t.square_size = downscale
        else:
            t.square_size = min(terrain1.square_size, terrain2.square_size)

        terrain1_norm_size = terrain1.size * terrain1.square_size
        terrain2_norm_size = terrain2.size * terrain2.square_size

        t.version = terrain1.version
        t.size = math.ceil(max(
            terrain1_new_position[0] + terrain1_norm_size,
            terrain1_new_position[1] + terrain1_norm_size,
            terrain2_new_position[0] + terrain2_norm_size,
            terrain2_new_position[1] + terrain2_norm_size,
        ) * (1 / t.square_size))

        t.size = 1 << (t.size - 1).bit_length()

        t.max_height = max(
            terrain1_new_position[2] + terrain1.max_height,
            terrain2_new_position[2] + terrain2.max_height,
        )
        # t.max_height = t.size
        new_square = t.size * t.size

        t.layer_names = terrain1.layer_names + terrain2.layer_names

        picked = [-1] * new_square

        t.layers[0] = [0] * new_square
        t.layers[1] = [0] * new_square
        t.layers[2] = [0] * new_square
        t.layers[3] = [0] * new_square
        t.layers[4] = [0] * new_square
        t.layers[5] = [0] * new_square

        terrain1_height_adjust = terrain1.max_height / t.max_height
        terrain1_height_offset = (terrain1_new_position[2] / t.max_height) * MAX_HEIGHT_BYTES
        terrain1_square_size_adjust = terrain1.square_size / t.square_size
        terrain1_square_size_adjust_rep = 1 / terrain1_square_size_adjust

        for y in range(int(terrain1.size * terrain1_square_size_adjust)):
            for x in range(int(terrain1.size * terrain1_square_size_adjust)):
                i = int(
                    (y + terrain1_new_position[1]) * t.size +
                    (x + terrain1_new_position[0])
                )
                t.layers[0][i] = int(terrain1.layers[0][int(
                    y * terrain1.size * terrain1_square_size_adjust_rep
                    + x * terrain1_square_size_adjust_rep
                )] * terrain1_height_adjust + terrain1_height_offset)
                picked[i] = 0

        terrain2_height_adjust = terrain2.max_height / t.max_height
        terrain2_height_offset = (terrain2_new_position[2] / t.max_height) * MAX_HEIGHT_BYTES
        terrain2_square_size_adjust = terrain2.square_size / t.square_size
        terrain2_square_size_adjust_rep = 1 / terrain2_square_size_adjust

        for y in range(int(terrain2.size * terrain2_square_size_adjust)):
            for x in range(int(terrain2.size * terrain2_square_size_adjust)):
                i = int(
                    (y + terrain2_new_position[1]) * t.size +
                    (x + terrain2_new_position[0])
                )
                d = int(terrain2.layers[0][int(
                    y * terrain2.size * terrain2_square_size_adjust_rep
                    + x * terrain2_square_size_adjust_rep
                )] * terrain2_height_adjust + terrain2_height_offset)
                if d > t.layers[0][i]:
                    t.layers[0][i] = d
                    picked[i] = 1

        for y in range(t.size):
            for x in range(t.size):
                new_i = y * t.size + x
                pick = picked[new_i]
                if pick == 0:
                    old_i = int(
                        (y - terrain1_new_position[1]) * terrain1.size * terrain1_square_size_adjust_rep +
                        (x - terrain1_new_position[0]) * terrain1_square_size_adjust_rep
                    )
                    t.layers[1][new_i] = terrain1.layers[1][old_i]
                    t.layers[2][new_i] = terrain1.layers[2][old_i]
                    t.layers[3][new_i] = terrain1.layers[3][old_i]
                    t.layers[4][new_i] = terrain1.layers[4][old_i]
                    t.layers[5][new_i] = terrain1.layers[5][old_i]
                elif pick == 1:
                    old_i = int(
                        (y - terrain2_new_position[1]) * terrain2.size * terrain2_square_size_adjust_rep +
                        (x - terrain2_new_position[0]) * terrain2_square_size_adjust_rep
                    )
                    t.layers[1][new_i] = min(255, terrain2.layers[1][old_i] + len(terrain1.layer_names))
                    t.layers[2][new_i] = min(255, terrain2.layers[2][old_i] + len(terrain1.layer_names))
                    t.layers[3][new_i] = min(255, terrain2.layers[3][old_i] + len(terrain1.layer_names))
                    t.layers[4][new_i] = min(255, terrain2.layers[4][old_i] + len(terrain1.layer_names))
                    t.layers[5][new_i] = min(255, terrain2.layers[5][old_i] + len(terrain1.layer_names))

        return t

    def load_byte(self):
        t = struct.unpack_from('B', self.data, offset=self.byte_read_offset)[0]
        self.byte_read_offset += 1
        return t

    def load_uint(self):
        t = struct.unpack_from('I', self.data, offset=self.byte_read_offset)[0]
        self.byte_read_offset += 4
        return t

    def load_string_list(self):
        layer_names_len = struct.unpack_from('i', self.data, offset=self.byte_read_offset)[0]
        self.byte_read_offset += 4
        layer_names = []
        for i in range(layer_names_len):
            string_len = struct.unpack_from('B', self.data, offset=self.byte_read_offset)[0]
            self.byte_read_offset += 1
            layer_names.append(
                b''.join(struct.unpack_from('c' * string_len, self.data, offset=self.byte_read_offset)).decode('utf-8')
            )
            self.byte_read_offset += string_len
        return layer_names

    def load_ushort_array(self, size):
        t = struct.unpack_from('H' * size, self.data, offset=self.byte_read_offset)
        self.byte_read_offset += 2 * size
        return t

    def load_byte_array(self, size):
        t = struct.unpack_from('B' * size, self.data, offset=self.byte_read_offset)
        self.byte_read_offset += 1 * size
        return t


def main():
    t = Terrain()
    with open(
            r'C:\Users\jack-\AppData\Local\BeamNG.drive\0.26\mods\unpacked\americanroad\levels\mymap\terenia24.ter',
            'rb'
    ) as f:
        t.load(f.read())


if __name__ == '__main__':
    main()
