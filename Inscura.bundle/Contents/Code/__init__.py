# -*- coding: utf-8 -*-

import re
import urllib


API_PREFIX = "/api/v1"
HTTP_TIMEOUT = 20
ARTWORK_CACHE_TIME = 60 * 60 * 24 * 7


def Start():
    Log.Info("Inscura metadata agent started")


def supported_languages():
    names = ["Chinese", "English", "Japanese", "Korean", "NoLanguage"]
    languages = []
    for name in names:
        try:
            language = getattr(Locale.Language, name)
        except Exception:
            continue
        if language not in languages:
            languages.append(language)
    return languages or [Locale.Language.NoLanguage]


class InscuraMovieAgent(Agent.Movies):
    name = "Inscura"
    languages = supported_languages()
    primary_provider = True
    accepts_from = ["com.plexapp.agents.localmedia"]

    def search(self, results, media, lang, manual=False):
        query_terms = media_query_terms(media)
        if not query_terms:
            return

        seen = {}
        rank = 0
        for query in query_terms:
            items = api_get("/media/search", {"q": query, "limit": pref_int("search_limit", 20)})
            if not items:
                continue
            for item in items:
                media_id = text(item.get("id"))
                if not media_id or media_id in seen:
                    continue
                score = score_candidate(media, item, query, rank)
                if (not manual) and score < pref_int("minimum_automatic_score", 65):
                    continue
                seen[media_id] = True
                results.Append(MetadataSearchResult(
                    id=media_id,
                    name=display_title(item),
                    year=item_year(item),
                    score=score,
                    lang=lang
                ))
                rank = rank + 1

    def update(self, metadata, media, lang=None, force=False, prefs=None, **kwargs):
        media_id = extract_media_id(text(metadata.id))
        if not media_id:
            return

        Log.Info("Inscura: updating metadata for media id %s", media_id)
        detail = api_get("/media/%s" % url_quote(media_id))
        if not detail:
            Log.Warn("Inscura: no detail returned for media id %s", media_id)
            return

        metas = detail.get("metas") or {}
        terms = detail.get("terms") or {}
        credits = detail.get("credits") or {}

        apply_core_metadata(metadata, detail, metas, terms)
        apply_taxonomies(metadata, metas, terms, prefs)
        apply_people(metadata, credits)
        apply_artwork(metadata, detail.get("assets") or [])


def api_base():
    value = pref_text("api_url", "http://192.168.10.198:28687").rstrip("/")
    if not value:
        value = "http://192.168.10.198:28687"
    return value


def api_headers():
    token = pref_text("api_token", "")
    if token:
        return {"Authorization": "Bearer " + token}
    return {}


def api_get(path, params=None):
    url = api_base() + API_PREFIX + path
    if params:
        url = url + "?" + query_string(params)
    try:
        content = http_content(url, api_headers(), 0)
        envelope = JSON.ObjectFromString(content)
        if envelope and envelope.get("error"):
            error = envelope.get("error") or {}
            Log.Warn("Inscura API error %s: %s", text(error.get("code")), text(error.get("message")))
            return None
        if envelope:
            return envelope.get("data")
    except Exception as exc:
        Log.Warn("Inscura API request failed: %s %s", url, exc)
    return None


def query_string(params):
    pairs = []
    for key, value in params.items():
        if value is None:
            continue
        pairs.append("%s=%s" % (url_quote(key), url_quote(text(value))))
    return "&".join(pairs)


def url_quote(value):
    value = text(value)
    try:
        value = value.encode("utf-8")
    except Exception:
        pass
    return urllib.quote(value, safe="")


def url_unquote(value):
    value = text(value)
    try:
        raw = urllib.unquote(value.encode("utf-8"))
        try:
            return raw.decode("utf-8")
        except Exception:
            return raw
    except Exception:
        return value


def extract_media_id(value):
    value = text(value).strip()
    if not value:
        return ""
    match = re.search(r"inscura://([^?/#]+)", value)
    if match:
        return match.group(1)
    if value.isdigit():
        return value
    match = re.search(r"(\d+)", value)
    if match:
        return match.group(1)
    return value


