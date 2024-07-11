import json
from os.path import join, exists, dirname
from os import listdir, mkdir, remove, rename, system, chdir
import sys
sys.path.append('/root/projects/ethereum_decompiler/esuer')
import tx_origin, re_entrancy

def compile_file():

    vul_type = 'tx-origin'

    for n in range(1,51):
        file = f'buggy_{n}'
        dst = join(contract_path,vul_type,file)

        if not exists(dst):
            mkdir(dst)

        system(f"solc {dst}.sol --bin-runtime --hashes --overwrite -o {dst}")

def run_ethersolve():

    vul_type = ''

    for n in range(1,51):
        file = f'buggy_{n}'
        dst = join(contract_path,vul_type,file)
        chdir(dst)
        for source_file in listdir(dst):
            if source_file.endswith('.bin-runtime'):
                content = open(source_file,'r').read().strip()
                if len(content) > 0:
                    system(f'java -jar /root/projects/ethereum_decompiler/F5/EtherSolve.jar -r {source_file} --{vul_type} -o ethersolve.json -j')
                    for result_file in listdir(dst):
                        if result_file.endswith(f'-{vul_type}.csv'):
                            rename(result_file,f'{source_file.split(".")[0]}-ethersolve.csv')

def run_vandal():

    vul_file = {'tx-origin':'originUsed', 're-entrancy':'reentrantCall'}

    for vul_type in vul_file:
        for n in range(1,51):
            file = f'buggy_{n}'
            dst = join(contract_path,vul_type,file)
            chdir(dst)
            for source_file in listdir(dst):
                if source_file.endswith('.bin-runtime'):
                    content = open(source_file,'r').read().strip()
                    if len(content) > 0:
                        system(f' /root/projects/ethereum_decompiler/evaluation_scripts_for_esuer/run_tools/vandal/vandal/bin/analyze.sh {source_file} /root/projects/ethereum_decompiler/evaluation_scripts_for_esuer/run_tools/vandal/vandal/datalog/demo_analyses.dl')
                        rename(f"{vul_file[vul_type]}.csv",f'{source_file.split(".")[0]}-vandal.csv')
                    for result_file in listdir(dst):
                        if result_file.endswith('.csv') and '-' not in result_file:
                            remove(result_file)

def run_esuer():

    vul_type = 're-entrancy'
    esuer_analyze = {'tx-origin':tx_origin.analyze, 're-entrancy':re_entrancy.analyze}

    for n in range(1,51):
        file = f'buggy_{n}'
        dst = join(contract_path,vul_type,file)
        chdir(dst)
        for source_file in listdir(dst):
            if source_file.endswith('.bin-runtime'):
                content = open(source_file,'r').read().strip()
                if len(content) > 0:
                    contract_name = source_file.split(".")[0]
                    result = esuer_analyze[vul_type](source_file)
                    with open(f'{contract_name}-esuer.json','w') as f:
                        json.dump(result,f,indent=4)

def get_myth_results():

    keyword = {'tx-origin':'==== Use of tx.origin', 're-entrancy':'==== State change after external call'}
    for vul_type in keyword:
        for n in range(1,51):
            file = f'buggy_{n}'
            dst = join(contract_path,vul_type,file)
            myth_result = join(contract_path,vul_type,'myth_results',f'{file}.sol.txt')
            with open(myth_result,'r') as f:
                flag = False
                for line in f:
                    if line.startswith(keyword[vul_type]):
                        flag = True
                    if flag == True:
                        if line.startswith('Contract: '):
                            contract_name = line.strip().split(': ')[1]
                        if line.startswith('PC address: '):
                            pc = line.strip().split(': ')[1]
                            with open(join(dst,f'{contract_name}-mythril.csv'),'a') as wf:
                                wf.write(f'{pc}\n')
                            flag = False




