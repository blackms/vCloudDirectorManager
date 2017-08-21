# vCloud Director Web Manager
## Description
This Web Panel interact with vCloud Director giving all the necessary information about utilization and organizations
details. It also permit to see how many and which ip addresses are in use for each nsx Edge.

FrontEnd is written using jQuery, MetisMenu and sbAdmin, but It will be rewritten using some different JS framework.

## ScreenShots
![](https://raw.githubusercontent.com/blackms/vCloudDirectorManager/master/imgs/screen_main.png | width=100)

## Compatibility
Up to 8.20

## Installation
### Creating Python Environment
Clone the repository:
```bash
git clone https://github.com/blackms/vCloudDirectorManager.git
```

Create the Virtual Environment
```bash
virtualenv venv
source venv/bin
pip install -r requirements.txt
```

## Configuration
Edit config.example inside `app` directory and rename it to config.ini

## Running
In order to start the app you have to run:
```bash
python vcd_summary.py
```

