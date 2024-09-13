""" Copy JSON data files from a source directory to a destination directory with optional compression
Usage:
- with compression:    `python copy_dataset path/to/src/dir path/to/dst/dir 1`
- without no compression: `python copy_dataset path/to/src/dir path/to/dst/dir 0`
"""

import sys
import os
import json

import brotli

def copy_dataset(src_dir: str, dst_dir: str, compress: bool = False)-> int:
    """Copy JSON data files from a source directory to a destination directory with optional compression"""
    print("----------------")
    print("Copy dataset:")
    print(f"Dest dir: {dst_dir}")
    print(f"compress: {compress}")
    print("----------------")

    if not os.path.isdir(src_dir):
        raise FileNotFoundError(f"source directory not found at '{src_dir}'")
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)

    for i in os.scandir(src_dir):
        if i.is_file():
            src_path = os.path.join(src_dir, i.name)
            dst_path = os.path.join(dst_dir, i.name)

            decompressed_dict = None

            with open(src_path, "rb") as compr_json_file:
                compr_bytes = compr_json_file.read()
                try:
                    decompr_bytes = brotli.decompress(compr_bytes)
                    decompressed_dict = json.loads(decompr_bytes.decode("utf-8"))
                except brotli.error:
                    try:
                        decompressed_dict = json.loads(compr_bytes.decode("utf-8"))
                    except json.JSONDecodeError:
                        print(f"Invalid JSON file: {i.name}. Ignored.")

            if decompressed_dict is None:
                continue

            json_str = json.dumps(decompressed_dict, separators=(',', ':'))

            # Issue #527: replace `id` by seq_id in tasks entities and communication nodes
            # keep these lines commented as a doc to help for another possible future key renaming
            # import re
            # json_str = re.sub(r'"home":([0-9]+),"id":([0-9]+)', r'"home":\1,"seq_id":\2', json_str)
            # json_str = re.sub(r'"id":([0-9]+),"home":([0-9]+)', r'"seq_id":\1,"home":\2', json_str)
            # json_str = re.sub(r'"entity":\{"id":([0-9]+),', r'"entity":{"seq_id":\1,', json_str)
            # json_str = re.sub(r'"home": ([0-9]+),\n([\s]+)"id": ([0-9]+)', r'"home": \1,\n\2"seq_id": \3', json_str)
            # json_str = re.sub(r'"type":"object","id":([0-9]+)', r'"type":"object","seq_id":\1', json_str)

            print(f"Generating {i.name}...")
            if compress:
                print("> Compressing...")
                with open(dst_path, "wb") as compr_json_file:
                    compressed_str = brotli.compress(string=json_str.encode("utf-8"), mode=brotli.MODE_TEXT)
                    compr_json_file.write(compressed_str)
            else:
                print("> No compression !")
                with open(dst_path, "wt", encoding="utf-8") as uncompr_json_file:
                    uncompr_json_file.write(json_str)

    return 0

if __name__ == "__main__":
    copy_dataset(sys.argv[1], sys.argv[2], compress=(sys.argv[3] in ['1', 'true', 'True', 'on', 'ON']))
