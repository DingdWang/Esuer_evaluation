# Standard lib imports
from os.path import abspath, dirname, join
import os
import logging
import csv
from rich.logging import RichHandler
import subprocess

project = 'tx_top1w'
output = 'output'
tool = 'esuer'

tool_path = dirname(abspath(__file__))
script_path = join(tool_path, 'esuer_evaluation_test.py')
evaluation_path = join(tool_path, "..")

data_PATH = join(evaluation_path, "..", "cfg_evm_data")
target_path = join(data_PATH, project)


log = logging.getLogger(__name__)

logging.basicConfig(
    level="INFO",
    handlers=[RichHandler(rich_tracebacks=True), logging.FileHandler(
        join(tool_path, f'{tool}_wrapper.log'), 'w')]
)


if __name__ == '__main__':

    log.info("[*] Start")

    write_file = f'{project}_{tool}.csv'
    write_path_file = f'{project}_{tool}_path.csv'

    executed = set()

    os.chdir(evaluation_path)
    if not os.path.exists(write_file):
        with open(write_file, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['addr', 'result', 'time', 'error_info'])
        with open(write_path_file, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['addr', 'Num of Paths'])
    else:
        with open(write_file, 'r') as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                if row[0] == 'addr':
                        continue #这一行是csv的第一行
                executed.add(row[0])
    
    for file in os.listdir(target_path):

        if os.path.splitext(file)[0] in executed:
            continue

        try:
            return_info = subprocess.run(
                ['python3.8', script_path, file])
            #  cmd = 'python3.8 rattle-cli -i tmp.bin -nsf'
            #  cmd = f'python3.8 rattle_evaluation_test.py {file}'
            #  os.system(cmd)

        except Exception as e:
            log.error(e)

    log.info("[*] done")
