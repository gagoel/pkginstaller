import os
import json


def parse_tests_configuration_file():   
    project_root = os.getenv('PROJECT_ROOT')
    if project_root == None:
        raise Exception('PROJECT_ROOT environment variable is not set.')
    
    test_config_file = os.path.join(project_root, 'tests/test-config.json')
    test_wcpgsite_configuration = None
    with open(test_config_file) as conf_file:
        try:
            test_wcpgsite_configuration = json.load(conf_file)
        except Exception as e:                  
            print('CONFIGURATION FILE PARSING FAILED.')
            raise e                         
    return test_wcpgsite_configuration
