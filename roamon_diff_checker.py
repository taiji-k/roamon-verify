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


# routinatorの出力したVRPS一覧(CSV)をpyasnが解釈可能な形にしてあるファイルを読み込むだけ
def load_vrps(file_path):
    asndb_vrps = pyasn.pyasn(file_path)
    return asndb_vrps


# RIBファイルをPyASNがパースしたファイルを読み込むってだけ
def load_rib(file_path):
    asndb_rib = pyasn.pyasn(file_path)
    return asndb_rib


# VRPsとRIBのデータと、ASNを1つ与えるとそのASの経路は正常かどうか見てくれる(True: 正常、 False: 食い違いがある(ROA登録アリ、経路広告なしは正常となる) )
# 1.そもそもそのASから経路広告してなかったらTrue
# 2.指定されたASから経路広告してたけど、そのASはROA登録してない場合True
# 3.指定されたASが経路広告しててROA登録もしてたが、ROA登録していないprefixを経路広告してたらFalse
def is_valid_vrp_specified_by_asn(vrps, rib, target_asn):
    # 与えられたASNがVRPsに存在するか調べる
    prefix_list_in_vrps = vrps.get_as_prefixes(target_asn)
    does_exist_in_vrps = not( prefix_list_in_vrps is None)
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
    valid_flag = IPSet(prefix_list_in_rib).issubset(IPSet(prefix_list_in_vrps))

    # if not valid_flag:
    #     logger.debug("VRPS IP: {}   ".format(vrps[target_asn]) )
    #     logger.debug("RIB IP : {}".format(IPSet(rib[target_asn])))

    return valid_flag

# 指定したIP(/32)を含むprefixを経路広告してたASが、そのprefixを正しくROA登録していたかを調べる関数
# 1.そもそも指定されたIPが経路広告されてなかったらTrue
# 2.指定されたIPが経路広告されてたけど、広告してたASが1つもROA登録してない場合True
# 3.指定されたIPが経路広告されててそのASが1つ以上ROA登録してたが、指定したIPをカバーするprefixをROA登録してなければFalse
def is_valid_vrp_specified_by_ip(vrps, rib, target_ip):
    ip_lookup_result_rib = rib.lookup(target_ip)

    # asnが存在しない場合, (None, None)が帰ってくる。ある場合は(1234, '8.8.8.0/24')とか。
    does_exist_in_rib = ip_lookup_result_rib[0] is not None
    if not does_exist_in_rib:
        logger.debug("ASN doesn't exist in RIB")
        # そもそもRIBにないASNは単に広告してないだかもしれないのでTrue
        return True

    target_asn = ip_lookup_result_rib[0]
    target_prefix = ip_lookup_result_rib[1]

    # ASNはVRPsにあるか調べる
    # TODO: pyasnのget_as_prefixes()はget_as_prefixes_effective()とどう違う？帰ってくるのがsetとlistという違いがあるが...
    prefix_list_in_vrps = vrps.get_as_prefixes(target_asn)
    does_exist_in_vrps = prefix_list_in_vrps is not None
    if not does_exist_in_vrps:
        logger.debug("ASN doesn't exist in VRPs")
        return True

    logger.debug("target_prefix: {}".format(target_prefix))

    # ROAに登録されてるプレフィックスは、指定されたIPをカバーする現実で広告されてるPrefixをカバーできてるか調べる
    # RIBのエントリのprefixは、必ずROA登録されてるprefixよりも小さいはず。(割り当て時より細分化して広告されることはあっても逆はないはず)
    valid_flag = IPSet([target_prefix]).issubset(IPSet(prefix_list_in_vrps))

    return valid_flag

# ファイルパスを与えるとVRPsとRIBのCSVファイルを読み込む
def load_all_data(file_path_vrps, file_path_rib):
    dummy_vrps = load_vrps(file_path_vrps)
    logger.debug("finish load vrps")
    dummy_rib = load_rib(file_path_rib)
    logger.debug("finish load rib")

    # logger.info("all_asn_in_VRPs {}".format(len(dummy_vrps.keys())))
    # logger.info("all_asn_in_RIB  {}".format(len(dummy_rib.keys())))
    return {"vrps": dummy_vrps, "rib": dummy_rib}


# ASNのリストを指定して、RIBとVRPsの食い違いがないか調べる
def check_specified_asns(vrps, rib, target_asns):
    #count = 0
    for asn in tqdm(target_asns):
        print('{} {}'.format(str(asn), is_valid_vrp_specified_by_asn(vrps, rib, asn)))
        # if count > 10000: break
        # count += 1

def check_specified_ips(vrps, rib, target_ips):
    for ip in tqdm(target_ips):
        print('{} {}'.format(str(ip), is_valid_vrp_specified_by_ip(vrps, rib, ip)))

# VRPsに出てくる全てのASNに対して、RIBとVRPsの食い違いがないか調べる
def check_all_asn_in_vrps(vrps, rib):
    all_target_asns = vrps.keys()
    check_specified_asns(vrps, rib, all_target_asns)


def main():
    # テスト...このスクリプト単体で実行することは通常は想定していない
    data = load_all_data("/Users/user1/temp/vrps.csv", "/Users/user1/temp/ip-as_rib.list")
    check_all_asn_in_vrps(data["vrps"], data["rib"])


if __name__ == '__main__':
    main()
