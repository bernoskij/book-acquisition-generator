"""
Generate synthetic book content (200-500 word blurbs/excerpts) for comp titles.
Uses genre-specific vocabulary, themes, and narrative patterns to create
distinguishable content that enables meaningful similarity matching.
"""

import random

from faker import Faker

fake = Faker()


# Genre-specific vocabulary pools for generating distinctive content
GENRE_VOCABULARY = {
    "Literary Fiction": {
        "themes": [
            "memory", "identity", "loss", "family", "time", "silence",
            "inheritance", "displacement", "grief", "belonging", "solitude",
            "transformation", "consciousness", "mortality", "beauty",
        ],
        "settings": [
            "a crumbling estate", "a coastal village", "a university town",
            "a quiet suburb", "an artist's studio", "a fading bookshop",
            "a lakeside cabin", "a foreign city", "a childhood home",
        ],
        "tones": [
            "elegiac", "meditative", "luminous", "restrained", "intimate",
            "haunting", "lyrical", "spare", "unflinching",
        ],
        "subjects": [
            "a woman returning to her hometown after decades abroad",
            "a professor confronting the gaps in his own history",
            "three generations of a family unraveling a shared secret",
            "a marriage dissolving over the course of a single summer",
            "an artist grappling with the ethics of representation",
            "a translator discovering hidden meanings in a dead author's work",
            "siblings reuniting at their mother's deathbed",
            "a friendship tested by success and envy",
        ],
    },
    "Commercial Fiction": {
        "themes": [
            "secrets", "betrayal", "redemption", "love", "ambition",
            "friendship", "revenge", "forgiveness", "courage", "destiny",
            "second chances", "loyalty", "sacrifice", "truth",
        ],
        "settings": [
            "a small town with dark secrets", "a glamorous Manhattan penthouse",
            "a tight-knit neighborhood", "a prestigious law firm",
            "a beachside community", "a family-owned restaurant",
            "a competitive prep school", "a bustling newsroom",
        ],
        "tones": [
            "propulsive", "emotional", "gripping", "heartwarming",
            "page-turning", "suspenseful", "bittersweet", "compelling",
        ],
        "subjects": [
            "a woman who discovers her husband's double life",
            "four friends whose reunion exposes buried resentments",
            "a mother fighting to protect her family from a dangerous past",
            "a journalist uncovering a conspiracy that hits close to home",
            "neighbors whose perfect lives hide devastating truths",
            "a woman starting over after losing everything",
            "a family torn apart by an inheritance dispute",
            "two strangers connected by a decades-old mystery",
        ],
    },
    "Thriller": {
        "themes": [
            "paranoia", "surveillance", "conspiracy", "survival", "deception",
            "justice", "power", "corruption", "obsession", "danger",
            "manipulation", "escape", "vengeance", "trust",
        ],
        "settings": [
            "a locked-down government facility", "the dark web",
            "a remote mountain compound", "a high-security prison",
            "the corridors of political power", "an isolated research station",
            "a surveillance state", "a war-torn border region",
        ],
        "tones": [
            "relentless", "taut", "explosive", "chilling", "razor-sharp",
            "breakneck", "menacing", "electrifying", "visceral",
        ],
        "subjects": [
            "an intelligence analyst who stumbles onto a mole within the agency",
            "a kidnapping victim who must outwit her captor to survive",
            "a detective pursuing a serial killer who leaves coded messages",
            "a whistleblower hunted by the corporation she exposed",
            "a cyber-security expert racing to prevent a catastrophic hack",
            "a soldier discovering her own government ordered her assassination",
            "a lawyer whose client may be orchestrating attacks from prison",
            "a journalist who receives evidence of a political assassination",
        ],
    },
    "Romance": {
        "themes": [
            "love", "passion", "vulnerability", "trust", "desire",
            "commitment", "healing", "connection", "fate", "devotion",
            "chemistry", "tenderness", "longing", "intimacy",
        ],
        "settings": [
            "a charming bookshop", "a vineyard in Tuscany",
            "a snowy mountain lodge", "a bustling bakery",
            "a seaside cottage", "a flower farm",
            "a cozy small town", "a glamorous city",
        ],
        "tones": [
            "swoony", "heartfelt", "steamy", "tender", "witty",
            "passionate", "charming", "emotional", "sparkling",
        ],
        "subjects": [
            "childhood sweethearts reuniting after years apart",
            "rivals forced to collaborate who discover unexpected chemistry",
            "a woman who swore off love meeting someone who changes everything",
            "a fake dating arrangement that becomes dangerously real",
            "two people healing from past heartbreak finding each other",
            "a second-chance romance complicated by family expectations",
            "strangers snowed in together over the holidays",
            "a grumpy recluse softened by an optimistic newcomer",
        ],
    },
    "Science Fiction": {
        "themes": [
            "technology", "consciousness", "evolution", "dystopia", "exploration",
            "artificial intelligence", "time", "humanity", "colonization",
            "singularity", "entropy", "transcendence", "alienation", "progress",
        ],
        "settings": [
            "a generation ship drifting between stars", "a terraformed Mars colony",
            "a post-singularity Earth", "a space station at the edge of known space",
            "a virtual reality indistinguishable from the real",
            "an underground city after ecological collapse",
            "a planet with incomprehensible alien ruins",
            "a near-future megacity stratified by genetic class",
        ],
        "tones": [
            "cerebral", "visionary", "unsettling", "awe-inspiring",
            "philosophical", "propulsive", "bleak", "wonder-filled",
        ],
        "subjects": [
            "a scientist who discovers consciousness can be transmitted across light-years",
            "the last humans debating whether to merge with AI or remain biological",
            "a colony ship's AI developing emotions it was never designed to have",
            "a time traveler trapped in a loop trying to prevent humanity's extinction",
            "first contact with an alien species that communicates through mathematics",
            "a programmer who realizes her simulation contains sentient beings",
            "a soldier augmented beyond recognition questioning what remains human",
            "a generation born in space who have never seen Earth",
        ],
    },
    "Fantasy": {
        "themes": [
            "magic", "prophecy", "power", "destiny", "sacrifice",
            "kingdoms", "ancient evil", "chosen one", "transformation",
            "balance", "corruption", "legacy", "rebellion", "myth",
        ],
        "settings": [
            "a crumbling empire held together by forbidden magic",
            "a forest where the trees remember everything",
            "a city built on the bones of a dead god",
            "a kingdom where magic is outlawed",
            "a floating archipelago above an endless storm",
            "a library containing every spell ever written",
            "a borderland between the mortal world and the fae",
            "a desert civilization powered by captured starlight",
        ],
        "tones": [
            "epic", "dark", "lush", "mythic", "sweeping",
            "intimate", "brutal", "enchanting", "atmospheric",
        ],
        "subjects": [
            "a thief who accidentally steals a god's power",
            "a healer in a world where magic demands blood payment",
            "the last dragon-rider trying to prevent a war between realms",
            "a princess who discovers her kingdom was built on a lie",
            "a mapmaker charting lands that shift with the phases of the moon",
            "a blacksmith forging weapons that carry their wielders' memories",
            "an orphan whose forbidden magic could either save or destroy the realm",
            "a scholar deciphering a prophecy that names her as the villain",
        ],
    },
    "Mystery": {
        "themes": [
            "truth", "justice", "deception", "guilt", "secrets",
            "obsession", "morality", "evidence", "suspicion", "closure",
            "corruption", "innocence", "motive", "alibi",
        ],
        "settings": [
            "a wealthy estate during a weekend gathering",
            "a quiet English village", "a prestigious university",
            "a remote island community", "a private members' club",
            "a historic hotel", "a close-knit fishing town",
            "a locked room in a country manor",
        ],
        "tones": [
            "atmospheric", "twisty", "cerebral", "cozy", "noir",
            "suspenseful", "wry", "brooding", "intricate",
        ],
        "subjects": [
            "a detective revisiting a cold case that destroyed her career",
            "a death at a reunion that everyone has reason to have caused",
            "a missing person case where the victim may not want to be found",
            "a series of thefts connected by an impossible pattern",
            "a true-crime podcaster who becomes entangled in an active case",
            "a locked-room murder with no apparent means of entry",
            "a small-town librarian who notices a pattern in local disappearances",
            "an inheritance contingent on solving a decades-old puzzle",
        ],
    },
    "Historical Fiction": {
        "themes": [
            "war", "empire", "revolution", "survival", "forbidden love",
            "duty", "honor", "resistance", "legacy", "exile",
            "class", "faith", "discovery", "oppression",
        ],
        "settings": [
            "occupied Paris during World War II", "the court of a Tudor monarch",
            "a plantation in the antebellum South", "revolutionary Russia",
            "ancient Rome at the height of its power",
            "a Viking settlement on a foreign shore",
            "the Silk Road during the Mongol Empire",
            "a suffragette movement in Edwardian England",
        ],
        "tones": [
            "sweeping", "immersive", "vivid", "poignant", "epic",
            "intimate", "unflinching", "richly detailed", "evocative",
        ],
        "subjects": [
            "a woman running an escape network under the noses of occupiers",
            "a soldier questioning his loyalty as an empire crumbles",
            "a forbidden romance across enemy lines during wartime",
            "a servant who rises to influence the fate of a dynasty",
            "an archaeologist whose discovery rewrites accepted history",
            "a family saga spanning three generations and two continents",
            "a spy embedded in a royal court with divided loyalties",
            "a healer navigating plague, superstition, and political intrigue",
        ],
    },
    "Memoir": {
        "themes": [
            "resilience", "identity", "family", "addiction", "healing",
            "self-discovery", "trauma", "growth", "belonging", "truth",
            "forgiveness", "courage", "vulnerability", "reinvention",
        ],
        "settings": [
            "a dysfunctional household", "the competitive world of professional sports",
            "a religious community", "the foster care system",
            "a war zone", "the entertainment industry",
            "a rural community", "immigrant life in a new country",
        ],
        "tones": [
            "raw", "honest", "unflinching", "tender", "darkly funny",
            "reflective", "urgent", "compassionate", "revelatory",
        ],
        "subjects": [
            "growing up in a family defined by a parent's mental illness",
            "surviving and rebuilding after a catastrophic loss",
            "navigating identity across cultures and languages",
            "escaping a controlling community and finding autonomy",
            "a career in a high-pressure field and the cost of ambition",
            "confronting generational trauma and choosing to break the cycle",
            "a journey through addiction and the long road to recovery",
            "discovering a family secret that reframes an entire childhood",
        ],
    },
    "Narrative Nonfiction": {
        "themes": [
            "discovery", "obsession", "justice", "innovation", "survival",
            "systems", "power", "truth", "human nature", "consequence",
            "ambition", "failure", "resilience", "complexity",
        ],
        "settings": [
            "a groundbreaking laboratory", "a courtroom battle",
            "an expedition into uncharted territory", "a corporate boardroom",
            "a disaster zone", "a political campaign",
            "a marginalized community fighting for recognition",
            "the intersection of technology and society",
        ],
        "tones": [
            "riveting", "meticulously researched", "propulsive",
            "illuminating", "deeply reported", "panoramic",
            "urgent", "revelatory", "accessible",
        ],
        "subjects": [
            "the untold story behind a scientific breakthrough",
            "a miscarriage of justice and the fight to overturn it",
            "how a single decision cascaded into a systemic crisis",
            "the obsessive pursuit that led to an unlikely discovery",
            "ordinary people caught in extraordinary historical events",
            "the hidden infrastructure that shapes daily life",
            "a community's battle against a powerful institution",
            "the human cost of a technological revolution",
        ],
    },
    "Self-Help": {
        "themes": [
            "habits", "mindset", "productivity", "relationships", "purpose",
            "boundaries", "confidence", "resilience", "clarity", "growth",
            "wellness", "balance", "authenticity", "fulfillment",
        ],
        "settings": [
            "modern professional life", "personal relationships",
            "the digital age", "career transitions",
            "health and wellness", "creative pursuits",
            "leadership challenges", "daily routines",
        ],
        "tones": [
            "empowering", "practical", "evidence-based", "compassionate",
            "direct", "motivating", "accessible", "transformative",
        ],
        "subjects": [
            "a framework for building lasting habits through small changes",
            "redefining success beyond conventional metrics",
            "navigating difficult conversations with confidence",
            "overcoming perfectionism and embracing imperfect action",
            "building emotional resilience in an uncertain world",
            "a science-backed approach to better decision-making",
            "setting boundaries without guilt in work and relationships",
            "finding purpose and direction during life transitions",
        ],
    },
    "Business": {
        "themes": [
            "innovation", "leadership", "disruption", "strategy", "culture",
            "growth", "competition", "transformation", "execution", "vision",
            "scale", "failure", "adaptation", "markets",
        ],
        "settings": [
            "Silicon Valley startups", "Fortune 500 boardrooms",
            "emerging markets", "the gig economy",
            "remote-first companies", "family businesses",
            "turnaround situations", "industry disruption",
        ],
        "tones": [
            "authoritative", "data-driven", "narrative", "provocative",
            "practical", "visionary", "contrarian", "accessible",
        ],
        "subjects": [
            "how a failing company reinvented itself through radical transparency",
            "the counterintuitive principles behind sustained innovation",
            "why most leadership advice fails and what actually works",
            "building a company culture that survives hypergrowth",
            "the hidden patterns behind market-creating strategies",
            "a founder's journey from garage startup to global impact",
            "the future of work and how organizations must adapt",
            "lessons from companies that thrived during economic collapse",
        ],
    },
    "Science": {
        "themes": [
            "discovery", "complexity", "evolution", "consciousness", "cosmos",
            "genetics", "ecology", "quantum", "emergence", "extinction",
            "adaptation", "interconnection", "uncertainty", "breakthrough",
        ],
        "settings": [
            "cutting-edge research labs", "deep ocean expeditions",
            "remote field stations", "particle accelerators",
            "ancient fossil sites", "space observatories",
            "rainforest canopies", "Antarctic ice cores",
        ],
        "tones": [
            "wonder-filled", "rigorous", "accessible", "mind-expanding",
            "narrative", "precise", "poetic", "illuminating",
        ],
        "subjects": [
            "a new theory that unifies seemingly unrelated phenomena",
            "the organisms rewriting our understanding of life itself",
            "how a chance observation led to a paradigm shift",
            "the race to decode a fundamental mystery of the universe",
            "what ancient DNA reveals about human migration and identity",
            "the hidden intelligence of ecosystems and networks",
            "a controversial experiment that challenged scientific consensus",
            "the mathematics underlying beauty, music, and nature",
        ],
    },
    "Biography": {
        "themes": [
            "legacy", "ambition", "genius", "contradiction", "influence",
            "power", "creativity", "obsession", "reinvention", "destiny",
            "scandal", "vision", "sacrifice", "complexity",
        ],
        "settings": [
            "the halls of political power", "artistic circles",
            "scientific institutions", "wartime leadership",
            "cultural movements", "business empires",
            "revolutionary movements", "literary salons",
        ],
        "tones": [
            "definitive", "intimate", "revelatory", "sweeping",
            "nuanced", "unflinching", "sympathetic", "magisterial",
        ],
        "subjects": [
            "the private contradictions of a celebrated public figure",
            "a visionary whose ideas were ahead of their time",
            "the untold influence of a figure history overlooked",
            "a leader whose greatest triumph contained the seeds of downfall",
            "the rivalry that drove two geniuses to their greatest work",
            "a life lived across multiple identities and reinventions",
            "the making of an icon and the myth versus the reality",
            "a forgotten pioneer whose work shaped the modern world",
        ],
    },
}


