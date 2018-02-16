import numpy as np
from cython_modules.cython_parse import getLayerOutline
from multiprocessing import Pool
import scipy.signal

class ColorPolicy:
    def __init__(self):
        self.data_structure = 'flattened_array'
        self._DATA_STRUCTURE_TYPES = ['flattened_array', 'interleaved_array',
                                      'tensor_array']
        self.averaging_kernel = None
        self.flat_av_kernel = None

        self.kernel_size = self.set_kernel_size(3)

    def set_kernel_size(self, kernel_size):
        """
        adjusts the kernel size for a specific array
        This function does not return anything, it sets kernels for
        Color Policy object
        :param kernel_size: is the target kernel size for an array
        """
        self.kernel_size = kernel_size
        self.averaging_kernel = np.ones((self.kernel_size,
                                    self.kernel_size))*(1/(self.kernel_size**2))
        self.flat_av_kernel = np.ravel(
                            np.ones((self.kernel_size, 1))*(1/self.kernel_size))

    def averaging_policy(self, color_matrix, vector_matrix=None, av_scale=3):
        """
        this function applies the averaging kernel and then samples
        the matrices to return averaged vector
        if no vector matrix is provided, only color_matrix is transformed as if
        it was a vector_matrix
        :param color_matrix: maps color on vector_matrix should be of size N*(k,m)
        where N is number of iterations and (k,m) is vector matrix size
        :param vector_matrix: has shape (k,m) or linear m = 1
        :param av_scale: specifies how much averaging is done
        :return color_matrix: returns averaged matrix
        :return vector_matrix: if vector matrix is given, its size is adjusted
        and new matrix is returned
        """
        self.kernel_size = self.set_kernel_size(av_scale)
        # firstly average the color matrix with kernel
        color_matrix = self.linear_convolution(color_matrix)
        # now take every nth element from both
        color_matrix = np.array([color[::av_scale] for color in color_matrix])
        if vector_matrix:
            vector_matrix = vector_matrix[::av_scale]
            return color_matrix, vector_matrix
        else:
            return color_matrix

    def sampling_policy(self, x_dim, y_dim, prob_x):
        """
        this function samples the array
        """
        return np.random.choice([True, False], (x_dim, y_dim),
                p=[prob_x, 1-prob_x])

    def linear_convolution(self, matrix):
        """
        performs the linear convlolution on color data given the kernel
        that is defaulted in a Color Policy object upon which the function calls
        :param matrix: matrix to be convoluted
        :return new_color_matrix: returns new color matrix
        """
        pool = Pool()
        multiple_results = [pool.apply_async(self.composite_convolution,
                            (np.array(m), self.flat_av_kernel))
                            for m in matrix]
        new_color_matrix = []
        for result in multiple_results:
            convolved_array = result.get(timeout=20)
            new_color_matrix.append(convolved_array)
        return new_color_matrix

    def composite_convolution(self, composite_matrix, kernel):
        """
        performs composite convolution, uses atomic convolutions
        on a composite matrix
        Note that composite matrix is 2D matrix
        :param composite_matrix: matrix to be convoluted
        :param kernel: kernel that is used during convolution
        :return resultant_matrix: returns convolved complex matrix
        """
        resultant_matrix = np.zeros(composite_matrix.shape)
        for i in range(3):
            resultant_matrix[:, i] = self.atomic_convolution(
                                                composite_matrix[:, i], kernel)
        return resultant_matrix

    def atomic_convolution(self, vecA, vecB):
        """
        convolves simply two vectors
        :param vecA: vector 1
        :param vecB: vector 2
        :return convolution result
        """
        return np.convolve(vecA, vecB, 'same')

    def apply_normalization(self, color_array, xc, yc, zc):
        """
        normalizes a large input color_array to unit vectors
        :param color_array: to be normalized, numpy array
        :param xc: nodes in x direction
        :param yc: nodes in y direction
        :parac zc: nodes in z direction
        """
        pool = Pool()
        multiple_results = [pool.apply_async(
                            self.atomic_normalization,
                            (color_array[i], xc, yc, zc))
                            for i in range(len(color_array))]
        color_array = [result.get(timeout=12) for result
                            in multiple_results]
        return color_array

    def atomic_normalization(self, color_array, xc, yc, zc):
        """
        performs unit normalization on tiny arrays
        :param xc: nodes in x direction
        :param yc: nodes in y direction
        :parac zc: nodes in z direction
        """
        normalized_color_array = np.array([x/np.linalg.norm(x)
                        if x.any() else [0.0,0.0,0.0] for x in color_array])\
                            .reshape(xc*yc*zc, 3)
        return normalized_color_array

    def apply_vbo_format(self, color_array):
        """
        transforms a given numpy array matrix representing vecotrs in space
        into linear vbo matrix - to fit vertex buffer object
        :param color_array: to be transformed, numpy array
        """
        pool = Pool()
        multiple_results = [pool.apply_async(self.color_matrix_flatten,
                                                (p, 24)) for p in color_array]
        new_color_matrix = []
        for result in multiple_results:
            repeated_array = result.get(timeout=20)
            new_color_matrix.append(repeated_array)
        return new_color_matrix

    def color_matrix_flatten(self, vector, times):
        return np.repeat(vector, times, axis=0).flatten()

    def normalize_flatten_dot_product(self, vector):
        pass

    def apply_dot_product(self, color_array, omf_header):
        layer_outline = getLayerOutline(omf_header)
        pool = Pool()
        color_results = [pool.apply_async(
                                ColorPolicy.compose_arrow_interleaved_array,
                                          (color_iteration, layer_outline))
                         for color_iteration in color_array]
        new_color_matrix = []
        for result in color_results:
            interleaved = result.get(timeout=20)
            new_color_matrix.append(interleaved)
        return new_color_matrix

    @staticmethod
    def atomic_dot_product(color_vector, relative_vector_set):
        return [np.dot(color_vector, vector) for vector in relative_vector_set]

    @staticmethod
    def compose_arrow_interleaved_array(raw_vector_data, layer_outline):
        """
        this function would create the interleaved array for arrow objects i.e.
        start_vertex, stop_vertex, colorR, colorG, colorB
        :param raw_vector_data: is one iteration, matrix of colors
        :param layer_outline: is layer outline for color mask
        :return: interleaved array, array with vertices and colors interleaved
        """
        interleaved_array = []
        # get start_vertex array
        rel_set = [[1, 1, 0], [-1, 0, 1], [0, 1, 0]]
        for vector_begin, vector_tip in zip(layer_outline, raw_vector_data):
            if vector_tip.any():
                vector_tip /= np.linalg.norm(vector_tip)
                vector_begin /= np.linalg.norm(vector_begin)
                color_type = ColorPolicy.atomic_dot_product(vector_tip,
                                                relative_vector_set=rel_set)
            else:
                color_type = [0,0,0]
            interleaved_array.extend([*vector_begin, *vector_tip, *color_type])
        return interleaved_array
