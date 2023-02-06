# Prerequsite
* The plugin binary should exist on the system and it should be able to run with the user you run the pytest.
* A Splunk instance (HEC port and splunkd port) should be accessible by the pytest.
* Splunk HEC token should not overwrite index. The tests relies on "index=main"
* Python version must be > 3.x

# Testing Instructions
0. Make sure all commands below are run from within the test directory
1. Install the dependencies in a virtual environment 
    `make setup-venv`  
2. Run Splunk within a Docker container if required
    `make setup-splunk`
4. Start the test with the required options configured  
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

