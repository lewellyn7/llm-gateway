# LLM Gateway Admin UI 迭代 PRD

> 版本：v1.1 | 状态：评审中 | 作者：Jarvis | 更新：2026-04-01

---

## 一、背景与目标

### 1.1 现状分析

当前 `admin.html` 存在以下体验缺陷：

| 问题 | 现状 | 影响 |
|------|------|------|
| **交互碎片化** | 创建租户/Key 使用 `window.location.reload()` 刷新整个页面 | 操作效率低，状态丢失 |
| **危险操作无确认** | 撤销 Key、删除租户直接执行 | 误操作风险高 |
| **数据展示原始** | 用量统计直接 `JSON.stringify` 输出 | 可读性差，无法快速洞察 |
| **表单无验证** | 可提交空邮箱、空名称 | 脏数据入库 |
| **列表无分页** | 数据量增长后页面卡顿 | 体验差 |
| **移动端不可用** | 表格水平溢出，按钮过小 | 移动办公无法使用 |

### 1.2 战略目标

1. **效率提升**：关键操作从 3 步优化到 1 步
2. **安全可控**：所有危险操作强制二次确认
3. **数据可读**：图表替代原始 JSON，趋势一目了然
4. **全端适配**：移动端操作成功率 ≥ 85%

### 1.3 成功指标

| 指标 | 当前值 | 目标值 | 衡量方式 |
|------|--------|--------|----------|
| 创建租户耗时 | ~45s（含页面刷新） | ≤ 15s | 操作计时 |
| 危险操作误操作率 | 未知 | < 1% | 日志统计 |
| 用量数据解读耗时 | ~60s | ≤ 10s | 用户测试 |
| 移动端任务完成率 | ~40% | ≥ 85% | 埋点统计 |

---

## 二、用户与场景

### 2.1 目标用户画像

| 用户 | 角色 | 痛点 |
|------|------|------|
| **李明** | 系统管理员 | 需快速创建租户、生成 API Key，当前操作繁琐 |
| **王芳** | 财务 | 需查看本月成本，判断是否超预算 |
| **张工** | 运维 | 移动端处理紧急问题，当前无法操作 |

### 2.2 核心场景

#### 场景 1：快速创建租户
```
时间：09:00
李明登录后台 → 点击"新建租户" → 模态框弹出
→ 输入"文杨科技"、邮箱"wy@example.com"、选择"Pro计划"
→ 表单实时校验通过 → 点击"创建"
→ 模态框显示 loading 1s → 成功关闭 → 列表刷新显示新租户
→ Toast 提示："租户创建成功"
总耗时：≤ 15s
```

#### 场景 2：误操作防护
```
时间：10:30
李明误点击"撤销"某 Key → 确认对话框弹出
内容："确定撤销 Key sk-xxxx... 吗？撤销后不可恢复。"
李明发现选错了 Key → 点击"取消" → 对话框关闭，无操作
若确认点击 → 执行撤销 → Toast 提示"Key 已撤销"
```

#### 场景 3：成本分析
```
时间：11:00
王芳查看用量 → 切换到"用量"Tab
→ 看到左侧 7 天请求量折线图（蓝线）
→ 右侧 7 天成本柱状图（绿柱）
→ 默认显示近 7 天，支持下拉选择"近 30 天"或自定义日期
→ 鼠标悬停显示具体数值
解读耗时：≤ 10s
```

#### 场景 4：移动端紧急处理
```
时间：14:00
张工在地铁上收到告警 → 手机打开 /admin
→ 表格自动横向滚动，姓名、电话等列可左右滑动
→ 操作按钮"详情"放大到 44px × 44px，易于点击
→ 点击"详情"查看租户信息
```

---

## 三、产品方案

### 3.1 功能清单

| ID | 功能 | 优先级 | 类型 | 说明 |
|----|------|--------|------|------|
| F01 | 通用模态框 | P0 Must | 组件 | 遮罩 + 居中弹窗，ESC/遮罩点击关闭 |
| F02 | 创建租户模态框 | P0 Must | 功能 | 名称（必填）+ 邮箱（必填，格式校验）+ 计划选择（下拉）|
| F03 | 生成 API Key 模态框 | P0 Must | 功能 | 租户选择（必填）+ 备注（可选）|
| F04 | 确认对话框组件 | P0 Must | 组件 | 自定义标题/内容/按钮文字 |
| F05 | 撤销 Key 确认 | P0 Must | 功能 | 显示 Key 前缀，确认执行 |
| F06 | 删除租户确认 | P0 Must | 功能 | 提示关联数据影响 |
| F07 | Toast 通知系统 | P0 Must | 组件 | 3 种类型（success/error/info），3s 自动消失 |
| F08 | 用量趋势图表 | P1 Should | 功能 | 折线图（请求量）+ 柱状图（成本）|
| F09 | 日期范围筛选 | P1 Should | 功能 | 近 7 天 / 近 30 天 / 自定义 |
| F10 | 表单实时验证 | P1 Should | 功能 | 邮箱格式、必填项即时反馈 |
| F11 | 列表分页 | P1 Should | 功能 | 每页 10 条，页码导航 |
| F12 | 移动端适配 | P1 Should | 优化 | 横向滚动表格 + 放大按钮 |
| F13 | 空状态引导 | P2 Could | 优化 | 无数据时显示引导插画 |
| F14 | Loading 状态 | P2 Could | 优化 | 按钮/模态框提交时显示 loading |

