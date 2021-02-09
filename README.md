
# viewgrade
This tool counts the grades in pdf docs from http://112.137.129.30/viewgrade/ (an UET site for grades publication)

```console
ncthuan:~$ python viewgrade.py "./data/sample/051926290121Du an cong nghe_INT3132 20_0001.pdf"

Total recognized: 73
Grade: %
 A+  : 65
 A   : 9
 B+  : 6
 B   : 2
 C+  : -
 C   : -
 D+  : 6
 D   : -
 F   : 6
 N/A : 1
```

## Installation
requirements:
* opencv
* numpy
* tesseract
* pytesseract
* pdf2image
* poppler

Yall gonna need an environment that has those packages above to run the code.<br>
Personally, I use annaconda or miniconda on Windows 10 so I might use the following commands:
```
conda install -c conda-forge tesseract
conda install -c conda-forge poppler
pip install pytesseract
pip install pdf2image
pip install opencv
```


## Usage
Command
```
python viewgrade.py "<path to local pdf grade file>"
```


## How it works
check out the notebook experiment.ipynb for more details

## Sample data
data/sample/

## To do
* function: send request to the server to get pdf files as bytes
* cmd with arg as a link
* try deep learning