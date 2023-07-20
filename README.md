# Challenge 3

### Folder Structure:
```
challenge3/
  content/
    - get_item.py -> python script to return a value for a given key
    - test_get_item.py -> unit tests
  requirements.txt
```

### Steps to run unit tests locally:
1. cd to the root folder containing the challenges
   
2. Setup python virtual environment:
   ```bash
   ➜  python3 -m venv .venv
   ➜  source .venv/bin/activate
   (.venv) ➜  pip install -r challenge3/requirements.txt 
   ```
    
3. Set PYTHONPATH:
   ```bash
   (.venv) ➜  export PYTHONPATH=./challenge3 
   ```
    
4. Run unit tests:
   ```bash
   (.venv) ➜  pytest -x challenge3/content
   ```