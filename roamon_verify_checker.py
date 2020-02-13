# encoding: UTF-8

from netaddr import *
import logging
from tqdm import tqdm
import math
import pyasn
import ipaddress
from enum import Enum

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# リストをn等分する
def divide_list_equally(target_list, divide_num):
    n = math.ceil(len(target_list) / divide_num)
    divided_list = [target_list[idx: min(idx + n, len(target_list))] for idx in range(0, len(target_list), n)]
    return divided_list


# ROVの結果の列挙型
class RovResult(Enum):
    VALID          = (0b0001, "VALID")
    INVALID        = (0b0010, "INVALID")
    NOT_FOUND      = (0b0100, "NOT_FOUND")
    NOT_ADVERTISED = (0b1000, "NOT_ADVERTISED")

    def __init__(self, id, text):
        self.id = id
        self.text = text

    def __str__(self):
        return self.text

# Prefixを指定してのROVの結果
class PrefixRovResultStruct:
    def __init__(self, roved_prefix, matched_advertised_prefix, advertising_asn, rov_result):
        self.roved_prefix = roved_prefix
        self.matched_advertised_prefix = matched_advertised_prefix
        self.advertising_asn = advertising_asn
        self.rov_result = rov_result

    def __str__(self):
        obj_to_dict = {"prefix":self.roved_prefix,
                       "advertised_prefix":self.matched_advertised_prefix,
                       "advertising_asn":self.advertising_asn,
                       "rov_result":self.rov_result
                       }
        return str(obj_to_dict)

# ASNを指定してのROVの結果。 ASが広告するすべてのprefixについてROVした結果が格納される
class AsnRovResultStruct:
    def __init__(self, specified_asn, rov_results_dict):
        self.specified_asn = specified_asn
        self.rov_results_dict = rov_results_dict

        self.advertised_prefixes = None
        if self.rov_results_dict is not None:
            self.advertised_prefixes = self.rov_results_dict.keys()

        self.__does_have_rov_failed_prefix = None

    def __str__(self):
        obj_to_dict = {"asn":self.specified_asn,
                       "rov_results_dict":self.rov_results_dict,
                       }
        return str(obj_to_dict)

    # このASの広告するprefixたちでROVに失敗したものが1つでもないか調べる
    def does_have_rov_failed_prefix(self):
        if self.__does_have_rov_failed_prefix is None:
            for rov_result_struct in self.rov_results_dict.values():
                if rov_result_struct != RovResult.VALID:
                    self.__does_have_rov_failed_prefix = True
                    break
            self.__does_have_rov_failed_prefix = False

        return self.__does_have_rov_failed_prefix


# あるprefixについてROV (Route Origin Validation) する関数
def rov(vrps, rib, specified_prefix):
    # 指定されたprefixにロンゲストマッチするprefixをBGPの経路情報から探す
    target_ip_parsed = ipaddress.ip_network(specified_prefix)
    ip_lookup_result_rib = rib.radix.search_best(str(target_ip_parsed.network_address), target_ip_parsed.prefixlen)

    # 経路広告されてなかったならここで終了
    does_exist_in_rib = ip_lookup_result_rib is not None
    if not does_exist_in_rib:
        logger.debug("ASN doesn't exist in RIB")
        return PrefixRovResultStruct(specified_prefix, "", "", RovResult.NOT_ADVERTISED)

    # ロンゲストマッチしたprefixと、それを広告してたASNを取り出す
    advertising_asn = ip_lookup_result_rib.asn
    matched_advertised_prefix = ip_lookup_result_rib.prefix

    # TODO: pyasnのget_as_prefixes()はget_as_prefixes_effective()とどう違う？帰ってくるのがsetとlistという違いがあるが...
    prefix_list_in_vrps = vrps.get_as_prefixes(advertising_asn)
    does_exist_in_vrps = prefix_list_in_vrps is not None

    # ロンゲストマッチしたprefixを広告していたASNが、ROAに登録されてなかった場合はここで終了
    if not does_exist_in_vrps:
        logger.debug("ASN doesn't exist in VRPs")
        return PrefixRovResultStruct(specified_prefix, matched_advertised_prefix, advertising_asn, RovResult.NOT_FOUND)

    #logger.debug("target_prefix: {}".format(matched_advertised_prefix))

    # ROAに登録されてるプレフィックスは、BGP経路情報の上で、指定されたprefixにロンゲストマッチしたprefixをカバーできているか調べる
    # RIBのエントリのprefixは、必ずROA登録されてるprefixよりも小さいはず。(割り当て時より細分化して広告されることはあっても逆はないはず)
    valid_flag = IPSet([matched_advertised_prefix]).issubset(IPSet(prefix_list_in_vrps))
    rov_result = RovResult.VALID if valid_flag else RovResult.INVALID

    result_struct = PrefixRovResultStruct(specified_prefix, matched_advertised_prefix, advertising_asn, rov_result)
    return result_struct


