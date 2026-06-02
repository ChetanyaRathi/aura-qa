"""dom_utils.py - shrink a live web page down to what matters.

A real page is thousands of lines. We keep only the things a user can act on
(buttons, inputs, links, selects) with their text, role, and a usable selector.
That small list is what we hand to the AI - cheap and accurate.
"""

from __future__ import annotations

# JavaScript that runs inside the page and returns a compact list of the
# interactive, visible elements plus a best-guess unique CSS selector for each.
_SNAPSHOT_JS = r"""
() => {
  function isVisible(el) {
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 &&
           style.visibility !== 'hidden' && style.display !== 'none' &&
           style.opacity !== '0';
  }

  function cssPath(el) {
    if (el.id) return '#' + CSS.escape(el.id);
    if (el.getAttribute('data-testid'))
      return '[data-testid="' + el.getAttribute('data-testid') + '"]';
    const parts = [];
    while (el && el.nodeType === 1 && parts.length < 5) {
      let sel = el.nodeName.toLowerCase();
      if (el.className && typeof el.className === 'string') {
        const cls = el.className.trim().split(/\s+/).slice(0, 2)
                      .map(c => '.' + CSS.escape(c)).join('');
        sel += cls;
      }
      const parent = el.parentNode;
      if (parent) {
        const siblings = Array.from(parent.children).filter(
          c => c.nodeName === el.nodeName);
        if (siblings.length > 1)
          sel += ':nth-of-type(' + (siblings.indexOf(el) + 1) + ')';
      }
      parts.unshift(sel);
      el = el.parentNode;
    }
    return parts.join(' > ');
  }

  const selector = 'a, button, input, select, textarea, ' +
                   '[role="button"], [role="link"], [onclick]';
  const nodes = Array.from(document.querySelectorAll(selector));
  const out = [];
  let i = 0;
  for (const el of nodes) {
    if (!isVisible(el)) continue;
    out.push({
      index: i++,
      tag: el.nodeName.toLowerCase(),
      role: el.getAttribute('role') || '',
      text: (el.innerText || el.value || '').trim().slice(0, 80),
      placeholder: el.getAttribute('placeholder') || '',
      aria: el.getAttribute('aria-label') || '',
      name: el.getAttribute('name') || '',
      type: el.getAttribute('type') || '',
      selector: cssPath(el)
    });
    if (out.length >= 120) break;  // keep the prompt small
  }
  return out;
}
"""


def snapshot(page) -> list[dict]:
    """Return a compact list of interactive, visible elements on the page."""
    return page.evaluate(_SNAPSHOT_JS)


def to_prompt_text(elements: list[dict]) -> str:
    """Turn the element list into a short numbered block for the AI."""
    lines = []
    for el in elements:
        label = el["text"] or el["aria"] or el["placeholder"] or el["name"]
        descr = f'[{el["index"]}] <{el["tag"]}'
        if el["type"]:
            descr += f' type={el["type"]}'
        if el["role"]:
            descr += f' role={el["role"]}'
        descr += f'> "{label}"  selector={el["selector"]}'
        lines.append(descr)
    return "\n".join(lines)
