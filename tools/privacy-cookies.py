#!/usr/bin/env python3
"""
Correct section 10 of the privacy policy — cookies and similar technologies.

    python3 tools/privacy-cookies.py

Run any time after prerender.py. Re-run after a re-export: the text lives in
the Design Canvas DICT, so an export brings the old wording back.

Two problems with what was published.

The first was false. It said the language preference is "stored locally in your
browser so that the site remembers it on your next visit". Nothing on this site
has ever stored it: there is no localStorage, no sessionStorage and no
document.cookie anywhere in the export — grep all nine pages and every hit is
zero. Before the switcher moved to URLs the preference lived in component state
and died on reload; now it lives in the address bar. A privacy policy that
claims a storage mechanism the site does not have is wrong in the direction
that matters, so it says what actually happens instead.

The second was about to become misleading. "Does not use third-party analytics"
was true and stays true of this site's pages — Google Search Console and Bing
Webmaster Tools add no script and set no cookie; they report on what the search
engine collected on its own side. But a reader has no way to tell that from
silence, so the consoles are named, and "analytics" is narrowed to "analytics
scripts", which is the thing a visitor can actually be affected by.

The sentence appears in each of the three privacy pages twice over: once per
language in the template's DICT, and once more in the prerendered copy, in that
page's own language. content/i18n/{en,zh,ar}.json holds the same prose as the
source of truth. Twelve occurrences in six files, all replaced here.

The Arabic is a translation of the new English, following the sentence shapes
already in the file. It should be read by a native speaker before it is relied
on — it is a legal document, and this tool cannot judge register.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FILES = ["privacy/index.html", "zh/privacy/index.html", "ar/privacy/index.html",
         "content/i18n/en.json", "content/i18n/zh.json", "content/i18n/ar.json"]

OLD = {
    "en": "This website does not use advertising cookies, cross-site trackers or third-party analytics. Your language preference is stored locally in your browser so that the site remembers it on your next visit; that preference stays on your device and is not transmitted to us. Standard server logs are retained for security and diagnostic purposes.",
    "zh": "本网站不使用广告 Cookie、跨站跟踪器或第三方分析工具。您的语言偏好保存在浏览器本地，以便下次访问时记住该设置；该偏好仅保留在您的设备上，不会传输给我们。标准服务器日志出于安全与诊断目的保留。",
    "ar": "لا يستخدم هذا الموقع ملفات تعريف ارتباط إعلانية، ولا أدوات تتبّع عبر المواقع، ولا تحليلات من أطراف ثالثة. ويُحفظ تفضيل اللغة محليًا في متصفّحك ليتذكّره الموقع في زيارتك التالية؛ ويبقى هذا التفضيل على جهازك ولا يُرسل إلينا. أمّا سجلات الخادم المعتادة فتُحفظ لأغراض الأمن والتشخيص.",
}

NEW = {
    "en": "This website does not use advertising cookies, cross-site trackers or third-party analytics scripts, and stores nothing on your device — your language choice is carried in the page address rather than saved in your browser. We do use the search engines' own webmaster consoles, which report on data those engines collect themselves and place no tracking on this site. Standard server logs are retained for security and diagnostic purposes.",
    "zh": "本网站不使用广告 Cookie、跨站跟踪器或第三方统计脚本，也不在您的设备上存储任何内容——语言选择由页面地址承载，而不是保存在浏览器里。我们使用搜索引擎自有的站长工具，它呈现的是搜索引擎自行收集的数据，不会在本站植入任何跟踪代码。标准服务器日志出于安全与诊断目的保留。",
    "ar": "لا يستخدم هذا الموقع ملفات تعريف ارتباط إعلانية، ولا أدوات تتبّع عبر المواقع، ولا نصوص تحليلات من أطراف ثالثة، ولا يخزّن شيئًا على جهازك؛ فاختيار اللغة يُحمَل في عنوان الصفحة بدل أن يُحفظ في متصفّحك. ونستخدم أدوات مشرفي المواقع الخاصة بمحرّكات البحث نفسها، وهي تعرض بيانات تجمعها تلك المحرّكات بذاتها ولا تضيف أيّ تتبّع إلى هذا الموقع. أمّا سجلات الخادم المعتادة فتُحفظ لأغراض الأمن والتشخيص.",
}

# The template is JSON-encoded, so a replacement carrying a quote, a backslash
# or a "</" would have to be escaped to match how the payload is written. None
# of the three does; this refuses rather than silently truncating a page.
for code, text in NEW.items():
    if any(c in text for c in '"\\<>&'):
        sys.exit(f"{code}: replacement contains a character that needs escaping")


def main():
    print(f"\n  {'file':<28} {'en':>4} {'zh':>4} {'ar':>4}   status")
    print("  " + "-" * 58)

    changed, done, failed = 0, 0, []
    for rel in FILES:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")

        counts = {c: text.count(OLD[c]) for c in OLD}
        if not any(counts.values()):
            already = sum(text.count(NEW[c]) for c in NEW)
            status = "already done" if already else "NOT FOUND"
            print(f"  {rel:<28} {'—':>4} {'—':>4} {'—':>4}   {status}")
            if already:
                done += 1
            else:
                failed.append(rel)
            continue

        for code in OLD:
            text = text.replace(OLD[code], NEW[code])
        path.write_text(text, encoding="utf-8")

        # Nothing of the old wording may survive anywhere in the file — the
        # prerendered copy carries it as well as the DICT, and a page that
        # disagrees with itself is worse than one that is merely out of date.
        after = path.read_text(encoding="utf-8")
        leftover = sum(after.count(OLD[c]) for c in OLD)
        row = "  ".join(f"{counts[c]:>4}" for c in ("en", "zh", "ar"))
        if leftover:
            print(f"  {rel:<28} {row}   {leftover} left behind")
            failed.append(rel)
            continue
        print(f"  {rel:<28} {row}   replaced")
        changed += 1

    if failed:
        sys.exit(f"\n  Failed: {', '.join(failed)} — the wording changed upstream.\n")
    print(f"\n  {changed} file(s) rewritten, {done} already current.\n")


if __name__ == "__main__":
    main()
