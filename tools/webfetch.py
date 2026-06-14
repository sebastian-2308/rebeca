import urllib.request
import urllib.error
import html
import re


def webfetch(url: str, format: str = "markdown") -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return f"(HTTP error: {e.code} {e.reason})"
    except urllib.error.URLError as e:
        return f"(URL error: {e.reason})"
    except Exception as e:
        return f"(error: {e})"

    if format == "text":
        clean = re.sub(r"<[^>]+>", " ", raw)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean[:10000]

    clean = raw
    clean = re.sub(r"<script[^>]*>.*?</script>", "", clean, flags=re.DOTALL)
    clean = re.sub(r"<style[^>]*>.*?</style>", "", clean, flags=re.DOTALL)
    clean = re.sub(r"<nav[^>]*>.*?</nav>", "", clean, flags=re.DOTALL)
    clean = re.sub(r"<footer[^>]*>.*?</footer>", "", clean, flags=re.DOTALL)

    clean = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1\n", clean, flags=re.DOTALL)
    clean = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1\n", clean, flags=re.DOTALL)
    clean = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1\n", clean, flags=re.DOTALL)
    clean = re.sub(r"<h4[^>]*>(.*?)</h4>", r"#### \1\n", clean, flags=re.DOTALL)
    clean = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", clean, flags=re.DOTALL)
    clean = re.sub(r"<br\s*/?>", "\n", clean)
    clean = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", clean, flags=re.DOTALL)
    clean = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", clean, flags=re.DOTALL)
    clean = re.sub(r"<pre[^>]*>(.*?)</pre>", r"```\n\1\n```\n", clean, flags=re.DOTALL)
    clean = re.sub(r"<a[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", r"[\2](\1)", clean)
    clean = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", clean, flags=re.DOTALL)
    clean = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", clean, flags=re.DOTALL)

    clean = re.sub(r"<[^>]+>", "", clean)
    clean = html.unescape(clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()

    return clean[:8000]
