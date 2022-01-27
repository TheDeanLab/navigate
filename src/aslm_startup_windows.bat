TITLE ASLM

cd "C:\Users\Dax\Documents\GitHub\ASLM\src"

set root=C:\Users\Dax\AppData\Local\Continuum\anaconda3

call %root%\Scripts\activate.bat %root%

call conda activate aslm

call python main.py --synthetic_hardware

cmd /k