def extract_gt(file,vul_type):
    keyword = {'tx-origin':'_txorigin', 're-entrancy':'_re_ent'}

    not_vulnerable = 'buyTicket_re_ent'
    # This is not a re-entrancy vulnerability.
    # Example:
    # address payable lastPlayer_re_ent2;
    # uint jackpot_re_ent2;
    # function buyTicket_re_ent2() public{
    #     if (!(lastPlayer_re_ent2.send(jackpot_re_ent2)))
    #         revert();
    #     lastPlayer_re_ent2 = msg.sender;
    #     jackpot_re_ent2    = address(this).balance;
    # }
    # It can be re-entered, but cannot be exploited by the re-entrancy.

    vul_funcs = set()
    with open(file,'r') as f:
        for line in f:
            sig, name = line.strip().split(': ')
            if keyword[vul_type] in name and not_vulnerable not in name:
                vul_funcs.add(sig)

    return vul_funcs

def cal_metric(TP,FP,FN):

    precision = len(TP) / (len(TP) + len(FP)) if (len(TP) + len(FP)) > 0  else 0
    recall = len(TP) / (len(TP) + len(FN)) if (len(TP) + len(FN)) > 0 else 0
    F1 = precision *recall *2 / (precision + recall) if (precision + recall) > 0 else 0
    return precision, recall, F1

