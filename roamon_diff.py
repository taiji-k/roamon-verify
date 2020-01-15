# encoding: UTF-8

from mrtparse import *
from netaddr import *
import logging
import csv
from tqdm import tqdm
from multiprocessing import Pool
from multiprocessing import Process
import math

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

dummy_vrps = {
        3333: IPSet(['192.0.2.0/24']),
        4444: IPSet(['10.0.4.0/8']),
        5555: IPSet(['15.0.4.0/8']),
        6666: IPSet(['16.0.4.0/24']),
    }


dummy_rib = {
        3334: IPSet(['192.0.2.0/24']),
        4444: IPSet(['10.0.4.0/8']), #　IPSet(['10.0.4.0/8']).add('14.0.4.0/8')　はできないっぽい
        5555: IPSet(['15.0.4.0/24']),
        6666: IPSet(['16.0.4.0/8']),
    }

def divide_list_equally(target_list, divide_num):
    n = math.ceil(len(target_list) / divide_num)
    divided_list = [target_list[idx: min(idx + n, len(target_list))] for idx in range(0, len(target_list), n)]
    return divided_list

def load_vrps_child(csv_row):
    result_vrps = {}
    for row in tqdm(csv_row):
        asn = int(row[0][2:])  # ASNは頭に"AS"とついてるのでそれを除外している
        prefix = IPSet([row[1]])
        if not asn in result_vrps:
            result_vrps[asn] = IPSet([])

        # 1つのASが複数のIPアドレスを持つ場合がある...?
        result_vrps[asn] = result_vrps[asn] | prefix

    logger.debug("load vrps work finishied. work len is {}".format(len(result_vrps)))
    return result_vrps

# routinatorの出力したVRPS一覧はCSVになってるので、それを読み込む
def load_vrps(file_path):
    result_vrps = {}
    with open(file_path) as f:
        reader = csv.reader(f)

        num_multch_process = 10
        p = Pool(num_multch_process)

        all_row = []
        for row in tqdm(reader):
            all_row.append(row)

        parted_all_row = divide_list_equally(all_row, num_multch_process)
        logger.debug("list parted!! {}".format(len(parted_all_row)))

        result = p.map(load_vrps_child, parted_all_row)
        for res in result:
            result_vrps.update(res)
    return result_vrps


def load_rib_child(csv_row):
    result_rib = {}
    for row in tqdm(csv_row):
        try:
            prefix = row[0]
            asn = int(row[1])
            # logger.debug("ASN: {}".format(asn))
        except:
            logger.debug("IndexError : {}".format(row))
            continue
        if not asn in result_rib:
            result_rib[asn] = []

        # 1つのASが複数のIPアドレスを持つ場合がある...?
        result_rib[asn].append(prefix)

    logger.debug("load rib work finishied. work len is {}".format(len(result_rib)))
    return result_rib

def load_rib(file_path):
    result_rib = {}
    with open(file_path) as f:
        reader = csv.reader(f)

        num_multch_process = 10
        p = Pool(num_multch_process)


        all_row = []
        for row in tqdm(reader):
            all_row.append(row)

        parted_all_row = divide_list_equally(all_row, num_multch_process)
        logger.debug("list parted!! {}".format(len(parted_all_row)))

        result = p.map(load_rib_child, parted_all_row)
        for res in result:
            result_rib.update(res)


    return result_rib


def is_valid(vrps, rib, target_asn):
    # RIBのエントリのprefixは、必ずRIBよりも小さいはず。(割り当て時より細分化して広告されることはあっても逆はないはず)
    # これだと登録がそもそももない場合と外側から区別ができない
    if not target_asn in vrps:
        logger.debug("ASN doesn't exist in VRPs")
        return False
    if not target_asn in rib:
        logger.debug("ASN doesn't exist in RIB")
        return False
    valid_flag = IPSet(rib[target_asn]).issubset(vrps[target_asn])
    # if not valid_flag:
    #     logger.debug("VRPS IP: {}   ".format(vrps[target_asn]) )
    #     logger.debug("RIB IP : {}".format(IPSet(rib[target_asn])))

    return IPSet(rib[target_asn]).issubset(vrps[target_asn])


def load_all_data(file_path_vrps, file_path_rib):
    dummy_vrps = load_vrps(file_path_vrps)
    logger.debug("finish load vrps")
    dummy_rib = load_rib(file_path_rib)
    logger.debug("finish load rib")


    logger.info("all_asn_in_VRPs {}".format(len(dummy_vrps.keys())))
    logger.info("all_asn_in_RIB  {}".format(len(dummy_rib.keys())))
    return {"vrps": dummy_vrps, "rib": dummy_rib}


def check_specified_asn(vrps, rib, target_asns):
    count = 0
    for asn in tqdm(target_asns):
        print('{} {}'.format(str(asn), is_valid(vrps, rib, asn)))
        # if count > 10000: break
        # count += 1


def check_all_asn_in_vrps(dummy_vrps, dummy_rib):
    all_target_asns = dummy_vrps.keys()
    check_specified_asn(dummy_vrps, dummy_rib, all_target_asns)


def main():
    data = load_all_data("/Users/user1/temp/vrps.csv", "/Users/user1/temp/ip-as_rib.list")
    check_all_asn_in_vrps(data["vrps"], data["rib"])


if __name__ == '__main__':
    main()

