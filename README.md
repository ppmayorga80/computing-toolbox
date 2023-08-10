# Computing Toolbox for Python

This is a library aiming to help programmers to sort every day tasks easily.
This library contains:
1. gcp
   1. secret-manager utils to access secret values
   2. gcp-storage utils to check if a file exists in Google Cloud or get a list of files in a bucket
2. jsonl class able to read and write json line file very quickly
3. http-request class able to get html files easily
4. async-http-request class able to get multiple files easily
5. utils
   1. deep_get function able to get dynamically values from a dictionary
   2. split function able to split a given interval of size n in m parts

    
# Installation
``pip install computing-toolbox``

# Usage
```python
from computing_toolbox.jsonl import Jsonl
#read whole file
data0 = [x for x in Jsonl("/path/to/file")]
#alternative to read 
data1 = list(Jsonl("/path/to/file"))

#read 100 rows after row 20
data2 = [x for x in Jsonl("/path/to/file", offset=20, limit=100)]

#write objects
data3=[{"name":"Newton"}, {"name":"Galileo"}]
Jsonl("/path/to/file","w").write(data3)
```

If the file is located in the cloud, 
you only need to configure your environment
`Jsonl` class will handle it for aws, gcp, etc.

`Jsonl` can handle `.zip` or `.gz` files automatically
you only need to specify the right extension in the path

# Install CLI tools
``pip install .``

# Author
Pedro Mayorga.
