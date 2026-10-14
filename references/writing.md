# Writing the explainer (site text + narration)

The reader is a curious practitioner — often the code's own author — who wants to *understand and
learn*, not just be told what happens. Three layers must coexist on every concept:

1. **What it does** — plain, simplified-technical sentences.
2. **Why it is done this way** — the decision, the alternative, why the alternative loses.
3. **What it is called** — the technical term next to the plain one, so the reader can search it.

A first version that only had layer 1 was judged "too short"; it "cut directly to the next
feature". Each mechanism needs its *why* and its *name*.

## Plain style (user rules, apply to site text, narration and your own reports)

A user asked for a rewrite pass with these rules after the first version; apply them from the start:

- Open each chapter, paragraph and "why" block with the conclusion or the most important point.
  No background first ("Cette étape réduit 40 000 pixels à 55 boîtes. D'abord…").
- Say things literally. No metaphor when a plain phrase works ("zone d'exclusion", not
  "zone interdite"; "aiguillage" became "choix du mode").
- No "it's not X, it's Y" constructions unless they correct a real, common misconception
  (128 in sRGB is 22 % of the light, not 50 %: keep that one).
- No rhetorical questions as transitions ("Pourquoi ? …"). State the reason: "La quantification a
  deux avantages." Headings name the topic without "?" ("Pourquoi la coupe médiane").
- No em dashes. Use a period or a comma.
- No bold in prose. Introduce a term in plain text or `<em>` with its `.tech` tag.
- Give as many reasons as there are; don't round to three.
- If it fits in a paragraph, write a paragraph. "Why" blocks are short paragraphs, not bullet
  lists. Keep numbered lists for real procedures.
- Avoid filler and mannered words: load-bearing, quietly, delve, landscape, "the real X",
  earns its keep, honestly, frankly, essentiel/crucial when "nécessaire" is true.
- Stop when done: no summary paragraph at the end of a chapter, no question to the reader.

## ASD-STE100 rules, adapted

ASD-STE100 (Simplified Technical English) is written for English. Apply its principles to any
language:

- **One term = one meaning, one concept = one term.** Pick the word for each concept once
  ("boîte" for a median-cut box, "candidat" for a box that can enter the palette) and never vary it.
  Put the list in the glossary.
- **Sentence length:** procedures ≤ 20 words, descriptions ≤ 25 words. One idea per sentence.
- **Active voice:** "L'application calcule…", not "Il est calculé…".
- **Procedures are numbered lists**, one action per item, in execution order.
- **Callouts:** warnings start with "Attention" (a pitfall, an invariant that broke before),
  useful information with "Note".
- **No idioms, no metaphors.** Give a literal example instead: "3,37 cm, arrondi au centimètre,
  donne 3 cm".
- **Paragraphs ≤ 6 sentences.**

## Technical terms alongside

- Inline: plain word, then the term in a `.tech` tag — `le pas <span class="tech">stride</span>`.
- Every chapter ends with a **"Termes techniques" table**: plain term | technical term | detail
  (formula, constant, origin paper/year, library it comes from).
- Name the real algorithm and its source: "coupe médiane (median cut, Heckbert 1982)",
  "ColorCutQuantizer (derived from Android's Palette API)", "CIEDE2000", "EMA / first-order low-pass".
- If the user half-remembers a famous technique ("something NASA used"), check the code. If it
  is *not* used (Kalman filter), say so explicitly in a Note and explain why the simpler tools suffice.
  Never invent a connection.

## "Why" blocks — what makes them good

Each block answers a decision in the code:

- State the decision as the first sentence (plain text, no bold), then the reason in 1–3 short sentences.
- Name the alternative and why it loses ("k-means: random start, iterative, can jump between
  near-identical frames; median cut: deterministic, one pass, integers").
- Use real numbers from running the code ("chroma drops from 0.26 to 0.13"; "two blue swatches
  40 apart in RGB = ΔE 0.135, two greens 40 apart = ΔE 0.006").
- Mention limits ("a color under 0.1 % of the frame can disappear. C'est un choix.").
- Mine the codebase for reasons: comments, ADRs, docs, commit messages, test names. Those carry
  the author's real intent; prefer them over generic textbook reasons.

## Defining jargon the reader asked about

When the user asks "what does X mean" (e.g. *quantized*), give it its own section — definition,
everyday example, the concrete numbers in this code (256 → 32 levels, 16.7 M → 32,768 bins),
and an interactive demo when possible.

## Narration text (TTS)

- Same rules, even shorter sentences. Sentences are split on `. : ? !` and used as sync points.
- **Write numbers as words** in the narration ("zéro virgule zéro huit", "mille neuf cent
  vingt"), digits on screen.
- Say each technical name once, introduced plainly: "C'est une sélection gloutonne, en anglais
  greedy selection."
- Start fragments that the scene will sync on with distinctive words; avoid two sentences in the
  same segment starting identically (the scene's `at("…")` matches the *first* sentence containing
  the fragment).
- Pattern per concept: conclusion → what → reason (stated, not asked) → alternative/limit → technical name.
- Mark chapter boundaries in the audio too: the first sentence of each chapter names it
  ("Premier problème : …", "Étape deux : découper.", "Mode une couleur."). The intro says how many
  chapters there are and that a title card opens each one.
- Budget: ~15 characters per second of speech. A 10–12 min video ≈ 10–12 k characters
  (≈ the same number of ElevenLabs credits on multilingual_v2).
