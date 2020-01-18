# roamon diff
ROAと実際の経路情報の齟齬を調べるツールです

## Usage
### Instllation
#### ローカルにインストールする場合
一番確実だと思います

リポジトリのクローン
```
$ git clone https://github.com/taiji-k/roamon.git
```

必要なパッケージのインストール
```
$ pip3 install netaddr pyfiglet tqdm requests beautifulsoup4 pyasn
```

他にDocker環境が必要です

#### Vagrantを使う場合
本リポジトリはプライベートのため、cloneにはログインが必要です  
`./vagrant/Vagrantfile`の一番下の方にgithubアカウントのユーザ名とパスワードを入れるところがあるので書き換えてください

あとPCのスペックに合わせて、仮想マシンに割り振るリソースを適当に増やしてください(Vagrantfileの真ん中くらいにあります)  
低いスペックちゃんと動くかは確認してません...
  
あとは以下のコマンドを打てばok
```
$ cd vagrant
$ vagrant up
$ vagrant ssh
>$ 
```

#### Dockerを使う場合
Docker in Docker をやる必要があるため *後回し* にします

~~本リポジトリはプライベートのため、cloneにはログインが必要です
~~`./docker/Dockerfile`にgithubのユーザ名とパスワードを入れるところがあるので書き換えておいてください~~

~~あとは以下のコマンドで準備が整ったコンテナが起動します~~

```
$ sudo docker build -t roamon ./docker
$ sudo docker run --rm -it roamon /bin/bash
>$ cd /roamon
```



### Quick start

#### 全ての情報のフェッチ 
標準では`/tmp`にデータを置きます   
数分かかります
```
$ python3 roamon_diff_controller.py get --all
```
#### ROA登録がちゃんとできているか調べる
VRPs(Verified ROA Payloads)の情報とRIB(実際の経路情報)を比較し、齟齬があるかどうかを調べます  
Trueが正常でFalseが齟齬ありです  

以下のように、そのASがちゃんとROA登録できているかを調べます。 Falseの場合はROA登録を **修正する必要があります** 。
 1. そもそもそのASから経路広告してなかったらTrue
 2. 指定されたASから経路広告してたけど、そのASはROA登録してない場合True
 3. 指定されたASが経路広告しててROA登録もしてたが、ROA登録していないprefixを経路広告してたらFalse
 
##### 全てのASについて調べる
デフォルトでは全てのASについて調べます
```
$ python3 roamon_diff_controller.py check

139553 True
136815 True
16018 False
202712 True
...
```

##### 特定のASだけチェック
例としてAS5745と63987について調べます。  
AS5745は自分が広告してる経路についてちゃんとROA登録できていることがわかります。
```
$ python3 roamon_diff_controller.py check -asns 5745 63987

5745 True
63987 False
```

##### 特定のIPアドレスだけチェック
203.0.113.0/24を含むprefixを広告していたASは、ちゃんとROA登録できていることがわかります。
```
$ python3 roamon_diff_controller.py check -ips  203.0.113.0/24 203.0.113.5

203.0.113.0/24 True
203.0.113.5 True
```


#### 経路ハイジャック?を調べる
指定されたASがROA登録したprefixが他のROA登録していないASに勝手に(同じかより小さいプレフィックスで)経路広告されていないかを調べます。  
  
Falseになっている場合、そのPrefixをROA登録していない他のASが経路広告してしまっています。  
ROAでOrigin ASの検証をしている組織でははじかれてしまうので対応が必要となります。

##### 全てのASについてチェック
デフォルトでは全てのASについてチェックします。  


`調査したAS | 経路広告されてる中で、調査したASがROA登録してるPrefixとロンゲストマッチしたPrefix | 経路広告したAS ` 
```
$ python3 roamon_diff_controller.py check-violation 

174 198.63.0.0/16 2914 False
174 185.189.173.0/24 199727 True
174 209.227.0.0/17 2914 False
174 204.142.180.0/23 174 False
174 167.160.15.0/24 174 False
...
```

##### ASの指定
AS番号を複数していできます。

```
$ python3 roamon_diff_controller.py check-violation  --asns 174

174 198.63.0.0/16 2914 False
174 185.189.173.0/24 199727 True
174 209.227.0.0/17 2914 False
174 204.142.180.0/23 174 False
174 167.160.15.0/24 174 False
...
```

##### IPアドレスの指定
指定されたIPアドレスを経路広告していたASと、そのIPアドレスをROA登録していたASが同一かどうかを調べます
(`python3 roamon_diff_controller.py check --ips`と似たようなもんだから必要ない？この辺よくわからなくなってきたので整理が必要...)
```
$ python3 roamon_diff_controller.py check-violation --ips 203.0.113.0/24 203.0.113.5

203.0.113.0/24 False
203.0.113.5 False
```

