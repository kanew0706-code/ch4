# 建立 Discord bot 並邀進你的 Server（Windows）

請先完成 [discord-server-setup.md](discord-server-setup.md)，你要已經有自己的 Server 和 `# food-log` 頻道。

照這份做完，你會拿到：

- 一個 bot（agent 在 Discord 上的「帳號」）
- 這個 bot 的 **token**，填進 `.env` 的 `DISCORD_TOKEN`
- bot 已經加入你的 Server

> Discord Developer Portal（開發者後台）只有英文介面，下面的按鈕名稱都照英文寫。
> Discord 偶爾會改版，找不到按鈕時，看看旁邊或同一頁往下捲。

---

> ## ⚠️ 先看這段：bot token 就是 bot 的密碼
>
> 拿到 token 的人可以**冒充你的 bot**，在你的 Server 裡讀所有訊息、發任何訊息。
>
> - ❌ **不能貼給任何人**：同學、助教、老師都不行。沒有人需要你的 token。
> - ❌ **不能貼進和 Claude 的對話**：包括 Claude Code 這個視窗。需要 token 的只有 `.env` 檔，Claude 不需要看到它。
> - ❌ **不能 commit 進 git、不能推上 GitHub**：GitHub 上有程式會自動掃描外流的 token。
> - ❌ 不能截圖、不能貼在 Discord、LINE、作業報告裡。
> - ✅ 唯一要放的地方：你電腦上的 `.env` 檔（第 5 步）。
>
> **萬一外流了**：馬上照第 4 步按「Reset Token」換一組新的，舊的會立刻失效。然後把新的填回 `.env`。

---

## 第 1 步：建立 application

application 是你在 Discord 開發者後台登記的「一個應用程式」，bot 是掛在它底下的。

1. 打開瀏覽器，到 <https://discord.com/developers/applications>。
2. 如果要求登入，用**和 Discord App 同一個帳號**登入。
3. 按右上角藍色的 **「New Application」**。
4. 「NAME」欄位輸入 bot 的名字，例如 `食物記錄小幫手`。
5. 勾選下面同意條款的方框。
6. 按 **「Create」**。
7. 如果跳出「我不是機器人」的驗證，照指示完成。
8. 進到這個 application 的 **General Information** 頁面，就代表建立成功。

---

## 第 2 步：讓別人不能把你的 bot 加到他們的 Server

這個 bot 只給你自己的 Server 用。要關掉「Public Bot」，但得先把預設的安裝連結關掉，不然存檔時會出錯。

1. 左邊選單按 **「Installation」**。
2. 找到 **「Install Link」** 下拉選單，改成 **「None」**。
3. 按畫面最下面跳出來的綠色 **「Save Changes」**。
4. 左邊選單按 **「Bot」**。
5. 找到 **「PUBLIC BOT」** 開關，把它**關掉**（變成灰色）。
6. 按 **「Save Changes」**。

> 為什麼要關：Public Bot 打開的話，任何拿到邀請網址的人都能把你的 bot 加到他們的 Server。他們在那邊傳的訊息不會被處理（agent 只聽你的 CHANNEL_ID），但還是沒必要讓別人加。

---

## 第 3 步：打開 Message Content Intent（一定要做）

還在 **「Bot」** 這一頁。

1. 往下捲到 **「Privileged Gateway Intents」** 這一區，裡面有三個開關。
2. 把 **「MESSAGE CONTENT INTENT」** 打開（變成藍色）。
3. 另外兩個 **「PRESENCE INTENT」**、**「SERVER MEMBERS INTENT」** **保持關閉**，agent 用不到。
4. 按最下面的 **「Save Changes」**。

### 為什麼一定要打開

**intent** 是 bot 向 Discord 申請「我要看哪些東西」。Discord 為了保護大家的隱私，預設**不給** bot 看別人訊息的內容。沒打開 Message Content Intent 的話，bot 收到的訊息裡：

- **文字是空的**：看不到上傳者打的「飯只吃一半」，也看不到修正用的回覆。
- **附件是空的**：**連照片都拿不到**。

結果就是 bot 明明在線上，卻對每張照片都沒反應。這是設定 Discord bot 最常見的錯誤。

> 「Privileged」的意思是「需要特別申請的權限」。bot 加入的 Server 少於 100 個時，自己打開開關就生效，不用送審。

---

## 第 4 步：拿到 bot token

還在 **「Bot」** 這一頁。

1. 回到頁面上方，找到 **「TOKEN」** 這一區。
2. 按 **「Reset Token」**。
   - 第一次建立 bot 時也是按這個鈕，沒有另外的「產生」按鈕。
3. 跳出確認視窗問你確定嗎，按 **「Yes, do it!」**。
4. 如果你的帳號有開兩步驟驗證，這裡會要你輸入驗證碼；沒開的話可能要輸入密碼。
5. 畫面會出現一串很長的亂碼，旁邊有 **「Copy」** 按鈕，按下去複製。
6. **馬上**接著做第 5 步，把它貼進 `.env`。

> ⚠️ **這串 token 只會顯示這一次。** 離開這一頁就看不到了。忘了複製也沒關係，再按一次「Reset Token」產生新的就好，舊的會自動失效。

