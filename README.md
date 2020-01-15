# roamon diff
ROAと実際の経路情報の齟齬を調べるツールです

## Usage
### Instllation
#### Dockerを使う場合
本リポジトリはプライベートのため、cloneにはログインが必要です
`./docker/Dockerfile`にgithubのユーザ名とパスワードを入れるところがあるので書き換えておいてください

あとは以下のコマンドで準備が整ったコンテナが起動します
```
$ sudo docker build -t roamon ./docker
$ sudo docker run --rm -it roamon /bin/bash
>$ cd /roamon
```

#### ローカルにインストールする場合
リポジトリのクローン
```
$ git clone https://github.com/taiji-k/roamon.git
```

必要なパッケージのインストール
```
$ pip3 install netaddr pyfiglet tqdm
```

他にDocker環境が必要です

### Quick start

#### 全ての情報のフェッチ 
標準では`/tmp`にデータを置きます   
数分かかります
```
$ python3 roamon_diff_controller.py get --all
```
#### 全ての情報のチェック
VRPs(Verified ROA Payloads)の情報とRIB(実際の経路情報)を比較し、齟齬があるかどうかを調べます  
Trueが正常でFalseが齟齬ありです  
ロードに数分かかります
```
$ python3 roamon_diff_controller.py check

139553 True
136815 True
16018 False
202712 True
...
```

#### 特定のASだけチェック
例としてAS5745と63987について調べます  
ロードに数分かかります
```
$ python3 roamon_diff_controller.py check -asns 5745 63987

5745 True
63987 False
```
