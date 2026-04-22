# shadcn/ui 元件對照表

SA-2 每次 build 前必須先查這份對照表。
能用 shadcn 的**一律 import**，不要重新造輪子。

路徑：`@/components/ui/{component}`

---

## 對照表

| Figma 設計模式 | shadcn 元件 | Import 路徑 | 備註 |
|---|---|---|---|
| 按鈕 / CTA / Icon Button | `Button` | `@/components/ui/button` | variant: default/outline/ghost/destructive |
| 文字輸入框 | `Input` | `@/components/ui/input` | |
| 多行文字 | `Textarea` | `@/components/ui/textarea` | |
| 下拉選單（單選）| `Select` | `@/components/ui/select` | SelectTrigger + SelectContent + SelectItem |
| 表單欄位標籤 | `Label` | `@/components/ui/label` | 搭配 htmlFor |
| 對話框 / Modal | `Dialog` | `@/components/ui/dialog` | DialogTrigger + DialogContent + DialogHeader |
| 確認對話框 | `AlertDialog` | `@/components/ui/alert-dialog` | 有 Cancel / Action 兩個按鈕 |
| 側邊抽屜 | `Sheet` | `@/components/ui/sheet` | side: left/right/top/bottom |
| 資料表格 | `Table` | `@/components/ui/table` | Table + TableHeader + TableBody + TableRow + TableCell |
| 狀態標籤 / Tag | `Badge` | `@/components/ui/badge` | variant: default/secondary/outline/destructive |
| 卡片容器 | `Card` | `@/components/ui/card` | CardHeader + CardTitle + CardContent + CardFooter |
| Tab 導航 | `Tabs` | `@/components/ui/tabs` | TabsList + TabsTrigger + TabsContent |
| 勾選框 | `Checkbox` | `@/components/ui/checkbox` | |
| 單選按鈕組 | `RadioGroup` | `@/components/ui/radio-group` | RadioGroupItem + Label |
| 開關 Toggle | `Switch` | `@/components/ui/switch` | |
| 日期選擇器 | `Calendar` + `Popover` | `@/components/ui/calendar` + `@/components/ui/popover` | 組合使用 |
| 搜尋 / 命令面板 | `Command` | `@/components/ui/command` | CommandInput + CommandList + CommandItem |
| 下拉選單（多項操作）| `DropdownMenu` | `@/components/ui/dropdown-menu` | 右鍵選單、More actions |
| 提示氣泡 | `Tooltip` | `@/components/ui/tooltip` | 需要 TooltipProvider 包覆 |
| 分頁 Label | `Label` | `@/components/ui/label` | |
| 分隔線 | `Separator` | `@/components/ui/separator` | horizontal/vertical |
| 可捲動區塊 | `ScrollArea` | `@/components/ui/scroll-area` | |
| 使用者頭像 | `Avatar` | `@/components/ui/avatar` | AvatarImage + AvatarFallback |
| 載入骨架 | `Skeleton` | `@/components/ui/skeleton` | |
| 進度條 | `Progress` | `@/components/ui/progress` | |
| 浮動定位 | `Popover` | `@/components/ui/popover` | PopoverTrigger + PopoverContent |
| 輸入框群組 | `InputGroup` | `@/components/ui/input-group` | 帶前後綴的輸入框 |

---

## 判斷規則（SA-2 必須遵守）

### ✅ 直接 import shadcn（不寫新 code）
以下情況直接 import，只需調整 props 和 className：
- 整個元件就是上表的某一個
- 元件是上表元件的簡單組合（例：Dialog + Form fields）
- 視覺差異只在顏色 / 間距（用 `className` 覆蓋即可）

### 🔨 需要自己寫
以下情況才自己 build（並寫入 `library-candidates.json`）：
- 業務邏輯專屬（例：班級管理的時間 combobox、課表格）
- 上表完全沒有對應的視覺模式
- 需要特殊動畫或複雜互動

### ⚠️ 混合使用
最常見的情況：shadcn 提供 shell，業務邏輯自己填：
```tsx
// Good: shadcn Dialog shell + 自訂表單內容
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

function EditClassDialog({ open, onClose, data }) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>編輯班級</DialogTitle>
        </DialogHeader>
        {/* 自訂業務表單內容 */}
        <Input placeholder="班級名稱" />
        <Button onClick={handleSubmit}>儲存</Button>
      </DialogContent>
    </Dialog>
  )
}
```

---

## Token 節省估算

| 情境 | 舊做法（FigmaDesigner） | 新做法（shadcn import） | 節省 |
|---|---|---|---|
| Dialog 元件 | 寫 ~120 行 JSX | `import { Dialog }` + 5 行組合 | ~90% |
| Table 元件 | 寫 ~80 行 JSX | `import { Table }` + thead/tbody | ~70% |
| Select 元件 | 寫 ~60 行 JSX | `import { Select }` + options | ~85% |
| Button 變體 | 寫 ~30 行 | `import { Button } variant="..."` | ~95% |
| 整頁 CRUD 表格 | 寫 ~400 行 | shadcn shell + ~80 行業務邏輯 | ~80% |

---

## 安裝新 shadcn 元件（如果某個元件還沒裝）

```bash
cd C:/hand2design/figmadesignershadcn
npx shadcn@latest add {component-name}
```

安裝後更新此檔案的對照表，並 commit。

---

## 已安裝清單（2026-04-22）

```
alert-dialog  avatar     badge      button    calendar
card          checkbox   command    dialog    dropdown-menu
input         input-group  label    popover   progress
radio-group   scroll-area  select   separator  sheet
skeleton      switch     table      tabs      textarea
tooltip
```
