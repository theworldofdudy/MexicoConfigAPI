# Description
The application consist on two component:
1. Python APIRest backend which interacts with web JS and parse configuration files
2. JS Web frontend interface


## Steps for setting up the environment
APIRest is based on fastAPI. We should use at least python 3.8
1.  To launch the service there are two alternatives.
    * directly which fastAPI command
    ```
    fastapi dev .\fastAPI_test.py
    ```
    * Using uvicorn interface
    ```
    uvicorn fastAPI_test:app --reload
    ```
2. Open localhost and show jsons response directly:

    ```
    http://127.0.0.1:8000
    ```

3. To launch website, open direclty the file index.html

## Files
Please locate files in the right folder. python apirest will search files in the right referenced folder
1. paraval.dat
2. titulosval.dat