from pathlib import Path
import json
import khquizgen as kh


def run(inputs_path=None, outputs_path=None):
    """
    Get the data and preprocess it appropriately
    """
    in_path = inputs_path if inputs_path else kh.INPUTS_PATH
    out_path = outputs_path if outputs_path else kh.OUTPUTS_PATH
    root = parse_q(get_raw_data(in_path))
    save_j_data(root, out_path)
    return root


def get_raw_data(in_path):
    """
    Get the data from the data.csv file inside the folder
    """
    in_file = Path.resolve(in_path.joinpath('questions.txt'))
    with open(in_file, 'r') as file:
        data = file.read()
    return data


def parse_q(raw_data: str):
    s_test = raw_data.splitlines()
    root, trunk_d, branch_d = {}, {}, {}
    trunk, branch, leaf = None, None, None
    for line in s_test:
        line = line.strip()
        if ':::' in line:

            if trunk:
                trunk_d[branch] = branch_d
                root[trunk] = trunk_d
                branch, leaf = None, None
                branch_d, trunk_d = {}, {}

            trunk = line.split(':::')[0].strip()

        elif '::' in line:
            if branch:
                trunk_d[branch] = branch_d
                branch_d = {}
            branch = line.split('::')[0].strip()

        elif ':' in line:
            leaf = line.split(':')
            if leaf[1]:
                if ',' in leaf[1]:
                    leaf[1] = leaf[1].split(',')
                    leaf[1] = [x.strip() for x in leaf[1]]
                else:
                    leaf[1] = [leaf[1].strip()]
            else:
                leaf[1] = []
            branch_d[leaf[0]] = leaf[1]

        elif '$$$$' in line:
            trunk_d[branch] = branch_d
            root[trunk] = trunk_d
        else:
            pass
    return root


def save_j_data(j_data, out_path):
    out_file = Path.resolve(out_path.joinpath('questions.json'))
    with open(out_file, 'w') as file:
        json.dump(j_data, indent=3, fp=file)
