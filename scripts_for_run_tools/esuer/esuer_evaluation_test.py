# Standard lib imports
import csv
import timeout_decorator
from rich.logging import RichHandler
import time
import logging
import json
import os
# from rich.progress import track
from os.path import abspath, dirname, join, exists
import sys
sys.setrecursionlimit(10000)

tool_path = dirname(abspath(__file__))
src_path = join(tool_path, '..', '..')
evaluation_path = join(tool_path, "..")
fail_path = join(evaluation_path, '..', 'debug', 'top1w_fail')

# Prepend .. to $PATH so the project modules can be imported below
sys.path.insert(0, src_path)
sys.path.insert(0, join(evaluation_path, '..', 'pyevmasm'))

# Local project imports
import esuer

project = 'tx_top1w'
output = 'output'
tool = 'esuer'


data_PATH = join(evaluation_path, "..", "cfg_evm_data")
target_path = join(data_PATH, project)
output_path = join(data_PATH, output)
os.chdir(output_path)
if not os.path.exists(f'{project}_{tool}'):
    os.mkdir(f'{project}_{tool}')

log = logging.getLogger(__name__)

logging.basicConfig(
    level="INFO",
    handlers=[RichHandler(rich_tracebacks=True), logging.FileHandler(
        join(tool_path, f'{tool}_2.log'), 'w')]
        # join(tool_path, 'tmp.log'), 'a')]
)


@timeout_decorator.timeout(120)
def test_tool(bytecode):
    cfg = esuer.Recover(bytecode, False, False, False)
    return cfg


def save_cfg(cfg,write_dir):

    dot_file = f'{filename}.dot'
    if exists(join(write_dir,dot_file)):
        return

    g = esuer.ControlFlowGraph(cfg.internal.contract)

    with open(join(write_dir,dot_file), 'w') as t:
        t.write(g.dot())
        t.flush()

def save_concract_info(cfg,write_dir):

    with open(join(write_dir,'hex'),'w') as f:
        f.write(cfg.internal.filedata.decode())
    
    with open(join(write_dir,'asm'),'w') as f:
        csvwriter = csv.writer(f)
        insns = [(x,y.name) for x,y in cfg.internal.contract.insns.items()]
        csvwriter.writerows(insns)

    with open(join(write_dir,'bb'),'w') as f:
        offsets = list(cfg.internal.contract.blockmap.keys())
        for offset in offsets:
            f.write(f'{offset}\n')

    with open(join(write_dir,'bb_id_offset'),'w') as f:
        csvwriter = csv.writer(f)
        bbs = [(id(x),x.offset) for x in cfg.internal.contract.blocks if isinstance(x,esuer.SSABasicBlock)]
        csvwriter.writerows(bbs)
    
    with open(join(write_dir,'succ'),'w') as f:
        csvwriter = csv.writer(f)
        edges = set()
        for bb in cfg.internal.contract.blocks:
            if not isinstance(bb,esuer.SSABasicBlock):
                continue
            for succ in bb.get_suss():
                edges.add((id(bb),id(succ)))
        csvwriter.writerows(edges)

@timeout_decorator.timeout(120)
def save_path(cfg):

    ssablockmap = cfg.internal.contract.ssablockmap
    start_bbs = ssablockmap[0]
    assert len(start_bbs) == 1
    start_bb = start_bbs[0]
    node_paths = {}

    def dfs_path_num(bb,path):

        if bb in path:
            return 0

        if bb in node_paths:
            return node_paths[bb]
        
        path = list(path)
        
        path_num = 0
        succs = bb.get_suss()
        for succ in succs:
            path_num += dfs_path_num(succ,tuple(path+[bb]))
        
        if len(succs) == 0:
            path_num = 1
        
        node_paths[bb] = path_num

        return path_num

    paths = dfs_path_num(start_bb,())
    
    return paths


if __name__ == '__main__':

    write_file = f'{project}_{tool}.csv'
    write_path_file = f'{project}_{tool}_path.csv'

    os.chdir(target_path)

    file = sys.argv[1]
    # file = "0x3b2d16288440b9571d1a42f6d4718742cd6bf7fd.json"

    if file.endswith('hex'):
        filename = sys.argv[2]
        bytecode = open(file, 'r').read()
    else:
        filename = os.path.splitext(file)[0]

        with open(file, 'r') as f:
            data = json.load(f)
            bytecode = bytes(data["bytecode"][2:], encoding='utf-8')

    log.info(f"[*] Analyzing {filename}")

    time_start = time.time()

    try:
        cfg = test_tool(bytecode)

    except Exception as e:
        # log.error(e)
        result = 'Error'
        used_time = 0
        error_info = str(e)
        os.system(f"cp {file} {fail_path}")
    else:
        time_end = time.time()
        result = 'Success'
        used_time = time_end-time_start
        error_info = ''
        log.info(f"[*] Analyzing done in {used_time} s")

        work_dir = join(output_path, f'{project}_{tool}',filename)
        if not exists(work_dir):
            os.mkdir(work_dir)

        log.info('[*] save cfg')
        save_concract_info(cfg, work_dir)
        save_cfg(cfg, work_dir)
        try:
            num_paths = save_path(cfg)
        except Exception as e:
            log.error("cannot save paths")
        else:
            with open(join(evaluation_path,write_path_file), 'a', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow([filename, num_paths])
        log.info('[*] save cfg done')

    log.info("[*] start record")
    os.chdir(evaluation_path)
    with open(write_file, 'a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([filename, result, used_time, error_info])

    log.info("[*] record done")
