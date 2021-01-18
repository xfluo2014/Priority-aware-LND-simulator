import os
import errno
import pathlib
import json

def ensure_directory_exists(base_directory):
    try:
        os.makedirs(base_directory)
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise ex

def load_dqn_weights_if_exist(i,dqn, weights_filename_prefix, weights_filename_extension=".h5"):
    # TODO should not work if only some weights available?
    dqn_filename = weights_filename_prefix + str(i) + weights_filename_extension
    if os.path.isfile(dqn_filename):
        print("Found old weights to use for agent {}".format(i))
        dqn.load(dqn_filename)

def save_dqn_weights(i, dqn, weights_filename_prefix, weights_filename_extension=".h5"):
    """
    Saves weights
    """
    p = pathlib.Path(weights_filename_prefix)
    if len(p.parts) > 1:
        dump_dirs = pathlib.Path(*p.parts[:-1])
        ensure_directory_exists(str(dump_dirs))
    dqn_filename = weights_filename_prefix + str(i) + weights_filename_extension
    dqn.save(dqn_filename)

    
#To record payment info for each payer
def record_pay_info():
	raise NotImplementedError()

#To display the statistics of payments
def pay_statistics():
	raise NotImplementedError()