### 3.2 信息架构

```
/admin
├── Header（固定）
│   ├── Logo + 标题
│   ├── 暗黑模式切换
│   └── 版本号 + 登出
├── Stats Cards（4 列）
│   ├── 租户数
│   ├── API Keys
│   ├── 今日请求
│   └── 本月成本
├── Tabs
│   ├── 🏢 租户
│   │   ├── 操作：新建租户（Modal）
│   │   └── 列表：ID + 名称 + 邮箱 + 计划 + 状态 + 操作
│   ├── 🔑 Keys
│   │   ├── 操作：生成 Key（Modal）
│   │   └── 列表：Key 前缀 + 租户 + 创建时间 + 操作
│   ├── 📊 用量
│   │   ├── 图表区（折线 + 柱状）
│   │   └── 筛选器（日期范围）
│   └── ⚙️ 设置
│       └── 配置表单
└── Footer（固定）
```

### 3.3 关键交互规格

#### 3.3.1 模态框（Modal）

| 属性 | 规格 |
|------|------|
| 遮罩 | 背景：`rgba(0,0,0,0.5)`，点击关闭 |
| 弹窗宽度 | 最大 `480px`，移动端 `90vw` |
| 居中方式 | `flex` 垂直水平居中 |
| 动画 | 遮罩 fade-in 200ms，弹窗 slide-up 200ms |
| 关闭方式 | ESC 键、遮罩点击、关闭按钮 |
| 标题区 | 左侧标题（16px 加粗）+ 右侧关闭按钮（×）|
| 内容区 | 内边距 24px |
| 底部区 | 内边距 16px 24px，按钮右对齐 |

#### 3.3.2 确认对话框

| 属性 | 规格 |
|------|------|
| 标题 | 红色加粗，如"确认撤销？" |
| 内容 | 说明后果，如"撤销后此 Key 将立即失效" |
| 取消按钮 | 灰色，文字"取消" |
| 确认按钮 | 红色，文字"确认撤销"，点击后变 loading |

#### 3.3.3 Toast 通知

| 属性 | 规格 |
|------|------|
| 位置 | 右上角，距顶部 20px |
| 间距 | 多条 toast 垂直堆叠，间距 8px |
| 宽度 | 固定 320px |
| 动画 | slide-in 从右侧，3s 后 slide-out |
| 类型 | success（绿）、error（红）、info（蓝）|

#### 3.3.4 表单验证规则

| 字段 | 规则 | 错误提示 |
|------|------|----------|
| 租户名称 | 必填，2-50 字符 | "名称不能为空" / "名称过长" |
| 邮箱 | 必填，符合 Email 格式 | "邮箱格式不正确" |
| 计划 | 必填，选择一项 | "请选择计划" |
| Key 备注 | 可选，最大 100 字符 | "备注过长" |

### 3.4 Not in Scope

- ❌ 不实现租户编辑功能（本期仅创建 + 删除）
- ❌ 不实现数据导出（Excel/CSV）
- ❌ 不实现自定义域名
- ❌ 不实现多语言切换
- ❌ 不实现操作日志审计

---

## 四、UI 设计规范

### 4.1 色彩系统

| 用途 | 颜色 | Tailwind Class |
|------|------|----------------|
| Primary | Indigo #4F46E5 | `indigo-600` |
| Primary Hover | Indigo #4338CA | `indigo-700` |
| Success | Green #22C55E | `green-500` |
| Success BG | Green #F0FDF4 | `green-50` |
| Danger | Red #EF4444 | `red-500` |
| Danger Hover | Red #DC2626 | `red-600` |
| Warning | Amber #F59E0B | `amber-500` |
| Text Primary | Gray #111827 | `gray-900` |
| Text Secondary | Gray #6B7280 | `gray-500` |
| Border | Gray #E5E7EB | `gray-200` |
| Dark BG | Gray #111827 | `gray-900` |
| Dark Card | Gray #1F2937 | `gray-800` |

