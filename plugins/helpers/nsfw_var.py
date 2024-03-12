import requests

endpoints = {
    "v1": {
        "end": [
            "pussy",
            "cum",
            "boobs",
            "bj",
            "anal",
            "hentai",
            "feet",
            "blowjob",
            "poke",
            "holo",
            "baka",
        ],
        "api": "http://api.nekos.fun:8080/api/",
        "checker": "image",
    },
    "v2": {
        "end": [
            "lewd",
            "spank",
            "gasm",
            "tickle",
            "slap",
            "pat",
            "neko",
            "meow",
            "lizard",
            "kiss",
            "hug",
            "fox_girl",
            "feed",
            "cuddle",
            "ngif",
            "smug",
            "woof",
            "wallpaper",
            "goose",
            "gecg",
            "avatar",
            "waifu",
        ],
        "api": "https://nekos.life/api/v2/img/",
        "checker": "url",
    },
    "v3": {
        "end": [
            "ass",
            "anal",
            "ahegao",
            "bite",
            "boobs",
            "bdsm",
            "boobjob",
            "blowjob",
            "creampie",
            "cuckold",
            "classic",
            "depression",
            "elves",
            "ero",
            "femdom",
            "footjob",
            "gangbang",
            "glasses",
            "gif",
            "hentai",
            "handjob",
            "incest",
            "jahy",
            "kill",
            "lick",
            "manga",
            "masturbation",
            "mobileWallpaper",
            "nsfwMobileWallpaper",
            "nsfwNeko",
            "nosebleed",
            "orgy",
            "public",
            "pantsu",
            "tentacles",
            "thighs",
            "uniform",
            "vagina",
            "yuri",
            "zettaiRyouiki",
        ],
        "api": "https://hmtai.hatsunia.cfd/v2/",
        "checker": "url",
    },
    "v4": {
        "end": [
            "doujin",
            "foxgirl",
            "gifs",
            "netorare",
            "maid",
            "panties",
            "school",
            "succubus",
            "uglybastard",
            "lewdneko",
        ],
        "api": "https://akaneko.cuteasfubuki.xyz/api/",
        "checker": "url",
    },
    "v5": {
        "end": ["nekolewd", "kitsune", "punch"],
        "api": "https://neko-love.xyz/api/v1/",
        "checker": "url",
    },
    "v6": {
        "end": ["furry", "ff", "futa", "nekoirl", "trap", "catboy"],
        "api": "https://api.xsky.dev/",
        "checker": "url",
    },
    "v7": {
        "end": ["jav", "rb"],
        "api": "https://scathach.redsplit.org/v3/nsfw/",
        "checker": "url",
    },
    "v8": {
        "end": [
            "hass",
            "hmidriff",
            "pgif",
            "4k",
            "holo",
            "hneko",
            "hkitsune",
            "kemonomimi",
            "hanal",
            "gonewild",
            "kanna",
            "pussy",
            "thigh",
            "hthigh",
            "gah",
            "coffee",
            "food",
            "paizuri",
            "tentacle",
            "hboobs",
        ],
        "api": "https://nekobot.xyz/api/image?type=",
        "checker": "message",
    },
}


def nekos(endpoint=None, endpoints=endpoints):
    if endpoint:
        for i in endpoints:
            if endpoint in endpoints[i]["end"]:
                api = endpoints[i]["api"]
                checker = endpoints[i]["checker"]
        result = requests.get(api + endpoint).json()
        return result[checker]
    return (
        endpoints["v1"]["end"]
        + endpoints["v2"]["end"]
        + endpoints["v3"]["end"]
        + endpoints["v4"]["end"]
        + endpoints["v5"]["end"]
        + endpoints["v7"]["end"]
        + endpoints["v8"]["end"]
    )


def nsfw(catagory):
    catagory.sort(key=str.casefold)
    horny = "**Catagory :** "
    for i in catagory:
        horny += f" `{i.lower()}` |"
    return horny
