import os


def get_path_from_root(*args):
    dname = os.path.dirname(os.path.abspath(__file__))  # wb_cleaning
    dname = os.path.dirname(dname)  # src
    dname = os.path.dirname(dname)  # wb_cleaning

    return os.path.join(dname, *args)


def get_data_dir(*args):
    return get_path_from_root('data', *args)


def get_configs_dir(*args):
    return get_path_from_root('configs', *args)


def get_txt_data_dir(corpus_id, text_type):
    if text_type == 'CLEAN':
        path = 'preprocessed'
    elif text_type == 'ORIG':
        path = 'raw'
    else:
        raise ValueError(
            f'Unexpected `text_type` {text_type}. Accepted values: `CLEAN` and `ORIG`...')

    return get_data_dir(path, 'text', corpus_id)
