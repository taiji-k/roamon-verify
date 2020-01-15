# encoding: UTF-8

import argparse
import roamon_diff_checker
import subprocess
import os
import logging
from pyfiglet import Figlet

# ログ関係の設定 (適当)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def fetch_rib_data(dir_path_data, file_path_rib):
    # TODO: 最新のRIBファイルを自動で選んでダウンロードできるようにする。現在は固定値。
    # RIBファイルのダウンロード
    subprocess.check_output(
        "wget http://archive.routeviews.org/bgpdata/2020.01/RIBS/rib.20200114.0200.bz2 -P " + dir_path_data,
        shell=True)
    # MRTフォーマットをパースし、PrefixとAS_PATHの列を取り出し、経路集約された部分を取り除いてOrigin ASを抜き出し、最終的に PrefixとOriginASがならぶCSVにする
    subprocess.check_output(
        "time bgpdump -Hm -t dump rib.20200114.0200.bz2 | cut -d \| -f6,7 | tr '\|' ' ' | sed s/\{.*\}// | awk '{print ($1),($NF)}' | tr ' ' ',' > " + file_path_rib,
        shell=True)
    logger.debug("finish fetch rib")


def fetch_vrps_data(file_path_vrps):
    # 入手したTALを永続化する準備
    subprocess.check_output(
        "sudo docker volume create routinator-tals",
        shell=True)
    # TALを入手
    subprocess.check_output(
        "sudo docker run --rm -v routinator-tals:/home/routinator/.rpki-cache/tals \
nlnetlabs/routinator init -f --accept-arin-rpa",
        shell=True)
    # routinator起動
    subprocess.check_output(
        "sudo docker run -d --rm --name routinator -v routinator-tals:/home/routinator/.rpki-cache/tals nlnetlabs/routinator",
        shell=True)
    # routinatorでROAを取得 & 検証してVRPのリストを得る
    subprocess.check_output(
        "sudo docker exec -it routinator /bin/sh -c 'routinator vrps 2>/dev/null | tail -n +2' > " + file_path_vrps,
        shell=True)
    # routinatorのコンテナを止める(と同時に消える)
    subprocess.check_output(
        "sudo docker stop routinator",
        shell=True)
    logger.debug("finish fetch vrps")