# 与えられたASNが広告してたprefixを調べ、全部ROVする
def rov_with_asn(vrps, rib, specified_asn):
    # 与えられたASNが広告してるprefixを調べる
    prefix_list_in_rib = rib.get_as_prefixes(specified_asn)

    # 広告してなければここで終了
    does_exist_in_rib = not (prefix_list_in_rib is None)
    if not does_exist_in_rib:
        logger.debug("ASN doesn't exist in RIB")
        return AsnRovResultStruct(specified_asn, {})

    # 与えられたASNが広告してたprefixを全部ROVする
    result_dict ={}
    for prefix in prefix_list_in_rib:
        result_dict[prefix] = rov(vrps, rib, prefix)

    asn_rov_result_struct = AsnRovResultStruct(specified_asn, result_dict)
    return asn_rov_result_struct


# 指定されたASがROA登録したprefixが他のROA登録していないASに勝手に(同じかより小さいプレフィックスで)経路広告されていないか調べる
# TODO: 検討して使わないなら消す
def is_violated_asn(vrps, rib, specified_asn):
    #　指令されたASがROA登録したprefixを調べる
    registered_prefixes_by_target_asn = vrps.get_as_prefixes(specified_asn)

    # 指令されたASがROA登録したprefixたちについて、それより小さい(経路選択時に勝っちゃう)prefixが経路広告されてないか調べる
    longest_matched_prefixes_and_asn = []
    for prefix in registered_prefixes_by_target_asn:
        prefix_parsed = ipaddress.ip_network(prefix)
        # logger.debug("HOGEHOGE! netaddr {} netpref {} org_pref {}".format(network_addr, network_prefix, prefix) )
        matched = rib.radix.search_best(str(prefix_parsed.network_address), prefix_parsed.prefixlen)
        # 検索失敗時はNoneが返る
        if matched is not None:
            longest_matched_prefixes_and_asn.append({"prefix":matched.prefix, "asn":matched.asn})

    # 指定されたASがROA登録してたPrefixより、経路選択時に優先されちゃう(=プレフィックスが同じかより小さい)現実に広告されてた経路を広告してたASは、ROA登録してたのか確かめる
    for suspiciouses in longest_matched_prefixes_and_asn:
        registered_prefixes = vrps.get_as_prefixes( suspiciouses["asn"] )
        is_violate_flag = None
        # そのASがROA登録してない場合
        if registered_prefixes is None:
            logger.debug("longest_matched_prefix {} advertised by AS{} are not ROA registered.".format(suspiciouses["prefix"], suspiciouses["asn"]) )
            # ROA登録してないだけで意図した正当な経路広告なのか、それとも経路ハイジャックなのかわからない...
            # なので潜在的に経路ハイジャックですということでTrue
            is_violate_flag = True
        else:
            # そのASがROA登録しててかつ、経路広告してるprefixがROA登録されてるprefixでちゃんとカバーされてるかどうか
            # logger.debug("HOGEHOGE! prefix {} asn {}".format(suspiciouses["prefix"], suspiciouses["asn"]) )
            is_roa_registered = IPSet( [suspiciouses["prefix"]] ).issubset(IPSet(vrps.get_as_prefixes( suspiciouses["asn"] )))
            is_violate_flag = not is_roa_registered

        # TODO: プリントじゃなくてなんか返す形にしたほうがいい...
        logger.info("{} {} {} {}".format(specified_asn, suspiciouses["prefix"], suspiciouses["asn"], is_violate_flag))


# 指定されたIPアドレス(/32に限らない)を経路広告してたASと、それをROA登録したASが同じかどうか調べる
# TODO: これROVとやること被ってるので消す?
def is_violated_prefix(vrps, rib, specified_prefix):
    # 指定されたIPアドレス(/32に限らない)にロンゲストマッチするprefixを広告してるASを探す
    specified_prefix_parsed = ipaddress.ip_network(specified_prefix)
    matched_in_rib = rib.radix.search_best(str(specified_prefix_parsed.network_address), specified_prefix_parsed.prefixlen)
    is_violated_flag = None
    # 検索失敗時(指定IPは経路広告されていない)
    if matched_in_rib is None:
        logger.debug("This ip {} is not longest matched in RIB.".format(specified_prefix))
        is_violated_flag = False
        return is_violated_flag

    route_advertising_asn = matched_in_rib.asn

    # 指定されたIPアドレス(/32に限らない)にロンゲストマッチするprefixをROA登録してるASを調べる
    matched_in_vrps = rib.radix.search_best(str(specified_prefix_parsed.network_address), specified_prefix_parsed.prefixlen)
    # ROA登録されてなかった場合、単にROA登録してないだけであって経路ハイジャックかどうか全くわからんのでFalse
    if matched_in_vrps is None:
        logger.debug("This ip {} is not longest matched in VRPs.".format(specified_prefix))
        is_violated_flag = False
        return is_violated_flag
    route_registering_asn = matched_in_vrps.asn

    # 経路広告してるASとROA登録したASが違うなら経路ハイジャックとしてる.
    #  だけど、例えばROA登録を、AS hogeが/16で、AS fugaが/24でしていたとする。経路広告はAS hogeのみが行ってた場合、おそらく当事者たちでは合意が取れているにもかかわらず「経路ハイジャック！」として検知されてしまう (検索でヒットするのはAS fugaのほうだから、ROA登録したASと広告してるASが異なるという判断)
    #  しかし、ROAを使ってOrigin ASを検証する場合、上のようなのは「OriginASが正当でない」として検出されるワケだから、別にいっか！ROAをちゃんと管理しないやつがわるい。
    is_violated_flag = not (route_advertising_asn == route_registering_asn)

    return is_violated_flag


