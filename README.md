# OceanAstra 官网

三语（英 / 中 / 阿）静态官网，由 Claude Design Canvas 设计并导出。GitHub Pages 直接托管仓库里的 HTML，不跑任何构建。

- 六个页面：首页、解决方案、关于我们、联系我们、隐私政策、使用条款
- **三种语言各有自己的 URL**：英文在根目录，中文在 `/zh/`，阿文在 `/ar/`。右上角 EN / 中文 / عربي 是跳转到当前页面的对应语种版本，不是只改页面内的文案 —— 语言因此能跟着链接、刷新和书签走。阿文为 RTL 从右至左排版
- 字体与图片是外部共享文件，六页复用；页面本身 140–225 KB，只有 React 从 unpkg CDN 加载

> 站点界面本身有三语，产品也宣称三语界面，但**不再对外承诺三语交付与支持**（2026-08-21 调整）。改文案时注意区分这两件事：产品界面语言是软件能力，支持语言是要配人的服务承诺。
>
> 2026-10-18 补齐了两处漏网的：首页那张卡片的第三格原本写「交付语言 / 英文 · 阿拉伯文 · 中文」（阿文同，中文则漂成了「出海中东 / 中东本地交付」），现在三语统一为「界面语言」，由 `tools/credential-language.py` 维护；JSON-LD 里两个 `contactPoint` 的 `availableLanguage` 已整个移除 —— 它声明的是某个渠道用哪些语言服务，正是撤回的那条承诺。三种语言仍以 `Organization.knowsLanguage` 表述，那是公司属性，不是服务承诺。

---

## 目录结构

```
index.html  solutions/  about/  contact/  privacy/  terms/   ← 页面（各 140–225 KB）
faq/  lark/                                                  ← 生成的静态页，不走 Design Canvas
assets/
  fonts/fonts.css       ← 336 条 @font-face，六页共享
  fonts/*.woff2         ← 118 个字体分片，按 unicode-range 需要时才下载
  img/favicon.svg       ← favicon（几何取自 logo-mark-only.svg，另加深色底盘）
  img/*.jpg             ← 页面配图
  img/logo/             ← OceanAstra 品牌标志（SVG + PNG，多种版本；站内未引用，供对外物料使用）
  img/partners/         ← 合作伙伴标志，已按 3:1 槽位合成好（见 tools/make-partner-logo.sh）
404.html  sitemap.xml  robots.txt  .nojekyll                 ← 站点配置
.well-known/security.txt                                     ← 安全联系方式（RFC 9116），2027-10-18 到期
content/
  company.json          ← 公司信息事实来源（法人名、执照号、地址、电话、邮箱）
  i18n/{en,zh,ar}.json  ← 三语文案定稿，页面 SEO 元数据取自这里
  faq.json              ← /faq/ 三页的问答
  lark.json             ← /lark/ 子站九个页面的文案
```

`assets/` 下的文件名是内容哈希，内容一变文件名就变，可以放心让 CDN 长期缓存。

`content/` 是文案与公司信息的事实来源。页面正文不从这里生成（那是 Design Canvas 的事），但 `/faq/` 三页、`llms.txt`、各页 `<head>` 的 SEO 元数据与 JSON-LD 结构化数据都从这里生成 —— 改完 `content/` 要按下面的顺序重跑脚本。原先的静态生成器（`build/`）已随设计改版删除。

```bash
python3 tools/address.py            # 只在地址变更时跑
python3 tools/build-faq.py
python3 tools/build-lark.py
python3 tools/seo-inject.py
python3 tools/analytics.py <令牌>   # 令牌：grep -o '"token": "[0-9a-f]*"' index.html
```

`build-faq.py` 与 `build-lark.py` 重建页面时不带分析脚本，所以 `analytics.py` 必须跑在最后。

