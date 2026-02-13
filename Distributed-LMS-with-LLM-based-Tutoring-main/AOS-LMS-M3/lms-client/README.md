# LMS Client

The client for the grpc enabled LMS. 

## Functions :
    1. Interface for the LMS Server

## Steps to run :
### Step 1: Create a virtual environment
```shell
python -m venv venv
```
### Step 2: Activate the virtual environment
```shell
venv/Scripts/activate
```

### Step 3: Install all requirements
```shell
pip install -r requirements.txt
```
    
### Step 4: Generate grpc python code
```shell

python -m grpc_tools.protoc -I.  --python_out=. --pyi_out=. --grpc_python_out=. ./Lms.proto
```
### Step 5: Run the source file
```shell
python main.py
```
    
