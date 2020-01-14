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

# routinatorの出力したVRPS一覧はCSVになってるので、それを読み込む
def load_vrps(file_path):
    result_vrps = {}
    with open(file_path) as f:
        reader = csv.reader(f)
        for row in reader:
            asn = int(row[0][2:])  # ASNは頭に"AS"とついてるのでそれを除外している
            prefix = IPSet([row[1]])
            if not asn in result_vrps:
                result_vrps[asn] = IPSet([])

            # 1つのASが複数のIPアドレスを持つ場合がある
            result_vrps[asn] = result_vrps[asn] | prefix
    return result_vrps


def load_rib_child(csv_row):
    result_rib = {}
    for row in tqdm(csv_row):
        try:
            prefix = IPSet([row[0]])
            asn = int(row[1])
        except:
            logger.debug("IndexError")
            continue
        if not asn in result_rib:
            result_rib[asn] = IPSet([])

        # 1つのASが複数のIPアドレスを持つ場合がある...?
        result_rib[asn] = result_rib[asn] | prefix

    return result_rib

def load_rib(file_path):
    result_rib = {}
    with open(file_path) as f:
        reader = csv.reader(f)

        num_multh_process = 10
        p = Pool(num_multh_process)


        all_row = []
        for row in tqdm(reader):
            all_row.append(row)

        n = math.ceil(len(all_row) / num_multh_process)
        parted_all_row = [all_row[idx: min(idx + n, n)] for idx in range(0,len(all_row), n)]
        logger.debug("list parted!!")
        result = p.map(load_rib_child, parted_all_row)
        for res in result:
            result_rib.update(res)


            # # logger.debug("asn: *{}*, prefix: *{}*".format(row[1], row[0]))
            #
            #
            #
            # prefix = IPSet([row[0]])
            #
            #
            # asn = int(row[1])
            # if not asn in result_rib:
            #     result_rib[asn] = IPSet([])
            #
            # # 1つのASが複数のIPアドレスを持つ場合がある...?
            # result_rib[asn] = result_rib[asn] | prefix
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

    return rib[target_asn].issubset(vrps[target_asn])


def main():
    all_target_asns = dummy_vrps.keys()
    logger.info("all_asn_in_VRPs {}".format(len(all_target_asns)))

    for asn in all_target_asns:
        print( '{} {}'.format(str(asn), is_valid(dummy_vrps, dummy_rib, asn)) )


if __name__ == '__main__':
    main()