`address.py` 要跑在 `seo-inject.py` 之前：地址在 26 个文件里有 17 种写法（完整一行、JSON-LD 的 `streetAddress`、`/about/` 公司信息表的 `Dubai, UAE` 缩写、`company.json` 的四行 `lines`、FAQ 里的整句话，再加地图链接与经纬度），三语各一套，脚本把它们一次改齐；`seo-inject.py` 随后按新的 `company.json` 重建 JSON-LD 与 `llms.txt`。`FORMS` 里存着每种写法历来的值，重新导出后再跑一次就能把旧地址换掉。

---

## 改内容

页面是 Design Canvas 的导出产物，**不要直接编辑这六个 HTML** —— 里面是打包后的模板和 base64 资源，手改极易破坏结构（尤其注意任何注入的 `</script>` 会提前截断 `__bundler/template`）。

正确做法是回到 Design Canvas 改，重新导出，再替换对应文件。导出后需要补三件事，因为导出产物不带这些：

1. **SEO 元数据** —— 导出的 `<title>` 是 `Bundled Page`，且没有 description / canonical / Open Graph。需在**外层 `<head>` 和 `__bundler/template` 两处**注入，文案取自 `content/i18n/en.json` 的各页 `title` 与 `description`。
2. **`<html lang>` 与语言同步脚本** —— 导出产物的 `<html>` 没有 `lang`/`dir`，切换语言时也不更新，屏幕阅读器会一直当成英文。同步脚本必须放在外层 `<head>`：放进 template 里不会执行，还会截断模板。
3. **核对办公地址** —— 导出产物带回的是 Design Canvas 源文件里的地址。2026-10-25 办公地址迁至 Business Bay 的 Churchill Tower 1，由 `tools/address.py` 维护，每次导出后都要跑。注意：执照 1646635 与 D-U-N-S 851077092 上印的仍是迪拜工业城的旧地址，站点已先行一步 —— 详见 `content/company.json` 的 `_needsReview`。
4. **核对数字宣称与语言口径** —— 导出稿曾出现「10+ 年中东本地经验」「10+ languages」这类与执照信息冲突的表述，`prepare-export.py` 的 `CLAIMS` 会把它们改掉。Design Canvas 源文件里可能仍有旧说法，每次导出后除了 `CLAIMS`，还要跑 `tools/credential-language.py`（首页语言卡片）与 `tools/privacy-cookies.py`（隐私政策第 10 节）—— 这两处的文案住在 DICT 里，重新导出会把旧说法带回来。两个脚本的 `PRIOR` 都存着历来的措辞，所以无论导出带回哪一版都能改掉。

## 本地预览

```bash
python3 -m http.server 4173
```

然后访问 http://localhost:4173 。必须用 HTTP 服务器打开：页面之间是相对路径，但 favicon 与 sitemap 用的是根绝对路径。

---

## 部署到 GitHub Pages

1. 提交并推送到 `main` 分支。
2. 仓库 Settings → Pages → Source 选 **Deploy from a branch**，分支 `main`，目录 `/ (root)`。
3. 绑定自定义域名（见下）。

### 自定义域名 oceanastra.net

**顺序很重要：先配 DNS，等解析生效，再加 `CNAME` 文件。** 反过来做会让 GitHub Pages 把 `zysncb.github.io` 重定向到一个还没解析的域名，站点在这段时间内无法访问。

`oceanastra.net` 的 DNS 托管在**阿里云云解析**（NS 为 `vip1.alidns.com` / `vip2.alidns.com`），邮箱走 **Lark Mail**（MX 指向 `larksuite.com`）。

第一步，在阿里云控制台 → 云解析 DNS → `oceanastra.net` → 解析设置，新增 **9 条**记录：

| 记录类型 | 主机记录 | 记录值 |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| AAAA | `@` | `2606:50c0:8000::153` |
| AAAA | `@` | `2606:50c0:8001::153` |
| AAAA | `@` | `2606:50c0:8002::153` |
| AAAA | `@` | `2606:50c0:8003::153` |
| CNAME | `www` | `zysncb.github.io` |

