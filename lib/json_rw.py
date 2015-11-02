'''
    json_rw
    -------

    Read/write json files. Basic usage:

        >>> from lib.json_rw import json_rw
        >>> json_data = json_rw.json_get_data('file.json')
        >>> json_rw.json_write_data(json_data, 'file.json')

'''


import json


class json_rw(object):
    """
    Read and write json files.
    """

    def json_write_data(json_data, filename):
        """Write json data into a file
        """
        with open(filename, 'w') as fp:
            json.dump(json_data, fp, indent=4,
                      sort_keys=True,
                      ensure_ascii=False)
            return True
        return False

    def json_get_data(filename):
        """Get data from json file
        """
        with open(filename, 'r') as fp:
            json_data = json.load(fp)
            return json_data
        return False


