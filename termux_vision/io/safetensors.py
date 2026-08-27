import json
import struct
import numpy as np

def save_safetensors(tensors_dict: dict, file_path: str):
    """
    Save dictionary of NumPy arrays to SafeTensors format with zero PyTorch dependency.
    """
    header = {}
    offset = 0
    buffer_bytes = bytearray()

    dtype_map = {
        np.dtype("float32"): "F32",
        np.dtype("float64"): "F64",
        np.dtype("int32"): "I32",
        np.dtype("int64"): "I64",
        np.dtype("uint8"): "U8",
    }

    for name, arr in tensors_dict.items():
        arr_cont = np.ascontiguousarray(arr)
        raw = arr_cont.tobytes()
        length = len(raw)
        st_dtype = dtype_map.get(arr_cont.dtype, "F32")
        
        header[name] = {
            "dtype": st_dtype,
            "shape": list(arr_cont.shape),
            "data_offsets": [offset, offset + length]
        }
        offset += length
        buffer_bytes.extend(raw)

    header_json = json.dumps(header).encode("utf-8")
    header_len = len(header_json)

    with open(file_path, "wb") as f:
        # 8-byte little endian header length
        f.write(struct.pack("<Q", header_len))
        f.write(header_json)
        f.write(buffer_bytes)

def load_safetensors(file_path: str) -> dict:
    """
    Load SafeTensors file into dictionary of NumPy arrays.
    """
    dtype_inv_map = {
        "F32": np.float32,
        "F64": np.float64,
        "I32": np.int32,
        "I64": np.int64,
        "U8": np.uint8,
    }

    with open(file_path, "rb") as f:
        header_len_bytes = f.read(8)
        header_len = struct.unpack("<Q", header_len_bytes)[0]
        header_json_bytes = f.read(header_len)
        header = json.loads(header_json_bytes.decode("utf-8"))

        data_start = 8 + header_len
        tensors = {}

        for name, meta in header.items():
            if name == "__metadata__":
                continue
            np_dtype = dtype_inv_map.get(meta["dtype"], np.float32)
            shape = meta["shape"]
            start_off, end_off = meta["data_offsets"]
            
            f.seek(data_start + start_off)
            raw = f.read(end_off - start_off)
            arr = np.frombuffer(raw, dtype=np_dtype).reshape(shape)
            tensors[name] = arr.copy()

    return tensors
