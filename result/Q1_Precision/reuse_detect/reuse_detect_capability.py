import binascii
import json
import re
from os.path import join,exists,abspath,dirname
from os import mkdir,listdir
from contextlib import suppress
import subprocess

import sys
sys.path.append(join(dirname(dirname(dirname(__file__))),'esuer'))
from esuer.evmasm import *
import esuer

class CompileError(Exception):
    pass


def convert_to_standard_json(es_doc):
    assert es_doc["Language"] == "Solidity", "not Solidity"
    res = {
        "language": es_doc["Language"],
        "sources": {source["FileName"]: {"content": source["Code"]} for source in es_doc["SourceCodes"]},
    }
    settings_str = es_doc.get("Settings", "")
    if settings_str:
        settings = json.loads(settings_str)
        # NOTE kava/Merlin 特殊情况
        with suppress(KeyError):
            del settings["compilationTarget"]
    else:
        settings = {
            "optimizer": {
                "enabled": es_doc["OptimizationUsed"],
                "runs": int(es_doc["Runs"]),
            }
        }
        if es_doc["EVMVersion"] != "Default":
            settings["evmVersion"] = es_doc["EVMVersion"]

    settings["outputSelection"] = {
            "*": {
                "*": ["evm.assembly","evm.deployedBytecode.object","evm.legacyAssembly"]
            }
        }
    
    res["settings"] = settings
    return res

def compile_standard_json(std_json, compiler_version):
    compiler_version_pattern = re.compile(r"^v(\d+\.\d+\.\d+)")
    m = compiler_version_pattern.search(compiler_version)
    assert m, "version error"
    version = m.group(1)
    version_tuple = tuple(map(int, version.split(".")))
    if version_tuple < (0, 4, 11):
        raise CompileError(f"compiler version too low")

    exe = f"~/.solc-select/artifacts/solc-{version}/solc-{version}"

    cmd = f"{exe} --standard-json"
    p = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        input=json.dumps(std_json).encode("utf-8"),
    )
    if p.returncode != 0:
        raise CompileError(f"returncode != 0, stdout: {p.stdout.decode('utf-8')}, stderr: {p.stderr.decode('utf-8')}")

    d = json.loads(p.stdout.decode("utf-8", errors="replace"))

    errors = [err.get("formattedMessage") for err in d.get("errors", ()) if err.get("severity") == "error"]
    if errors:
        raise CompileError(json.dumps(errors))

    return d

def compile_esdoc(es_doc):

    std_json = convert_to_standard_json(es_doc['source'])
    compile_res = compile_standard_json(std_json, es_doc['source']["CompilerVersion"])

    for source_file in compile_res['contracts']:
        for contract in compile_res['contracts'][source_file]:
            if compile_res['contracts'][source_file][contract]['evm']['legacyAssembly'] and contract == es_doc['source']['ContractName']:
                hex = compile_res['contracts'][source_file][contract]['evm']['deployedBytecode']['object']
                lasm = compile_res['contracts'][source_file][contract]['evm']['legacyAssembly']['.data']['0']['.code']
                asm = compile_res['contracts'][source_file][contract]['evm']['assembly']
                if '.auxdata' in compile_res['contracts'][source_file][contract]['evm']['legacyAssembly']['.data']['0']:
                    auxdata = compile_res['contracts'][source_file][contract]['evm']['legacyAssembly']['.data']['0']['.auxdata']
                else:
                    auxdata = None
                return hex, lasm, asm, auxdata

    raise Exception('cannot find target contract and legacy assembly')

def reused_tag_from_asm(lasm,hex):

    # collect reused tags
    tags = ['tag 0']
    current_tag = 'tag 0'
    tag_use = {}
    tag_used = set()
    tag_reused = set()
    last_tag_away = False
    have_content = False
    for inst in lasm:
        if inst['name'] == 'tag':
            new_tag = f"tag {inst['value']}"
            if not last_tag_away and have_content:
                if current_tag not in tag_use:
                    tag_use[current_tag] = []
                tag_use[current_tag].append(new_tag)
            tags.append(new_tag)
            current_tag = new_tag
            last_tag_away = False
            have_content = False
            continue
        elif inst['name'] == 'PUSH [tag]':
            if current_tag not in tag_use:
                tag_use[current_tag] = []
            used_tag = f"tag {inst['value']}"
            tag_use[current_tag].append(used_tag)
            if used_tag in tag_used:
                tag_reused.add(used_tag)
            tag_used.add(used_tag)
        elif inst['name'] in ['JUMP','REVERT','RETURN','STOP','INVALID','SELFDESTRUCT']:
            last_tag_away = True
        have_content = True
    
    # collect offset for each tag
    insns = list(EVMAsm.disassemble_all(binascii.unhexlify(hex[2:]), 0))
    insns.sort(key=lambda x: x.pc)
    max_pc = insns[-1].pc
    tag_pc = {'tag 0':{"start":0}}
    n = 1
    for x in insns:
        if x.name == "JUMPDEST":
            tag_pc[tags[n]] = {"start": x.pc}
            n += 1
    
    for n,tag in enumerate(tags):
        if n+1 < len(tags):
            tag_pc[tag]['end'] = tag_pc[tags[n+1]]["start"]-1
        else:
            tag_pc[tag]['end'] = max_pc

    reused_tag = set([tag_pc[x]['start'] for x in tag_reused])
    update = True
    while update:
        update = False
        origin_tag_reused = set(list(tag_reused))
        for tag in origin_tag_reused:
            if tag in tag_use:
                tag_reused.update(tag_use[tag])
        if tag_reused != origin_tag_reused:
            update = True

    tag_reused = sorted(tag_reused,key=lambda x:tag_pc[x]['start'])
    reused_offset = []
    for tag in tag_reused:
        tag_offset = (tag_pc[tag]["start"],tag_pc[tag]['end'])
        if len(reused_offset) == 0:
            reused_offset.append(tag_offset)
            continue
        if tag_offset[0] == reused_offset[-1][1] + 1:
            new_offset = (reused_offset[-1][0],tag_offset[1])
            reused_offset[-1] = new_offset
        else:
            reused_offset.append(tag_offset)

    tag_info = {'tags_offset':tag_pc,'tag_use':tag_use}

    return reused_offset, reused_tag, tag_info

