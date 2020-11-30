# KEST_Recon
Reconstruction software for the KEST project

INSTALLATION:

WinPython64-3.8.6.0cod = Python 3.8 64bit + PyQt5 + Spyder + VSCode

Mandatory additional packages (online available):
- Add TIFFFile (tifffile-2020.11.26-py3-none-any.whl)
- Add pyFFTW (pyFFTW-0.12.0-cp38-cp38-win_amd64.whl)
- Add openCV_python (opencv_python-4.4.0.46-cp38-cp38-win_amd64.whl)
- Add cv2_tools (python wheel avalable online - cv2_tools-2.4.0-py3-none-any.whl)

C-developed code for the project:
- Despeckle
- TIGRE_FDK

To enable GPU monitoring:
- Install locally CUDA Toolkit in order to have nvidia-smi
- Add to system PATH the following line: C:\Program Files\NVIDIA Corporation\NVSMI
- Add GpUtil with the command line: pip install gputil
