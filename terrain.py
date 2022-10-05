import math
import struct


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
             max_height=None):
        print(position, square_size, max_height)
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
        square = self.size * self.size
        self.layers = [
            self.load_ushort_array(square),  # height map
            self.load_byte_array(square),  # layer map
            self.load_byte_array(square),  # layer texture map
            self.load_byte_array(square),
            self.load_byte_array(square),
            self.load_byte_array(square),
        ]
        self.layer_names = self.load_string_list()
        return self

    def save(self):
        square = self.size * self.size
        data_struct = '=cI' + ('H' * square) + ('c' * square * 5) + 'i'
        data = [
                   bytes([self.version]),
                   self.size
               ] + [
                   x for x in self.layers[0]
               ] + [
                   bytes([x]) for layer in self.layers[1:] for x in layer
               ] + [len(self.layer_names)]
        for name in self.layer_names:
            data_struct += 'c' + ('c' * len(name))
            data.append(bytes([len(name)]))
            data += [bytes([x]) for x in name.encode('utf-8')]
        self.data = struct.pack(data_struct, *data)
        return self.data

    def merge(self, terrain2: 'Terrain'):
        t = Terrain()
        t.position = [min(self.position[i], terrain2.position[i]) for i in range(3)]
        self_new_position = [self.position[i] - t.position[i] for i in range(3)]
        terrain2_new_position = [terrain2.position[i] - t.position[i] for i in range(3)]

        if self_new_position[2] != terrain2_new_position[2]:
            raise RuntimeError('merging heights not implemented yet')

        t.version = self.version
        t.size = math.ceil(max(
            self_new_position[0] + self.size,
            self_new_position[1] + self.size,
            terrain2_new_position[0] + terrain2.size,
            terrain2_new_position[1] + terrain2.size,
        ))
        t.size = 1 << (t.size - 1).bit_length()
        t.max_height = t.size
        new_square = t.size * t.size
        t.layer_names = self.layer_names + terrain2.layer_names

        picked = [-1] * new_square

        t.layers[0] = [0] * new_square
        t.layers[1] = [0] * new_square
        t.layers[2] = [0] * new_square
        t.layers[3] = [0] * new_square
        t.layers[4] = [0] * new_square
        t.layers[5] = [0] * new_square

        self_height_adjust = self.max_height / t.max_height
        for y in range(self.size):
            for x in range(self.size):
                i = int(
                    (y + self_new_position[1]) * t.size +
                    x + self_new_position[0]
                )
                t.layers[0][i] = int(self.layers[0][y * self.size + x] * self_height_adjust)
                picked[i] = 0

        terrain2_height_adjust = terrain2.max_height / t.max_height
        for y in range(terrain2.size):
            for x in range(terrain2.size):
                i = int(
                    (y + terrain2_new_position[1]) * t.size +
                    x + terrain2_new_position[0]
                )
                d = int(terrain2.layers[0][y * terrain2.size + x] * terrain2_height_adjust)
                if d > t.layers[0][i]:
                    t.layers[0][i] = d
                    picked[i] = 1

        for y in range(t.size):
            for x in range(t.size):
                new_i = y * t.size + x
                pick = picked[new_i]
                if pick == 0:
                    old_i = int(
                        (y - self_new_position[1]) * self.size +
                        (x - self_new_position[0])
                    )
                    t.layers[1][new_i] = self.layers[1][old_i]
                    t.layers[2][new_i] = self.layers[2][old_i]
                    t.layers[3][new_i] = self.layers[3][old_i]
                    t.layers[4][new_i] = self.layers[4][old_i]
                    t.layers[5][new_i] = self.layers[5][old_i]
                elif pick == 1:
                    old_i = int(
                        (y - terrain2_new_position[1]) * terrain2.size +
                        (x - terrain2_new_position[0])
                    )
                    t.layers[1][new_i] = terrain2.layers[1][old_i] + len(self.layer_names)
                    t.layers[2][new_i] = terrain2.layers[2][old_i] + len(self.layer_names)
                    t.layers[3][new_i] = terrain2.layers[3][old_i]
                    t.layers[4][new_i] = terrain2.layers[4][old_i]
                    t.layers[5][new_i] = terrain2.layers[5][old_i]

        t.save()

        return t

    def load_byte(self):
        t = struct.unpack_from('c', self.data, offset=self.byte_read_offset)[0][0]
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
            string_len = struct.unpack_from('c', self.data, offset=self.byte_read_offset)[0][0]
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
        t = [x[0] for x in struct.unpack_from('c' * size, self.data, offset=self.byte_read_offset)]
        self.byte_read_offset += 1 * size
        return t


if __name__ == '__main__':
    t = Terrain()
    with open(
            r'C:\Users\jack-\AppData\Local\BeamNG.drive\0.26\mods\unpacked\americanroad\levels\mymap\terenia24.ter',
            'rb'
    ) as f:
        t.load(f.read())