# ファイルパスを与えるとVRPsとRIBのpyasn用のファイルを読み込む
def load_all_data(file_path_vrps, file_path_rib):
    asndb_vrps = pyasn.pyasn(file_path_vrps)
    logger.debug("finish load vrps from {}".format(file_path_vrps))
    asndb_rib = pyasn.pyasn(file_path_rib)
    logger.debug("finish load rib from {}".format(file_path_rib))

    return {"vrps": asndb_vrps, "rib": asndb_rib}


# ASNのリストを渡し、そのASらが広告している全てのprefixに対してROVを行う
def check_specified_asns(vrps, rib, target_asns):
    asn_rov_result_struct_dict = {}
    for asn in tqdm(target_asns):
        asn_rov_result_struct = rov_with_asn(vrps, rib, asn)
        logger.debug(" restype: {} res:   {}".format(type(asn_rov_result_struct), str(asn_rov_result_struct) ))

        # 処理が進むにつれ結果がでてきてほしい(貯めて最後に一気に出るのはいや)のでここでプリントしてしまう
        for prefix, rov_res in asn_rov_result_struct.rov_results_dict.items():
            print(asn, end="\t")
            print(prefix, end="\t")
            # print(rov_res.matched_advertised_prefix, end="\t")
            # print(rov_res.advertising_asn, end="\t")
            print(rov_res.rov_result)

        asn_rov_result_struct_dict[asn] = asn_rov_result_struct
    return asn_rov_result_struct_dict


# prefixのリストを渡し、全てについてROVをする
def check_specified_prefixes(vrps, rib, specified_prefixes):
    result = {}
    for prefix in tqdm(specified_prefixes):
        result[prefix] = rov(vrps, rib, prefix)

        # 処理が進むにつれ結果がでてきてほしいのでここでプリントしてしまう
        print(prefix, end="\t")
        # print(result[prefix].matched_advertised_prefix, end="\t")
        # print(result[prefix].advertising_asn, end="\t")
        print(result[prefix].rov_result)

    return result

# TODO: 検討して使わないなら消す
def check_violation_specified_asns(vrps, rib, target_asns):
    for asn in tqdm(target_asns):
        is_violated_asn(vrps, rib, asn)


# IPアドレス("8.8.8.0/24"とか"8.8.8.8"とか)を与えて、経路ハイジャック的なのを調べる
# TODO: 検討して使わないなら消す
def check_violation_specified_prefixes(vrps, rib, specified_prefixes):
    for prefix in tqdm(specified_prefixes):
        print('{} {}'.format(str(prefix), is_violated_prefix(vrps, rib, prefix)))


# VRPsに出てくる全てのASNに対して、RIBとVRPsの食い違いがないか調べる
def check_all_asn_in_vrps(vrps, rib):
    all_target_asns = set()
    for node in vrps.radix.nodes():
        all_target_asns.add(node.asn)

    return check_specified_asns(vrps, rib, all_target_asns)

def check_all_prefixes_in_vrps(vrps, rib):
    all_target_prefixes = set()
    for node in vrps.radix.nodes():
        all_target_prefixes.add(node.prefix)

    return check_specified_prefixes(vrps, rib, all_target_prefixes)

# TODO: 検討して使わないなら消す
def check_violation_all_asn_in_vrps(vrps, rib):
    all_target_asns = set()
    for node in vrps.radix.nodes():
        all_target_asns.add(node.asn)

    check_violation_specified_asns(vrps, rib, all_target_asns)


def main():
    # テスト...このスクリプト単体で実行することは通常は想定していない
    data = load_all_data("/Users/user1/temp/vrps.csv", "/Users/user1/temp/ip-as_rib.list")
    check_all_asn_in_vrps(data["vrps"], data["rib"])


if __name__ == '__main__':
    main()
