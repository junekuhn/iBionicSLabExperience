import json
import os
import sys

import util.Logger as Logger

default_json_template = {'dog_id': None, 'creation_date': None, 'dog_size': None,
                         'phase_1': {'level_1': None},
                         'phase_2': {'level_1': None, 'level_2': None, 'level_3': None, 'level_4': None},
                         'phase_3': {'level_1': None, 'level_2': None, 'level_3': None, 'level_4': None,
                                     'level_5': None, 'level_6': None},
                         'phase_4': {'level_1': None, 'level_2': None, 'level_3': None, 'level_4': None,
                                     'level_5': None},
                         'phase_5': {'level_1': None, 'level_1D': None, 'level_2': None, 'level_2D': None,
                                     'level_3D': None, 'level_4D': None, 'level_5D': None, 'level_6D': None,
                                     'level_7D': None, 'level_8D': None, 'level_9D': None}}


def get_file_path(dog_id):
    """
    Get the file where we stored a dogs saved progress
    :param dog_id:
    :return: File
    """
    if not os.path.exists(os.path.join(sys.path[0], "dogs")):
        os.makedirs(os.path.join(sys.path[0], "dogs"))
    return os.path.join(sys.path[0], "dogs", str(dog_id) + '.json')


def save(dog_id, phase, level):
    file_path = get_file_path(dog_id)
    if not os.path.isfile(file_path):
        create_new_file(dog_id)

    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
        data["phase_%s" % phase]["level_%s" % level] = Logger.timestamp()

    os.remove(file_path)
    with open(file_path, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)


def save_size(dog_id, dog_size):
    file_path = get_file_path(dog_id)
    if not os.path.isfile(file_path):
        create_new_file(dog_id)

    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
        data["dog_size"] = dog_size

    os.remove(file_path)
    with open(file_path, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)


def load(dog_id):
    """
    Load a dogs information from the file system
    :param dog_id:
    :return: a JSON representation of the dogs data
    """
    file_path = get_file_path(dog_id)
    if not os.path.exists(file_path):
        create_new_file(dog_id)

    with open(file_path, 'r') as json_file:
        return json.load(json_file)


def create_new_file(dog_id):
    if os.path.isfile(get_file_path(dog_id)):  # Check if the file already exists
        return
    newdog = dict(default_json_template)  # Make a copy of the default template
    newdog['dog_id'] = dog_id
    newdog['creation_date'] = Logger.timestamp()

    with open(get_file_path(dog_id), 'w') as outfile:
        json.dump(newdog, outfile, indent=4, sort_keys=True)
