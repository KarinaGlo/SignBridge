import re
from pathlib import Path

html = Path('web/index.html').read_text(encoding='utf-8')
texts = re.findall(r'>([^<]+)<', html)
candidates = []
english_words = [
    'live captions', 'caption size', 'connected', 'listening', 'people & devices', 
    'teacher', 'student', 'invite devices', 'end class', 'give the floor', 
    'stop sharing', 'everyone can contribute', 'personal workspace', 'demo workspace',
    'learning without borders', 'environmental studies', 'notice', 'think', 'share',
    'speech output on', 'recognizing signs', 'clean water starts'
]

for t in texts:
    s = t.strip()
    if not s or s.startswith('&') or s.isdigit():
        continue
    for ew in english_words:
        if ew in s.lower():
            candidates.append((ew, s))

print('Found candidates:', len(candidates))
for ew, s in set(candidates):
    print(f'  [{ew}] -> "{s}"')

