"""
process.py  –  Categorise + sentiment-score raw reviews, build aggregated JSON
Input:   data/reviews_raw.json
Outputs: data/agg_data.json  +  data/subcat_data.json
"""

import json, re, os
from collections import Counter, defaultdict

os.makedirs("data", exist_ok=True)

# ── CATEGORY DEFINITIONS ──────────────────────────────────────────────────────
CATEGORIES = {
    "App Experience": [
        "crash","crashing","app crash","force close","bug","bugs","glitch","app freeze",
        "freezing","frozen","not loading","not opening","app not working","app is slow",
        "slow app","loading issue","lagging","laggy","hangs","oops something went wrong",
        "blank screen","login issue","unable to login","cannot login","otp not","otp issue",
        "login error","add to cart","cart issue","unable to add","wishlist issue",
        "payment page crash","unable to track","cant track","can't track","tracking page",
        "update app","app update","reinstall","uninstall","share button not",
        "search not working","search issue","filter not working","save applied filter",
        "filter issue","sort issue","navigation issue","confusing interface",
        "multiple store options","too many bugs","app has bugs","nice app","good app",
        "best app","worst app","bad app","app performance","slow performance",
    ],
    "Order Management": [
        "wrong product","wrong item","different product","different item","wrong colour",
        "wrong color","wrong design","received wrong","got wrong","sent wrong",
        "delivered wrong","sending different","not what i ordered","received different",
        "used product","used item","second hand","old product","old stock","used garment",
        "fake product","duplicate product","counterfeit","without a label","no label",
        "label missing","tag missing","no tag","tampered","open box","broken seal",
        "missing item","missing product","items missing","not all items",
        "received only 1","received only one","got only one","delivered only one",
        "incomplete order","partial order","order not placed","order stuck",
        "order not confirmed","not yet dispatched","cancelled without consent",
        "cancelled without reason","self cancelled","cancelled by app","sent me wrong",
        "pillow cover",
    ],
    "Delivery & Logistics": [
        "not delivered","undelivered","delivery boy","delivery agent","delivery partner",
        "delivery executive","delivery date","expected date","delivery time",
        "late delivery","delayed delivery","delivery delay","delay in delivery",
        "fast delivery","quick delivery","on time delivery","arrived","not arrived",
        "yet to arrive","out for delivery","in transit","nearest hub","distribution center",
        "delivery attempt","delivery failed","pincode","not serviceable","not deliverable",
        "cash on delivery","cod not available","delivery boy rude","rude delivery",
        "abusive language","days to deliver","weeks to deliver","still not received",
        "not yet received","still waiting for delivery","courier","xpressbees","shadowfax",
        "delhivery","ekart","bluedart","dispatch","dispatched","shipped","shipment",
        "delivery speed slow","slow delivery","delivery too late","delivery","parcel not",
    ],
    "Returns & Refunds": [
        "return not picked","return pickup","return rejected","return denied",
        "return not accepted","return cancelled","return request","reverse pickup",
        "return window","no return","return issue","refund","money back","refund pending",
        "exchange","exchanged","amount not credited","money not credited",
        "refund not credited","return policy","return process","myncash","myntra cash",
        "credit note forced","replacement",
    ],
    "Customer Support": [
        "customer care","customer support","customer service","support agent",
        "support team","helpline","toll free","no response from","support not responding",
        "support not picking","scripted response","no solution from","no resolution",
        "escalate","raised complaint","called customer care","support is useless",
        "support is pathetic","worst support","helpful support","good customer service",
        "great support","chatbot only",
    ],
    "Product Quality": [
        "fabric quality","material quality","build quality","product quality","fabric is",
        "material is","cloth quality","stitching","finishing","size too big","size too small",
        "size issue","size problem","doesn't fit","does not fit","poor fit","color fading",
        "colour fading","color bleed","genuine product","authentic product","original product",
        "low quality","poor quality","bad quality","cheap quality","very poor quality",
        "good quality","best quality","nice quality","durable","not durable",
        "shrink after wash","faded after wash","quality has gone down","quality degraded",
        "quality of product",
    ],
    "Pricing & Offers": [
        "platform fee","convenience fee","handling fee","extra charges","hidden charges",
        "delivery charges high","shipping charge","overpriced","very expensive",
        "too expensive","price is high","coupon not working","coupon expired",
        "coupon not applied","promo code","voucher code","supercash not","super cash not",
        "cashback not","loyalty points","reward points","gift voucher","gift card",
        "price increased","price hike",
    ],
    "Payment & Checkout": [
        "payment failed","payment failure","payment not done","transaction failed",
        "transaction declined","money deducted but","amount deducted but",
        "charged but order","debited but not","upi failed","card failed","card declined",
        "payment gateway issue","double charged","charged twice",
        "order failed after payment",
    ],
    "Packaging": [
        "packaging damaged","torn package","damaged box","box damaged","poorly packed",
        "bad packaging","good packaging","nice packaging","secure packaging","well packed",
        "polybag",
    ],
    "Overall Satisfaction": [],
}

