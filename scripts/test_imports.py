try:
    import vtk
except ImportError as e:
    print(f'VTK was not imported: {e}')
print('==> Package VTK imported successfully!')

try:
    import numpy
except ImportError as e:
    print(f'numpy was not imported: {e}')
print('==> Package numpy imported successfully!')

try:
    import yaml
except ImportError as e:
    print(f'yaml was not imported: {e}')
print('==> Package yaml imported successfully!')

try:
    import brotli
except ImportError as e:
    print(f'brotli was not imported: {e}')
print('==> Package brotli imported successfully!')

try:
    import schema
except ImportError as e:
    print(f'schema was not imported: {e}')
print('==> Package schema imported successfully!')

try:
    import sklearn
except ImportError as e:
    print(f'sklearn was not imported: {e}')
print('==> Package sklearn imported successfully!')

try:
    import colorama
except ImportError as e:
    print(f'colorama was not imported: {e}')
print('==> Package colorama imported successfully!')

try:
    import mpi4py
except ImportError as e:
    print(f'mpi4py was not imported: {e}')
print('==> Package mpi4py imported successfully!')

try:
    from pyzoltan.core import zoltan
except ImportError as e:
    print(f'pyzoltan was not imported: {e}')
print('==> Package pyzoltan imported successfully!')

