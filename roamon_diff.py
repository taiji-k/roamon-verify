# encoding: UTF-8

from mrtparse import *
from netaddr import *
import logging
import csv
from tqdm import tqdm

# logging.basicConfig(level=logging.DEBUG)
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

class MrtEntry:
    def __init__(self):
        self.nlri = []
        self.as_path = []
        self.as4_path = []

    def __repr__(self):
        return "<MrtEntry {} : {} : {}>".format(self.nlri, self.as_path, self.as4_path)

def bgp_attr(attr, mrt_entry):
    # if attr.type == BGP_ATTR_T['ORIGIN']:
#     self.origin = ORIGIN_T[attr.origin]
    # elif attr.type == BGP_ATTR_T['NEXT_HOP']:
    #     self.next_hop.append(attr.next_hop)
    if attr.type == BGP_ATTR_T['AS_PATH']:
        mrt_entry.as_path = []
        for seg in attr.as_path:
            if seg['type'] == AS_PATH_SEG_T['AS_SET']:
                mrt_entry.as_path.append('{%s}' % ','.join(seg['val']))
            elif seg['type'] == AS_PATH_SEG_T['AS_CONFED_SEQUENCE']:
                mrt_entry.as_path.append('(' + seg['val'][0])
                mrt_entry.as_path += seg['val'][1:-1]
                mrt_entry.as_path.append(seg['val'][-1] + ')')
            elif seg['type'] == AS_PATH_SEG_T['AS_CONFED_SET']:
                mrt_entry.as_path.append('[%s]' % ','.join(seg['val']))
            else:
                mrt_entry.as_path += seg['val']
    # elif attr.type == BGP_ATTR_T['MULTI_EXIT_DISC']:
    #     self.med = attr.med
    # elif attr.type == BGP_ATTR_T['LOCAL_PREF']:
    #     self.local_pref = attr.local_pref
    # elif attr.type == BGP_ATTR_T['ATOMIC_AGGREGATE']:
    #     self.atomic_aggr = 'AG'
    # elif attr.type == BGP_ATTR_T['AGGREGATOR']:
    #     self.aggr = '%s %s' % (attr.aggr['asn'], attr.aggr['id'])
    # elif attr.type == BGP_ATTR_T['COMMUNITY']:
    #     self.comm = ' '.join(attr.comm)
    elif attr.type == BGP_ATTR_T['MP_REACH_NLRI']:
        next_hop = attr.mp_reach['next_hop']
        if type != 'BGP4MP':
            return
        for nlri in attr.mp_reach['nlri']:
            mrt_entry.nlri.append('%s/%d' % (nlri.prefix, nlri.plen))
    # TODO: UNREACH NLRIは考慮しなくていい？
    # elif attr.type == BGP_ATTR_T['MP_UNREACH_NLRI']:
    #     if self.type != 'BGP4MP':
    #         return
    #     for withdrawn in attr.mp_unreach['withdrawn']:
    #         self.withdrawn.append(
    #             '%s/%d' % (withdrawn.prefix, withdrawn.plen))
    elif attr.type == BGP_ATTR_T['AS4_PATH']:
        mrt_entry.as4_path = []
        for seg in attr.as4_path:
            if seg['type'] == AS_PATH_SEG_T['AS_SET']:
                mrt_entry.as4_path.append('{%s}' % ','.join(seg['val']))
            elif seg['type'] == AS_PATH_SEG_T['AS_CONFED_SEQUENCE']:
                mrt_entry.as4_path.append('(' + seg['val'][0])
                mrt_entry.as4_path += seg['val'][1:-1]
                mrt_entry.as4_path.append(seg['val'][-1] + ')')
            elif seg['type'] == AS_PATH_SEG_T['AS_CONFED_SET']:
                mrt_entry.as4_path.append('[%s]' % ','.join(seg['val']))
            else:
                mrt_entry.as4_path += seg['val']
    # elif attr.type == BGP_ATTR_T['AS4_AGGREGATOR']:
    #     self.as4_aggr = '%s %s' % (attr.as4_aggr['asn'], attr.as4_aggr['id'])



def td_v2(m, mrt_entry):
    # global peer
    # self.type = 'TABLE_DUMP2'
    # self.flag = 'B'
    # self.ts = m.ts
    if m.subtype == TD_V2_ST['PEER_INDEX_TABLE']:
        # peer = copy.copy(m.peer.entry)
        pass
    elif (m.subtype == TD_V2_ST['RIB_IPV4_UNICAST']
          or m.subtype == TD_V2_ST['RIB_IPV4_MULTICAST']
          or m.subtype == TD_V2_ST['RIB_IPV6_UNICAST']
          or m.subtype == TD_V2_ST['RIB_IPV6_MULTICAST']):
        # self.num = m.rib.seq
        mrt_entry.nlri.append('%s/%d' % (m.rib.prefix, m.rib.plen))
        for entry in m.rib.entry:

            # self.org_time = entry.org_time
            # self.peer_ip = peer[entry.peer_index].ip
            # self.peer_as = peer[entry.peer_index].asn
            #as_path = []
            # self.origin = ''
            # self.next_hop = []
            # self.local_pref = 0
            # self.med = 0
            # self.comm = ''
            # self.atomic_aggr = 'NAG'
            # self.aggr = ''
            #as4_path = []
            # self.as4_aggr = ''
            for attr in entry.attr:
                bgp_attr(attr, mrt_entry)

            # self.print_routes()


def load_rib(file_path):
    d = Reader(file_path)
    result_rib = {}
    for m in tqdm(d):
        m = m.mrt
        mrt_entry = MrtEntry()

        if m.err:
            continue

        if m.type == MRT_T['TABLE_DUMP']:
            # TODO: 実装 !
            pass
        elif m.type == MRT_T['TABLE_DUMP_V2']:
            td_v2(m, mrt_entry)
            logger.debug("{}".format(str(mrt_entry)))
            if(len(mrt_entry.as_path) <= 0):
                logger.debug("AS_PATH is 0!")
                continue
            asn = mrt_entry.as_path[0]
            # logger.debug("{}".format(str(mrt_entry)))
            prefix = IPSet(mrt_entry.nlri)
            result_rib[asn] = prefix
        elif m.type == MRT_T['BGP4MP']:
            # TODO: 実装 !
            pass
    return result_rib
# dummy_vrps = [
#         {"asn": 3333, "prefix": IPSet(['192.0.2.0/24']) },
#         {"asn": 4444, "prefix": IPSet(['10.0.4.0/8']).add('14.0.4.0/8') }
#     ]
#
# dummy_rib = [
#         {"asn": 3334, "prefix": IPSet(['192.0.2.0/24'])},
#         {"asn": 4444, "prefix": IPSet(['10.0.4.0/8']).add('14.0.4.0/8')}
#     ]

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

