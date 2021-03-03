[![Build status](https://github.com/QualiSystems/cloudshell-logging/workflows/CI/badge.svg?branch=master)](https://github.com/QualiSystems/cloudshell-logging/actions?query=branch%3Amaster)
[![codecov](https://codecov.io/gh/QualiSystems/cloudshell-logging/branch/master/graph/badge.svg)](https://codecov.io/gh/QualiSystems/cloudshell-logging)
[![PyPI version](https://shields.io/pypi/v/cloudshell-logging)](https://pypi.org/project/cloudshell-logging)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

<p align="center">
<img src="https://github.com/QualiSystems/devguide_source/raw/master/logo.png"></img>
</p>

# Cloudshell logger

## Overview
The **cloudshell-logging** open source python package creates a thread and process-safe logger for CloudShell shells and scripts. This package also organizes logs in different files according to resource and sandbox. 
 
## Installation

`pip install cloudshell-logging`

## Usage

#### Where can I see the execution logs?
All logs are saved on the Execution Server where the script or driver is running (except for L1 shell logs, which reside on the Quali Server). For exact locations, see the Troubleshooting Guide’s [Collecting Logs](https://help.quali.com/online%20help/0.0/cloudshell/Content/Troubleshooting/Collecting-logs.htm) article.

#### How do I customize my shell or script’s logging policy?
The simplest way to get a hold of a logger object is to use the **get_qs_logger** module:

```python
from cloudshell.logging.qs_logger import get_qs_logger
logger = get_qs_logger(log_file_prefix=file_prefix,log_category=reservation_id,log_group=resource_name)
logger.info("log something")
For example:
def some_command(self, context):
    """

    :param ResourceCommandContext context:
    :return:
    """
    logger = get_qs_logger(log_file_prefix='CloudShell Sandbox Orchestration',
                           log_category=context.reservation.reservation_id,
                           log_group=context.resource.name)
    logger.info("this is a log in the command")
    return "done"
```

For the default logger, the **log_category** parameter defines the folder under which logs will be grouped, whereas the **log_group** parameter defines the file. The CloudShell convention is to create a folder for each reservation id and a file for each resource name. For orchestration scripts, the file name is the environment name.

You can then use the regular logging level syntax to write messages as a part of the driver package or script flow:
```python
logger.debug("debug message")
logger.info("info message")
logger.warning("warning message")
logger.error("error message")
```

Only messages which are not less than the log level currently set for the driver will be saved to file. For example, if the log level is “info”, only log levels “info”, “warning”, “error” and “critical” apply.

Typically, changing the log level to a more verbose value would be done only in order to debug an issue, as writing too much to the logs can be expensive.

There are two places to manage the logging level:
* Execution Server (global level)
* Driver environment (driver level)

To change the global log level for all drivers make changes based on topic [Setting the logging level for Python drivers](https://help.quali.com/Online%20Help/0.0/Portal/Content/Admn/Tst-n-Cmd-Exc.htm#Setting).

To change the log level on the driver level, edit the configuration file `[venv]\[drivername]\Lib\site-packages\cloudshell\core\logger\qs_config.ini` and change the LOG_LEVEL and LOG_PRIORITY values.

```
Changing LOG_PRIORITY attribute to CONFIG is mandatory to override global log level value which can be set in customer.config
```

For example, changing the log level to “WARNING”:
```python
[Logging]
;Possible Log Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL='WARNING'
;Possible Log Priorities: ENV, CONFIG
;ENV - get log level from environment variable specified in Execution Server customer.config
;CONFIG - get log level from current configuration file
LOG_PRIORITY='CONFIG'
LOG_FORMAT= '%(asctime)s [%(levelname)s]: %(name)s %(module)s - %(funcName)-20s %(message)s'
TIME_FORMAT= '%d-%b-%Y--%H-%M-%S'
WINDOWS_LOG_PATH='{ALLUSERSPROFILE}\QualiSystems\logs'
UNIX_LOG_PATH='/var/log/qualisystems'
DEFAULT_LOG_PATH='../../Logs'
```
Note that this change is only valid for that virtual environment, so if you upgrade the shell or the script, CloudShell will create a new virtual environment that uses the default values.
 

We use tox and pre-commit for testing. For details, click [here](https://github.com/QualiSystems/cloudshell-package-repo-template#description-of-services).
