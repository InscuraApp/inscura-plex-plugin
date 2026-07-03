# -*- coding: utf-8 -*-

import os
import re
import urllib
import json

import Media
import Stack
import VideoFiles


API_BASE = os.environ.get("INSCURA_API_URL", "http://192.168.10.198:28687").rstrip("/")
API_TOKEN = os.environ.get("INSCURA_API_TOKEN", "").strip()
API_PREFIX = "/api/v1"


def Scan(path, files, mediaList, subdirs, language=None, root=None, **kwargs):
  VideoFiles.Scan(path, files, mediaList, subdirs, root)

  for file_path in files:
    if should_skip(file_path):
      continue

    basename = os.path.basename(file_path)
    stem = os.path.splitext(basename)[0]
    name, year = clean_movie_name(stem)
    movie = Media.Movie(name, year)
    movie.source = VideoFiles.RetrieveSource(basename)
    movie.parts.append(file_path)

    inscura_id = find_inscura_id(file_path, stem, name)
    if inscura_id:
      movie.guid = "com.plexapp.agents.inscura://%s?lang=xn" % inscura_id

    mediaList.append(movie)

  Stack.Scan(path, files, mediaList, subdirs)


def should_skip(file_path):
  ext = os.path.splitext(file_path)[1].lower().lstrip(".")
  if ext not in VideoFiles.video_exts:
    return True
  name = os.path.basename(file_path).lower()
  for rx in VideoFiles.ignore_samples + VideoFiles.ignore_trailers + VideoFiles.ignore_extras:
    if re.search(rx, name):
      return True
  return False


def clean_movie_name(stem):
  code = first_code_candidate(stem)
  cleaned, year = VideoFiles.CleanName(stem)
  if code:
    return code, year
  return cleaned, year


def find_inscura_id(file_path, stem, cleaned_name):
  queries = []
  push_query(queries, first_code_candidate(stem))
  push_query(queries, stem)
  push_query(queries, os.path.basename(file_path))
  push_query(queries, cleaned_name)

  for query in queries:
    item = search_first(query)
    if item and item.get("id") is not None:
      return unicode(item.get("id"))
  return None


def first_code_candidate(value):
  candidates = code_candidates(value)
  if candidates:
    return candidates[0]
  return None


def code_candidates(value):
  compact = normalize_search_text(value)
  result = []

  for match in re.finditer(r"fc2(?:ppv)?(\d{5,8})", compact, flags=re.I):
    push_query(result, "FC2-PPV-" + match.group(1))

  for match in re.finditer(r"([a-z]{2,10})(\d{2,8})", compact, flags=re.I):
    prefix = match.group(1)
    if prefix.lower() == "ppv":
      continue
    push_query(result, prefix.upper() + "-" + match.group(2))

  return result


def normalize_search_text(value):
  value = to_unicode(value).lower()
  return re.sub(ur"[\s\-_./\\()\[\]{}【】「」『』·・]+", "", value, flags=re.U)


def search_first(query):
  url = "%s%s/media/search?q=%s&limit=1" % (
    API_BASE,
    API_PREFIX,
    urllib.quote(to_utf8(query), safe="")
  )
  if API_TOKEN:
    url = url + "&token=" + urllib.quote(API_TOKEN, safe="")

  try:
    data = urllib.urlopen(url).read()
    envelope = json.loads(data)
    items = envelope.get("data") or []
    if items:
      return items[0]
  except Exception, exc:
    try:
      print "Inscura scanner API request failed: %s %s" % (url, exc)
    except:
      pass
  return None


def push_query(values, value):
  value = to_unicode(value).strip()
  if not value:
    return
  normalized = normalize_search_text(value)
  for current in values:
    if normalize_search_text(current) == normalized:
      return
  values.append(value)


def to_unicode(value):
  if value is None:
    return u""
  if isinstance(value, unicode):
    return value
  try:
    return unicode(value, "utf-8", "ignore")
  except:
    try:
      return unicode(value)
    except:
      return u""


def to_utf8(value):
  value = to_unicode(value)
  try:
    return value.encode("utf-8")
  except:
    return str(value)
