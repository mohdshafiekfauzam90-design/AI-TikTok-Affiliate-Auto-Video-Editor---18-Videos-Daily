#!/usr/bin/env python3
"""Tukar model Whisper rasmi OpenAI (.pt) kepada format ggml untuk whisper.cpp
TANPA perlu memasang PyTorch (checkpoint dibaca terus dengan numpy).

Format output sama dengan whisper.cpp/models/convert-pt-to-ggml.py (f16).

Guna:
  python3 tools/convert_pt_to_ggml.py large-v3.pt whisper_assets_dir ggml-large-v3.bin
  (whisper_assets_dir = folder 'whisper/assets' dari pakej openai-whisper:
   mengandungi mel_filters.npz dan multilingual.tiktoken)
"""
import base64
import pickle
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np

DTYPES = {"HalfStorage": np.float16, "FloatStorage": np.float32,
          "DoubleStorage": np.float64, "LongStorage": np.int64,
          "IntStorage": np.int32, "BoolStorage": np.bool_,
          "BFloat16Storage": "bf16"}


class _Storage:
    def __init__(self, name):
        self.name = name


def _rebuild_tensor_v2(storage, offset, size, stride, *_args, **_kw):
    arr = storage
    item = arr.itemsize
    return np.lib.stride_tricks.as_strided(
        arr[offset:], shape=tuple(size), strides=tuple(s * item for s in stride)).copy()


def load_pt(path: Path) -> dict:
    zf = zipfile.ZipFile(path)
    names = zf.namelist()
    prefix = names[0].split("/")[0]
    cache: dict = {}

    class U(pickle.Unpickler):
        def find_class(self, module, name):
            if module == "torch._utils" and name == "_rebuild_tensor_v2":
                return _rebuild_tensor_v2
            if module == "torch" and name.endswith("Storage"):
                return _Storage(name)
            if module == "collections" and name == "OrderedDict":
                import collections
                return collections.OrderedDict
            if module == "torch._utils" and name == "_rebuild_parameter":
                return lambda data, *_: data
            return super().find_class(module, name)

        def persistent_load(self, pid):
            _, stype, key, _loc, _numel = pid
            if key not in cache:
                raw = zf.read(f"{prefix}/data/{key}")
                dt = DTYPES[stype.name]
                if dt == "bf16":
                    u16 = np.frombuffer(raw, np.uint16).astype(np.uint32) << 16
                    cache[key] = u16.view(np.float32)
                else:
                    cache[key] = np.frombuffer(raw, dt)
            return cache[key]

    with zf.open(f"{prefix}/data.pkl") as f:
        return U(f).load()


def convert(pt: Path, assets: Path, out: Path) -> None:
    ckpt = load_pt(pt)
    hp = ckpt["dims"]
    sd = ckpt["model_state_dict"]
    n_mels = hp["n_mels"]
    filters = np.load(assets / "mel_filters.npz")[f"mel_{n_mels}"].astype(np.float32)
    tokens = {}
    for line in (assets / "multilingual.tiktoken").read_text().splitlines():
        if line:
            tok, rank = line.split()
            tokens[base64.b64decode(tok)] = int(rank)

    with open(out, "wb") as f:
        f.write(struct.pack("i", 0x67676D6C))
        for k in ("n_vocab", "n_audio_ctx", "n_audio_state", "n_audio_head", "n_audio_layer",
                  "n_text_ctx", "n_text_state", "n_text_head", "n_text_layer", "n_mels"):
            f.write(struct.pack("i", hp[k]))
        f.write(struct.pack("i", 1))  # use_f16
        f.write(struct.pack("i", filters.shape[0]))
        f.write(struct.pack("i", filters.shape[1]))
        filters.tofile(f)
        f.write(struct.pack("i", len(tokens)))
        for key in tokens:
            f.write(struct.pack("i", len(key)))
            f.write(key)
        for name, t in sd.items():
            data = np.asarray(t).squeeze()
            if name in ("encoder.conv1.bias", "encoder.conv2.bias"):
                data = data.reshape(data.shape[0], 1)
            n_dims = len(data.shape)
            if n_dims < 2 or name in ("encoder.conv1.bias", "encoder.conv2.bias",
                                      "encoder.positional_embedding",
                                      "decoder.positional_embedding"):
                data, ftype = data.astype(np.float32), 0
            else:
                data, ftype = data.astype(np.float16), 1
            nb = name.encode()
            f.write(struct.pack("iii", n_dims, len(nb), ftype))
            for i in range(n_dims):
                f.write(struct.pack("i", data.shape[n_dims - 1 - i]))
            f.write(nb)
            np.ascontiguousarray(data).tofile(f)
    print(f"ggml model -> {out} ({out.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    convert(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