PRIORITY = [
    "Payment & Checkout","Order Management","Returns & Refunds",
    "Delivery & Logistics","Customer Support","App Experience",
    "Packaging","Pricing & Offers","Product Quality","Overall Satisfaction",
]

# ── SUBCATEGORY DEFINITIONS (negative reviews only) ───────────────────────────
SUBCATEGORIES = {
    "Delivery & Logistics": {
        "Delay in Delivery": [
            "late","delay","delayed","not delivered","not yet received","still not received",
            "not arrived","slow delivery","days late","delivery date","expected date",
            "postponed","rescheduled","not dispatched","still waiting","no movement",
            "in transit","nearest hub","distribution center","days over","not received",
            "15 days","20 days","25 days","30 days","delivery too late","slow delivery",
        ],
        "Delivery Executive Issue": [
            "delivery boy","delivery agent","delivery executive","delivery partner",
            "delivery person","courier boy","rude","abusive","unprofessional",
            "fraud call","scam call","demanded money","privacy","xpressbees","shadowfax",
            "delivery attempt","not reachable","not deliverable","pincode","not serviceable",
        ],
    },
    "Returns & Refunds": {
        "Return Issue": [
            "return not picked","pickup not done","return pickup","return rejected",
            "return denied","return not accepted","return cancelled","return request",
            "reverse pickup","return policy","no return","exchange issue","exchange not",
            "exchange cancelled","exchange rejected","pickup issue","not picking up",
            "return","exchange",
        ],
        "Refund Issue": [
            "refund not","no refund","refund pending","refund delay","refund not received",
            "refund not credited","amount not credited","money not credited",
            "money not returned","refund deducted","platform fee on return",
            "days no refund","myncash","store credit","refund",
        ],
    },
    "Customer Support": {
        "Unable to Connect": [
            "no response","not responding","not picking","always busy","toll free",
            "number busy","call not connecting","chat not available","no one replied",
            "ignored","not replied","nobody",
        ],
        "Unable to Solve Issue": [
            "scripted response","same response","no solution","no resolution",
            "issue not resolved","unresolved","not resolved","nothing done",
            "called multiple times","still not solved","no accountability","no action",
            "useless","pathetic","not helpful","worst support","no help","zero help",
        ],
    },
    "App Experience": {
        "App Crash":              ["crash","crashing","crashed","app crash","force close","stopped"],
        "Slow / Long Loading":    ["slow loading","long loading","takes time","slow to open","performance","slow app","loading","laggy","lag"],
        "Unable to Make Payment": ["unable to pay","cannot pay","payment page crash","payment not working","checkout crash"],
        "Search Issue":           ["search not working","search issue","search problem","search error","wrong search"],
        "Filter & Sort Issue":    ["filter","filters","save filter","applied filter","sort","sorting"],
        "Bugs / App Freeze":      ["bug","bugs","glitch","freeze","freezing","frozen","hang","hangs","error","wrong information","not working"],
        "Login / OTP Issue":      ["login","log in","otp","sign in","unable to login","cannot login","otp not","login error"],
        "Navigation Issue":       ["navigation","confusing","hard to navigate","interface","menu","multiple store"],
    },
    "Product Quality": {
        "Quality Issue":               ["poor quality","bad quality","low quality","quality degraded","quality gone","not durable","shrink","stitching","size issue","doesn't fit","size problem"],
        "Fake / Stained / Old Products":["fake","duplicate","counterfeit","not original","stain","stained","wrinkled","old stock","used product","used garment","second hand","damaged product"],
        "Color Fade":                  ["color fading","colour fading","color fade","colour fade","color bleed","faded after"],
    },
    "Order Management": {
        "Wrong Product Delivered":     ["wrong product","wrong item","different product","different item","wrong colour","wrong color","wrong design","received wrong","got wrong","sent wrong","delivered wrong","not what i ordered","received different"],
        "Tags / Label Missing":        ["without label","no label","label missing","tag missing","no tag","tags removed"],
        "Order Cancelled by Business": ["cancelled by app","cancelled by themselves","self cancelled","cancelled without consent","cancelled without reason","cancelled without"],
        "Missing / Incomplete Order":  ["missing item","missing product","items missing","not all items","received only 1","received only one","got only one","delivered only one","incomplete order","partial order","delivered only"],
    },
    "Payment & Checkout": {
        "Payment Failed / Unable to Pay": ["payment failed","payment failure","payment not done","transaction failed","money deducted but","amount deducted","upi failed","card failed","payment gateway","order failed after payment"],
        "COD Not Available":              ["cod not available","cash on delivery not","no cod","cod not"],
    },
    "Pricing & Offers": {
        "Unable to Apply Coupon":                ["coupon not working","coupon expired","coupon invalid","coupon not applied","promo code not","voucher not","code not working"],
        "Unable to Apply SuperCash":             ["supercash","super cash","myncash","myntra cash","wallet not","cashback not","loyalty points"],
        "Platform / Convenience / Delivery Fees":["platform fee","convenience fee","handling fee","delivery charge","delivery charges","shipping charge","extra charges","hidden charges","fee"],
        "Price is High":                         ["overpriced","very expensive","too expensive","high price","price is high","costly","price hike","price increased","expensive"],
        "Offer / Discount Issue":                ["offer not","offer expired","discount not","deal not","no offer","firstorderfree","offer issue","promised discount","discount not applied"],
    },
}

