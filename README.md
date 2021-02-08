
# viewgrade
This tool analyzes the grades in pdf docs from http://112.137.129.30/viewgrade/ (UET site for)

```console
ncthuan:~$ python viewgrade.py "./data/sample/051926290121Du an cong nghe_INT3132 20_0001.pdf"
Total recognized: 73
Grade: %
 A+  : 65
 A   : 9
 B+  : 6
 B   : 2
 C+  : 0
 C   : 0
 D+  : 6
 D   : 0
 F   : 6
 N/A : 1
```

## Installing
Still updating


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