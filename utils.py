from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys

import numpy as np
from six.moves.urllib.request import urlretrieve

import common

url = 'https://catalog.ldc.upenn.edu/desc/addenda/'
last_percent_reported = None


def download_progress_hook(count, blockSize, totalSize):
    """A hook to report the progress of a download. This is mostly intended for
    users with slow internet connections. Reports every 1% change in download
    progress.
    """
    global last_percent_reported
    percent = int(count * blockSize * 100 / totalSize)

    if last_percent_reported != percent:
        if percent % 5 == 0:
            sys.stdout.write("%s%%" % percent)
            sys.stdout.flush()
        else:
            sys.stdout.write(".")
            sys.stdout.flush()

        last_percent_reported = percent


def maybe_download(filename, expected_bytes, force=False):
    """Download a file if not present, and make sure it's the right size."""
    if force or not os.path.exists(filename):
        print('Attempting to download:', filename)
        filename, _ = urlretrieve(url + filename, filename,
                                  reporthook=download_progress_hook)
        print('\nDownload Complete!')
    statinfo = os.stat(filename)

    if statinfo.st_size == expected_bytes:
        print('Found and verified', filename)
    else:
        raise Exception(
            'Failed to verify ' + filename + \
            '. Can you get to it with a browser?')
    return filename


def create_folder_if_not_exist(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


def sparse_tuple_from(sequences, dtype=np.int32):
    """Create a sparse representention of x.
    Args:
        sequences: a list of lists of type dtype where each element is a sequence
    Returns:
        A tuple with (indices, values, shape)
    """
    indices = []
    values = []

    for n, seq in enumerate(sequences):
        indices.extend(zip([n] * len(seq), range(len(seq))))
        values.extend(seq)

    indices = np.asarray(indices, dtype=np.int64)
    values = np.asarray(values, dtype=dtype)
    shape = np.asarray([len(sequences), np.asarray(indices).max(0)[1] + 1], dtype=np.int64)

    return indices, values, shape


# load the training or test dataset from disk
def get_data_set(dirname, start_index=None, end_index=None):
    # start = time.time()
    inputs, codes = common.unzip(list(common.read_data_for_lstm_ctc(dirname, start_index, end_index)))
    # print("unzip time",time.time() - start )
    inputs = inputs.swapaxes(1, 2)

    # print(dirname, ' inputs.shape', inputs.shape)
    # print(dirname, " codes", codes)
    targets = [np.asarray(i) for i in codes]
    # print("targets", targets)
    # print("train_inputs.shape[1]", train_inputs.shape[1])
    # Creating sparse representation to feed the placeholder
    # print("tttt", targets)
    sparse_targets = sparse_tuple_from(targets)
    # print(train_targets)
    seq_len = np.ones(inputs.shape[0]) * common.OUTPUT_SHAPE[1]
    # print(train_seq_len.shape)
    # We don't have a validation dataset :(
    return inputs, sparse_targets, seq_len


def decode_a_seq(indexes, spars_tensor):
    decoded = []
    for m in indexes:
        str_seq = common.DIGITS[spars_tensor[1][m] - 1]
        decoded.append(str_seq)
    # Replacing blank label to none
    # str_decoded = str_decoded.replace(chr(ord('9') + 1), '')
    # Replacing space label to space
    # str_decoded = str_decoded.replace(chr(ord('0') - 1), ' ')
    # print("ffffffff", str_decoded)
    return decoded


def decode_sparse_tensor(sparse_tensor):
    print("sparse_tensor = ", sparse_tensor)
    decoded_indexes = list()
    current_i = 0
    current_seq = []
    for offset, i_and_index in enumerate(sparse_tensor[0]):
        i = i_and_index[0]
        if i != current_i:
            decoded_indexes.append(current_seq)
            current_i = i
            current_seq = list()
        current_seq.append(offset)
    decoded_indexes.append(current_seq)
    print("decoded_indexes = ", decoded_indexes)
    result = []
    for index in decoded_indexes:
        # print("index = ", index)
        result.append(decode_a_seq(index, sparse_tensor))
    # print(result)
    return result
