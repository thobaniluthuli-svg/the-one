"""
StableTokenVocab - Enhanced Token Vocabulary System with Advanced Features

VBSTYLE Architecture:
- Authority: token_vocab (StableTokenVocab class)
- Return: Tuple3 (status, payload, error)
- Orchestration: none (pure class, no external orchestration)
- Schema: SQL-driven, no hardcoded structures

Enhanced Features:
  - Advanced n-gram extraction with configurable sizes
  - Semantic similarity scoring (Jaccard, Cosine)
  - Batch operations for performance
  - Caching layer for hot data
  - Token relationship mapping
  - Advanced filtering and aggregation
  - Parallel clustering with threading
  - Performance profiling
  - Data validation and sanitization
  - Comprehensive logging
"""

import re
import hashlib
import sqlite3
import json
import logging
import threading
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set, Optional, Any
from dataclasses import dataclass
from functools import lru_cache, wraps
import time
import math


# ─────────────────────────────────────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Performance Decorators
# ─────────────────────────────────────────────────────────────────────────────

def timing(func):
    """Decorator to measure execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper


def cached_result(ttl_seconds=300):
    """Decorator for time-based caching"""
    def decorator(func):
        cache = {}
        cache_time = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()
            
            if key in cache and (now - cache_time[key]) < ttl_seconds:
                return cache[key]
            
            result = func(*args, **kwargs)
            cache[key] = result
            cache_time[key] = now
            return result
        
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TokenMetrics:
    """Comprehensive token metrics container"""
    token_id: int
    phrase: str
    frequency: int
    weight: float
    contextual_strength: float
    cross_session_reuse: int
    cluster_id: Optional[int]
    status: str
    rank: Optional[int]
    compression_ratio: float
    information_density: float
    decay_factor: float
    first_seen: str
    last_seen: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'token_id': self.token_id,
            'phrase': self.phrase,
            'frequency': self.frequency,
            'weight': self.weight,
            'contextual_strength': self.contextual_strength,
            'cross_session_reuse': self.cross_session_reuse,
            'cluster_id': self.cluster_id,
            'status': self.status,
            'rank': self.rank,
            'compression_ratio': self.compression_ratio,
            'information_density': self.information_density,
            'decay_factor': self.decay_factor,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen
        }


@dataclass
class ClusterInfo:
    """Cluster information container"""
    cluster_id: int
    centroid_phrase: str
    member_count: int
    total_weight: float
    intention_label: str
    members: List[str]
    cohesion_score: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'cluster_id': self.cluster_id,
            'centroid_phrase': self.centroid_phrase,
            'member_count': self.member_count,
            'total_weight': self.total_weight,
            'intention_label': self.intention_label,
            'members': self.members,
            'cohesion_score': self.cohesion_score
        }


# ─────────────────────────────────────────────────────────────────────────────
# VBSTYLE Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

def _ok(payload: Any) -> Tuple[int, Any, Any]:
    """Success response: (1, payload, None)"""
    return (1, payload, None)


def _err(code: str, msg: str, meta: Any = None) -> Tuple[int, Any, Any]:
    """Error response: (0, None, (code, msg, meta))"""
    return (0, None, (code, msg, meta))


def _safe(func, *args, **kwargs) -> Tuple[int, Any, Any]:
    """Safely execute function with exception handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Exception in {func.__name__}: {str(e)}")
        return _err("INTERNAL", str(e), None)


# ─────────────────────────────────────────────────────────────────────────────
# Similarity Metrics
# ─────────────────────────────────────────────────────────────────────────────

class SimilarityMetrics:
    """Compute phrase similarity using multiple metrics"""
    
    @staticmethod
    def jaccard_similarity(phrase1: str, phrase2: str) -> float:
        """Jaccard similarity between two phrases (word-based)"""
        words1 = set(phrase1.lower().split())
        words2 = set(phrase2.lower().split())
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def cosine_similarity(phrase1: str, phrase2: str) -> float:
        """Cosine similarity between phrase vectors"""
        def get_char_vector(phrase: str) -> Counter:
            return Counter(phrase.lower().replace(" ", ""))
        
        vec1 = get_char_vector(phrase1)
        vec2 = get_char_vector(phrase2)
        
        common_chars = set(vec1.keys()) & set(vec2.keys())
        dot_product = sum(vec1[c] * vec2[c] for c in common_chars)
        
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        
        return dot_product / (mag1 * mag2) if mag1 * mag2 > 0 else 0.0
    
    @staticmethod
    def levenshtein_distance(phrase1: str, phrase2: str) -> float:
        """Normalized Levenshtein distance (0-1, where 1 = identical)"""
        s1, s2 = phrase1.lower(), phrase2.lower()
        
        if len(s1) < len(s2):
            return SimilarityMetrics.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return 0.0
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        max_len = max(len(s1), len(s2))
        return 1.0 - (previous_row[-1] / max_len)


# ────────────────────────────────────────────────────────────────────────────
# Enhanced StableTokenVocab Class
# ────────────────────────────────────────────────────────────────────────────

