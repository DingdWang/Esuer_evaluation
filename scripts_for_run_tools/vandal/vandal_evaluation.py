# Standard lib imports
import sys
from os.path import abspath, dirname, join
import os
import json
import logging
import time
import csv
import subprocess

# Prepend .. to $PATH so the project modules can be imported below
evaluation_path = dirname(abspath(__file__))
vandal_path = join(evaluation_path,'vandal','bin','decompile')
dataset_path = join(evaluation_path,'Dataset','source/')
tmp_file_path = join(evaluation_path,'tmp','tmp_file.hex')
result_path = join(evaluation_path,'results/')
csv_path = join(evaluation_path,'tx_top1w_vandal.csv')
# Local project imports


# data_PATH = "/root/projects/ethereum_decompiler/F5/evm_data/bytecode"

log = logging.getLogger(__name__)

logging.basicConfig(
	level="INFO",
        filename = 'vandal.log',
        filemode='w',
        datefmt='%a %d %b %Y %H:%M:%S',
        format='%(asctime)s %(filename)s %(levelname)s %(message)s'
)





if __name__ == '__main__':

    log.info ("[*] Start")

    write_file = csv_path

   # os.chdir(evaluation_path)
    with open(write_file,'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['addr','result','time','error_info'])
   # os.chdir(target_path)

    for file in os.listdir(dataset_path):

        with open(dataset_path+file,'r') as f:
            data = json.load(f)
            bytecode = data["bytecode"]
        with open(tmp_file_path,'w') as f_tmp:
            f_tmp.write(bytecode)
        filename = os.path.splitext(file)[0]
        log.info (f"[*] Analyzing {file}")
        time_start = time.time()
        try:
            return_info = subprocess.run(['python3',vandal_path,tmp_file_path,'-g',result_path+filename+'.dot'],timeout=120,check=True,capture_output=True)
        except subprocess.CalledProcessError as e:
            log.error(e.stderr)
            result = 'Error'
            used_time = 0
            error_info = str(e.stderr)
        except subprocess.TimeoutExpired as e:
            log.error(e)
            result = 'Error'
            used_time = 0
            error_info = str(e)
        except Exception as e:
            log.error(e)
            result = 'Error'
            used_time = 0
            error_info = str(e)
        else:
            time_end = time.time()
            used_time = time_end-time_start
            result = 'Success'
            error_info = ''
            log.info(f"[*] Analyzing done in {used_time} s")
            log.info('[*] save cfg')
        log.info("[*] start record")
        #os.chdir(evaluation_path)
        with open(write_file,'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow([filename, result, used_time, error_info])
        log.info("[*] record done")
        #os.chdir(target_path)

    log.info("[*] done")