def pref_text(key, default=""):
    try:
        value = Prefs[key]
        if value is None:
            return default
        return text(value).strip()
    except Exception:
        return default


def pref_bool(key, default=False):
    try:
        return bool_value(Prefs[key], default)
    except Exception:
        return default


def pref_bool_from(prefs, key, default=False):
    try:
        if prefs is not None and key in prefs:
            return bool_value(prefs[key], default)
    except Exception:
        pass
    return pref_bool(key, default)


def bool_value(value, default=False):
    if value is None:
        return default
    try:
        if isinstance(value, basestring):
            return value.strip().lower() in ("1", "true", "yes", "on")
    except Exception:
        pass
    return bool(value)


def pref_int(key, default):
    value = pref_text(key, text(default))
    try:
        return int(value)
    except Exception:
        return default


def text(value):
    if value is None:
        return ""
    try:
        if isinstance(value, unicode):
            return value
    except NameError:
        pass
    try:
        return unicode(value)
    except Exception:
        return str(value)


def media_query_terms(media):
    file_values = []
    push(file_values, safe_attr(media, "filename"))
    try:
        for item in media.items:
            push(file_values, safe_attr(item, "filename"))
            for part in item.parts:
                push(file_values, safe_attr(part, "file"))
    except Exception:
        pass

    expanded = []
    for value in file_values:
        decoded = url_unquote(value)
        basename = file_basename(decoded)
        stem = strip_extension(basename)
        for code in code_candidates(stem):
            push(expanded, code)
        push(expanded, stem)
        push(expanded, basename)
        push(expanded, decoded)

    title_values = []
    push(title_values, safe_attr(media, "name"))
    push(title_values, safe_attr(media, "title"))
    try:
        for item in media.items:
            push(title_values, safe_attr(item, "name"))
            push(title_values, safe_attr(item, "title"))
    except Exception:
        pass

    for value in title_values:
        decoded = url_unquote(value)
        basename = file_basename(decoded)
        stem = strip_extension(basename)
        for code in code_candidates(stem):
            push(expanded, code)
        push(expanded, stem)
        push(expanded, basename)
        push(expanded, decoded)
    return expanded[:12]


def safe_attr(obj, name):
    try:
        return getattr(obj, name)
    except Exception:
        return ""


def push(values, value):
    value = text(value).strip()
    if not value:
        return
    for current in values:
        if normalize(current) == normalize(value):
            return
    values.append(value)


def file_basename(value):
    value = text(value).replace("\\", "/")
    if "/" in value:
        return value.rsplit("/", 1)[-1]
    return value


def strip_extension(value):
    value = text(value)
    if "." in value:
        stem, ext = value.rsplit(".", 1)
        if ext and len(ext) <= 6:
            return stem
    return value


def normalize(value):
    value = text(value).lower()
    value = re.sub(ur"[\s\-_./\\()\[\]{}【】「」『』·・]+", "", value, flags=re.U)
    return value