解析线路选「默认」，TTL 保持默认即可。IP 取自 GitHub 官方接口 `https://api.github.com/meta` 的 `pages` 字段，如需复核可直接查询该接口。

> ⚠️ **不要动现有的 MX 和 TXT 记录** —— 那是 Lark 邮箱的路由和 SPF 验证，删掉会导致 `hello@` / `support@` 立刻收不到信。A 记录和 MX 记录在同一个 `@` 上共存是正常的。
>
> ⚠️ **不要在 `@` 上添加 CNAME 记录。** DNS 规范不允许根域同时存在 CNAME 和 MX，加了会破坏邮箱。GitHub Pages 的根域必须用 A/AAAA 记录，这也是上面要加 8 条而不是 1 条的原因。

第二步，确认解析已生效，并确认邮箱路由没被碰坏：

```bash
dig +short oceanastra.net && echo "--- MX 应仍为 larksuite ---" && dig +short MX oceanastra.net
```

A 记录返回那四个 IP、MX 仍指向 `larksuite.com`，才算好了。

第三步，创建 `CNAME` 文件并推送：

```bash
echo "oceanastra.net" > CNAME && git add CNAME && git commit -m "Point Pages at oceanastra.net" && git push
```

> 也可以在 Settings → Pages 的 Custom domain 输入框里填，效果一样 —— 但 GitHub 会自己往仓库提交一个 `CNAME` 文件，本地再 push 就会冲突。用了输入框的话，记得先 `git pull` 再继续。

最后在 Settings → Pages 勾选 **Enforce HTTPS**（Let's Encrypt 证书签发通常要几分钟到一小时，期间该选项可能是灰的，属正常）。

> 站点依赖自定义域名下的根路径（favicon、sitemap、canonical 均为绝对地址），不适合部署在 `zysncb.github.io/OceanAstra-Website/` 这类项目页子路径下。**申请 Apple 开发者账号也务必用公司自有域名**，见下。

---

## Apple 开发者公司账号：网站相关清单

Apple 在审核 Organization 账号时会人工查看官网。以下**加粗**项是 Apple 明确列出的要求，其余是审核实践中反复出现的注意点。

### 必须做到

- [x] **网站可公开访问** —— 已于 2026-08-20 验证 https://oceanastra.net 返回 HTTPS 200。不能有密码保护、不能是"建设中"占位页、不能整站 `noindex`。审核期间不要下线或大改。
- [ ] **域名归公司所有** —— Apple 要求域名与申请主体相关联。建议域名 WHOIS 注册人写公司法人全名。
- [ ] **网站显示的法人名称与 D-U-N-S 记录逐字一致** —— 这是最常见的驳回原因。本站在页脚（每一页）和「关于我们 → 公司信息」两处展示法人名称，请确保两处与 D-U-N-S、贸易执照完全相同，包括 `L.L.C.` 的标点写法。
- [x] **申请时填写的邮箱使用公司域名** —— 用 `hello@oceanastra.net`，不能用 Gmail / QQ 邮箱。该邮箱必须真实可收信，Apple 会往这里发验证邮件。

### 强烈建议

- [ ] 电话号码真实可接通，且与 D-U-N-S 记录一致 —— **网站上不再展示电话**（公司不提供电话支持渠道），但 Apple 申请表单里填写的号码必须真实可接通，审核员可能致电核实公司身份，接电话的人要知道这回事。号码保留在 `company.json` 作为事实来源。
- [ ] 网站有实质内容：公司做什么、提供什么产品/服务、如何联系。本站的首页、解决方案、关于我们三页已覆盖。
- [ ] 具备隐私政策与使用条款页面（已包含）。App 上架时也需要隐私政策 URL。
- [ ] App 上架需要提供 Support URL —— 独立的 `/support/` 页已随改版删除，改用 **`https://oceanastra.net/contact/`**，该页有「服务支持」卡片与 `support@oceanastra.net`，满足要求。
- [ ] 全站无死链 —— 改版后没有自动检查了，替换页面后手动点一遍导航与页脚。