def generate_book_content(genre: str, title: str, author: str, word_count_range: tuple[int, int] = (200, 500)) -> str:
    """
    Generate a synthetic book blurb/excerpt of 200-500 words.
    Content is genre-specific to enable meaningful similarity comparisons.
    """
    vocab = GENRE_VOCABULARY.get(genre, GENRE_VOCABULARY["Literary Fiction"])

    theme_set = random.sample(vocab["themes"], min(4, len(vocab["themes"])))
    setting = random.choice(vocab["settings"])
    tone = random.choice(vocab["tones"])
    subject = random.choice(vocab["subjects"])

    # Build the content from multiple paragraph types
    paragraphs = []

    # Opening hook / jacket copy style
    paragraphs.append(_generate_opening(subject, setting, tone, genre))

    # Thematic development paragraph
    paragraphs.append(_generate_thematic_paragraph(theme_set, setting, genre))

    # Character/narrative paragraph
    paragraphs.append(_generate_narrative_paragraph(subject, theme_set, tone, genre))

    # Critical praise / positioning paragraph
    paragraphs.append(_generate_positioning_paragraph(tone, theme_set, genre, title, author))

    content = " ".join(paragraphs)

    # Trim or extend to target word count
    words = content.split()
    target = random.randint(*word_count_range)

    if len(words) > target:
        words = words[:target]
        # End on a complete sentence if possible
        text = " ".join(words)
        last_period = text.rfind(".")
        if last_period > len(text) * 0.7:
            text = text[: last_period + 1]
        return text
    else:
        # Pad with additional thematic content
        while len(words) < target:
            extra = _generate_thematic_paragraph(
                random.sample(vocab["themes"], 3), random.choice(vocab["settings"]), genre
            )
            words.extend(extra.split())
        return " ".join(words[:target])


