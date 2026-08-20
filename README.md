# OceanAstra 官网

三语（英 / 中 / 阿）静态官网，零依赖、零运行时构建。GitHub Pages 直接托管仓库里已生成的 HTML。

- 默认语言：英文，位于站点根目录 `/`
- 中文：`/zh/`，阿拉伯文：`/ar/`（阿文为 RTL 从右至左排版）
- 页面：首页、解决方案、关于我们、技术支持、联系我们、隐私政策、使用条款（7 页 × 3 语 = 21 页，另加 404）

---

## 目录结构

```
content/
  company.json          ← 公司信息唯一事实来源（法人名、执照号、地址、电话、邮箱）
  i18n/en.json          ← 英文全部文案
  i18n/zh.json          ← 中文全部文案
  i18n/ar.json          ← 阿拉伯文全部文案
assets/
  css/site.css          ← 唯一样式表（占位版，待接入正式 Design System 后重做）
  js/site.js            ← 仅渐进增强：移动端菜单、语言偏好记忆
  img/favicon.svg
build/
  build.mjs             ← 生成器（node build/build.mjs）
  templates.mjs         ← HTML 模板
  check.mjs             ← 内链与锚点检查（node build/check.mjs）

index.html  solutions/  about/  support/  contact/  privacy/  terms/   ← 生成物（英文）
zh/…  ar/…                                                            ← 生成物（中 / 阿）
404.html  sitemap.xml  robots.txt  .nojekyll                          ← 生成物
```

**生成物是提交进仓库的**，GitHub Pages 不跑任何构建。好处是即使 CI 挂了、Node 环境变了，线上站点也不受影响 —— 这一点在 Apple 审核期间尤其重要。

---

## 改内容

改文案 → 编辑 `content/i18n/*.json`（三个语言文件结构完全相同，改哪个改哪个）。
改公司信息（电话、地址、执照号等）→ 只改 `content/company.json`，21 个页面会同步更新。

然后重新生成：

```bash
node build/build.mjs && node build/check.mjs
```

`check.mjs` 会验证每一个站内链接和锚点都指向真实存在的文件。**提交前务必跑一次** —— 官网上的死链是人工审核最容易注意到的瑕疵。

## 本地预览

```bash
python3 -m http.server 4173
```

然后访问 http://localhost:4173 。注意必须用 HTTP 服务器打开，直接双击 HTML 文件会因为站内链接是根绝对路径（`/zh/`）而失效。

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

> 如果暂时不用自定义域名、而是走 `zysncb.github.io/OceanAstra-Website/` 这种项目页路径，需要把 `content/company.json` 里的 `basePath` 改成 `"/OceanAstra-Website"` 再重新生成，否则所有根绝对路径都会 404。**但申请 Apple 开发者账号请务必用公司自有域名**，见下。

---

## Apple 开发者公司账号：网站相关清单

Apple 在审核 Organization 账号时会人工查看官网。以下**加粗**项是 Apple 明确列出的要求，其余是审核实践中反复出现的注意点。

### 必须做到

- [ ] **网站可公开访问** —— 不能有密码保护、不能是"建设中"占位页、不能整站 `noindex`。审核期间不要下线或大改。
- [ ] **域名归公司所有** —— Apple 要求域名与申请主体相关联。建议域名 WHOIS 注册人写公司法人全名。
- [ ] **网站显示的法人名称与 D-U-N-S 记录逐字一致** —— 这是最常见的驳回原因。本站在页脚（每一页）和「关于我们 → 公司信息」两处展示法人名称，请确保两处与 D-U-N-S、贸易执照完全相同，包括 `L.L.C.` 的标点写法。
- [ ] **申请时填写的邮箱使用公司域名** —— 例如 `info@oceanastra.com`，不能用 Gmail / QQ 邮箱。该邮箱必须真实可收信，Apple 会往这里发验证邮件。

### 强烈建议

- [ ] 电话号码真实可接通，且与 D-U-N-S 记录一致 —— Apple 可能会打电话核实公司身份，接电话的人要知道这回事。
- [ ] 网站有实质内容：公司做什么、提供什么产品/服务、如何联系。本站的首页、解决方案、关于我们三页已覆盖。
- [ ] 具备隐私政策与使用条款页面（已包含）。App 上架时也需要隐私政策 URL。
- [ ] 具备技术支持页面（已包含）—— App 上架需要提供 Support URL，可直接用 `/support/`。
- [ ] 全站无死链（用 `node build/check.mjs` 验证）。

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
- `support@oceanastra.net` —— 技术支持，同时作为 App Store 的 App 支持联系方式

只有这两个信箱，全站不出现第三个地址。

### 仍待完成的三项

`content/company.json` 顶部 `"_placeholders": true`，构建时会打印清单：

| 项 | 状态 | 说明 |
|---|---|---|
| 两个信箱开通 | ✅ 已完成 | `hello@` / `support@` 已在 Lark Mail 生效。注意 Apple 申请不接受 Gmail，执照上登记的那个个人 Gmail 不能用于账号申请 |
| `dunsNumber` | **空缺** | 执照的 D&B D-U-N-S 栏为空，需先向邓白氏申请，这是 Apple 企业账号的前置条件 |
| DNS 解析 | **待办** | 必须先解析生效，**再**添加 `CNAME` 文件，顺序反了会导致站点暂时无法访问 |

全部完成后把 `"_placeholders"` 改成 `false`，构建时就不再提示。

---

## 一些设计决定

**为什么用生成器而不是手写 21 个 HTML。** 改一次电话号码要动 21 个文件，早晚会漏。内容集中在 JSON、生成物提交进仓库，兼顾了可维护性和"服务端零构建"。

**为什么没有联系表单。** 静态站的表单必须依赖第三方服务（Formspree 等），多一个可能挂掉的外部依赖，而 Apple 审核只需要看到可用的联系方式。目前直接展示邮箱和电话，更可靠也更容易核实。

**为什么没有第三方分析和 Cookie 横幅。** 不装分析工具就不需要 Cookie 同意横幅，隐私政策也能写得干净。语言偏好只存在浏览器 localStorage，不回传。

**关于第三方软件代理的措辞。** 「精选企业软件代理」一节已按确认的合作关系点名 **Lark** 与 **Amap**，并在该节末尾附商标归属声明（「Lark 与 Amap 为其各自权利人的商标，每项合作的具体范围及商务性质在商务洽谈阶段书面确认」）。措辞刻意停留在「我们代理的平台 / Platforms we represent」，未使用「官方授权经销商」「Authorised Reseller」这类需要厂商书面授权背书的表述 —— 如果确有对应授权书，可以再升级措辞。

**经营范围提示。** 执照登记的两项活动是 *IT Infrastructure* 和 *Computer Systems & Communication Equipment Software Design*，均属软件设计/IT 基建。官网上的「ERP 自研」和「CorpOS」落在这个范围内，但「第三方软件代理」通常对应的是贸易类活动。这不影响 Apple 审核，但建议向注册代理（PRO）确认是否需要增补经营活动。