def reused_bb_from_esuer(hex):
    # get reused BB from esuer
    try:
        target = esuer.Recover(hex,[],False,False)
    except Exception:
        raise Exception("Esuer fail")

    reused = set()
    for offset in target.internal.contract.ssablockmap:
        if len(target.internal.contract.ssablockmap[offset]) > 1:
            reused.add(offset)

    reused = sorted(list(reused))

    return reused

def analyze_file(filepath):
    count = 0
    all_precision = 0
    all_recall = 0
    all_F1 = 0
    with open(filepath,'r') as rf:
        for line in rf:
            file, TP, FP, FN = line.strip().split(',')
            try:
                precision = int(TP) / (int(TP) + int(FP))
                recall = int(TP) / (int(TP) + int(FN))
                F1 = precision * recall * 2 / (precision + recall)
            except Exception:
                print(file)
                continue
            with open(f'{filepath}_metric','a') as wf:
                wf.write(f'{file},{precision:.4f},{recall:.4f},{F1:.4f}\n')
            count += 1
            all_precision += precision
            all_recall += recall
            all_F1 += F1

    with open(f'{filepath}_metric','a') as wf:
        wf.write(f'Average,{all_precision/count:.4f},{all_recall/count:.4f},{all_F1/count:.4f}\n')

def debug(file):
    with open(file,'r') as f:
        es_doc = json.load(f)

    hex, lasm, asm, auxdata = compile_esdoc(es_doc)
    assert len(f'0x{hex}') == len(es_doc['bytecode']), "different hex"
        

    if auxdata:
        bytecode = es_doc['bytecode'][:-len(auxdata)]
    else:
        bytecode = es_doc['bytecode']
    reused_offset, reused_tag, tag_info = reused_tag_from_asm(lasm,bytecode)
    reused_bb = reused_bb_from_esuer(es_doc['bytecode'])

    T = 0
    FP = 0
    FN = 0
    errors = {"FP":[]}
    for bb in reused_bb:
        if not any([bb>=x[0] and bb < x[1] for x in reused_offset]):
            FP += 1
            errors['FP'].append(bb)
        else:
            T += 1
            reused_tag.discard(bb)
    
    FN = len(reused_tag)
    errors['FN'] = list(reused_tag)

def main():

    dataset_path = "/root/projects/ethereum_decompiler/cfg_evm_data/tx_top1w"

    for file in listdir(abspath(dataset_path)):

        with open(join(dataset_path,file),'r') as f:
            es_doc = json.load(f)

        try:
            hex, lasm, asm, auxdata = compile_esdoc(es_doc)
            assert len(f'0x{hex}') == len(es_doc['bytecode']), "different hex"

            if auxdata:
                bytecode = es_doc['bytecode'][:-len(auxdata)]
            else:
                bytecode = es_doc['bytecode']
            reused_offset, reused_tag, tag_info = reused_tag_from_asm(lasm,bytecode)
            reused_bb = reused_bb_from_esuer(es_doc['bytecode'])
        except Exception as e:
            with open('reuse_detect_error','a') as f:
                f.write(f'{file},{e}\n')
            continue

        T = 0
        FP = 0
        FN = 0
        errors = {"FP":[]}
        for bb in reused_bb:
            if not any([bb>=x[0] and bb < x[1] for x in reused_offset]):
                FP += 1
                errors['FP'].append(bb)
            else:
                T += 1
                reused_tag.discard(bb)
        
        FN = len(reused_tag)
        errors['FN'] = list(reused_tag)

        with open('reuse_detect_result','a') as f:
            f.write(f'{file},{T},{FP},{FN}\n')

        if FP or FN:
            record = {"errors":errors,"esuer":reused_bb,"asm_tag":tag_info,"asm":asm}
            with open(join('result',file),'w') as f:
                f.write(json.dumps(record,indent=4).replace('\\n','\n'))


if __name__ == '__main__':

    main()
    # debug(join("/root/projects/ethereum_decompiler/cfg_evm_data/tx_top1w",'0x7c87b6ff9c2ec3466c6fac9b89bb58a4bf12a5bb.json'))

    analyze_file('reuse_detect_result')