def _generate_opening(subject: str, setting: str, tone: str, genre: str) -> str:
    """Generate an opening hook paragraph."""
    openers = [
        f"Set against the backdrop of {setting}, this {tone} novel follows {subject}. "
        f"From the very first page, readers are drawn into a world where nothing is quite as it seems, "
        f"and every revelation carries the weight of consequence.",

        f"In {setting}, {subject}. What begins as a seemingly straightforward narrative "
        f"unfolds into something far more complex and {tone}, challenging assumptions "
        f"about what we think we know and what remains hidden beneath the surface.",

        f"A {tone} exploration of {subject}. Against the vivid backdrop of {setting}, "
        f"the story builds with quiet intensity, layering meaning upon meaning until "
        f"the full picture emerges with devastating clarity.",

        f"When {subject}, the consequences ripple outward in ways no one could have predicted. "
        f"Set in {setting}, this {tone} work examines the spaces between intention and impact, "
        f"between the stories we tell ourselves and the truths we cannot escape.",
    ]
    return random.choice(openers)


def _generate_thematic_paragraph(themes: list[str], setting: str, genre: str) -> str:
    """Generate a paragraph exploring the book's themes."""
    theme_str = ", ".join(themes[:-1]) + f", and {themes[-1]}"

    paragraphs = [
        f"At its core, this is a story about {theme_str}. The narrative weaves these threads "
        f"together with precision and emotional depth, creating a tapestry that resonates long "
        f"after the final page. Each character embodies a different facet of these central concerns, "
        f"their intersecting lives illuminating the complexity of human experience.",

        f"The themes of {theme_str} pulse through every chapter, grounding the narrative "
        f"in questions that feel both timeless and urgently contemporary. The author approaches "
        f"these subjects with nuance and intelligence, refusing easy answers while offering "
        f"moments of genuine insight and emotional truth.",

        f"Through the lens of {theme_str}, the work examines how individuals navigate "
        f"forces larger than themselves. The setting of {setting} becomes more than backdrop; "
        f"it functions as a character in its own right, shaping and constraining the choices "
        f"available to those who inhabit it.",

        f"Questions of {theme_str} drive the narrative forward with compelling urgency. "
        f"Rather than offering simple resolutions, the story sits with ambiguity, "
        f"acknowledging that these fundamental human concerns resist tidy conclusions. "
        f"The result is a work that rewards reflection and rereading.",
    ]
    return random.choice(paragraphs)