# ── CATEGORY CLASSIFIER ───────────────────────────────────────────────────────
SHORT_TRIGGERS = [
    "crash","bug","refund","return","delivery","payment","otp","login",
    "fraud","wrong product","missing","exchange","cod","courier",
]

def classify_category(text: str) -> str:
    t = text.lower()
    words = t.split()
    if len(words) <= 4 and not any(tr in t for tr in SHORT_TRIGGERS):
        return "Overall Satisfaction"
    scores = {cat: sum(len(kw.split()) + 1 for kw in CATEGORIES[cat] if kw in t)
              for cat in PRIORITY}
    best = max(scores, key=scores.get)
    if scores.get(best, 0) < 2:
        return "Overall Satisfaction"
    # prevent App Experience from stealing delivery/order keywords
    if best == "App Experience" and scores[best] <= 3:
        other = max((k for k in scores if k not in ("App Experience","Overall Satisfaction")),
                    key=scores.get, default=None)
        if other and scores[other] >= scores[best]:
            best = other
    # edge-case patches
    if best == "Overall Satisfaction":
        if any(kw in t for kw in ["pickup","pick up"]) and any(kw in t for kw in ["late","slow","delay","not","issue"]):
            best = "Delivery & Logistics"
        elif any(kw in t for kw in ["to cart","add cart","wishlist","too many bugs","share button","slow app"]):
            best = "App Experience"
    return best


