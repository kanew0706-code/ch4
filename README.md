# 風景照片記錄 agent

在自己電腦上執行的 Discord agent：指定頻道裡有人傳風景或景點照片，它用 `claude -p` 判斷是哪裡、照片裡有哪些景物，把照片存檔、在 Excel 記一筆，再回覆上傳者這個地方的特色介紹。程式關掉就不處理。

- 需求：[docs/requirements.md](docs/requirements.md)
- 架構：[docs/architecture.md](docs/architecture.md)
- Discord 設定：[docs/discord-server-setup.md](docs/discord-server-setup.md)、[docs/discord-bot-setup.md](docs/discord-bot-setup.md)

## 準備

1. 照上面兩份 Discord 文件建好 Server、頻道和 bot。
2. 把 `.env.example` 複製一份改名成 `.env`，填入四個設定：

   | 設定 | 意思 |
   |---|---|
   | `DISCORD_TOKEN` | bot 的 token。**絕對不能公開、不能 commit** |
   | `CHANNEL_ID` | agent 要聽的那個頻道的 ID |
   | `CLAUDE_MODEL` | claude -p 用的模型，例如 `haiku` |
   | `DATA_DIR` | 照片和 Excel 存放的資料夾，例如 `./data` |

3. 確認 `claude --version` 有反應（Claude Code 已安裝並登入）。

## 啟動

在專案資料夾打開終端機：

```
uv sync
uv run python -m place_agent
```

- `uv sync` 只有第一次、或套件有變動時需要執行。
- 看到 `✅ 已上線` 就可以在頻道傳照片了。
- 按 `Ctrl + C` 結束。

**agent 開著的時候，請不要用 Excel 開著 `records.xlsx`。** 檔案被打開時會寫不進去，終端機會印出警告並每 5 秒重試一次；大約 1 分鐘後還是寫不進去，這張照片就會回覆失敗。想看紀錄，可以先複製一份再打開。

## 資料存放位置

```
DATA_DIR/
├─ records.xlsx                                紀錄
└─ photos/
   ├─ 2026-10-26 12-30-45 台北101.jpg
   ├─ 2026-10-26 12-30-45 台北101-2.jpg          同一秒撞名
   ├─ 2026-10-26 13-00-10 無法確定-海邊夕陽.jpg   認不出地點
   └─ 2026-10-26 13-05-00 不是地方-馬克杯.jpg     不是風景
```

## 四段防護的位置

| 防護 | 檔案 | 大約行數 |
|---|---|---|
| 防護 1：claude -p 的檔案範圍隔離 | `src/place_agent/analyzer.py` | 88–98 |
| 防護 2：上傳者文字只當資料 | `src/place_agent/analyzer.py` | 106–110 |
| 防護 3：檔名清洗 | `src/place_agent/storage.py` | 47–53 |
| 防護 4：Excel 公式注入 | `src/place_agent/ledger.py` | 56–59 |

程式改過之後行號可能會跑掉，用這行指令重新找（PowerShell）：

```
Select-String -Path src\place_agent\*.py -Pattern "==== 防護"
```

**怎麼關掉某一段防護**：把「開始」和「結束」之間的每一行程式前面加上 `#`。在 VS Code 裡，選取這幾行後按 `Ctrl + /` 就可以。每段防護前面都有一行「沒有防護時」的寫法，所以整段註解掉之後，程式還是能跑，只是少了這層保護。

平常四段一律開著。

## 測試

```
uv run pytest
```
