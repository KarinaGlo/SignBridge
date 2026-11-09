from html.parser import HTMLParser
from pathlib import Path

class Validator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.self_closing = {
            'meta', 'link', 'img', 'br', 'hr', 'input', 'col', 'area', 'base', 'param', 'source', 'track', 'wbr'
        }
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() not in self.self_closing:
            self.stack.append((tag.lower(), self.getpos()))

    def handle_endtag(self, tag):
        tag_l = tag.lower()
        if tag_l in self.self_closing:
            return
        if not self.stack:
            self.errors.append(f"Unexpected end tag </{tag_l}> at {self.getpos()}")
            return
        last_tag, last_pos = self.stack.pop()
        if last_tag != tag_l:
            self.errors.append(f"Mismatched tag: expected </{last_tag}> (opened at {last_pos}), got </{tag_l}> at {self.getpos()}")

content = Path('web/index.html').read_text(encoding='utf-8')
parser = Validator()
parser.feed(content)

print(f"Validation finished. Unclosed tags: {len(parser.stack)}, Errors: {len(parser.errors)}")
if parser.errors:
    for e in parser.errors[:10]:
        print("  Error:", e)
if parser.stack:
    for t in parser.stack:
        print("  Unclosed:", t)

assert len(parser.errors) == 0, "HTML has syntax errors!"
assert len(parser.stack) == 0, "HTML has unclosed tags!"
print("=== HTML VALIDATION 100% CLEAN! ===")

