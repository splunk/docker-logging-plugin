# Testing Instructions
0. (Optional) Use a virtual environment for the test  
    `virtualenv --python=python3.5 venv`  
    `source venv/bin/activate`
1. Install the dependencies  
    `pip install -r requirements.txt`  
2. Start the test with the required options configured  
    `python -m pytest <options>`  

    **Options are:**  
    --splunkd-url
    * Description: splunkd url used to send test data to. Eg: https://localhost:8089  
    * Default: https://localhost:8089

    --splunk-user
    * Description: splunk username  
    * Default: admin

    --splunk-password
    * Description: splunk user password  
    * Default: changeme

    --splunk-hec-url
    * Description: splunk hec endpoint used by logging plugin.  
    * Default: https://localhost:8088

    --splunk-hec-token
    * Description: splunk hec token for authentication.
    * Required

    --docker-plugin-path
    * Description: docker plugin binary path  
    * Required

    --fifo-path
    * Description: full file path to the fifo  
    * Required