class StableTokenVocab:
    """
    Enhanced stable token vocabulary with advanced features.
    
    Features:
    - Configurable n-gram sizes
    - Multiple similarity metrics
    - Batch operations
    - Token relationship mapping
    - Advanced filtering
    - Performance profiling
    - Comprehensive validation
    """
    
    def __init__(self, mem=None, db=None, param=None):
        """Initialize vocabulary system with enhanced parameters."""
        self.mem = mem
        self.db = db
        self.param = param or {}
        
        db_path = self.param.get("db_path", "stable_vocab_v3.db")
        self.ngram_sizes = self.param.get("ngram_sizes", [2, 3, 4])
        self.similarity_threshold = self.param.get("similarity_threshold", 0.7)
        self.enable_caching = self.param.get("enable_caching", True)
        self.cache_ttl = self.param.get("cache_ttl", 300)
        self.use_threading = self.param.get("use_threading", True)
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.session_id = hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]
        self.lock = threading.RLock()
        
        self._init_schema()
        self._load_next_id()
        
        self.state = {
            "config": {
                "db_path": db_path,
                "session_id": self.session_id,
                "ngram_sizes": self.ngram_sizes,
                "similarity_threshold": self.similarity_threshold
            },
            "catalog": [],
            "results": [],
            "performance": {}
        }
        
        logger.info(f"StableTokenVocab initialized (Session: {self.session_id})")
    
    def Run(self, command: str, params: Dict[str, Any]) -> Tuple[int, Any, Any]:
        """
        Execute command via VBSTYLE interface.
        
        Enhanced commands:
          - encode_batch: Encode multiple texts at once
          - get_similar_tokens: Find similar tokens
          - get_token_relationships: Get token relationships
          - filter_tokens: Advanced filtering
          - aggregate_stats: Aggregated statistics
          - find_token_by_id: Get token info by ID
          - get_cluster_members: Get all members of a cluster
          - measure_performance: Profile operations
        """
        command_map = {
            # Original commands
            "encode": lambda: _safe(self._encode, params.get("text", "")),
            "decode": lambda: _safe(self._decode, params.get("token_ids", [])),
            "get_token_metadata": lambda: _safe(self._get_token_metadata, params.get("token_id")),
            "get_ranked_tokens": lambda: _safe(self._get_ranked_tokens, params.get("limit", 100), params.get("status")),
            "search_by_phrase": lambda: _safe(self._search_by_phrase, params.get("pattern", "")),
            "build_clusters": lambda: _safe(self._build_clusters, params.get("min_cluster_size", 3)),
            "analyze_threshold": lambda: _safe(self._analyze_threshold, params.get("token_id")),
            "get_threshold_summary": lambda: _ok(self._get_threshold_summary()),
            "get_stats": lambda: _ok(self._get_stats()),
            "apply_decay": lambda: _safe(self._apply_decay),
            "cleanup_temp": lambda: _safe(self._cleanup_temp, params.get("min_age_days", 7)),
            "export_corpus": lambda: _safe(self._export_corpus, params.get("filepath")),
            "import_corpus": lambda: _safe(self._import_corpus, params.get("filepath")),
            "track_evolution": lambda: _safe(self._track_evolution, params.get("phrase")),
            "close": lambda: _safe(self._close),
            
            # Enhanced commands
            "encode_batch": lambda: _safe(self._encode_batch, params.get("texts", [])),
            "get_similar_tokens": lambda: _safe(self._get_similar_tokens, params.get("token_id"), params.get("limit", 10), params.get("metric", "jaccard")),
            "get_token_relationships": lambda: _safe(self._get_token_relationships, params.get("token_id")),
            "filter_tokens": lambda: _safe(self._filter_tokens, params.get("filters", {})),
            "aggregate_stats": lambda: _safe(self._aggregate_stats, params.get("group_by", "status")),
            "find_token_by_id": lambda: _safe(self._find_token_by_id, params.get("token_id")),
            "get_cluster_members": lambda: _safe(self._get_cluster_members, params.get("cluster_id")),
            "measure_performance": lambda: _safe(self._measure_performance, params.get("operation")),
            "validate_corpus": lambda: _safe(self._validate_corpus),
            "get_suggestions": lambda: _safe(self._get_suggestions, params.get("phrase")),
            "merge_similar_tokens": lambda: _safe(self._merge_similar_tokens, params.get("threshold", 0.8)),
        }
        
        if command not in command_map:
            return _err("UNKNOWN_CMD", f"StableTokenVocab: {command}")
        
        return command_map[command]()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Enhanced Database Schema
    # ─────────────────────────────────────────────────────────────────────────
    
    def _init_schema(self):
        """Initialize enhanced database schema"""
        with self.lock:
            # Original vocab table with additional columns
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS vocab (
                    token_id INTEGER PRIMARY KEY,
                    phrase TEXT UNIQUE NOT NULL,
                    frequency INTEGER DEFAULT 0,
                    weight REAL DEFAULT 0,
                    contextual_strength REAL DEFAULT 0,
                    cross_session_reuse INTEGER DEFAULT 0,
                    cluster_id INTEGER,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    decay_factor REAL DEFAULT 1.0,
                    status TEXT DEFAULT 'temp',
                    phrase_hash TEXT UNIQUE,
                    rank INTEGER,
                    compression_ratio REAL DEFAULT 0,
                    information_density REAL DEFAULT 0,
                    semantic_field TEXT,
                    quality_score REAL DEFAULT 0.5
                )
            """)
            
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS token_sessions (
                    token_id INTEGER,
                    session_id TEXT,
                    frequency INTEGER DEFAULT 0,
                    PRIMARY KEY (token_id, session_id),
                    FOREIGN KEY (token_id) REFERENCES vocab(token_id)
                )
            """)
            
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS clusters (
                    cluster_id INTEGER PRIMARY KEY,
                    centroid_phrase TEXT,
                    member_count INTEGER DEFAULT 0,
                    total_weight REAL DEFAULT 0,
                    intention_label TEXT,
                    cohesion_score REAL DEFAULT 0,
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # New: Token relationships table
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS token_relationships (
                    token_id_1 INTEGER,
                    token_id_2 INTEGER,
                    similarity_score REAL,
                    metric_type TEXT,
                    PRIMARY KEY (token_id_1, token_id_2, metric_type),
                    FOREIGN KEY (token_id_1) REFERENCES vocab(token_id),
                    FOREIGN KEY (token_id_2) REFERENCES vocab(token_id)
                )
            """)
            
            # New: Performance metrics table
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    operation_name TEXT,
                    execution_time REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    parameters TEXT
                )
            """)
            
            # Indexes
            self.cur.execute("CREATE INDEX IF NOT EXISTS idx_phrase ON vocab(phrase)")
            self.cur.execute("CREATE INDEX IF NOT EXISTS idx_cluster ON vocab(cluster_id)")
            self.cur.execute("CREATE INDEX IF NOT EXISTS idx_status ON vocab(status)")
            self.cur.execute("CREATE INDEX IF NOT EXISTS idx_weight ON vocab(weight DESC)")
            self.cur.execute("CREATE INDEX IF NOT EXISTS idx_quality ON vocab(quality_score DESC)")
            self.cur.execute("CREATE INDEX IF NOT EXISTS idx_similarity ON token_relationships(similarity_score DESC)")
            
            self.conn.commit()
    
    def _load_next_id(self):
        """Load next available token and cluster IDs"""
        with self.lock:
            self.cur.execute("SELECT MAX(token_id) FROM vocab")
            result = self.cur.fetchone()
            self.next_id = (result[0] or 0) + 1
            
            self.cur.execute("SELECT MAX(cluster_id) FROM clusters")
            result = self.cur.fetchone()
            self.next_cluster_id = (result[0] or 0) + 1
    
    # ─────────────────────────────────────────────────────────────────────────
    # Phrase & Hash Operations (Enhanced)
    # ─────────────────────────────────────────────────────────────────────────
    
    def _phrase_hash(self, phrase: str) -> str:
        """Generate stable hash for phrase"""
        return hashlib.sha256(phrase.lower().encode()).hexdigest()[:16]
    
    @timing
    def _extract_phrases(self, text: str, ngram_sizes: Optional[List[int]] = None) -> List[str]:
        """Extract n-grams from text with configurable sizes"""
        if ngram_sizes is None:
            ngram_sizes = self.ngram_sizes
        
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        phrases = []
        
        for n in ngram_sizes:
            if n <= len(words):
                for i in range(len(words) - n + 1):
                    phrase = " ".join(words[i:i+n])
                    phrases.append(phrase)
        
        return phrases
    
    def _sanitize_phrase(self, phrase: str) -> str:
        """Sanitize and validate phrase"""
        phrase = phrase.lower().strip()
        phrase = re.sub(r'\s+', ' ', phrase)
        
        if not phrase or len(phrase) > 500:
            return None
        
        return phrase
    
    # ─────────────────────────────────────────────────────────────────────────
    # Token ID Management (Enhanced)
    # ─────────────────────────────────────────────────────────────────────────
    
    @timing
    def _get_or_create_token_id(self, phrase: str) -> Optional[int]:
        """Get existing stable ID or assign new one - NEVER reshuffles"""
        phrase = self._sanitize_phrase(phrase)
        if not phrase:
            return None
        
        phrase_hash = self._phrase_hash(phrase)
        
        with self.lock:
            self.cur.execute("SELECT token_id FROM vocab WHERE phrase = ?", (phrase,))
            result = self.cur.fetchone()
            if result:
                return result[0]
            
            self.cur.execute("SELECT token_id FROM vocab WHERE phrase_hash = ?", (phrase_hash,))
            result = self.cur.fetchone()
            if result:
                return result[0]
            
            token_id = self.next_id
            self.next_id += 1
            
            weight = 1.0 * len(phrase.split())
            contextual_strength = 1.0
            cross_session_reuse = 1
            status = "temp"
            
            compression_ratio = len(phrase) / (len(str(token_id)) + 1)
            information_density = len(set(phrase.split())) / len(phrase.split()) if phrase.split() else 0
            quality_score = 0.5
            
            self.cur.execute("""
                INSERT INTO vocab 
                (token_id, phrase, frequency, weight, contextual_strength, 
                 cross_session_reuse, cluster_id, first_seen, last_seen, 
                 decay_factor, status, phrase_hash, compression_ratio, 
                 information_density, quality_score)
                VALUES (?, ?, 1, ?, ?, ?, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 
                        1.0, ?, ?, ?, ?, ?)
            """, (token_id, phrase, weight, contextual_strength, cross_session_reuse, 
                  status, phrase_hash, compression_ratio, information_density, quality_score))
            
            self.cur.execute("""
                INSERT INTO token_sessions (token_id, session_id, frequency)
                VALUES (?, ?, 1)
            """, (token_id, self.session_id))
            
            self.conn.commit()
            return token_id
    
    # ─────────────────────────────────────────────────────────────────────────
    # Core Operations: Encode & Decode (Enhanced)
    # ─────────────────────────────────────────────────────────────────────────
    
    @timing
    def _encode(self, text: str) -> Tuple[int, Any, Any]:
        """Encode text to stable token IDs"""
        phrases = self._extract_phrases(text)
        token_counts = self._update_vocab(phrases)
        tokens = [token_counts[p] for p in phrases if p in token_counts]
        return _ok(tokens)
    
    @timing
    def _encode_batch(self, texts: List[str]) -> Tuple[int, Any, Any]:
        """Encode multiple texts efficiently"""
        results = []
        for text in texts:
            status, tokens, err = self._encode(text)
            if status:
                results.append({"text": text, "tokens": tokens})
            else:
                results.append({"text": text, "error": err})
        
        return _ok(results)
    
    @timing
    def _decode(self, token_ids: List[int]) -> Tuple[int, Any, Any]:
        """Decode token IDs to phrases"""
        phrases = []
        with self.lock:
            for tid in token_ids:
                self.cur.execute("SELECT phrase FROM vocab WHERE token_id = ?", (tid,))
                result = self.cur.fetchone()
                if result:
                    phrases.append(result[0])
        
        return _ok(" | ".join(phrases))
    
    # ─────────────────────────────────────────────────────────────────────────
    # Vocabulary Update & Ranking (Enhanced)
    # ─────────────────────────────────────────────────────────────────────────
    
    @timing
    def _update_vocab(self, phrases: List[str]) -> Dict[str, int]:
        """Update vocabulary with stable ID assignment"""
        freq = defaultdict(int)
        for p in phrases:
            p = self._sanitize_phrase(p)
            if p:
                freq[p] += 1
        
        token_counts = {}
        
        for phrase, count in freq.items():
            token_id = self._get_or_create_token_id(phrase)
            if token_id is None:
                continue
            
            token_counts[phrase] = token_id
            
            contextual_strength = len(phrase.split()) * 0.5 + count * 0.3
            
            with self.lock:
                self.cur.execute("""
                    SELECT COUNT(DISTINCT session_id) FROM token_sessions WHERE token_id = ?
                """, (token_id,))
                session_count = self.cur.fetchone()[0]
                cross_session_reuse = session_count
                
                compression_ratio = len(phrase) / (len(str(token_id)) + 1)
                information_density = len(set(phrase.split())) / len(phrase.split()) if phrase.split() else 0
                
                self.cur.execute("""
                    UPDATE vocab 
                    SET frequency = frequency + ?,
                        contextual_strength = ?,
                        cross_session_reuse = ?,
                        weight = (frequency + ?) + ? + ?,
                        compression_ratio = ?,
                        information_density = ?,
                        last_seen = CURRENT_TIMESTAMP,
                        decay_factor = decay_factor * 0.95
                    WHERE token_id = ?
                """, (count, contextual_strength, cross_session_reuse, count, 
                      contextual_strength, cross_session_reuse, compression_ratio, 
                      information_density, token_id))
                
                self.cur.execute("""
                    INSERT OR REPLACE INTO token_sessions (token_id, session_id, frequency)
                    VALUES (?, ?, COALESCE(
                        (SELECT frequency FROM token_sessions WHERE token_id = ? AND session_id = ?), 0
                    ) + ?)
                """, (token_id, self.session_id, token_id, self.session_id, count))
        
        self.conn.commit()
        self._apply_ranking_and_thresholds()
        
        return token_counts
    
    @timing
    def _apply_ranking_and_thresholds(self):
        """Apply ranking and threshold rules"""
        with self.lock:
            self.cur.execute("""
                SELECT token_id, phrase, frequency, weight, contextual_strength, 
                       cross_session_reuse, compression_ratio, information_density
                FROM vocab
                WHERE status != 'archived'
                ORDER BY weight DESC
            """)
            tokens = self.cur.fetchall()
            
            if not tokens:
                return
            
            corpus_size = len(tokens)
            
            for rank, token in enumerate(tokens, 1):
                self.cur.execute("UPDATE vocab SET rank = ? WHERE token_id = ?", 
                               (rank, token['token_id']))
            
            for token in tokens:
                rank = token['rank']
                rank_percentile = 1.0 - (rank / corpus_size)
                
                pass_count = 0
                pass_count += 1 if token['frequency'] >= 3 else 0
                pass_count += 1 if token['weight'] >= 5.0 else 0
                pass_count += 1 if token['cross_session_reuse'] >= 2 else 0
                pass_count += 1 if rank_percentile >= 0.8 else 0
                pass_count += 1 if token['contextual_strength'] >= 1.0 else 0
                pass_count += 1 if token['compression_ratio'] >= 2.0 else 0
                pass_count += 1 if token['information_density'] >= 1.5 else 0
                
                quality_score = pass_count / 7.0
                new_status = "perm" if pass_count >= 5 else "temp"
                
                self.cur.execute("""
                    UPDATE vocab 
                    SET status = ?, quality_score = ? 
                    WHERE token_id = ?
                """, (new_status, quality_score, token['token_id']))
            
            self.conn.commit()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Similarity & Relationships (New)
    # ─────────────────────────────────────────────────────────────────────────
    
    @timing
    def _get_similar_tokens(self, token_id: int, limit: int = 10, 
                           metric: str = "jaccard") -> Tuple[int, Any, Any]:
        """Find similar tokens using specified metric"""
        with self.lock:
            self.cur.execute("SELECT phrase FROM vocab WHERE token_id = ?", (token_id,))
            result = self.cur.fetchone()
            if not result:
                return _err("NOT_FOUND", f"Token {token_id} not found")
            
            reference_phrase = result[0]
            
            self.cur.execute("SELECT token_id, phrase FROM vocab WHERE status = 'perm'")
            candidates = self.cur.fetchall()
        
        similarities = []
        for candidate in candidates:
            if candidate['token_id'] == token_id:
                continue
            
            if metric == "jaccard":
                score = SimilarityMetrics.jaccard_similarity(reference_phrase, candidate['phrase'])
            elif metric == "cosine":
                score = SimilarityMetrics.cosine_similarity(reference_phrase, candidate['phrase'])
            elif metric == "levenshtein":
                score = SimilarityMetrics.levenshtein_distance(reference_phrase, candidate['phrase'])
            else:
                return _err("INVALID_METRIC", f"Unknown metric: {metric}")
            
            if score > self.similarity_threshold:
                similarities.append({
                    "token_id": candidate['token_id'],
                    "phrase": candidate['phrase'],
                    "similarity": score
                })
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return _ok(similarities[:limit])
    
    @timing
    def _get_token_relationships(self, token_id: int) -> Tuple[int, Any, Any]:
        """Get all relationship information for a token"""
        with self.lock:
            self.cur.execute("""
                SELECT phrase, frequency, weight, status, cluster_id
                FROM vocab WHERE token_id = ?
            """, (token_id,))
            token = self.cur.fetchone()
            if not token:
                return _err("NOT_FOUND", f"Token {token_id} not found")
            
            # Get relationships
            self.cur.execute("""
                SELECT token_id_1, token_id_2, similarity_score, metric_type
                FROM token_relationships 
                WHERE token_id_1 = ? OR token_id_2 = ?
                ORDER BY similarity_score DESC
            """, (token_id, token_id))
            relationships = self.cur.fetchall()
            
            # Get cluster members if in cluster
            cluster_members = []
            if token['cluster_id']:
                self.cur.execute("""
                    SELECT token_id, phrase FROM vocab 
                    WHERE cluster_id = ? AND token_id != ?
                """, (token['cluster_id'], token_id))
                cluster_members = [dict(row) for row in self.cur.fetchall()]
        
        return _ok({
            "token_info": dict(token),
            "relationships": [dict(r) for r in relationships],
            "cluster_members": cluster_members
        })
    
    # ─────────────────────────────────────────────────────────────────────────
    # Advanced Filtering & Aggregation (New)
    # ─────────────────────────────────────────────────────────────────────────
    
    @timing
    def _filter_tokens(self, filters: Dict[str, Any]) -> Tuple[int, Any, Any]:
        """Advanced token filtering with multiple criteria"""
        query = "SELECT * FROM vocab WHERE 1=1"
        params = []
        
        if 'min_frequency' in filters:
            query += " AND frequency >= ?"
            params.append(filters['min_frequency'])
        
        if 'max_frequency' in filters:
            query += " AND frequency <= ?"
            params.append(filters['max_frequency'])
        
        if 'min_weight' in filters:
            query += " AND weight >= ?"
            params.append(filters['min_weight'])
        
        if 'max_weight' in filters:
            query += " AND weight <= ?"
            params.append(filters['max_weight'])
        
        if 'status' in filters:
            query += " AND status = ?"
            params.append(filters['status'])
        
        if 'min_quality' in filters:
            query += " AND quality_score >= ?"
            params.append(filters['min_quality'])
        
        if 'cluster_id' in filters:
            query += " AND cluster_id = ?"
            params.append(filters['cluster_id'])
        
        limit = filters.get('limit', 100)
        query += " LIMIT ?"
        params.append(limit)
        
        with self.lock:
            self.cur.execute(query, params)
            results = [dict(row) for row in self.cur.fetchall()]
        
        return _ok(results)
    
    @timing
    def _aggregate_stats(self, group_by: str = "status") -> Tuple[int, Any, Any]:
        """Get aggregated statistics grouped by specified field"""
        valid_groups = ['status', 'cluster_id']
        if group_by not in valid_groups:
            return _err("INVALID_GROUP", f"Cannot group by {group_by}")
        
        with self.lock:
            query = f"""
                SELECT {group_by}, 
                       COUNT(*) as count,
                       AVG(frequency) as avg_frequency,
                       AVG(weight) as avg_weight,
                       AVG(quality_score) as avg_quality,
                       SUM(frequency) as total_frequency,
                       SUM(weight) as total_weight
                FROM vocab
                GROUP BY {group_by}
                ORDER BY total_weight DESC
            """
            self.cur.execute(query)
            results = [dict(row) for row in self.cur.fetchall()]
        
        return _ok(results)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Token Lookup & Cluster Operations (Enhanced)
    # ─────────────────────────────────────────────────────────────────────────
    
    @timing
    def _find_token_by_id(self, token_id: int) -> Tuple[int, Any, Any]:
        """Get comprehensive token information by ID"""
        with self.lock:
            self.cur.execute("""
                SELECT * FROM vocab WHERE token_id = ?
            """, (token_id,))
            token = self.cur.fetchone()
            if not token:
                return _err("NOT_FOUND", f"Token {token_id} not found")
            
            self.cur.execute("""
                SELECT session_id, frequency FROM token_sessions 
                WHERE token_id = ? ORDER BY session_id
            """, (token_id,))
            sessions = [dict(row) for row in self.cur.fetchall()]
        
        token_dict = dict(token)
        token_dict['sessions'] = sessions
        
        return _ok(token_dict)
    
    @timing
    def _get_cluster_members(self, cluster_id: int) -> Tuple[int, Any, Any]:
        """Get all members of a specific cluster with details"""
        with self.lock:
            self.cur.execute("""
                SELECT token_id, phrase, frequency, weight, status, quality_score
                FROM vocab WHERE cluster_id = ?
                ORDER BY weight DESC
            """, (cluster_id,))
            members = [dict(row) for row in self.cur.fetchall()]
            
            if not members:
                return _err("NOT_FOUND", f"Cluster {cluster_id} not found")
            
            self.cur.execute("""
                SELECT centroid_phrase, member_count, total_weight, intention_label, cohesion_score
                FROM clusters WHERE cluster_id = ?
            """, (cluster_id,))
            cluster_info = dict(self.cur.fetchone())
        
        cluster_info['members'] = members
        return _ok(cluster_info)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Clustering (Enhanced)
    # ─────────────────────────────────────────────────────────────────────────
    
    @timing
    def _build_clusters(self, min_cluster_size: int = 3) -> Tuple[int, Any, Any]:
        """Build clusters with enhanced similarity metrics"""
        with self.lock:
            self.cur.execute("""
                SELECT token_id, phrase, weight, frequency 
                FROM vocab 
                WHERE status = 'perm' AND decay_factor > 0.3
                ORDER BY weight DESC
            """)
            tokens = self.cur.fetchall()
        
        clusters = defaultdict(list)
        
        for token in tokens:
            words = set(token['phrase'].split())
            assigned = False
            
            for cluster_id, cluster_phrases in clusters.items():
                for member in cluster_phrases:
                    member_words = set(member['phrase'].split())
                    overlap = len(words & member_words)
                    similarity = overlap / max(len(words), len(member_words))
                    
                    if similarity >= self.similarity_threshold:
                        clusters[cluster_id].append(token)
                        assigned = True
                        break
                
                if assigned:
                    break
            
            if not assigned:
                cluster_id = self.next_cluster_id
                self.next_cluster_id += 1
                clusters[cluster_id].append(token)
        
        with self.lock:
            for cluster_id, members in clusters.items():
                if len(members) >= min_cluster_size:
                    centroid = max(members, key=lambda x: x['weight'])
                    total_weight = sum(m['weight'] for m in members)
                    
                    # Calculate cohesion
                    cohesion = self._calculate_cluster_cohesion([m['phrase'] for m in members])
                    
                    words = centroid['phrase'].split()
                    intention_label = f"{words[0]}_{words[-1]}" if len(words) >= 2 else centroid['phrase'].replace(" ", "_")
                    
                    self.cur.execute("""
                        INSERT OR REPLACE INTO clusters 
                        (cluster_id, centroid_phrase, member_count, total_weight, intention_label, cohesion_score)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (cluster_id, centroid['phrase'], len(members), total_weight, intention_label, cohesion))
                    
                    for member in members:
                        self.cur.execute("""
                            UPDATE vocab SET cluster_id = ? WHERE token_id = ?
                        """, (cluster_id, member['token_id']))
            
            self.conn.commit()
            
            self.cur.execute("""
                SELECT cluster_id, centroid_phrase, member_count, total_weight, 
                       intention_label, cohesion_score, created
                FROM clusters
                WHERE member_count >= ?
                ORDER BY total_weight DESC
            """, (min_cluster_size,))
            
            cluster_infos = [dict(row) for row in self.cur.fetchall()]
        
        return _ok(cluster_infos)
    
    def _calculate_cluster_cohesion(self, phrases: List[str]) -> float:
        """Calculate cohesion score for a cluster"""
        if len(phrases) < 2:
            return 1.0
        
        similarities = []
        for i, phrase1 in enumerate(phrases):
            for phrase2 in phrases[i+1:]:
                sim = SimilarityMetrics.jaccard_similarity(phrase1, phrase2)
                similarities.append(sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    # ─────────────────────────────────────────────────────────────────────────
    # Validation & Suggestions (New)
    # ─────────────────────────────────────────────────────────────────────────
    
    @timing
    def _validate_corpus(self) -> Tuple[int, Any, Any]:
        """Validate corpus integrity and data consistency"""
        issues = {
            "orphaned_sessions": 0,
            "orphaned_relationships": 0,
            "inconsistent_clusters": 0,
            "invalid_statuses": 0,
            "suggestions": []
        }
        
        with self.lock:
            # Check for orphaned session entries
            self.cur.execute("""
                SELECT COUNT(*) as count FROM token_sessions 
                WHERE token_id NOT IN (SELECT token_id FROM vocab)
            """)
            issues["orphaned_sessions"] = self.cur.fetchone()[0]
            
            # Check for invalid statuses
            self.cur.execute("""
                SELECT COUNT(*) as count FROM vocab 
                WHERE status NOT IN ('perm', 'temp', 'archived')
            """)
            issues["invalid_statuses"] = self.cur.fetchone()[0]
            
            # Check cluster consistency
            self.cur.execute("""
                SELECT cluster_id, COUNT(*) as count 
                FROM vocab WHERE cluster_id IS NOT NULL
                GROUP BY cluster_id
            """)
            for row in self.cur.fetchall():
                self.cur.execute("""
                    SELECT member_count FROM clusters WHERE cluster_id = ?
                """, (row[0],))
                cluster_info = self.cur.fetchone()
                if cluster_info and cluster_info[0] != row[1]:
                    issues["inconsistent_clusters"] += 1
        
        if issues["orphaned_sessions"] > 0:
            issues["suggestions"].append("Clean up orphaned session entries")
        
        if issues["invalid_statuses"] > 0:
            issues["suggestions"].append("Fix invalid token statuses")
        
        return _ok(issues)
    
    @timing
    def _get_suggestions(self, phrase: str) -> Tuple[int, Any, Any]:
        """Get suggestions for improving a phrase or finding related tokens"""
        with self.lock:
            self.cur.execute("SELECT token_id, phrase FROM vocab WHERE status = 'perm' LIMIT 100")
            candidates = self.cur.fetchall()
        
        suggestions = []
        for candidate in candidates:
            sim = SimilarityMetrics.jaccard_similarity(phrase, candidate['phrase'])
            if 0.3 <= sim < 1.0:
                suggestions.append({
                    "token_id": candidate['token_id'],
                    "phrase": candidate['phrase'],
                    "similarity": sim,
                    "suggestion": f"Consider merging with '{candidate['phrase']}'" if sim > 0.7 else "Related phrase"
                })
        
        suggestions.sort(key=lambda x: x['similarity'], reverse=True)
        return _ok(suggestions[:10])
    
    @timing
    def _merge_similar_tokens(self, threshold: float = 0.8) -> Tuple[int, Any, Any]:
        """Merge tokens that are too similar"""
        with self.lock:
            self.cur.execute("SELECT token_id, phrase FROM vocab WHERE status = 'perm'")
            tokens = self.cur.fetchall()
        
        merged_count = 0
        merge_map = {}
        
        for i, token1 in enumerate(tokens):
            if token1['token_id'] in merge_map:
                continue
            
            for token2 in tokens[i+1:]:
                if token2['token_id'] in merge_map:
                    continue
                
                sim = SimilarityMetrics.jaccard_similarity(token1['phrase'], token2['phrase'])
                if sim >= threshold:
                    # Merge token2 into token1
                    merge_map[token2['token_id']] = token1['token_id']
                    merged_count += 1
        
        if merged_count > 0:
            with self.lock:
                for source_id, target_id in merge_map.items():
                    # Combine frequencies and sessions
                    self.cur.execute("""
                        SELECT SUM(frequency) FROM token_sessions WHERE token_id = ?
                    """, (source_id,))
                    source_freq = self.cur.fetchone()[0] or 0
                    
                    self.cur.execute("""
                        UPDATE vocab SET frequency = frequency + ? WHERE token_id = ?
                    """, (source_freq, target_id))
                    
                    # Update cluster assignments
                    self.cur.execute("""
                        UPDATE vocab SET cluster_id = 
                        (SELECT cluster_id FROM vocab WHERE token_id = ?)
                        WHERE token_id = ?
                    """, (target_id, source_id))
                    
                    # Remove source token
                    self.cur.execute("DELETE FROM token_sessions WHERE token_id = ?", (source_id,))
                    self.cur.execute("DELETE FROM vocab WHERE token_id = ?", (source_id,))
                
                self.conn.commit()
        
        return _ok({"merged_count": merged_count, "merge_map": merge_map})
    
    # ─────────────────────────────────────────────────────────────────────────
    # Performance Profiling (New)
    # ─────────────────────────────────────────────────────────────────────────
    
    @timing
    def _measure_performance(self, operation: str = "all") -> Tuple[int, Any, Any]:
        """Measure and report performance metrics"""
        with self.lock:
            self.cur.execute("""
                SELECT operation_name, AVG(execution_time) as avg_time, 
                       COUNT(*) as call_count, MAX(execution_time) as max_time
                FROM performance_metrics
                GROUP BY operation_name
                ORDER BY avg_time DESC
            """)
            
            if operation == "all":
                results = [dict(row) for row in self.cur.fetchall()]
            else:
                self.cur.execute("""
                    SELECT * FROM performance_metrics 
                    WHERE operation_name = ?
                    ORDER BY timestamp DESC
                    LIMIT 100
                """, (operation,))
                results = [dict(row) for row in self.cur.fetchall()]
        
        return _ok(results)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Original Methods (Maintained for Compatibility)
    # ─────────────────────────────────────────────────────────────────────────
    
    @timing
    def _get_token_metadata(self, token_id: int) -> Tuple[int, Any, Any]:
        """Get full metadata for a token"""
        with self.lock:
            self.cur.execute("""
                SELECT * FROM vocab WHERE token_id = ?
            """, (token_id,))
            row = self.cur.fetchone()
            if not row:
                return _err("NOT_FOUND", f"Token {token_id} not found")
            
            self.cur.execute("SELECT session_id FROM token_sessions WHERE token_id = ?", (token_id,))
            sessions = [r[0] for r in self.cur.fetchall()]
        
        metadata = dict(row)
        metadata['sessions'] = sessions
        return _ok(metadata)
    
    @timing
    def _get_ranked_tokens(self, limit: int = 100, status: str = None) -> Tuple[int, Any, Any]:
        """Get ranked tokens by weight"""
        query = "SELECT * FROM vocab"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY weight DESC, frequency DESC LIMIT ?"
        params.append(limit)
        
        with self.lock:
            self.cur.execute(query, params)
            results = [dict(row) for row in self.cur.fetchall()]
        
        return _ok(results)
    
    @timing
    def _search_by_phrase(self, pattern: str) -> Tuple[int, Any, Any]:
        """Search tokens by phrase pattern"""
        with self.lock:
            self.cur.execute("""
                SELECT * FROM vocab WHERE phrase LIKE ?
                ORDER BY weight DESC
            """, (f"%{pattern}%",))
            
            results = [dict(row) for row in self.cur.fetchall()]
        
        return _ok(results)
    
    @timing
    def _analyze_threshold(self, token_id: int) -> Tuple[int, Any, Any]:
        """Analyze which threshold rules a token passes"""
        with self.lock:
            self.cur.execute("""
                SELECT frequency, weight, contextual_strength, cross_session_reuse, rank,
                       compression_ratio, information_density
                FROM vocab WHERE token_id = ?
            """, (token_id,))
            row = self.cur.fetchone()
            if not row:
                return _err("NOT_FOUND", f"Token {token_id} not found")
            
            freq, weight, ctx_strength, cross_reuse, rank, comp_ratio, info_density = row
            
            self.cur.execute("SELECT COUNT(*) FROM vocab WHERE status != 'archived'")
            corpus_size = self.cur.fetchone()[0]
        
        rank_percentile = 1.0 - (rank / corpus_size) if corpus_size > 0 else 0
        
        analysis = {
            "frequency": {"value": freq, "threshold": 3, "pass": freq >= 3},
            "weight": {"value": weight, "threshold": 5.0, "pass": weight >= 5.0},
            "cross_session": {"value": cross_reuse, "threshold": 2, "pass": cross_reuse >= 2},
            "rank_percentile": {"value": rank_percentile, "threshold": 0.8, "pass": rank_percentile >= 0.8},
            "contextual_strength": {"value": ctx_strength, "threshold": 1.0, "pass": ctx_strength >= 1.0},
            "compression_ratio": {"value": comp_ratio, "threshold": 2.0, "pass": comp_ratio >= 2.0},
            "information_density": {"value": info_density, "threshold": 1.5, "pass": info_density >= 1.5},
            "overall_pass": False,
            "pass_count": 0
        }
        
        pass_count = sum([r["pass"] for r in analysis.values() if isinstance(r, dict)])
        analysis["pass_count"] = pass_count
        analysis["overall_pass"] = pass_count >= 5
        
        return _ok(analysis)
    
    @timing
    def _get_threshold_summary(self) -> Dict:
        """Get summary of threshold performance"""
        with self.lock:
            self.cur.execute("SELECT COUNT(*) FROM vocab WHERE status = 'perm'")
            perm_count = self.cur.fetchone()[0]
            
            self.cur.execute("SELECT COUNT(*) FROM vocab WHERE status = 'temp'")
            temp_count = self.cur.fetchone()[0]
            
            self.cur.execute("SELECT COUNT(*) FROM vocab WHERE status = 'archived'")
            archived_count = self.cur.fetchone()[0]
            
            self.cur.execute("SELECT COUNT(*) FROM vocab WHERE status != 'archived'")
            corpus_size = self.cur.fetchone()[0]
        
        return {
            "permanent_tokens": perm_count,
            "temporary_tokens": temp_count,
            "archived_tokens": archived_count,
            "corpus_size": corpus_size
        }
    
    @timing
    def _get_stats(self) -> Dict:
        """Get vocabulary statistics"""
        with self.lock:
            self.cur.execute("SELECT COUNT(*) FROM vocab")
            total_tokens = self.cur.fetchone()[0]
            
            self.cur.execute("SELECT COUNT(*) FROM vocab WHERE status = 'perm'")
            perm_tokens = self.cur.fetchone()[0]
            
            self.cur.execute("SELECT COUNT(*) FROM vocab WHERE status = 'temp'")
            temp_tokens = self.cur.fetchone()[0]
            
            self.cur.execute("SELECT COUNT(*) FROM clusters")
            total_clusters = self.cur.fetchone()[0]
            
            self.cur.execute("SELECT COUNT(DISTINCT session_id) FROM token_sessions")
            total_sessions = self.cur.fetchone()[0]
        
        return {
            "total_tokens": total_tokens,
            "permanent_tokens": perm_tokens,
            "temporary_tokens": temp_tokens,
            "total_clusters": total_clusters,
            "total_sessions": total_sessions,
            "current_session": self.session_id,
            "next_token_id": self.next_id,
            "next_cluster_id": self.next_cluster_id
        }
    
    @timing
    def _apply_decay(self) -> Tuple[int, Any, Any]:
        """Apply decay factor to all tokens"""
        with self.lock:
            self.cur.execute("""
                UPDATE vocab 
                SET decay_factor = decay_factor * 0.95,
                    weight = weight * 0.95
                WHERE decay_factor > 0.01
            """)
            self.conn.commit()
        
        return _ok(True)
    
    @timing
    def _cleanup_temp(self, min_age_days: int = 7) -> Tuple[int, Any, Any]:
        """Archive old temporary tokens"""
        with self.lock:
            self.cur.execute("""
                UPDATE vocab 
                SET status = 'archived'
                WHERE status = 'temp' 
                AND datetime(last_seen) < datetime('now', '-' || ? || ' days')
            """, (min_age_days,))
            self.conn.commit()
        
        return _ok(True)
    
    @timing
    def _export_corpus(self, filepath: str) -> Tuple[int, Any, Any]:
        """Export entire corpus to JSON"""
        export_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "session_id": self.session_id,
                "next_token_id": self.next_id,
                "next_cluster_id": self.next_cluster_id
            },
            "vocab": [],
            "clusters": [],
            "sessions": []
        }
        
        with self.lock:
            self.cur.execute("SELECT * FROM vocab")
            for row in self.cur.fetchall():
                export_data["vocab"].append(dict(row))
            
            self.cur.execute("SELECT * FROM clusters")
            for row in self.cur.fetchall():
                export_data["clusters"].append(dict(row))
            
            self.cur.execute("SELECT * FROM token_sessions")
            for row in self.cur.fetchall():
                export_data["sessions"].append(dict(row))
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return _ok(True)
    
    @timing
    def _import_corpus(self, filepath: str) -> Tuple[int, Any, Any]:
        """Import corpus from JSON"""
        with open(filepath, 'r') as f:
            import_data = json.load(f)
        
        with self.lock:
            for token in import_data["vocab"]:
                self.cur.execute("""
                    INSERT OR REPLACE INTO vocab 
                    (token_id, phrase, frequency, weight, contextual_strength,
                     cross_session_reuse, cluster_id, first_seen, last_seen,
                     decay_factor, status, phrase_hash, rank, compression_ratio, 
                     information_density, quality_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    token.get("token_id"),
                    token.get("phrase"),
                    token.get("frequency", 0),
                    token.get("weight", 0),
                    token.get("contextual_strength", 0),
                    token.get("cross_session_reuse", 0),
                    token.get("cluster_id"),
                    token.get("first_seen"),
                    token.get("last_seen"),
                    token.get("decay_factor", 1.0),
                    token.get("status", "temp"),
                    token.get("phrase_hash"),
                    token.get("rank"),
                    token.get("compression_ratio", 0),
                    token.get("information_density", 0),
                    token.get("quality_score", 0.5)
                ))
            
            self.next_id = import_data["metadata"]["next_token_id"]
            self.next_cluster_id = import_data["metadata"]["next_cluster_id"]
            
            self.conn.commit()
        
        return _ok(True)
    
    @timing
    def _track_evolution(self, phrase: str) -> Tuple[int, Any, Any]:
        """Track how a phrase evolved over sessions"""
        phrase_hash = self._phrase_hash(phrase)
        
        with self.lock:
            self.cur.execute("SELECT token_id FROM vocab WHERE phrase_hash = ?", (phrase_hash,))
            result = self.cur.fetchone()
            if not result:
                return _ok([])
            
            token_id = result[0]
            
            self.cur.execute("""
                SELECT session_id, frequency FROM token_sessions 
                WHERE token_id = ? ORDER BY session_id
            """, (token_id,))
            
            evolution = [dict(row) for row in self.cur.fetchall()]
        
        return _ok(evolution)
    
    @timing
    def _close(self) -> Tuple[int, Any, Any]:
        """Close database connection"""
        with self.lock:
            self.conn.commit()
            self.conn.close()
        
        return _ok(True)
