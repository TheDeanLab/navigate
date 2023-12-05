TITLE Navigate

cd "C:\Users\Dax\Documents\GitHub\navigate\src"

set root=C:\Users\Dax\AppData\Local\Continuum\anaconda3

call %root%\Scripts\activate.bat %root%

call conda activate navigate

call python main.py --synthetic_hardware

cmd /k
