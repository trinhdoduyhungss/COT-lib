import os
import pandas as pd


def read_csv(file_path):
    data = pd.read_csv(file_path)
    data = data.set_index(data.columns[0])
    return data


def read_json(file_path):
    data = pd.read_json(file_path, encoding='utf-8-sig')
    data = data.set_index(data.columns[0])
    return data


def read_jsonl(file_path):
    data = pd.read_json(file_path, lines=True, encoding='utf-8-sig')
    data = data.set_index(data.columns[0])
    return data


def fill_missing_values(input_data):
    """
    Fill missing values in input_data

    Args:
        input_data (list): list of dataframes

    Returns:
        target_df (dataframe): dataframe with missing values filled
    """
    target_df = input_data[-1]
    for i in range(len(input_data) - 2, -1, -1):
        for col in target_df.columns:
            miss_bool = target_df[target_df.isnull().any(axis=1)].index
            target_df.loc[miss_bool, col] = input_data[i].loc[miss_bool, col]
    return target_df


def merge_tables(input_files, output_file):
    """
    Merge tables in input_files and save to output_file

    Args:
        input_files (list): list of input files
        output_file (str): output file

    Returns:
        None
    """
    multi_tables = []
    for file in input_files:
        if file.endswith('.csv'):
            multi_tables.append(read_csv(file))
        elif file.endswith('.json'):
            multi_tables.append(read_json(file))
        elif file.endswith('.jsonl'):
            multi_tables.append(read_jsonl(file))
        else:
            raise ValueError('File type not supported')
    df = fill_missing_values(multi_tables)
    df = df.reset_index()
    df.to_csv(output_file.replace('.json', '.csv'), index=False)
    df.to_json(output_file.replace('.csv', '.jsonl'), orient='records', force_ascii=False, lines=True)


def find_files(input_dir):
    """
    Find files in input_dir

    Args:
        input_dir (str): input directory

    Returns:
        files (list): list of files in input_dir
    """
    files = []
    for file in os.listdir(input_dir):
        if file.endswith('.csv') or file.endswith('.json') or file.endswith('.jsonl'):
            def get_file_details(f):
                return {f: os.path.getmtime(f)}

            files.append(get_file_details(os.path.join(input_dir, file)))
    files = sorted(files, key=lambda x: list(x.values())[0])
    return list(map(lambda x: list(x.keys())[0], files))


if __name__ == '__main__':
    input_dir = 'D:/Projects/COT-lib/datasets/VND'
    output_file = 'D:/Projects/COT-lib/datasets/vnd.csv'
    input_files = find_files(input_dir)[1:]
    merge_tables(input_files, output_file)
