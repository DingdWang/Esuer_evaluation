# Standard lib imports
import sys
from os.path import abspath, dirname, join
import os
import json
import logging
import time


import csv
import subprocess

import sys

# Prepend .. to $PATH so the project modules can be imported below
evaluation_path = dirname(abspath(__file__))
gigahorse_cli_path = join(evaluation_path,'gigahorse','gigahorse-toolchain','gigahorse.py')
dataset_path = join(evaluation_path,'..','..','Dataset','source/')
tmp_file_path = join(evaluation_path,'tmp','tmp_file.hex')
result_path = join(evaluation_path,'results/')
csv_path = join(evaluation_path,'tx_top1w_gigahorse.csv')
#mythril_folder_path =  join(evaluation_path,'mythril/')
# Local project imports


# data_PATH = "/root/projects/ethereum_decompiler/F5/evm_data/bytecode"

log = logging.getLogger(__name__)

logging.basicConfig(
	level="INFO",
        filename = 'gigahorse.log',
        filemode='w',
        datefmt='%a %d %b %Y %H:%M:%S',
        format='%(asctime)s %(filename)s %(levelname)s %(message)s'
)



def cp_file(address):
    if os.path.exists(result_path+address):
        os.mkdir(result_path+address)
    cmd = 'cp .temp/'+address+'/out/contract.tac '+result_path+address+'/contract.tac'
    #os.system(cmd)
    cmd = 'cp .temp/'+address+'/out/function_calls.json '+result_path+address+'/contract.tac'

    cmd = 'cp .temp/'+address+'/out/contract.tac '+result_path+address+'/contract.tac'




#sys.path.append(mythril_folder_path)


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
            return_info = subprocess.run(['python3',gigahorse_cli_path,'-C','clients/visualizeout.py',tmp_file_path],timeout=120,check=True,capture_output=True)
            #return_info = subprocess.run(['java','-jar',jar_path,'--runtime','--dot','--output',result_path+filename+'.dot',tmp_file_path],timeout=120,check=True,capture_output=True)
            #cmd = 'java -jar /root/evm_decompiler/cfg_evaluation_tool\&scripts/ethersolve/EtherSolve/UI/build/libs/EtherSolve-1.0-SNAPSHOT.jar'+" --runtime --dot --output /evm_decompiler/cfg_evaluation_tool\&scripts/ethersolve/results/"+filename +'.dot ' + '/root/evm_decompiler/cfg_evaluation_tool\&scripts/ethersolve/tmp/tmp_file'
            #os.system(cmd)
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
            result = 'Success'

            cp_file(file)

            used_time = time_end-time_start
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

