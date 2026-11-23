# Monday Nov 23 publish — operator checklist

Docs tip after this commit lands; retag `v3.0.1` to match.

## 1. Substack (blocker)

Paste [`docs/releases/v3.0.1/verity-engine-oss-3-0-1-golden-release.md`](../releases/v3.0.1/verity-engine-oss-3-0-1-golden-release.md) as a **new** post (do not update the Jan v2 essay in place).

After publish, copy the permalink and replace every CTA that still points at `https://ajjcop.substack.com` (root) in:

- `docs/releases/v3.0.1/verity-engine-oss-3-0-1-release-description.md` (+ rebuild description PDF)
- `docs/launch/BLOG_POST.md` / pack twin
- syndication kit X thread item 7

Keep the GitHub PDF link as:
`https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.1/docs/releases/v3.0.1/verity-engine-oss-3.0.1-golden-release-paper.pdf`

## 2. Smoke

```bash
python -m venv /tmp/vn301smoke && /tmp/vn301smoke/bin/pip install -q 'verityngn[deep]==3.0.1'
/tmp/vn301smoke/bin/python -c "import verityngn; print(verityngn.__version__)"
curl -sI https://verityindex.com/gallery | head -1
```

## 3. Secondary posts

Stagger from [`v3_release_pack/SURFACES.md`](v3_release_pack/SURFACES.md). **Do not attach** `docs/launch/decks/VerityNgn_3_Release_with_examples.pptx`. Attach golden / Multimodal / papers PDFs from the GitHub release assets.