### 4.2 字体规范

| 用途 | 大小 | 字重 | Tailwind Class |
|------|------|------|----------------|
| 页面标题 | 20px | 700 | `text-xl font-bold` |
| 卡片标题 | 14px | 500 | `text-sm font-medium` |
| 正文 | 14px | 400 | `text-sm` |
| 辅助文字 | 12px | 400 | `text-xs` |
| 按钮文字 | 14px | 500 | `text-sm font-medium` |
| 统计数字 | 30px | 700 | `text-3xl font-bold` |

### 4.3 间距规范

| 用途 | 间距 | Tailwind Class |
|------|------|----------------|
| 页面内边距 | 16px | `px-4` |
| 卡片间距 | 16px | `gap-4` |
| 卡片内边距 | 20px | `p-5` |
| 按钮内边距 | 12px 16px | `py-3 px-4` |
| 表单项间距 | 16px | `space-y-4` |
| 表格单元格 | 12px 16px | `px-3 py-3` |

### 4.4 阴影规范

| 用途 | 样式 | Tailwind Class |
|------|------|----------------|
| 卡片默认 | `0 1px 3px rgba(0,0,0,0.1)` | `shadow-sm` |
| 卡片悬停 | `0 4px 6px rgba(0,0,0,0.1)` | `hover:shadow-md` |
| 模态框 | `0 25px 50px rgba(0,0,0,0.25)` | `shadow-2xl` |
| Toast | `0 4px 6px rgba(0,0,0,0.1)` | `shadow-lg` |

### 4.5 圆角规范

| 用途 | 圆角 | Tailwind Class |
|------|------|----------------|
| 卡片 | 12px | `rounded-xl` |
| 按钮 | 8px | `rounded-lg` |
| 输入框 | 8px | `rounded-lg` |
| Toast | 8px | `rounded-lg` |
| 模态框 | 16px | `rounded-2xl` |
| 头像/图标 | 50% | `rounded-full` |

### 4.6 动画规范

| 动画 | 时长 | 缓动 | CSS |
|------|------|------|-----|
| 页面淡入 | 200ms | ease-out | `opacity 0→1` |
| 卡片悬停 | 150ms | ease | `transform scale(1.01)` |
| 模态框弹出 | 200ms | ease-out | `translateY(20px→0) + opacity` |
| Toast 滑入 | 300ms | ease-out | `translateX(100%→0)` |
| Toast 滑出 | 300ms | ease-in | `translateX(0→100%)` |
| 按钮 Loading | 持续 | linear | `rotate 360deg` |
| Tab 切换 | 200ms | ease | `opacity + translateY` |

### 4.7 移动端断点

| 断点 | 宽度 | 布局变化 |
|------|------|----------|
| Mobile | < 640px | 单列，卡片全宽 |
| Tablet | 640px - 1024px | 2 列统计卡片 |
| Desktop | > 1024px | 4 列统计卡片，完整表格 |

### 4.8 无障碍规范

| 规范 | 要求 |
|------|------|
| 颜色对比度 | 文字与背景对比度 ≥ 4.5:1 |
| 点击目标 | 最小 44px × 44px（移动端）|
| 焦点可见 | 键盘导航时有可见焦点环 |
| ARIA 标签 | 按钮、表单需有 `aria-label` |
| 键盘操作 | 模态框支持 ESC 关闭 |

---

## 五、技术方案

### 5.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.x (CDN) | 现有前端框架 |
| Tailwind CSS | 3.x (CDN) | 现有样式框架 |
| Chart.js | 4.x (CDN) | 新增图表库 |
| Axios | 1.x (CDN) | 现有 HTTP 库 |

### 5.2 CDN 引入

```html
<!-- Chart.js 新增 -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
```

### 5.3 组件结构

```html
<div id="app">
  <!-- Toast 容器 -->
  <div class="toast-container">
    <div v-for="toast in toasts" :key="toast.id" 
         :class="['toast', toast.type]">
      {{ toast.message }}
    </div>
  </div>

  <!-- 通用模态框 -->
  <div id="modal-overlay" class="modal-overlay hidden">
    <div class="modal-content">
      <div class="modal-header">
        <h3>{{ modalTitle }}</h3>
        <button @click="closeModal">×</button>
      </div>
      <div class="modal-body">
        <!-- 动态内容 slot -->
      </div>
      <div class="modal-footer">
        <button @click="closeModal">取消</button>
        <button @click="submit" :disabled="loading">
          <span v-if="loading">处理中...</span>
          <span v-else>确认</span>
        </button>
      </div>
    </div>
  </div>

  <!-- 确认对话框 -->
  <div id="confirm-dialog" class="modal-overlay hidden">
    <div class="confirm-content">
      <h3 class="text-red-600">{{ confirmTitle }}</h3>
      <p>{{ confirmMessage }}</p>
      <div class="confirm-actions">
        <button @click="cancelConfirm">取消</button>
        <button class="btn-danger" @click="executeConfirm">确认</button>
      </div>
    </div>
  </div>

  <!-- 页面内容 -->
  ...
</div>
```

