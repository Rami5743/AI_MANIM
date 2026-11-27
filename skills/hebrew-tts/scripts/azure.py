"""One Azure text-to-speech request, with the waits the free tier needs.

The key is never in code: in a cloud session the network proxy adds it to
every request to the host (the header carries a placeholder); elsewhere set
AZURE_SPEECH_KEY.
"""
import hashlib, os, time, urllib.error, urllib.request

REGION = os.environ.get("AZURE_SPEECH_REGION", "westeurope")


def speak(doc, fmt="riff-48khz-16bit-mono-pcm", region=None):
    url = f"https://{region or REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    req = urllib.request.Request(url, data=doc.encode("utf-8"), method="POST", headers={
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": fmt,
        "User-Agent": "hebrew-tts",
        "Ocp-Apim-Subscription-Key": os.environ.get("AZURE_SPEECH_KEY", "proxy-injected")})
    for attempt in range(12):
        try:
            return urllib.request.urlopen(req).read()
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise SystemExit(f"Azure: {e.code} {e.read()[:300]!r}")
            time.sleep(int(e.headers.get("Retry-After") or 0) or 10 * (attempt + 1))
    raise SystemExit("Azure: still 429 after 12 tries")


def document(body, voice, lang="he-IL"):
    return (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">'
            f'<voice name="{voice}"><s>{body}</s></voice></speak>')


def cached(doc, cache_dir, region=None):
    """The audio of doc, from cache_dir if it was spoken before."""
    path = os.path.join(cache_dir, hashlib.sha256(doc.encode()).hexdigest()[:20] + ".wav")
    if not os.path.exists(path):
        os.makedirs(cache_dir, exist_ok=True)
        data = speak(doc, region=region)
        with open(path + ".tmp", "wb") as f:      # never leave an empty file behind
            f.write(data)
        os.replace(path + ".tmp", path)
    return path