def classify_subcat(text: str, main_cat: str) -> str | None:
    if main_cat not in SUBCATEGORIES:
        return None
    t = text.lower()
    scores = {sc: sum(len(kw.split()) + 1 for kw in kws if kw in t)
              for sc, kws in SUBCATEGORIES[main_cat].items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else list(SUBCATEGORIES[main_cat].keys())[0]


# ── SENTIMENT ENGINE ──────────────────────────────────────────────────────────
STRONG_NEG = [
    "worst","terrible","horrible","pathetic","fraud","fraudulent","cheat","cheated",
    "scam","useless","waste","wasted","fake","duplicate","disgusting","awful",
    "unacceptable","not delivered","never delivered","not received","still waiting",
    "no refund","refund not","wrong product","wrong item","damaged","convenience fee",
    "platform fee deducted","bekar","bakwas","ghatiya","kharab","bura","bekaar",
    "faltu","dhoka","thag","nakli",
]
STRONG_POS = [
    "excellent","amazing","awesome","fantastic","wonderful","outstanding","superb",
    "brilliant","love it","loved it","great app","best app","highly recommend",
    "very good","very nice","very happy","very satisfied","fast delivery",
    "quick delivery","on time delivery","early delivery","good quality","best quality",
    "original product","genuine product","easy to use","smooth experience","seamless",
    "hassle free","bahut accha","bahut acha","bahut badhiya","bohot accha","bohot acha",
    "zabardast","mast","shandar",
]
COMPLAINT = [
    "delay","delayed","late delivery","very late","not on time","pickup late",
    "not picked up","waiting","still waiting","not yet","not received yet",
    "15 days","20 days","25 days","refund not","refund pending","no refund",
    "money not returned","wrong size","wrong colour","wrong product","wrong item",
    "not working","not opening","crash","freeze","bug","glitch","oops","login issue",
    "otp issue","support not","no one responded","not responding","ignored",
    "cancelled","order cancelled","not available","not deliverable","return rejected",
    "exchange rejected","charged","fee charged","deducted","disappointed",
    "frustrating","data leak","fraud call",
]
HINDI_NEG = {"bekar","bakwas","ghatiya","kharab","bura","faltu","bekaar","dhoka","thag","nakli"}
HINDI_POS = {"accha","acha","achha","badhiya","badiya","shandar","mast","zabardast","bahut","bohot"}
NEUTRAL_HINTS = [
    "okay","ok","average","decent","not bad","could be better","needs improvement",
    "improve","bit slow","little slow","bit late","somewhat",
]


def sentiment(text: str, star: int) -> str:
    t = text.lower().strip()
    tc = re.sub(r"[^\w\s]", " ", t)
    words = set(tc.split())
    neg = sum(3 for p in STRONG_NEG if p in t)
    pos = sum(3 for p in STRONG_POS if p in t)
    neg += sum(2 for s in COMPLAINT if s in t)
    for w in words:
        if w in HINDI_NEG: neg += 3
        if w in HINDI_POS: pos += 2
    neutral_hits = sum(1 for s in NEUTRAL_HINTS if s in t)

    if len(t.split()) <= 3:
        if words & HINDI_NEG:                                          return "Negative"
        if words & HINDI_POS or any(w in {"good","nice","best","love","great","excellent","super","superb"} for w in words): return "Positive"
        if any(w in {"bad","worst","fraud","fake","useless","terrible","horrible","pathetic"} for w in words): return "Negative"
        if star >= 4: return "Positive"
        if star <= 2: return "Negative"
        return "Neutral"

    if   neg > pos: se = "Negative"
    elif pos > neg: se = "Neutral" if neg > 0 and neutral_hits > 0 else "Positive"
    else:           se = "Positive" if star >= 4 else ("Negative" if star <= 2 else "Neutral")

    if re.search(r"\b(need|needs)\b.{0,15}\b(faster|better|improve)\b", t):       se = "Negative"
    if re.search(r"\b(slow|slower)\b.{0,20}\b(delivery|deliveries|service)\b", t): se = "Negative"
    if re.search(r"\bgood\b.{0,30}\bbut\b.{0,30}(slow|late|delay|issue|problem)", t): se = "Neutral"
    if re.search(r"\b(should|please)\b.{0,15}\b(improve|fix|resolve)\b", t):       se = "Negative"
    return se


# ── AGGREGATION ───────────────────────────────────────────────────────────────
def build_agg(reviews: list[dict]) -> dict:
    by_date: dict = defaultdict(lambda: {
        "count":0,"pos":0,"neg":0,"neu":0,"ts":0,"android":0,"ios":0,"rat":[0,0,0,0,0]
    })
    by_cat: dict = defaultdict(lambda: {
        "count":0,"pos":0,"neg":0,"neu":0,"android":0,"ios":0,
        "rat":[0,0,0,0,0],"posRevs":[],"negRevs":[]
    })
    rat = [0,0,0,0,0]
    pos = neg = neu = 0

    for r in reviews:
        se = r["se"]
        by_date[r["d"]]["count"]  += 1
        by_date[r["d"]]["ts"]     += r["s"]
        by_date[r["d"]]["rat"][r["s"]-1] += 1
        if r["src"] == "android": by_date[r["d"]]["android"] += 1
        else:                      by_date[r["d"]]["ios"]     += 1
        if   se == "Positive": by_date[r["d"]]["pos"] += 1
        elif se == "Negative": by_date[r["d"]]["neg"] += 1
        else:                  by_date[r["d"]]["neu"] += 1

        bc = by_cat[r["c"]]
        bc["count"] += 1
        bc["rat"][r["s"]-1] += 1
        if r["src"] == "android": bc["android"] += 1
        else:                      bc["ios"]     += 1
        if   se == "Positive": bc["pos"] += 1; (bc["posRevs"].append({"t":r["t"],"s":r["s"],"d":r["d"],"src":r["src"]}) if len(bc["posRevs"])<5 else None)
        elif se == "Negative": bc["neg"] += 1; (bc["negRevs"].append({"t":r["t"],"s":r["s"],"d":r["d"],"src":r["src"]}) if len(bc["negRevs"])<5 else None)
        else:                  bc["neu"] += 1

        rat[r["s"]-1] += 1
        if   se == "Positive": pos += 1
        elif se == "Negative": neg += 1
        else:                  neu += 1

    total     = len(reviews)
    android_r = [r for r in reviews if r["src"]=="android"]
    ios_r     = [r for r in reviews if r["src"]=="ios"]

    def plat_stats(revs):
        n = len(revs)
        if not n: return {"n":0,"avg":"0","pp":0,"np":0,"rat":[0,0,0,0,0]}
        pr = [0,0,0,0,0]
        for rv in revs: pr[rv["s"]-1] += 1
        return {"n":n,"avg":round(sum(rv["s"] for rv in revs)/n,2),
                "pp":round(len([rv for rv in revs if rv["se"]=="Positive"])/n*100,1),
                "np":round(len([rv for rv in revs if rv["se"]=="Negative"])/n*100,1),
                "rat":pr}

    return {
        "total":total,"avg":round(sum(r["s"] for r in reviews)/total,2) if total else 0,
        "pos":pos,"neg":neg,"neu":neu,"rat":rat,
        "android":len(android_r),"ios":len(ios_r),
        "by_date":{k:dict(v) for k,v in by_date.items()},
        "by_cat":{k:dict(v) for k,v in by_cat.items()},
        "plat":{"android":plat_stats(android_r),"ios":plat_stats(ios_r)},
        "date_min":min(r["d"] for r in reviews) if reviews else "",
        "date_max":max(r["d"] for r in reviews) if reviews else "",
    }


def build_subcat(reviews: list[dict]) -> dict:
    tree: dict = defaultdict(lambda: defaultdict(list))
    for r in reviews:
        if r["se"] == "Negative" and r["c"] in SUBCATEGORIES:
            sc = classify_subcat(r["t"], r["c"])
            tree[r["c"]][sc].append({"t":r["t"],"s":r["s"],"d":r["d"],"src":r["src"]})
    return {mc:{sc:revs for sc,revs in scs.items()} for mc,scs in tree.items()}


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("Loading raw reviews …")
    with open("data/reviews_raw.json", encoding="utf-8") as f:
        raw = json.load(f)

    agg_out    = {}
    subcat_out = {}

    for brand in ("ajio", "myntra"):
        revs = raw[brand]
        print(f"Processing {brand.upper()} ({len(revs)} reviews) …")
        # classify
        for r in revs:
            r["c"]  = classify_category(r["text"])
            r["se"] = sentiment(r["text"], r["score"])
            r["t"]  = r["text"][:150]   # alias used in UI
            r["s"]  = r["score"]
            r["d"]  = r["date"]

        agg_out[brand]    = build_agg(revs)
        subcat_out[brand] = build_subcat(revs)

        sc = Counter(r["se"] for r in revs)
        total = len(revs)
        print(f"  pos={sc['Positive']/total*100:.1f}% "
              f"neg={sc['Negative']/total*100:.1f}% "
              f"neu={sc.get('Neutral',0)/total*100:.1f}%")

    with open("data/agg_data.json","w",encoding="utf-8") as f:
        json.dump(agg_out, f, ensure_ascii=True, separators=(",",":"))
    with open("data/subcat_data.json","w",encoding="utf-8") as f:
        json.dump(subcat_out, f, ensure_ascii=True, separators=(",",":"))

    print("\n✅  Saved data/agg_data.json  +  data/subcat_data.json")


if __name__ == "__main__":
    main()