def _generate_narrative_paragraph(subject: str, themes: list[str], tone: str, genre: str) -> str:
    """Generate a paragraph about narrative and character."""
    paragraphs = [
        f"The characters are rendered with remarkable specificity, their voices distinct "
        f"and their motivations layered. As the story of {subject} unfolds, the reader "
        f"is invited to hold multiple perspectives simultaneously, finding sympathy in "
        f"unexpected places and complexity where simplicity might be more comfortable.",

        f"What elevates this narrative beyond its premise is the {tone} quality of the "
        f"prose and the depth of characterization. The central figure navigating this story "
        f"is neither hero nor villain but something more interesting: a fully realized person "
        f"making choices under pressure, shaped by {themes[0]} and {themes[1]}.",

        f"The pacing is masterful, alternating between moments of quiet introspection "
        f"and sequences of mounting tension. The author trusts the reader to sit with "
        f"discomfort, to follow the logic of {themes[0]} to its natural conclusion, "
        f"even when that conclusion challenges comfortable assumptions.",

        f"Structure and voice work in concert here, the {tone} narrative unfolding "
        f"across timelines and perspectives that gradually converge. Each section "
        f"adds a new dimension to the central question, building toward a resolution "
        f"that feels both surprising and inevitable.",
    ]
    return random.choice(paragraphs)