def compare_results():

    key_opcode = {'tx-origin':'ORIGIN', 're-entrancy':'SSTORE'}

    for vul_type in key_opcode:
        precision_esuer_all = 0
        recall_esuer_all = 0
        F1_esuer_all = 0
        count_esuer = 0

        precision_ethersolve_all = 0
        recall_ethersolve_all = 0
        F1_ethersolve_all = 0
        count_ethersolve = 0

        precision_vandal_all = 0
        recall_vandal_all = 0
        F1_vandal_all = 0
        count_vandal = 0

        precision_mythril_all = 0
        recall_mythril_all = 0
        F1_mythril_all = 0
        count_mythril = 0

        for n in range(1,51):
            file = f'buggy_{n}'
            dst = join(contract_path,vul_type,file)
            chdir(dst)
            for source_file in listdir(dst):
                if source_file.endswith('-esuer.json'):
                    contract_name = source_file.split("-esuer.")[0]
                    gt = extract_gt(f'{contract_name}.signatures',vul_type)
                    if len(gt) == 0:
                        continue
                    with open(f'{contract_name}-esuer.json','r') as f:
                        esuer_result = json.load(f)
                    
                    sig_esuer_result = {f"{x['function'][2:]:0>8}":x for x in esuer_result}

                    FP_esuer = set(sig_esuer_result.keys()) - gt
                    FN_esuer = gt - set(sig_esuer_result.keys())
                    TP_esuer = set(sig_esuer_result.keys()) & gt
                    with open('../esuer.json','a') as f:
                        f.write(f'{file}\t{contract_name}\t{FP_esuer}\t{FN_esuer}\n')

                    precision_esuer, recall_esuer, F1_esuer = cal_metric(TP_esuer,FP_esuer,FN_esuer)
                    with open('../esuer_metric.json','a') as f:
                        f.write(f'{file}\t{contract_name}\t{precision_esuer:.4f}\t{recall_esuer:.4f}\t{F1_esuer:.4f}\n')

                    count_esuer += 1
                    precision_esuer_all += precision_esuer
                    recall_esuer_all += recall_esuer
                    F1_esuer_all += F1_esuer

                    if vul_type == 'tx-origin':
                        gt_offset = set([str(sig_esuer_result[x]['offset']) for x in gt])
                    if vul_type == 're-entrancy':
                        gt_call_offset = set([str(sig_esuer_result[x]['offset']) for x in gt])
                        gt_offset = set()
                        for x in gt:
                            for s in sig_esuer_result[x]['sources']['sstore']:
                                gt_offset.update(str(o) for o in s)

                    with open(f'{contract_name}-ethersolve.csv','r') as f:
                        ethersolve_result = set()
                        for line in f:
                            offset , opcode, _ = line.split(',',2)
                            if offset == 'offset':
                                continue
                            opcode = opcode.split(': ',1)[1]
                            if opcode != key_opcode[vul_type]:
                                continue
                            ethersolve_result.add(offset)

                    FP_ethersolve = ethersolve_result - gt_offset
                    FN_ethersolve = gt_offset - ethersolve_result
                    TP_ethersolve = ethersolve_result & gt_offset

                    with open('../ethersolve.json','a') as f:
                        f.write(f'{file}\t{contract_name}\t{FP_ethersolve}\t{FN_ethersolve}\n')
                    
                    precision_ethersolve, recall_ethersolve, F1_ethersolve = cal_metric(TP_ethersolve,FP_ethersolve,FN_ethersolve)
                    with open('../ethersolve_metric.json','a') as f:
                        f.write(f'{file}\t{contract_name}\t{precision_ethersolve:.4f}\t{recall_ethersolve:.4f}\t{F1_ethersolve:.4f}\n')

                    count_ethersolve += 1
                    precision_ethersolve_all += precision_ethersolve
                    recall_ethersolve_all += recall_ethersolve
                    F1_ethersolve_all += F1_ethersolve
        
                    with open(f'{contract_name}-vandal.csv','r') as f:
                        vandal_result = set()
                        for line in f:
                            vandal_result.add(str(int(line.strip(),16)))

                    if vul_type == 'tx-origin':
                        FP_vandal = vandal_result - gt_offset
                        FN_vandal = gt_offset - vandal_result
                        TP_vandal = vandal_result & gt_offset
                    if vul_type == 're-entrancy':
                        FP_vandal = vandal_result - gt_call_offset
                        FN_vandal = gt_call_offset - vandal_result
                        TP_vandal = vandal_result & gt_call_offset

                    with open('../vandal.json','a') as f:
                        f.write(f'{file}\t{contract_name}\t{FP_vandal}\t{FN_vandal}\n')
                    
                    precision_vandal, recall_vandal, F1_vandal = cal_metric(TP_vandal,FP_vandal,FN_vandal)
                    with open('../vandal_metric.json','a') as f:
                        f.write(f'{file}\t{contract_name}\t{precision_vandal:.4f}\t{recall_vandal:.4f}\t{F1_vandal:.4f}\n')

                    count_vandal += 1
                    precision_vandal_all += precision_vandal
                    recall_vandal_all += recall_vandal
                    F1_vandal_all += F1_vandal

                    if not exists(f'{contract_name}-mythril.csv'):
                        if len(gt) == 0:
                            continue
                        else:
                            mythril_result = set()
                    else:
                        with open(f'{contract_name}-mythril.csv','r') as f:
                            mythril_result = set(f.read().split('\n'))
                            mythril_result.discard('')

                    FP_mythril = mythril_result - gt_offset
                    FN_mythril = gt_offset - mythril_result
                    TP_mythril = mythril_result & gt_offset

                    with open('../mythril.json','a') as f:
                        f.write(f'{file}\t{contract_name}\t{FP_mythril}\t{FN_mythril}\n')
                    
                    precision_mythril, recall_mythril, F1_mythril = cal_metric(TP_mythril,FP_mythril,FN_mythril)
                    with open('../mythril_metric.json','a') as f:
                        f.write(f'{file}\t{contract_name}\t{precision_mythril:.4f}\t{recall_mythril:.4f}\t{F1_mythril:.4f}\n')

                    count_mythril += 1
                    precision_mythril_all += precision_mythril
                    recall_mythril_all += recall_mythril
                    F1_mythril_all += F1_mythril

        with open('../esuer_metric.json','a') as f:
            f.write(f'Average\t{precision_esuer_all/count_esuer:.4f}\t{recall_esuer_all/count_esuer:.4f}\t{F1_esuer_all/count_esuer:.4f}\n')

        with open('../ethersolve_metric.json','a') as f:
            f.write(f'Average\t{precision_ethersolve_all/count_ethersolve:.4f}\t{recall_ethersolve_all/count_ethersolve:.4f}\t{F1_ethersolve_all/count_ethersolve:.4f}\n')

        with open('../vandal_metric.json','a') as f:
            f.write(f'Average\t{precision_vandal_all/count_vandal:.4f}\t{recall_vandal_all/count_vandal:.4f}\t{F1_vandal_all/count_vandal:.4f}\n')

        with open('../mythril_metric.json','a') as f:
            f.write(f'Average\t{precision_mythril_all/count_mythril:.4f}\t{recall_mythril_all/count_mythril:.4f}\t{F1_mythril_all/count_mythril:.4f}\n')

if __name__ == '__main__':

    contract_path = join(dirname(__file__),'contracts')
    compare_results()