def normalize_code(value):
    value = text(value).upper()
    value = re.sub(r"[^A-Z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def code_candidates(value):
    compact = normalize(value)
    result = []
    for match in re.finditer(r"fc2(?:ppv)?(\d{5,8})", compact, flags=re.I):
        push(result, "FC2-PPV-" + match.group(1))
    for match in re.finditer(r"([a-z]{2,10})(\d{2,8})", compact, flags=re.I):
        prefix = match.group(1)
        if prefix.lower() == "ppv":
            continue
        push(result, prefix.upper() + "-" + match.group(2))
    return result


def display_title(item):
    title = first_text(item, ["title", "name"])
    code = first_text(item, ["code"])
    if code and title and normalize(code) not in normalize(title):
        return "%s - %s" % (code, title)
    return title or code or ("Inscura #" + text(item.get("id")))


def item_year(item):
    value = first_text(item.get("metas") or {}, ["release_date", "premiered"])
    if not value:
        value = first_text(item, ["releaseDate", "release_date"])
    if len(value) >= 4 and value[:4].isdigit():
        return int(value[:4])
    return None


def score_candidate(media, item, query, rank):
    query_norm = normalize(query)
    query_code = normalize_code(query)
    title = first_text(item, ["title", "name"])
    code = first_text(item, ["code"])
    filename = first_text(item, ["fileName", "relativePath"])
    relative_path = first_text(item, ["relativePath"])

    score = max(40, 94 - rank)
    file_score = file_match_score(query, filename, relative_path)
    if file_score:
        score = max(score, file_score)
    if code:
        if normalize_code(code) == query_code:
            score = 100
        elif normalize(code) in query_norm or query_norm in normalize(code):
            score = max(score, 95)
    if title and normalize(title) == query_norm:
        score = max(score, 96)
    if filename and query_norm and query_norm in normalize(filename):
        score = max(score, 90)

    media_year = safe_attr(media, "year")
    candidate_year = item_year(item)
    try:
        if media_year and candidate_year and int(media_year) != int(candidate_year):
            score = score - 8
    except Exception:
        pass
    score = score - duration_penalty(media, item)
    return max(0, min(100, int(score)))


def file_match_score(query, filename, relative_path):
    query_name = file_basename(url_unquote(query))
    query_stem = strip_extension(query_name)
    candidates = []
    push(candidates, filename)
    push(candidates, relative_path)
    for value in list(candidates):
        push(candidates, file_basename(value))
        push(candidates, strip_extension(file_basename(value)))

    query_norm = normalize(query)
    query_name_norm = normalize(query_name)
    query_stem_norm = normalize(query_stem)
    for value in candidates:
        candidate_norm = normalize(value)
        if not candidate_norm:
            continue
        if candidate_norm in (query_norm, query_name_norm, query_stem_norm):
            return 100
        if query_stem_norm and query_stem_norm in candidate_norm:
            return 96
        if candidate_norm and candidate_norm in query_norm:
            return 94
    return 0


def duration_penalty(media, item):
    media_duration = media_duration_ms(media)
    item_duration = parse_int(item.get("durationMs"))
    if not media_duration or not item_duration:
        return 0
    delta = abs(media_duration - item_duration)
    tolerance = max(3000, min(media_duration, item_duration) * 0.03)
    if delta <= tolerance:
        return 0
    if delta <= 120000:
        return 4
    return 12


def media_duration_ms(media):
    for name in ["duration", "duration_ms", "durationMs"]:
        value = parse_int(safe_attr(media, name))
        if value:
            return value
    try:
        for item in media.items:
            for name in ["duration", "duration_ms", "durationMs"]:
                value = parse_int(safe_attr(item, name))
                if value:
                    return value
    except Exception:
        pass
    return 0


def apply_core_metadata(metadata, detail, metas, terms):
    safe_set(metadata, "title", meta_value(metas, ["title"]) or first_text(detail, ["title"]) or text(detail.get("fileName")))
    safe_set(metadata, "original_title", meta_value(metas, ["original_title", "originaltitle"]))
    safe_set(metadata, "sort_title", meta_value(metas, ["sort_title", "sorttitle"]))

    plot = meta_value(metas, ["description", "plot", "overview", "summary"])
    safe_set(metadata, "summary", plot)
    safe_set(metadata, "tagline", meta_value(metas, ["tagline"]) or outline(plot))

    rating = parse_float(meta_value(metas, ["rating"]))
    if rating is not None:
        safe_set(metadata, "rating", rating)
    audience_rating = parse_float(meta_value(metas, ["imdb_rating", "tmdb_rating", "themoviedb_rating"]))
    if audience_rating is not None:
        safe_set(metadata, "audience_rating", audience_rating)

    content_rating = meta_value(metas, ["content_rating", "certification", "mpaa"])
    safe_set(metadata, "content_rating", content_rating)

    release_date = meta_value(metas, ["release_date", "premiered"])
    apply_release_date(metadata, release_date)

    studio = first_term(terms, ["studio", "maker", "label"]) or meta_value(metas, ["studio", "maker", "label"])
    safe_set(metadata, "studio", studio)

    duration_ms = detail.get("durationMs")
    if duration_ms:
        safe_set(metadata, "duration", duration_ms)


def apply_release_date(metadata, value):
    value = text(value).strip()
    if not value:
        return
    if len(value) >= 4 and value[:4].isdigit():
        safe_set(metadata, "year", int(value[:4]))
    try:
        safe_set(metadata, "originally_available_at", Datetime.ParseDate(value).date())
    except Exception:
        pass


def apply_taxonomies(metadata, metas, terms, prefs=None):
    replace_tag_set(metadata, "genres", term_names(terms, ["genre"]))
    replace_tag_set(metadata, "countries", split_values(meta_value(metas, ["production_countries", "origin_countries", "country"])))

    tags = term_names(terms, ["tag"])
    push(tags, meta_value(metas, ["code"]))
    push(tags, meta_value(metas, ["release_source"]))
    for value in term_names(terms, ["label"]):
        push(tags, value)
    replace_tag_set(metadata, "tags", tags)

    if pref_bool_from(prefs, "import_collections", True):
        collections = term_names(terms, ["collection"])
        for value in term_names(terms, ["series"]):
            push(collections, value)
        if pref_bool_from(prefs, "clear_existing_collections", False):
            replace_tag_set(metadata, "collections", collections)
        else:
            add_tag_values(metadata, "collections", collections)


def apply_people(metadata, credits):
    cast = credits.get("cast") or []
    crew = credits.get("crew") or []

    safe_clear(metadata, "roles")
    for item in cast:
        try:
            role = metadata.roles.new()
            role.name = text(item.get("actorName"))
            role.role = role_label(item.get("roles") or [])
            avatar = asset_url(item.get("actorAvatar"))
            if avatar:
                role.photo = avatar
        except Exception as exc:
            Log.Debug("Inscura: failed to add cast member: %s", exc)

    apply_crew(metadata, "directors", crew, ["director"])
    apply_crew(metadata, "writers", crew, ["writer", "screenplay", "author"])
    apply_crew(metadata, "producers", crew, ["producer", "executive-producer", "executive producer"])


def apply_crew(metadata, set_name, crew, wanted_slugs):
    safe_clear(metadata, set_name)
    target = safe_attr(metadata, set_name)
    if missing_target(target):
        return
    seen = []
    for item in crew:
        if not person_has_role(item, wanted_slugs):
            continue
        name = text(item.get("actorName")).strip()
        if not name or normalize(name) in seen:
            continue
        seen.append(normalize(name))
        try:
            person = target.new()
            person.name = name
            avatar = asset_url(item.get("actorAvatar"))
            if avatar:
                person.photo = avatar
        except Exception:
            try:
                target.add(name)
            except Exception:
                pass


def apply_artwork(metadata, assets):
    posters = []
    art = []
    for item in assets:
        kind = text(item.get("kind")).lower()
        url = asset_url(item)
        if not url:
            continue
        if kind in ("poster", "keyart"):
            posters.append(url)
        elif kind in ("fanart", "landscape", "screenshot"):
            art.append(url)

    apply_art_set(metadata, "posters", posters)
    apply_art_set(metadata, "art", art)


def apply_art_set(metadata, set_name, urls):
    target = safe_attr(metadata, set_name)
    if missing_target(target):
        return
    urls = unique_values(urls)
    try:
        target.clear()
    except Exception:
        pass

    valid_keys = []
    sort_order = 1
    for url in urls:
        proxy = proxy_for_url(url, sort_order)
        if not proxy:
            continue
        try:
            target[url] = proxy
            valid_keys.append(url)
            sort_order = sort_order + 1
        except Exception as exc:
            Log.Warn("Inscura: failed to assign artwork %s: %s", url, exc)
    try:
        target.validate_keys(valid_keys)
    except Exception:
        pass


def proxy_for_url(url, sort_order):
    try:
        content = http_content(url, api_headers(), ARTWORK_CACHE_TIME)
        try:
            return Proxy.Media(content, sort_order=sort_order)
        except Exception:
            return Proxy.Preview(content, sort_order=sort_order)
    except Exception as exc:
        Log.Warn("Inscura: artwork request failed %s: %s", url, exc)
    return None


def http_content(url, headers, cache_time):
    try:
        return HTTP.Request(
            url,
            headers=headers,
            cacheTime=cache_time,
            timeout=HTTP_TIMEOUT
        ).content
    except TypeError:
        return HTTP.Request(
            url,
            headers=headers,
            cacheTime=cache_time
        ).content


def asset_url(asset):
    if not asset:
        return ""
    url = text(asset.get("url")).strip()
    if not url:
        url = text(asset.get("remoteUrl")).strip()
    if not url:
        url = text(asset.get("sourceUrl")).strip()
    token = pref_text("api_token", "")
    if token and "/api/v1/" in url and "token=" not in url:
        separator = "&" if "?" in url else "?"
        url = url + separator + "token=" + url_quote(token)
    return url


def meta_value(metas, keys):
    for key in keys:
        value = first_text(metas, [key])
        if value:
            return value
    for key in keys:
        suffix = ":" + key
        for meta_key, value in metas.items():
            if text(meta_key).lower().endswith(suffix.lower()) and text(value).strip():
                return text(value).strip()
    return ""


def first_text(mapping, keys):
    if not mapping:
        return ""
    for key in keys:
        try:
            value = mapping.get(key)
        except Exception:
            value = None
        value = text(value).strip()
        if value:
            return value
    return ""


def term_names(terms, keys):
    result = []
    for key in keys:
        for term_key, values in terms.items():
            if text(term_key).lower() == key.lower() or text(term_key).lower().endswith(":" + key.lower()):
                for item in values or []:
                    push(result, item.get("name"))
    return result


def first_term(terms, keys):
    values = term_names(terms, keys)
    if values:
        return values[0]
    return ""


def split_values(value):
    value = text(value)
    if not value:
        return []
    parts = re.split(ur"[,/|;、，]+", value, flags=re.U)
    return [part.strip() for part in parts if part.strip()]


def unique_values(values):
    result = []
    for value in values:
        push(result, value)
    return result


def replace_tag_set(metadata, set_name, values):
    safe_clear(metadata, set_name)
    add_tag_values(metadata, set_name, values)


def add_tag_values(metadata, set_name, values):
    target = safe_attr(metadata, set_name)
    if missing_target(target):
        return
    for value in unique_values(values):
        try:
            target.add(value)
        except Exception:
            pass


def safe_set(obj, name, value):
    if value is None:
        return
    if isinstance(value, basestring) and not value.strip():
        return
    try:
        setattr(obj, name, value)
    except Exception:
        pass


def safe_clear(obj, name):
    try:
        getattr(obj, name).clear()
    except Exception:
        pass


def missing_target(value):
    return value is None or value == ""


def parse_float(value):
    try:
        value = text(value).strip()
        if not value:
            return None
        parsed = float(value)
        if parsed <= 0:
            return None
        return parsed
    except Exception:
        return None


def parse_int(value):
    try:
        value = text(value).strip()
        if not value:
            return 0
        return int(float(value))
    except Exception:
        return 0


def outline(value):
    value = text(value).strip()
    if not value:
        return ""
    if len(value) <= 160:
        return value
    for separator in [u"。", u".", u"！", u"!", u"？", u"?"]:
        index = value.find(separator)
        if 40 <= index <= 160:
            return value[:index + 1]
    return value[:157].rstrip() + "..."


def role_label(roles):
    names = []
    for role in roles:
        push(names, role.get("name"))
    return " / ".join(names)


def person_has_role(item, wanted_slugs):
    wanted = [normalize_role(value) for value in wanted_slugs]
    for role in item.get("roles") or []:
        if normalize_role(role.get("slug")) in wanted:
            return True
        if normalize_role(role.get("name")) in wanted:
            return True
    return False


def normalize_role(value):
    return text(value).strip().lower().replace("_", "-")
