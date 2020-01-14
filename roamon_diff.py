# encoding: UTF-8

from mrtparse import *
from netaddr import *
import logging

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
    for asn in all_target_asns:
        print( '{} {}'.format(str(asn), is_valid(dummy_vrps, dummy_rib, asn)) )


if __name__ == '__main__':
    main()