### 5.4 API 接口（复用现有）

| 接口 | 方法 | 用途 |
|------|------|------|
| `/api/admin/tenants` | GET | 获取租户列表 |
| `/api/admin/tenants` | POST | 创建租户 |
| `/api/admin/tenants/:id` | DELETE | 删除租户 |
| `/api/admin/keys` | GET | 获取 Key 列表 |
| `/api/admin/keys` | POST | 生成 Key |
| `/api/admin/keys/:id` | DELETE | 撤销 Key |
| `/api/admin/usage` | GET | 获取用量统计 |

### 5.5 Vue 响应式数据结构

```javascript
// 模态框状态
const modalState = reactive({
  isOpen: false,
  type: 'create-tenant', // 'create-tenant' | 'create-key'
  title: '',
  loading: false,
  form: { name: '', email: '', plan: 'free' }
})

// 确认对话框状态
const confirmState = reactive({
  isOpen: false,
  title: '',
  message: '',
  onConfirm: null // 回调函数
})

// Toast 通知
const toasts = ref([])
const showToast = (message, type = 'info') => {
  const id = Date.now()
  toasts.value.push({ id, message, type })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 3000)
}
```

---

## 六、风险与降级

### 6.1 风险矩阵

| ID | 风险 | 概率 | 影响 | 应对 |
|----|------|------|------|------|
| R1 | Chart.js CDN 加载失败 | 低 | 低 | 降级为表格展示 |
| R2 | 模态框 z-index 冲突 | 低 | 中 | 设置固定 z-index 层级 |
| R3 | 表单提交时网络超时 | 中 | 中 | 增加超时提示 + 重试按钮 |
| R4 | 移动端 Vue 响应式性能差 | 低 | 中 | 减少不必要的响应式监听 |

### 6.2 降级方案

| 场景 | 降级策略 |
|------|----------|
| 图表加载失败 | 显示"图表加载中..."，1s 后改为原始 JSON 表格 |
| 模态框打不开 | 检查 z-index，强制设置为 9999 |
| 表单提交失败 | Toast 提示"网络异常，请重试"，保留表单内容 |

---

## 七、里程碑

| 阶段 | 时间 | 交付内容 | 验收标准 |
|------|------|----------|----------|
| M1 | 第 1 天 | P0 功能（模态框 + 确认框 + Toast） | 可创建租户/Key，危险操作有确认 |
| M2 | 第 2 天 | P1 功能（图表 + 分页 + 表单验证） | 用量图表正常，列表可分页 |
| M3 | 第 3 天 | P1 移动端 + P2 空状态 | 移动端可正常操作 |
| M4 | 第 4 天 | 整体测试 + Bug 修复 | 全流程回归通过 |

---

## 八、验收标准

### 8.1 功能验收

| 功能 | 验收条件 |
|------|----------|
| 创建租户 | 填写正确信息 → 点击创建 → 模态框关闭 → 列表显示新租户 → Toast 提示成功 |
| 创建 Key | 选择租户 → 点击生成 → 显示完整 Key（可复制）→ 列表新增 |
| 撤销 Key | 点击撤销 → 确认对话框 → 点击确认 → Key 从列表移除 |
| 删除租户 | 点击删除 → 确认对话框 → 显示关联影响 → 确认后删除 |
| 用量图表 | 切换到用量 Tab → 2s 内显示图表 → 悬停显示数值 |
| 表单验证 | 邮箱格式错误 → 实时显示错误提示 → 修正后提示消失 |
| 分页 | 租户 > 10 个 → 显示分页器 → 点击页码 → 列表更新 |

### 8.2 性能验收

| 指标 | 标准 |
|------|------|
| 页面首次加载 | < 2s |
| 模态框打开 | < 100ms |
| 图表渲染 | < 500ms |
| 表单提交到响应 | < 1.5s |

### 8.3 兼容性验收

| 环境 | 标准 |
|------|------|
| Chrome 90+ | 全部功能正常 |
| Safari 15+ | 全部功能正常 |
| iOS Safari 15+ | 移动端可正常操作 |
| Android Chrome 100+ | 移动端可正常操作 |
