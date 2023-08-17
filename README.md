# Receipt scanner PoC


## Preprocessor script

1. Download repository to a folder

2. Download images to same folder, any folder name:
receipt-scanner

```
|-- main.py
|-- requirements.txt
|-- images/
|---- image1.png
```

### Installation steps

1. Install packages:
```shell
pip install -r requirements.txt
```

2. Run `main.py` with image name:
```shell
python main.py -i "images/image1.png"
```

eg:
```shell
python main.py -i "images/X51005268275.jpg"
```

#TO DO
- Need to fix table logic for missing items