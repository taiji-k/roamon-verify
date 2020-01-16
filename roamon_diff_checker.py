# encoding: UTF-8

from netaddr import *
import logging
import csv
from tqdm import tqdm
from multiprocessing import Pool
import math
import pyasn

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# リストをn等分する
def divide_list_equally(target_list, divide_num):
    n = math.ceil(len(target_list) / divide_num)
    divided_list = [target_list[idx: min(idx + n, len(target_list))] for idx in range(0, len(target_list), n)]
    return divided_list


# VRPsをマルチプロセスで読み込む際に実際の読み込み部分をやる関数
def load_vrps_worker(csv_row):
    result_vrps = {}
    for row in tqdm(csv_row):
        asn = int(row[0][2:])  # ASNは頭に"AS"とついてるのでそれを除外している
        prefix = IPSet([row[1]])
        if not asn in result_vrps:
            result_vrps[asn] = IPSet([])

        # 1つのASが複数のIPアドレスを持つ場合がある...はず
        result_vrps[asn] = result_vrps[asn] | prefix

    logger.debug("load vrps work finishied. work len is {}".format(len(result_vrps)))
    return result_vrps


# routinatorの出力したVRPS一覧はCSVになってるので、それを読み込む関数
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

        result = p.map(load_vrps_worker, parted_all_row)
        for res in result:
            result_vrps.update(res)
    return result_vrps





# RIBファイルをPyASNがパースしたファイルを読み込むってだけ
def load_rib(file_path):
    asndb = pyasn.pyasn(file_path)
    return asndb


# VRPsとRIBのデータと、ASNを1つ与えるとそのASの経路は正常かどうか見てくれる(True: 正常、 False: 食い違いがある(ROA登録アリ、経路広告なしは正常となる) )
def is_valid(vrps, rib, target_asn):
    # 与えられたASNがVRPsに存在するか調べる
    does_exist_in_vrps = target_asn in vrps
    if not does_exist_in_vrps:
        # 基本的にこっちの条件分岐はありえない。VRPsに入ってるASNしかこの関数に渡されないので。
        logger.debug("ASN doesn't exist in VRPs")
        return True

    prefix_list_in_rib = rib.get_as_prefixes(target_asn)
    # 与えられたASNがRIBに存在するか調べる
    does_exist_in_rib = not (prefix_list_in_rib is None)
    if not does_exist_in_rib:
        logger.debug("ASN doesn't exist in RIB")
        # そもそもRIBにないASNは単に広告してないだかもしれないのでTrue
        return True

    # ROAに登録されてるプレフィックスは現実で広告されてるプレフィックスをカバーできてるか調べる
    # RIBのエントリのprefixは、必ずROA登録されてるprefixよりも小さいはず。(割り当て時より細分化して広告されることはあっても逆はないはず)
    valid_flag = IPSet(prefix_list_in_rib).issubset(vrps[target_asn])

    # if not valid_flag:
    #     logger.debug("VRPS IP: {}   ".format(vrps[target_asn]) )
    #     logger.debug("RIB IP : {}".format(IPSet(rib[target_asn])))

    return valid_flag


# ファイルパスを与えるとVRPsとRIBのCSVファイルを読み込む
def load_all_data(file_path_vrps, file_path_rib):
    dummy_vrps = load_vrps(file_path_vrps)
    logger.debug("finish load vrps")
    dummy_rib = load_rib(file_path_rib)
    logger.debug("finish load rib")

    logger.info("all_asn_in_VRPs {}".format(len(dummy_vrps.keys())))
    # logger.info("all_asn_in_RIB  {}".format(len(dummy_rib.keys())))
    return {"vrps": dummy_vrps, "rib": dummy_rib}


# ASNのリストを指定して、RIBとVRPsの食い違いがないか調べる
def check_specified_asn(vrps, rib, target_asns):
    count = 0
    for asn in tqdm(target_asns):
        print('{} {}'.format(str(asn), is_valid(vrps, rib, asn)))
        # if count > 10000: break
        # count += 1


# VRPsに出てくる全てのASNに対して、RIBとVRPsの食い違いがないか調べる
def check_all_asn_in_vrps(vrps, rib):
    all_target_asns = vrps.keys()
    check_specified_asn(vrps, rib, all_target_asns)


def main():
    # テスト...このスクリプト単体で実行することは通常は想定していない
    data = load_all_data("/Users/user1/temp/vrps.csv", "/Users/user1/temp/ip-as_rib.list")
    check_all_asn_in_vrps(data["vrps"], data["rib"])


if __name__ == '__main__':
    main()
