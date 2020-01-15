# roamon diff
ROAと実際の経路情報の齟齬を調べるツールです

## Usage
### Instllation
リポジトリのクローン
```
$ git clone https://github.com/taiji-k/roamon.git
```

必要なパッケージのインストール
```
$ pip3 install netaddr pyfiglet tqdm
```

### Quick start

#### 全ての情報のフェッチ 
標準では`/tmp`にデータを置きます   
数分かかります
```
$ python3 roamon_diff/roamon_diff_controller get --all
```
#### 全ての情報のチェック
VRPs(Verified ROA Payloads)の情報とRIB(実際の経路情報)を比較し、齟齬があるかどうかを調べます  
Trueが正常でFalseが齟齬ありです  
ロードに数分かかります
```
$ python3 roamon_diff/roamon_diff_controller check

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
$ python3 roamon_diff/roamon_diff_controller check -asns 5745 63987

5745 True
63987 False
```