---

## 第 5 步：把 token 和 CHANNEL_ID 存進 .env

`.env` 是放在專案資料夾裡的設定檔，已經寫在 `.gitignore` 裡，git 不會把它 commit 上去。

1. 按鍵盤 `Windows 鍵`，輸入 `記事本`（或 `Notepad`），按 Enter 打開。
2. 輸入下面兩行，把 `=` 後面換成你自己的值，**等號前後不要有空白，也不要加引號**：
   ```
   DISCORD_TOKEN=剛剛複製的那串token
   CHANNEL_ID=discord-server-setup.md第4步拿到的那串數字
   ```
   `CLAUDE_MODEL` 和 `DATA_DIR` 之後寫程式時再補。
3. 按 `Ctrl + Shift + S`（另存新檔）。
4. 在存檔視窗：
   - 上面的路徑列切到專案資料夾 `C:\Users\herol\ch4`。
   - **「存檔類型」** 改成 **「所有檔案 (\*.\*)」**。這一步很重要，不改的話會存成 `.env.txt`，程式讀不到。
   - **「檔案名稱」** 輸入 `.env`。
   - **「編碼」** 選 **「UTF-8」**。
5. 按 **「存檔」**。
6. 確認有存對：打開檔案總管，到 `C:\Users\herol\ch4`，上方選單 **「檢視」→「顯示」→ 勾選「副檔名」**，應該看得到一個叫 `.env` 的檔案，**而不是** `.env.txt`。
7. 確認 git 不會收它：在專案資料夾執行 `git status`，輸出裡**不應該**出現 `.env`。

> 以後要改 `.env`，在檔案總管對它按右鍵 →「開啟檔案」→ 選「記事本」。
> 請不要叫 Claude 幫你打開或顯示 `.env` 的內容，那樣 token 就會出現在對話裡。

---

## 第 6 步：設定 bot 的權限並產生邀請網址

回到瀏覽器的 Developer Portal。

1. 左邊選單按 **「OAuth2」**。
2. 往下捲到 **「OAuth2 URL Generator」** 這一區。
3. 在 **「SCOPES」** 的一堆勾選框裡，只勾 **「bot」**。
4. 勾了之後，下面會多出 **「BOT PERMISSIONS」** 這一區。在 **「TEXT PERMISSIONS」** 和 **「GENERAL PERMISSIONS」** 底下，**只勾這三個**：

   | 權限 | 位置 | 為什麼需要 |
   |---|---|---|
   | **View Channels** | GENERAL PERMISSIONS | 看得到 `food-log` 頻道和裡面的新訊息 |
   | **Send Messages** | TEXT PERMISSIONS | 回覆「處理中」和結果 |
   | **Read Message History** | TEXT PERMISSIONS | 用「回覆」功能掛在原照片底下，以及找到修正要對應的那則結果 |

   - **不要勾 「Administrator」**（管理員）。萬一 token 外流，管理員權限能讓對方刪掉整個 Server。
   - 把自己發的訊息改成結果，不需要另外的權限。
5. 最下面 **「GENERATED URL」** 會出現一條網址，按旁邊的 **「Copy」**。

---

## 第 7 步：把 bot 邀進你的 Server

1. 在瀏覽器開一個新分頁，按 `Ctrl + V` 貼上剛剛的網址，按 Enter。
2. 頁面會顯示 bot 的名字。在 **「新增至伺服器」**（Add to server）下拉選單，選你在 `discord-server-setup.md` 建的那個 Server。
   - 選單裡只會出現你有「管理伺服器」權限的 Server。你自己建的一定會在裡面。
3. 按 **「繼續」**（Continue）。
4. 下一頁列出第 6 步勾的三個權限，確認沒錯，按 **「授權」**（Authorize）。
5. 如果出現「我不是機器人」的驗證，照指示完成。
6. 看到「已授權」（Authorized）的畫面就完成了，可以關掉這個分頁。
7. 回到 Discord App，你的 Server 右邊成員清單會出現這個 bot，名字旁邊有 **「APP」**（或「BOT」）標籤。
   - 它現在顯示**離線**是正常的。agent 程式還沒寫，等程式跑起來它才會上線。

> 如果你在 `discord-server-setup.md` 第 2 步把 `food-log` 設成了**私人頻道**：還要對 `# food-log` 按右鍵 →「編輯頻道」→「權限」→「新增成員或身分組」→ 加入這個 bot，不然 bot 看不到那個頻道。

---

## 完成檢查

- [ ] Developer Portal 裡有你的 application，**Bot** 頁的 **MESSAGE CONTENT INTENT** 是開的
- [ ] **PUBLIC BOT** 是關的
- [ ] `C:\Users\herol\ch4\.env` 存在（不是 `.env.txt`），裡面有 `DISCORD_TOKEN` 和 `CHANNEL_ID`
- [ ] `git status` 看不到 `.env`
- [ ] token **沒有**貼在任何其他地方：對話、聊天軟體、截圖、作業
- [ ] bot 出現在你 Server 的成員清單裡（顯示離線）
