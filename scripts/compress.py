# Compress or decompress files in a source directory and write to a destination directory
# Usage: python compress path/to/src/dir path/to/dst/dir "compress" (or "uncompress")

import sys
import os
import json
import re

import brotli

def compress(src_dir: str, dst_dir: str, operation: str = "compress")-> int:

    if not os.path.isdir(src_dir):
        raise FileNotFoundError(f"source directory not found at '{src_dir}'")
    if not os.path.isdir(dst_dir):
        raise FileNotFoundError(f"destination directory not found at '{dst_dir}'")

    print(f"{operation} from directory {src_dir} to {dst_dir}\n--------------------")
    for i in os.scandir(src_dir):
        if i.is_file():
            src_path = os.path.join(src_dir, i.name)
            dst_path = os.path.join(dst_dir, i.name)

            # compress an uncompressed input file
            if operation == "compress":
                print(f"Uncompressing {i.name}...")
                with open(src_path, "rt", encoding="utf-8") as uncompr_json_file:
                    uncompr_str = uncompr_json_file.read()
                    decompressed_dict = json.loads(uncompr_str) 
            # else uncompress a compressed input file
            else:
                with open(src_path, "rb") as compr_json_file:
                    compr_bytes = compr_json_file.read()
                    try:
                        decompr_bytes = brotli.decompress(compr_bytes)
                        decompressed_dict = json.loads(decompr_bytes.decode("utf-8"))
                    except brotli.error:
                        decompressed_dict = json.loads(compr_bytes.decode("utf-8"))

            json_str = json.dumps(decompressed_dict, separators=(',', ':'))

            # Issue 527: replace `id` by seq_id in communication from/to and in entity nodes
            # json_str = re.sub(r'"home":([0-9]+),"id"', r'"home":\1,"seq_id"', json_str)

            if operation == "compress":
                print(f"Generating compressed file  {i.name}...")
                with open(dst_path, "wb") as compr_json_file:
                    compressed_str = brotli.compress(string=json_str.encode("utf-8"), mode=brotli.MODE_TEXT)
                    compr_json_file.write(compressed_str)
            else:
                print(f"Generating uncompressed file {i.name}...")
                with open(dst_path, "wt", encoding="utf-8") as uncompr_json_file:
                    uncompr_json_file.write(json_str)

    return 0

if __name__ == "__main__":
    compress(sys.argv[1], sys.argv[2], sys.argv[3] or "compress")
