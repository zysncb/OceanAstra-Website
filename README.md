# OceanAstra 官网

三语（英 / 中 / 阿）静态官网，由 Claude Design Canvas 设计并导出。GitHub Pages 直接托管仓库里的 HTML，不跑任何构建。

- 六个页面：首页、解决方案、关于我们、联系我们、隐私政策、使用条款
- **三种语言在页面内切换**（右上角 EN / 中文 / عربي），不是三套 URL。阿文为 RTL 从右至左排版
- 字体与图片是外部共享文件，六页复用；页面本身 140–225 KB，只有 React 从 unpkg CDN 加载

---

## 目录结构

```
index.html  solutions/  about/  contact/  privacy/  terms/   ← 页面（各 140–225 KB）
assets/
  fonts/fonts.css       ← 336 条 @font-face，六页共享
  fonts/*.woff2         ← 118 个字体分片，按 unicode-range 需要时才下载
  img/favicon.svg       ← favicon（几何取自 logo-mark-only.svg，另加深色底盘）
  img/*.jpg             ← 页面配图
  img/logo/             ← OceanAstra 品牌标志（SVG + PNG，多种版本；站内未引用，供对外物料使用）
  img/partners/         ← 合作伙伴标志，已按 3:1 槽位合成好（见 tools/make-partner-logo.sh）
404.html  sitemap.xml  robots.txt  .nojekyll                 ← 站点配置
content/
  company.json          ← 公司信息事实来源（法人名、执照号、地址、电话、邮箱）
  i18n/{en,zh,ar}.json  ← 三语文案定稿，页面 SEO 元数据取自这里
```

`assets/` 下的文件名是内容哈希，内容一变文件名就变，可以放心让 CDN 长期缓存。

`content/` 现在**不参与构建**，它是文案与公司信息的事实来源，供改稿、翻译和核对 Apple 材料时查阅。原先的静态生成器（`build/`）已随设计改版删除。

---

## 改内容

页面是 Design Canvas 的导出产物，**不要直接编辑这六个 HTML** —— 里面是打包后的模板和 base64 资源，手改极易破坏结构（尤其注意任何注入的 `</script>` 会提前截断 `__bundler/template`）。

正确做法是回到 Design Canvas 改，重新导出，再替换对应文件。导出后需要补三件事，因为导出产物不带这些：

1. **SEO 元数据** —— 导出的 `<title>` 是 `Bundled Page`，且没有 description / canonical / Open Graph。需在**外层 `<head>` 和 `__bundler/template` 两处**注入，文案取自 `content/i18n/en.json` 的各页 `title` 与 `description`。
2. **`<html lang>` 与语言同步脚本** —— 导出产物的 `<html>` 没有 `lang`/`dir`，切换语言时也不更新，屏幕阅读器会一直当成英文。同步脚本必须放在外层 `<head>`：放进 template 里不会执行，还会截断模板。
3. **核对数字宣称** —— 导出稿曾出现「10+ 年中东本地经验」「10+ languages」这类与执照信息和三语事实冲突的表述，已在当前页面中修正为「中东本地交付」与真实语言列表。Design Canvas 源文件里可能仍有，每次导出都要复查。

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
| 注册地址 | Office 08, Building R.SH.038, Saih Shuaib 2, Dubai Industrial City, Dubai, UAE |
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

## 一些设计决定

**为什么要把资源从导出产物里拆出来。** Design Canvas 的导出把字体、图片、脚本全部内联成自包含单文件，首页因此有 8.9 MB，且六个页面各存一份，整站 44 MB。更要命的是 woff2 分片本来带 `unicode-range`、浏览器只该下载用得到的那几片，内联成 base64 后这个机制失效 —— 英文访客也被迫下载全部 303 个中文字体分片。

现在字体和图片是外部文件，按内容哈希命名、六页共享。**英文首屏只下载 4 个字体分片**，切到中文或阿拉伯文时才增量加载对应分片。首屏从 8.9 MB 降到约 900 KB。

每次从 Design Canvas 重新导出后，这个拆分需要重做一遍。

**为什么三语不再是三套 URL。** 改版前是 `/`、`/zh/`、`/ar/` 各一套静态页，带 hreflang，三语都能被搜索引擎索引。现在语言在页面内切换，只有一套 URL —— 代价是中文与阿拉伯文内容对 SEO 不可见，搜索引擎只读得到英文那一版。如果中东本地搜索流量重要，这一点需要重新评估。

**为什么没有联系表单。** 静态站的表单必须依赖第三方服务（Formspree 等），多一个可能挂掉的外部依赖，而 Apple 审核只需要看到可用的联系方式。目前展示三个公司域名邮箱（咨询 / 服务支持 / 合作伙伴），更可靠也更容易核实。

**为什么网站上没有电话。** 公司不提供电话支持渠道，所以联系页原本那一栏（含一条电话支持的描述）已整栏移除，办公地点的「来信或来电」也改成只说来信 —— 留着会与实际服务方式矛盾。注意这只是不对外宣传电话渠道：Apple 申请仍需填写可接通的公司电话。

**为什么没有第三方分析和 Cookie 横幅。** 不装分析工具就不需要 Cookie 同意横幅，隐私政策也能写得干净。语言偏好只存在浏览器 localStorage，不回传。

**关于合作关系的措辞。** 「集成合作方案」一节按确认的合作关系点名 **Lark** 与 **Amap**，并在末尾附商标归属声明（「Lark 与 Amap 为其各自权利人的商标，每项合作的具体范围及商务性质在商务洽谈阶段书面确认」）。措辞刻意停留在「我们代理的平台 / Platforms we work with」，未使用「官方授权经销商」「Authorised Reseller」这类需要厂商书面授权背书的表述 —— 如果确有对应授权书，可以再升级措辞。

合作伙伴 logo 直接使用厂商原始文件、未改色：两个标志都是深色字，放在深色卡片上看不见，因此预先合成到浅色底板上（`tools/make-partner-logo.sh`），而不是给别人的商标换颜色。

**经营范围提示。** 执照登记的两项活动是 *IT Infrastructure* 和 *Computer Systems & Communication Equipment Software Design*，均属软件设计/IT 基建。官网上的「AI 组织方案」「行业管理方案」落在这个范围内，但「集成合作方案」涉及的软件代理通常对应贸易类活动。这不影响 Apple 审核，但建议向注册代理（PRO）确认是否需要增补经营活动。
