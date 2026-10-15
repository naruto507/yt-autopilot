import json, os, re
from anthropic import Anthropic
import hookscore

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
_c = None
FORMULAS = ", ".join(f["name"] for f in hookscore.FORMULAS)
SYS = f"""You run the writing side of a faceless YouTube channel. Rules:
- The first 15 seconds does three jobs: confirm what the title promised, open a question the viewer cannot close, prove the payoff exists.
- Hooks use one of these formulas: {FORMULAS}. Spoken, 9-24 words, say "you" early, name what it costs to ignore it.
- Script: one idea per scene, short spoken sentences, no channel intro, no "before we start", no subscribe pitch until the very last line (one ask only).
- Never invent a statistic, quote, source or result. If a fact is not well established, leave it out. No health, legal or money-result promises.
- Titles max 60 chars, thumbnail text max 4 words and a different angle from the title.
- Reply with JSON only, no markdown fences."""

def ask(user, tokens=4000):
    global _c
    _c = _c or Anthropic()
    r = _c.messages.create(model=MODEL, max_tokens=tokens, system=SYS, messages=[{"role": "user", "content": user}])
    return r.content[0].text

def js(t):
    return json.loads(re.search(r"\{.*\}|\[.*\]", t, re.S).group(0))

def pick_topic(ch, ideas, past):
    return ask(f"Niche: {ch['niche']}\nStyle: {ch['style']}\nWhat is winning in this niche right now (learn the patterns, never copy a title):\n"
               + "\n".join(ideas) + "\nAlready made, do not repeat:\n" + "\n".join(past[-40:])
               + "\nReturn ONE fresh video topic as a single line, nothing else.", 200).strip().strip('"')

def make_package(ch, topic, ideas=()):
    long = ch["fmt"] == "long"
    base = f"Niche: {ch['niche']}\nStyle/language notes: {ch['style']}\nTopic: {topic}\nWinning titles in niche (patterns only): {list(ideas)}\n"
    best = None
    for _ in range(2):  # regenerate once if the best hook is weak
        h = js(ask(base + 'Return {"hooks":[5 different openers],"titles":[3],"thumb_text":""}'))
        sc = sorted(((hookscore.score(x)[1], x) for x in h["hooks"]), reverse=True)[0]
        if not best or sc[0] > best[0][0]:
            best = (sc, h)
        if sc[0] >= 60:
            break
    (score, hook), h = best
    title = next((t for t in h["titles"] if len(t) <= 60), h["titles"][0][:60])
    spec = "10-22 scenes, 900-1200 words total" if long else "7-10 scenes, 100-130 words total, last line loops back to the hook so it replays"
    s = js(ask(base + f"Hook (scene 1 narration, verbatim): {hook}\nTitle: {title}\n"
               'Return {"scenes":[{"narration":"","visual":"2-4 word stock footage search, concrete and literal"}],'
               '"description":"2 short paragraphs + 3 hashtags, no fake claims","tags":[]}. ' + spec, 6000))
    return dict(title=title, hook=hook, hook_score=score, thumb_text=h["thumb_text"], **s)