### 已按贸易执照填入的真实数据

以下均转录自 **Dubai Commercial License No. 1646635**（签发 20/08/2026，到期 19/08/2027）：

| 字段 | 值 |
|---|---|
| 法人名（英） | OceanAstra Technologies L.L.C |
| 法人名（阿） | أوشن أسترا للتكنولوجيا ذ.م.م |
| 执照号 | 1646635 |
| 商业登记号 | 2913183 |
| 迪拜商会会员号 | 698189 |
| 发照机关 | Department of Economy and Tourism, Government of Dubai |
| 注册地址 | 3707, Churchill Tower 1, Business Bay, Dubai, UAE |
| 电话 | +971 50 813 8014 |
| 成立年份 | 2026 |

> 执照上英文名印为全大写 `OCEANASTRA TECHNOLOGIES L.L.C`，站点渲染为 Title Case（逐词完全一致，仅大小写不同）以便正文阅读。若 D-U-N-S 记录要求严格一致，改 `content/company.json` 的 `legalName.en` 即可。

### 域名与邮箱

- 域名：**oceanastra.net**（站点与邮箱同域）
- `hello@oceanastra.net` —— 咨询、新项目、商务、媒体，以及隐私政策与使用条款的联系方式
- `support@oceanastra.net` —— 服务支持，同时作为 App Store 的 App 支持联系方式
- `partners@oceanastra.net` —— 合作伙伴、渠道与生态洽谈

全站只出现这三个地址，且都在公司域名下。

### 待办状态（更新于 2026-08-20）

`content/company.json` 顶部 `"_placeholders": true`，未完成项记录在 `_needsReview`：

| 项 | 状态 | 说明 |
|---|---|---|
| 三个信箱开通 | ✅ 已完成 | `hello@` / `support@` / `partners@` 已在 Lark Mail 生效。注意 Apple 申请不接受 Gmail，执照上登记的那个个人 Gmail 不能用于账号申请 |
| DNS 解析 | ✅ 已完成 | 根域 A/AAAA 指向 GitHub Pages、`www` CNAME 指向 `zysncb.github.io`、MX 未受影响，站点已在 https://oceanastra.net 通过 HTTPS 正常访问 |
| `dunsNumber` | ⏳ 等待发放 | 已于 2026-08-20 向邓白氏提交申请，预计数天内发放。拿到号码后填入 `content/company.json` 的 `dunsNumber` 并重新生成 —— 这是 Apple 企业账号的前置条件 |

D-U-N-S 号码到手后填入 `company.json`，并把 `"_placeholders"` 改成 `false`。注意页面上的公司信息是导出时写死的，改 `company.json` **不会**自动更新页面 —— 涉及对外展示的字段（法人名、执照号、地址、电话、邮箱）需回 Design Canvas 改后重新导出。

---

## 两个站点的内容同步