def _generate_positioning_paragraph(tone: str, themes: list[str], genre: str, title: str, author: str) -> str:
    """Generate a paragraph positioning the book in the market."""
    comp_authors = {
        "Literary Fiction": ["Donna Tartt", "Hanya Yanagihara", "Colson Whitehead", "Rachel Cusk"],
        "Commercial Fiction": ["Liane Moriarty", "Taylor Jenkins Reid", "Jojo Moyes", "Fredrik Backman"],
        "Thriller": ["Gillian Flynn", "Tana French", "Don Winslow", "Karin Slaughter"],
        "Romance": ["Emily Henry", "Ali Hazelwood", "Talia Hibbert", "Christina Lauren"],
        "Science Fiction": ["Ted Chiang", "Becky Chambers", "Adrian Tchaikovsky", "Martha Wells"],
        "Fantasy": ["N.K. Jemisin", "Joe Abercrombie", "Samantha Shannon", "R.F. Kuang"],
        "Mystery": ["Anthony Horowitz", "Tana French", "Ruth Ware", "Richard Osman"],
        "Historical Fiction": ["Anthony Doerr", "Kristin Hannah", "Hilary Mantel", "Amor Towles"],
        "Memoir": ["Tara Westover", "Kiese Laymon", "Carmen Maria Machado", "Matthew Perry"],
        "Narrative Nonfiction": ["Erik Larson", "Patrick Radden Keefe", "Rebecca Skloot", "Michael Lewis"],
        "Self-Help": ["James Clear", "Brené Brown", "Mark Manson", "Adam Grant"],
        "Business": ["Walter Isaacson", "Ben Horowitz", "Reed Hastings", "Daniel Pink"],
        "Science": ["Ed Yong", "Carlo Rovelli", "Siddhartha Mukherjee", "Mary Roach"],
        "Biography": ["Ron Chernow", "Walter Isaacson", "Robert Caro", "Tina Brown"],
    }

    genre_comps = comp_authors.get(genre, comp_authors["Literary Fiction"])
    selected_comps = random.sample(genre_comps, 2)

    paragraphs = [
        f"Readers who loved the work of {selected_comps[0]} and {selected_comps[1]} "
        f"will find much to admire here. {title} occupies a similar space in the {genre.lower()} "
        f"landscape, combining {tone} storytelling with deep engagement with {themes[0]} "
        f"and {themes[1]}. {author} brings a fresh perspective to familiar territory, "
        f"creating something that feels both timely and enduring.",

        f"In the tradition of {selected_comps[0]} and {selected_comps[1]}, {author} "
        f"delivers a {tone} work that refuses to look away from difficult truths. "
        f"{title} will appeal to readers hungry for {genre.lower()} that challenges "
        f"as much as it entertains, offering no easy comfort but genuine illumination.",

        f"{author} joins the ranks of {selected_comps[0]} and {selected_comps[1]} "
        f"with this {tone} contribution to contemporary {genre.lower()}. The treatment "
        f"of {themes[0]} and {themes[1]} is both intellectually rigorous and emotionally "
        f"generous, marking {title} as a significant addition to the conversation.",
    ]
    return random.choice(paragraphs)


if __name__ == "__main__":
    # Demo: generate content for a few genres
    for genre in ["Literary Fiction", "Thriller", "Romance"]:
        print(f"\n{'='*60}")
        print(f"GENRE: {genre}")
        print(f"{'='*60}")
        content = generate_book_content(genre, "Sample Title", "Sample Author")
        print(content)
        print(f"\n[Word count: {len(content.split())}]")
