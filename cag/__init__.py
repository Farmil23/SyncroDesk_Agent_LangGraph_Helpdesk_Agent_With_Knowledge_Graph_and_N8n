# Re-export supaya bisa: from cag import QA_CACHE, CACHE_THRESHOLD, ...
# Penjelasan lengkap ada di cag/cache.py
from cag.cache import CACHE_THRESHOLD, QA_CACHE, build_cache_query_text, cache_aktif

__all__ = ["CACHE_THRESHOLD", "QA_CACHE", "build_cache_query_text", "cache_aktif"]