Invobay（[invobay.com](https://invobay.com)，仓库 `zysncb/invobay-website`，Astro 静态站）是本公司的产品，两个站点对同一件事的说法必须一致：

- **公司事实**（法人名、执照号、发照机关、地址、邮箱）以本仓库 `content/company.json` 为准，逐字一致。
- **Invobay 的产品说法**以 `invobay-website/src/i18n/en.ts` 为准。
- 任何一边改了这两类内容，另一边同步改。

### 产品线现状：Flying 下线，Invobay 并入行业管理方案

两处变动（2026-10-18）：

- **Flying 已从全站移除** —— 页面正文、FAQ、`llms.txt`、结构化数据与 `content/` 都不再提它，建筑装饰行业也不再作为「专门构建系统的行业」出现。
- **Invobay 归入业务线 02「行业管理方案」**，与 CarSaas 并列，不单独成线。全站仍是三条业务线。

这两件事都已经落到页面正文上，不是只改了 `content/`。页面文案住在导出产物的 DICT 里，所以各有一个可重复执行的脚本：

| 脚本 | 做什么 |
|---|---|
| `tools/drop-flying.py` | 摘掉首页那条 bullet、解决方案页那一整组，并改写三处「二选一」的句子 |
| `tools/add-invobay.py` | 把 Invobay 的 bullet、两个分组与新增段落插进业务线 02；新文案从 `content/i18n` 读，脚本只决定位置 |

**重新导出后这两个脚本都要再跑一遍**，顺序见 `tools/prepare-export.py` 开头 —— Design Canvas 的源文件里 Flying 还在，而它从没听说过 Invobay。跑完要接着跑 `prerender.py`，否则爬虫读到的静态副本还是旧的。

把 Invobay 放进业务线 02 改变了这条线的性质：CarSaas 是企业自己选择上的行业系统，而阿联酋电子发票是法规要求必须运行的，且 Invobay 本身不含任何 AI。这条线的 summary、lede 和新增的那段话都把这一点说明白了，没有让原本的 AI 叙事顺带把它罩进去。章节末尾那组交付保证也因此改成了明确针对行业系统的标题 —— 其中「AI 职员或 AI 辅助」「部署在贵司基础设施」对 Invobay 并不成立，它是 invobay.com 上的托管产品。

对外口径（与 invobay.com 一致，发布前经产品负责人确认）：

- OceanAstra **不是**阿联酋财政部认证的服务商（ASP），也不申请成为服务商。
- Invobay 通过 API 与经认证的服务商对接；服务商由企业自行指定，并由企业与其直接签约。
- 不利用经由服务商获得的数据去招揽该服务商的客户。
- 正式上线前不公布任何已合作 ASP 的名称、logo、价格与数据。
- 产品状态照 CarSaas 的写法标「开发中 / 即将上线」。

### 产品线现状：CorpOS 下线，Lark 升为业务线 01

两处变动（2026-10-21）：

- **CorpOS 已从全站移除** —— 页面正文、FAQ、`llms.txt`、结构化数据与 `content/` 都不再提它。产品未上线前先撤下，以后上线再补回来。
- **Lark 从业务线 03 的一条 bullet 升为业务线 01「AI 办公平台 / AI Workplace」** —— 与 Lark 签署经销协议之后，这是公司真正在卖的那条线。业务线 03 保留 Amap 与「其他平台按个案评估」，全站仍是三条业务线。

两件事由同一个脚本完成，因为它们本来就是一件事：CorpOS 不是业务线 01 里的一个产品，而是那条线「解决方案」分组的全部内容，单独摘掉它会剩下一条有标题、有适用场景、中间却是空的业务线。

**为什么这条线的名字里仍有 AI。** 扛着「让 AI 融入每一家中东企业」这句话的原本是 CorpOS。它一下线，全站的 AI 叙事就空了——第一版曾把 01 线写成「数字化办公平台」，AI 掉到第三条 bullet，结果整站只剩标语在说 AI。改法不是把词撒回去，而是换一个主语：**从「我们自研一个 AI 产品」改成「我们让 AI 在你已经在用的系统里真正跑起来」**。这对一家 2026 年成立、尚无产品上线的公司更站得住，而且 Lark 本来就带 AI。所以 01 线的首段讲的是「能力随许可一起到货，用起来不会」，分组里第一组就是「把 AI 用起来」，首页卡片第一条 bullet 也是 AI。解决方案页的大标题与首页「三条业务线」的导语也相应把 AI 放了回去。

| 脚本 | 做什么 |
|---|---|
| `tools/drop-corpos.py` | 整体重写业务线 01（首页卡片与解决方案页那一整节），删掉业务线 03 里的 Lark 条目并改写其脚注，重写「关于我们」里三条线那段话，以及三处用散文点到业务线 01 的句子 |

和前两个脚本一样，**重新导出后要再跑一遍** —— Design Canvas 的源文件里 CorpOS 仍是业务线 01，而它没听说过这份经销协议。顺序见 `tools/prepare-export.py` 开头。新文案全部从 `content/i18n` 读，脚本只决定位置；只有那三句散文两头都写在脚本的 `TEXT` 里，因为它们不住在 `content/`。

对外口径（2026-10-21 确认）：

- OceanAstra 依据**已签署的经销协议**供应 Lark，站点措辞为「Lark 授权经销商 / Authorised Lark reseller」。⚠️ 这个措辞以及任何合作伙伴徽标的使用，**发布前需按 Lark 的品牌规范核对** —— Lark 的合作伙伴计划有自己的层级名称，用词可能要跟着改。
- 站点说「以迪拉姆报价、凭采购单开票」，**没有**承诺发票含 5% VAT —— 那要等 VAT 登记完成后才能写进去。
- 站点**没有**承诺任何语言的支持服务。2026-08-21 撤回的三语交付与支持承诺，没有被这条新业务线带回来。
- 业务线 02 的文案仍在说「AI 职员或 AI 辅助」。那是 CarSaas 的说法，与 CorpOS 无关，故保留未动。

### /lark/ 子站

线上销售 Lark 的落地页，由 `tools/build-lark.py` 从 `content/lark.json` 生成，**三语各有自己的 URL**：

| URL | 回答的问题 |
|---|---|
| `/lark/`、`/zh/lark/`、`/ar/lark/` | Lark 是什么、为什么通过经销商买、我们做什么、AI 那部分、适合谁 |
| `/lark/pricing/` 等三语 | 怎么报价、怎么走采购、以及我们不做什么 |
| `/lark/migration/` 等三语 | 从 Microsoft 365 / Google Workspace 迁移：能迁什么、迁不干净什么、顺序 |

**为什么单做一组页面，而不是加进主站。** 那六个页面是 Design Canvas 的 bundle：加一页就要重新导出，而且 bundle 只有一套 URL、按访客选的语言渲染——所以主站上的中文与阿拉伯文内容对爬虫是不可见的（见下面「为什么三语不再是三套 URL」）。而这条业务线的买家恰恰读中文和阿拉伯文。于是照 `/faq/` 的做法生成：一种语言一个真实 URL、不跑 JavaScript、每个字都在响应里。`/zh/lark/` 是搜索引擎能索引的页面，`/zh/` 不是。

**为什么是子目录而不是 `lark.oceanastra.net`。** 域名 2026 年 8 月才启用，权重本就薄，再拆一个子域等于对半砍；把别人的商标放进子域名，多数品牌规范也不允许；而且买家查「这家公司靠不靠谱」时，落在同一个域下能直接看到执照号和迪拜地址。

**怎么被找到。** `seo-inject.py` 的 `EXTRA` 把这九页写进 `sitemap.xml`（每页带三语 hreflang）和 `llms.txt`；站内则由业务线 01 的卡片（首页）与「我们提供什么」分组（解决方案页）链过去，链接按语言各指各的，走的是 `add-invobay.py` 当初为 invobay.com 注入的那套 `link` / `linkLabel` 机制。

> 已知的小瑕疵：那套注入的锚点 markup 写死了 `target="_blank"`，对 invobay.com 是对的，对站内的 `/lark/` 就成了「新标签页打开」。要改得让 `target` 跟着 DICT 字段走，涉及改模板，暂未动。

**这些页面刻意不说的话**（与主站同一口径，改文案时请一并守住）：发票只说「以迪拉姆报价、凭采购单开票」，不提 VAT；不承诺任何语言的支持服务；不公布任何折扣，也不报多年锁定价（我们自己的进价折扣可由 Lark 书面通知调整）；不出现任何未在 Lark 公开套餐表里列明的产品名——所以 Base 和 AnyCross 点了名，AI 同事只做描述、没点名。

---

## 安全联系方式

`.well-known/security.txt` 按 RFC 9116 提供安全问题的联系方式，内容指向 `support@oceanastra.net`。

**`Expires` 为 2027-10-18，到期前必须续期** —— 过期的 security.txt 等于没有。仓库有 `.nojekyll`，以点开头的目录能正常发布；部署后确认：

```bash
curl -I https://oceanastra.net/.well-known/security.txt
```

---

## 一些设计决定

**为什么要把资源从导出产物里拆出来。** Design Canvas 的导出把字体、图片、脚本全部内联成自包含单文件，首页因此有 8.9 MB，且六个页面各存一份，整站 44 MB。更要命的是 woff2 分片本来带 `unicode-range`、浏览器只该下载用得到的那几片，内联成 base64 后这个机制失效 —— 英文访客也被迫下载全部 303 个中文字体分片。

现在字体和图片是外部文件，按内容哈希命名、六页共享。**英文首屏只下载 4 个字体分片**，切到中文或阿拉伯文时才增量加载对应分片。首屏从 8.9 MB 降到约 900 KB。

每次从 Design Canvas 重新导出后，这个拆分需要重做一遍。

**为什么三语不再是三套 URL。** 改版前是 `/`、`/zh/`、`/ar/` 各一套静态页，带 hreflang，三语都能被搜索引擎索引。现在语言在页面内切换，只有一套 URL —— 代价是中文与阿拉伯文内容对 SEO 不可见，搜索引擎只读得到英文那一版。如果中东本地搜索流量重要，这一点需要重新评估。

> 这件事已经开始有代价了：`/lark/` 子站的买家正是读中文与阿拉伯文的人。所以生成出来的页面（`/faq/` 与 `/lark/` 共十二页）都是一种语言一个真实 URL、带 hreflang、不跑 JavaScript 的，和主站那六页相反。六个导出页要补上这一点，只能回 Design Canvas 改。

**为什么没有联系表单。** 静态站的表单必须依赖第三方服务（Formspree 等），多一个可能挂掉的外部依赖，而 Apple 审核只需要看到可用的联系方式。目前展示三个公司域名邮箱（咨询 / 服务支持 / 合作伙伴），更可靠也更容易核实。

**为什么网站上没有电话。** 公司不提供电话支持渠道，所以联系页原本那一栏（含一条电话支持的描述）已整栏移除，办公地点的「来信或来电」也改成只说来信 —— 留着会与实际服务方式矛盾。注意这只是不对外宣传电话渠道：Apple 申请仍需填写可接通的公司电话。

**为什么没有第三方分析和 Cookie 横幅。** 不装分析工具就不需要 Cookie 同意横幅，隐私政策也能写得干净。语言偏好只存在浏览器 localStorage，不回传。

**关于合作关系的措辞。** 两种措辞并存，因为两段关系不一样。**Lark** 已签署经销协议，所以业务线 01 用了「Lark 授权经销商 / Authorised Lark reseller」，并说明供应依据的是一份已签署的协议 —— 这正是本节原先留的那个口子（没有书面授权就不用这类表述，有了再升级）。**Amap** 没有对应文件，所以仍停留在「我们代理的平台 / Platforms we work with」。两节末尾都保留商标归属声明。升级后的措辞与任何合作伙伴徽标，发布前仍需按 Lark 自己的品牌规范核对。

合作伙伴 logo 直接使用厂商原始文件、未改色：两个标志都是深色字，放在深色卡片上看不见，因此预先合成到浅色底板上（`tools/make-partner-logo.sh`），而不是给别人的商标换颜色。

**经营范围提示。** 执照登记的两项活动是 *IT Infrastructure* 和 *Computer Systems & Communication Equipment Software Design*，均属软件设计/IT 基建。「行业管理方案」落在这个范围内，但转售第三方软件许可通常对应贸易类活动 —— 这条原本只关系到「集成合作方案」里的代理，现在 Lark 是业务线 01、公司要据此报价开票，它就从一条提示变成了开单之前要先落实的事。请向注册代理（PRO）确认是否需要增补经营活动，并一并确认 VAT 登记：站点现在只说「以迪拉姆报价、凭采购单开票」，要在发票上收 5% VAT 必须先完成登记，登记之后才能把这句话写进文案。
