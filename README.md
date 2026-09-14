# Smṛtimuktāphalam

Vaidyanātha Dīkṣita's *Smṛtimuktāphalam*, the Tamil edition (with the Sanskrit
mūla and its Tamil rendering), in seven volumes — transcribed, indexed by the
book's own contents list, and readable mūla beside rendering.

**Open `index.html`** — the anukramaṇikā over all seven kāṇḍas. Each kāṇḍa is
one self-contained page (`smp1.html` … `smp7.html`) and works off a `file://`
path as well as off GitHub Pages.

## Source

The seven volumes were taken from the scans published by
[svradhakrishnasastri.in](https://svradhakrishnasastri.in/), on its
[Śāstra books page](https://svradhakrishnasastri.in/sastra/) — with thanks.
The scans are not copied here; go there for the printed pages.

## What is here

| path | what it is |
|------|------------|
| `index.html`, `smp1.html` … `smp7.html` | the site |
| `ocr/<tag>/pages/leaf-NNN.md` | machine OCR of each text leaf, as returned; `NNN` is the PDF page of the scan |
| `ocr/<tag>/toc/`, `ocr/<tag>/front/` | the contents pages and front matter, OCR'd with their own prompts |
| `ocr/<tag>/manifest.tsv` | the class each leaf was sorted into (text, toc, front, picture, blank) |
| `text/<tag>.md` | the assembled text of a volume, with page anchors |
| `text/<tag>_blocks.jsonl` | one record per block: script, PDF page, printed page |
| `text/<tag>_toc.tsv` | the contents list: printed page, Sanskrit title, Tamil title |
| `text/<tag>_headings.tsv` | each contents entry checked against the headings printed in the body |
| `text/smp2_sources.tsv` | the digest's own list of its authorities and works (printed in part 2) |

The transcription is machine OCR and has not been proof-read in full. A
citation into this edition is by volume and printed page.

| tag | kāṇḍa |
|-----|-------|
| smp1 | वर्णाश्रमधर्मकाण्डः · வர்ணாசிரம தர்மகாண்டம் |
| smp2 | आह्निककाण्ड: - पूर्वभाग: · ஆஹ்நிக காண்டம் - பூர்வபாகம் |
| smp3 | आह्निककाण्ड: - उत्तरभाग: · ஆஹ்நிக காண்டம் - உத்தரபாகம் |
| smp4 | आशौचकाण्ड: · ஆசௌச காண்டம் |
| smp5 | श्राद्धकाण्ड: - पूर्वभाग: · சிராத்த காண்டம் - பூர்வபாகம் |
| smp6 | श्राद्धकाण्ड: - उत्तरभाग: · சிராத்த காண்டம் - உத்தர பாகம் |
| smp7 | तिथिनिर्णयकाण्ड: / प्रायश्चित्तकाण्ड: · திதி நிர்ணய காண்டம் / ப்ராயச்சித்த காண்டம் |
