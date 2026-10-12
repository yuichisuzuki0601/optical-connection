# 光通信実験

スマートフォンの画面の明暗を使って文字列を送る実験用プロジェクトです。`sender` が画面を明滅させ、`device` が受光素子で明暗を検出します。

## 構成

- `device/`: MicroPythonで動くESP32側のコードとファームウェア
- `sender/`: Node.jsの標準モジュールだけで動く送信ページ
- `justfile`: 送信ページとデバイスの操作コマンド

## Senderを起動する

プロジェクトのルートで実行します。

```sh
just sender-start
```

`just sender-start` はMacの `en0` に割り当てられたLAN内IPv4アドレスのページを先に開き、その後 `npm run start` でサーバーを起動します。ブラウザに接続エラーが出た場合は、サーバー起動後に再読み込みしてください。

`just` を使わない場合は、ルートから次のように起動できます。

```sh
cd sender
npm run start
```

既定のポートは3000です。PCでは `http://localhost:3000` を開きます。同じLAN上のスマートフォンでは `http://<PCのIPアドレス>:3000` を開きます。`just` を使わずにポートを変更する場合は、`sender` ディレクトリで `PORT=8080 npm run start` を実行します。

送信ボタンを押すと入力欄からフォーカスを外し、0.5秒待ってから3秒のカウントダウンを始めます。その後、画面を2秒間黒に固定してから送信します。この間は画面と受光素子の位置を動かさないでください。

「Connection Check」は受光素子の反応を見るためのテストです。同じ準備時間の後、白500ms・黒500msを10回繰り返します。接続の成立や受信成功を判定する機能ではありません。

## Deviceを起動する

対応するMicroPythonファームウェアを書き込んだESP32を接続し、`mpremote` を使える状態で、プロジェクトのルートから実行します。

```sh
just device-start
```

このコマンドは `device/src/` をデバイスへコピーし、`main.py` を実行して出力を `device/.log` に保存します。現在の `main.py` はOLEDに `HELLO` を表示し、タクトスイッチで表示を消し、受光素子の明暗変化をログに出します。文字列の復元処理は `device/src/protocol/optical_receiver.py` にありますが、`main.py` にはまだ接続していません。現在のログには明暗の継続時間 `duration` も出ません。

ファームウェアの書き込みや開発用stubの導入など、その他のコマンドは `just --list` で確認できます。

## 送信方式

入力文字列をUTF-8のバイト列へ変換し、交互明滅の開始マーカー、本文長、本文、CRC-16、交互明滅の終了マーカーの順にフレーム化します。本文長、本文、CRC-16のビットはManchester方式で明暗に変換します。

`sender/app.js` の `HALF_BIT_MS` は明滅の半ビット時間で、現在は100msです。受信処理を使う場合は、`device/src/protocol/optical_receiver.py` の `OpticalReceiver.HALF_BIT_MS` も同じ値に合わせます。
