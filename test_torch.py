import sys, torch
print("python:", sys.executable)
print("torch file:", torch.__file__)
print("torch version:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
