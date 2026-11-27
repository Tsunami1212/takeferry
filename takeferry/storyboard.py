"""Turn approved shot notes and recorded takes into an editable storyboard."""
import hashlib
import json

from .brief import TakeError, identifier, keys, text


def board_id(*parts):
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def diagram_text(value):
    # Mermaid's numeric entity form keeps a writer's directions inside a quoted label.
    return "".join(c if c.isalnum() or c in " .,!?/-:" else f"#{ord(c)};" for c in value[:160])


def storyboard(ledger, shots, format="canvas"):
    if not isinstance(shots, list) or not 1 <= len(shots) <= 48:
        raise TakeError("Use between one and 48 shots in shooting order.")
    if format not in ("canvas", "mermaid", "cards"):
        raise TakeError("Choose canvas, mermaid or cards.")
    cards, links, seen = [], [], set()
    previous, y = None, 0

    def card(identity, kind, title, detail, column, top):
        key = board_id(*identity)
        cards.append({"id": key, "kind": kind, "title": title, "detail": detail, "x": column * 430, "y": top})
        return key

    def connect(source, target, label):
        links.append({"id": board_id("edge", source, target, label), "from": source, "to": target, "label": label})

    for shot in shots:
        keys(shot, ("shot", "beat"), ("camera", "references"))
        name = identifier(shot["shot"], "shot")
        if name in seen:
            raise TakeError("List each shot once.")
        seen.add(name)
        beat = text(shot["beat"], "beat", 2000)
        detail = [beat]
        if "camera" in shot:
            detail.append(text(shot["camera"], "camera", 500))
        key = card(("shot", name), "shot", name, "\n".join(detail), 1, y)
        if previous:
            connect(previous, key, "next shot")
        previous = key
        refs = shot.get("references", [])
        if not isinstance(refs, list) or len(refs) > 24:
            raise TakeError("Use up to 24 named references per shot.")
        ref_names = set()
        for index, ref in enumerate(refs):
            keys(ref, ("name", "role"))
            title = text(ref["name"], "reference name", 200)
            role = text(ref["role"], "reference role", 512)
            if title in ref_names:
                raise TakeError("Give each storyboard reference a distinct name within its shot.")
            ref_names.add(title)
            ref_id = card(("reference", name, title), "reference", title, role, 0, y + index * 210)
            connect(ref_id, key, role)
        recorded = ledger.list(name)
        selected = recorded["selection"] or {}
        for index, take in enumerate(recorded["takes"]):
            brief = take["brief"]
            take_id = take["id"]
            lines = [brief["provider"] + " / " + brief["model"], brief["camera"],
                     f'{brief["duration"]} seconds, {brief["ratio"]}', take["state"]]
            if selected.get("take_id") == take_id:
                lines.append(f'Selected {selected["start"]:g} to {selected["stop"]:g} seconds')
            item = card(("take", take_id), "take", take_id, "\n".join(lines), 2, y + index * 210)
            parent = brief.get("parent")
            connect(board_id("take", parent) if parent else key, item, "revision" if parent else "take")
        y += max(len(refs), len(recorded["takes"]), 1) * 210 + 90

    if format == "cards":
        return {"format": format, "document": {"cards": cards, "links": links}}
    if format == "mermaid":
        lines = ["flowchart LR"]
        for c in cards:
            label = c["title"] + " / " + c["detail"].replace("\n", " / ")
            lines.append(f'  n{c["id"]}["{diagram_text(label)}"]')
        for edge in links:
            lines.append(f'  n{edge["from"]} -->|"{diagram_text(edge["label"])}"| n{edge["to"]}')
        return {"format": format, "document": "\n".join(lines)}
    colors = {"reference": "3", "shot": "4", "take": "5"}
    nodes = [{"id": c["id"], "type": "text", "text": c["title"] + "\n\n" + c["detail"],
              "x": c["x"], "y": c["y"], "width": 360, "height": 180, "color": colors[c["kind"]]} for c in cards]
    edges = [{"id": e["id"], "fromNode": e["from"], "toNode": e["to"], "toEnd": "arrow", "label": e["label"]}
             for e in links]
    return {"format": format, "document": {"nodes": nodes, "edges": edges}}
