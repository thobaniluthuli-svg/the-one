"""
StableTokenVocab - Stable Token Vocabulary System with Clustering & Persistence

VBSTYLE Architecture:
- Authority: token_vocab (StableTokenVocab class)
- Return: Tuple3 (status, payload, error)
- Orchestration: none (pure class, no external orchestration)
- Schema: SQL-driven, no hardcoded structures

Methods:
  - Run(command, params) -> Tuple[int, Any, Any]
  - encode(text) -> token_ids
  - decode(token_ids) -> phrase_string
  - get_metadata(token_id) -> metadata_dict
  - get_ranked(limit, status) -> ranked_token_list
  - search(pattern) -> search_results
  - build_clusters(min_size) -> cluster_info
  - analyze_threshold(token_id) -> threshold_analysis
  - get_stats() -> statistics
"""

import re
import hashlib
import sqlite3
import json
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Tuple, Set, Optional, Any


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
        return _err("INTERNAL", str(e), None)


# ────────────────────────────────────────────���────────────────────────────────
# StableTokenVocab Class
# ─────────────────────────────────────────────────────────────────────────────

class StableTokenVocab:
    """
    Stable token vocabulary with clustering and persistence.
    Symbolic dictionary compression over language corpora.
    
    Database schema guarantees stable token IDs across sessions.
    """
    
    def __init__(self, mem=None, db=None, param=None):
        """Initialize vocabulary system with optional parameters."""
        self.mem = mem
        self.db = db
        self.param = param or {}
        
        db_path = self.param.get("db_path", "stable_vocab_v3.db")
        
        self.conn = sqlite3.connect(db_path)
        self.cur = self.conn.cursor()
        self.session_id = hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]
        
        self._init_schema()
        self._load_next_id()
        
        self.state = {
            "config": {
                "db_path": db_path,
                "session_id": self.session_id
            },
            "catalog": [],
            "results": []
        }
    
    def Run(self, command: str, params: Dict[str, Any]) -> Tuple[int, Any, Any]:
        """
        Execute command via VBSTYLE interface.
        
        Commands:
          - encode: Encode text to token IDs
          - decode: Decode token IDs to phrases
          - get_token_metadata: Get token metadata
          - get_ranked_tokens: Get ranked tokens by weight
          - search_by_phrase: Search tokens by pattern
          - build_clusters: Build phrase clusters
          - analyze_threshold: Analyze token threshold performance
          - get_threshold_summary: Get corpus threshold summary
          - get_stats: Get vocabulary statistics
          - apply_decay: Apply decay factor to all tokens
          - cleanup_temp: Archive old temporary tokens
          - export_corpus: Export corpus to JSON
          - import_corpus: Import corpus from JSON
          - track_evolution: Track phrase evolution across sessions
          - close: Close database connection
        """
        if command == "encode":
            return _safe(self._encode, params.get("text", ""))
        elif command == "decode":
            return _safe(self._decode, params.get("token_ids", []))
        elif command == "get_token_metadata":
            return _safe(self._get_token_metadata, params.get("token_id"))
        elif command == "get_ranked_tokens":
            return _safe(self._get_ranked_tokens, params.get("limit", 100), params.get("status"))
        elif command == "search_by_phrase":
            return _safe(self._search_by_phrase, params.get("pattern", ""))
        elif command == "build_clusters":
            return _safe(self._build_clusters, params.get("min_cluster_size", 3))
        elif command == "analyze_threshold":
            return _safe(self._analyze_threshold, params.get("token_id"))
        elif command == "get_threshold_summary":
            return _ok(self._get_threshold_summary())
        elif command == "get_stats":
            return _ok(self._get_stats())
        elif command == "apply_decay":
            return _safe(self._apply_decay)
        elif command == "cleanup_temp":
            return _safe(self._cleanup_temp, params.get("min_age_days", 7))
        elif command == "export_corpus":
            return _safe(self._export_corpus, params.get("filepath"))
        elif command == "import_corpus":
            return _safe(self._import_corpus, params.get("filepath"))
        elif command == "track_evolution":
            return _safe(self._track_evolution, params.get("phrase"))
        elif command == "close":
            return _safe(self._close)
        else:
            return _err("UNKNOWN_CMD", f"StableTokenVocab: {command}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Database Schema & Initialization
    # ─────────────────────────────────────────────────────────────────────────
    
    def _init_schema(self):
        """Initialize database schema with stable ID guarantees."""
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
                information_density REAL DEFAULT 0
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
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.cur.execute("CREATE INDEX IF NOT EXISTS idx_phrase ON vocab(phrase)")
        self.cur.execute("CREATE INDEX IF NOT EXISTS idx_cluster ON vocab(cluster_id)")
        self.cur.execute("CREATE INDEX IF NOT EXISTS idx_status ON vocab(status)")
        self.cur.execute("CREATE INDEX IF NOT EXISTS idx_weight ON vocab(weight DESC)")
        
        self.conn.commit()
    
    def _load_next_id(self):
        """Load next available token ID to ensure stability."""
        self.cur.execute("SELECT MAX(token_id) FROM vocab")
        result = self.cur.fetchone()
        self.next_id = (result[0] or 0) + 1
        
        self.cur.execute("SELECT MAX(cluster_id) FROM clusters")
        result = self.cur.fetchone()
        self.next_cluster_id = (result[0] or 0) + 1
    
    # ─────────────────────────────────────────────────────────────────────────
    # Phrase & Hash Operations
    # ─────────────────────────────────────────────────────────────────────────
    
    def _phrase_hash(self, phrase: str) -> str:
        """Generate stable hash for phrase."""
        return hashlib.sha256(phrase.lower().encode()).hexdigest()[:16]
    
    def _extract_phrases(self, text: str, n: int = 3) -> List[str]:
        """Extract n-gram phrases from text."""
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        phrases = []
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i+n])
            phrases.append(phrase)
        return phrases
    
    # ─────────────────────────────────────────────────────────────────────────
    # Token ID Management
    # ─────────────────────────────────────────────────────────────────────────
    
    def _get_or_create_token_id(self, phrase: str) -> int:
        """Get existing stable ID or assign new one - NEVER reshuffles."""
        phrase_hash = self._phrase_hash(phrase)
        
        # Check by phrase
        self.cur.execute("SELECT token_id FROM vocab WHERE phrase = ?", (phrase,))
        result = self.cur.fetchone()
        if result:
            return result[0]
        
        # Check by hash
        self.cur.execute("SELECT token_id FROM vocab WHERE phrase_hash = ?", (phrase_hash,))
        result = self.cur.fetchone()
        if result:
            return result[0]
        
        # Create new token
        token_id = self.next_id
        self.next_id += 1
        
        weight = 1.0 * len(phrase.split())
        contextual_strength = 1.0
        cross_session_reuse = 1
        status = "temp"
        
        compression_ratio = len(phrase) / (len(str(token_id)) + 1)
        information_density = len(set(phrase.split())) / len(phrase.split()) if phrase.split() else 0
        
        self.cur.execute("""
            INSERT INTO vocab 
            (token_id, phrase, frequency, weight, contextual_strength, 
             cross_session_reuse, cluster_id, first_seen, last_seen, 
             decay_factor, status, phrase_hash, compression_ratio, information_density)
            VALUES (?, ?, 1, ?, ?, ?, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1.0, ?, ?, ?, ?)
        """, (token_id, phrase, weight, contextual_strength, cross_session_reuse, 
              status, phrase_hash, compression_ratio, information_density))
        
        self.cur.execute("""
            INSERT INTO token_sessions (token_id, session_id, frequency)
            VALUES (?, ?, 1)
        """, (token_id, self.session_id))
        
        self.conn.commit()
        return token_id
    
    # ─────────────────────────────────────────────────────────────────────────
    # Vocabulary Update & Ranking
    # ─────────────────────────────────────────────────────────────────────────
    
    def _update_vocab(self, phrases: List[str]) -> Dict[str, int]:
        """Update vocabulary with stable ID assignment."""
        freq = defaultdict(int)
        for p in phrases:
            freq[p] += 1
        
        token_counts = {}
        
        for phrase, count in freq.items():
            token_id = self._get_or_create_token_id(phrase)
            token_counts[phrase] = token_id
            
            contextual_strength = len(phrase.split()) * 0.5 + count * 0.3
            
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
    
    def _apply_ranking_and_thresholds(self):
        """Apply ranking and threshold rules to determine permanent status."""
        self.cur.execute("""
            SELECT token_id, phrase, frequency, weight, contextual_strength, cross_session_reuse,
                   compression_ratio, information_density
            FROM vocab
            WHERE status != 'archived'
            ORDER BY weight DESC
        """)
        tokens = self.cur.fetchall()
        
        if not tokens:
            return
        
        corpus_size = len(tokens)
        
        for rank, (token_id, phrase, freq, weight, ctx_strength, cross_reuse, comp_ratio, info_density) in enumerate(tokens, 1):
            self.cur.execute("UPDATE vocab SET rank = ? WHERE token_id = ?", (rank, token_id))
        
        for token_id, phrase, freq, weight, ctx_strength, cross_reuse, comp_ratio, info_density in tokens:
            self.cur.execute("SELECT rank FROM vocab WHERE token_id = ?", (token_id,))
            rank = self.cur.fetchone()[0]
            
            rank_percentile = 1.0 - (rank / corpus_size)
            
            # Simple threshold: top 20% or freq >= 3
            if rank_percentile >= 0.8 or freq >= 3:
                new_status = "perm"
            else:
                new_status = "temp"
            
            self.cur.execute("UPDATE vocab SET status = ? WHERE token_id = ?", (new_status, token_id))
        
        self.conn.commit()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Core Operations: Encode & Decode
    # ─────────────────────────────────────────────────────────────────────────
    
    def _encode(self, text: str) -> Tuple[int, Any, Any]:
        """Encode text to stable token IDs."""
        phrases = self._extract_phrases(text)
        token_counts = self._update_vocab(phrases)
        tokens = [token_counts[p] for p in phrases]
        return _ok(tokens)
    
    def _decode(self, token_ids: List[int]) -> Tuple[int, Any, Any]:
        """Decode token IDs to phrases."""
        phrases = []
        for tid in token_ids:
            self.cur.execute("SELECT phrase FROM vocab WHERE token_id = ?", (tid,))
            result = self.cur.fetchone()
            if result:
                phrases.append(result[0])
        return _ok(" | ".join(phrases))
    
    # ─────────────────────────────────────────────────────────────────────────
    # Token Metadata & Search
    # ─────────────────────────────────────────────────────────────────────────
    
    def _get_token_metadata(self, token_id: int) -> Tuple[int, Any, Any]:
        """Get full metadata for a token."""
        self.cur.execute("""
            SELECT phrase, token_id, frequency, weight, contextual_strength, 
                   cross_session_reuse, cluster_id, first_seen, last_seen, 
                   decay_factor, status, rank, compression_ratio, information_density
            FROM vocab WHERE token_id = ?
        """, (token_id,))
        row = self.cur.fetchone()
        if not row:
            return _err("NOT_FOUND", f"Token {token_id} not found")
        
        self.cur.execute("SELECT session_id FROM token_sessions WHERE token_id = ?", (token_id,))
        sessions = [r[0] for r in self.cur.fetchall()]
        
        metadata = {
            "phrase": row[0], "token_id": row[1], "frequency": row[2], "weight": row[3],
            "contextual_strength": row[4], "cross_session_reuse": row[5], "cluster_id": row[6],
            "first_seen": row[7], "last_seen": row[8], "sessions": sessions, "decay_factor": row[9],
            "status": row[10], "rank": row[11], "compression_ratio": row[12], "information_density": row[13]
        }
        return _ok(metadata)
    
    def _get_ranked_tokens(self, limit: int = 100, status: str = None) -> Tuple[int, Any, Any]:
        """Get ranked tokens by weight."""
        query = """
            SELECT token_id, phrase, frequency, weight, contextual_strength,
                   cross_session_reuse, cluster_id, first_seen, last_seen,
                   decay_factor, status, rank, compression_ratio, information_density
            FROM vocab
        """
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY weight DESC, frequency DESC LIMIT ?"
        params.append(limit)
        
        self.cur.execute(query, params)
        results = []
        
        for row in self.cur.fetchall():
            self.cur.execute("SELECT session_id FROM token_sessions WHERE token_id = ?", (row[0],))
            sessions = [r[0] for r in self.cur.fetchall()]
            
            metadata = {
                "phrase": row[1], "token_id": row[0], "frequency": row[2], "weight": row[3],
                "contextual_strength": row[4], "cross_session_reuse": row[5], "cluster_id": row[6],
                "first_seen": row[7], "last_seen": row[8], "sessions": sessions, "decay_factor": row[9],
                "status": row[10], "rank": row[11], "compression_ratio": row[12], "information_density": row[13]
            }
            results.append(metadata)
        
        return _ok(results)
    
    def _search_by_phrase(self, pattern: str) -> Tuple[int, Any, Any]:
        """Search tokens by phrase pattern."""
        self.cur.execute("""
            SELECT token_id, phrase, frequency, weight, contextual_strength,
                   cross_session_reuse, cluster_id, first_seen, last_seen,
                   decay_factor, status, rank, compression_ratio, information_density
            FROM vocab WHERE phrase LIKE ?
            ORDER BY weight DESC
        """, (f"%{pattern}%",))
        
        results = []
        for row in self.cur.fetchall():
            self.cur.execute("SELECT session_id FROM token_sessions WHERE token_id = ?", (row[0],))
            sessions = [r[0] for r in self.cur.fetchall()]
            
            metadata = {
                "phrase": row[1], "token_id": row[0], "frequency": row[2], "weight": row[3],
                "contextual_strength": row[4], "cross_session_reuse": row[5], "cluster_id": row[6],
                "first_seen": row[7], "last_seen": row[8], "sessions": sessions, "decay_factor": row[9],
                "status": row[10], "rank": row[11], "compression_ratio": row[12], "information_density": row[13]
            }
            results.append(metadata)
        
        return _ok(results)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Clustering & Threshold Analysis
    # ─────────────────────────────────────────────────────────────────────────
    
    def _build_clusters(self, min_cluster_size: int = 3) -> Tuple[int, Any, Any]:
        """Build clusters based on phrase similarity."""
        self.cur.execute("""
            SELECT token_id, phrase, weight, frequency 
            FROM vocab 
            WHERE status = 'perm' AND decay_factor > 0.3
            ORDER BY weight DESC
        """)
        tokens = self.cur.fetchall()
        
        clusters = defaultdict(list)
        
        for token_id, phrase, weight, freq in tokens:
            words = set(phrase.split())
            assigned = False
            
            for cluster_id, cluster_phrases in clusters.items():
                for member_phrase in cluster_phrases:
                    member_words = set(member_phrase[1].split())
                    overlap = len(words & member_words)
                    similarity = overlap / max(len(words), len(member_words))
                    
                    if similarity >= 0.7:
                        clusters[cluster_id].append((token_id, phrase, weight))
                        assigned = True
                        break
                
                if assigned:
                    break
            
            if not assigned:
                cluster_id = self.next_cluster_id
                self.next_cluster_id += 1
                clusters[cluster_id].append((token_id, phrase, weight))
        
        for cluster_id, members in clusters.items():
            if len(members) >= min_cluster_size:
                centroid = max(members, key=lambda x: x[2])
                total_weight = sum(m[2] for m in members)
                words = centroid[1].split()
                intention_label = f"{words[0]}_{words[-1]}" if len(words) >= 2 else centroid[1].replace(" ", "_")
                
                self.cur.execute("""
                    INSERT OR REPLACE INTO clusters 
                    (cluster_id, centroid_phrase, member_count, total_weight, intention_label)
                    VALUES (?, ?, ?, ?, ?)
                """, (cluster_id, centroid[1], len(members), total_weight, intention_label))
                
                for token_id, _, _ in members:
                    self.cur.execute("""
                        UPDATE vocab SET cluster_id = ? WHERE token_id = ?
                    """, (cluster_id, token_id))
        
        self.conn.commit()
        
        self.cur.execute("""
            SELECT cluster_id, centroid_phrase, member_count, total_weight, intention_label, created
            FROM clusters
            WHERE member_count >= ?
            ORDER BY total_weight DESC
        """, (min_cluster_size,))
        
        cluster_infos = []
        for row in self.cur.fetchall():
            cluster_infos.append({
                "cluster_id": row[0], "centroid_phrase": row[1], "member_count": row[2],
                "total_weight": row[3], "intention_label": row[4], "created": row[5]
            })
        
        return _ok(cluster_infos)
    
    def _analyze_threshold(self, token_id: int) -> Tuple[int, Any, Any]:
        """Analyze which threshold rules a token passes."""
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
    
    # ─────────────────────────────────────────────────────────────────────────
    # Statistics & Summary
    # ─────────────────────────────────────────────────────────────────────────
    
    def _get_threshold_summary(self) -> Dict:
        """Get summary of threshold performance across corpus."""
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
    
    def _get_stats(self) -> Dict:
        """Get vocabulary statistics."""
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
    
    # ─────────────────────────────────────────────────────────────────────────
    # Maintenance & Evolution Tracking
    # ─────────────────────────────────────────────────────────────────────────
    
    def _apply_decay(self) -> Tuple[int, Any, Any]:
        """Apply decay factor to all tokens."""
        self.cur.execute("""
            UPDATE vocab 
            SET decay_factor = decay_factor * 0.95,
                weight = weight * 0.95
            WHERE decay_factor > 0.01
        """)
        self.conn.commit()
        return _ok(True)
    
    def _cleanup_temp(self, min_age_days: int = 7) -> Tuple[int, Any, Any]:
        """Archive old temporary tokens."""
        self.cur.execute("""
            UPDATE vocab 
            SET status = 'archived'
            WHERE status = 'temp' 
            AND datetime(last_seen) < datetime('now', '-' || ? || ' days')
        """, (min_age_days,))
        self.conn.commit()
        return _ok(True)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Import/Export
    # ─────────────────────────────────────────────────────────────────────────
    
    def _export_corpus(self, filepath: str) -> Tuple[int, Any, Any]:
        """Export entire corpus to JSON."""
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
        
        self.cur.execute("SELECT * FROM vocab")
        for row in self.cur.fetchall():
            export_data["vocab"].append(dict(zip([c[0] for c in self.cur.description], row)))
        
        self.cur.execute("SELECT * FROM clusters")
        for row in self.cur.fetchall():
            export_data["clusters"].append(dict(zip([c[0] for c in self.cur.description], row)))
        
        self.cur.execute("SELECT * FROM token_sessions")
        for row in self.cur.fetchall():
            export_data["sessions"].append(dict(zip([c[0] for c in self.cur.description], row)))
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return _ok(True)
    
    def _import_corpus(self, filepath: str) -> Tuple[int, Any, Any]:
        """Import corpus from JSON."""
        with open(filepath, 'r') as f:
            import_data = json.load(f)
        
        for token in import_data["vocab"]:
            self.cur.execute("""
                INSERT OR REPLACE INTO vocab 
                (token_id, phrase, frequency, weight, contextual_strength,
                 cross_session_reuse, cluster_id, first_seen, last_seen,
                 decay_factor, status, phrase_hash, rank, compression_ratio, information_density)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (token["token_id"], token["phrase"], token["frequency"], token["weight"],
                  token.get("contextual_strength", 0), token.get("cross_session_reuse", 0),
                  token.get("cluster_id"), token["first_seen"], token["last_seen"],
                  token.get("decay_factor", 1.0), token["status"], token["phrase_hash"],
                  token.get("rank"), token.get("compression_ratio", 0), token.get("information_density", 0)))
        
        self.next_id = import_data["metadata"]["next_token_id"]
        self.next_cluster_id = import_data["metadata"]["next_cluster_id"]
        
        self.conn.commit()
        return _ok(True)
    
    def _track_evolution(self, phrase: str) -> Tuple[int, Any, Any]:
        """Track how a phrase's metrics evolved over sessions."""
        phrase_hash = self._phrase_hash(phrase)
        
        self.cur.execute("SELECT token_id FROM vocab WHERE phrase_hash = ?", (phrase_hash,))
        result = self.cur.fetchone()
        if not result:
            return _ok([])
        
        token_id = result[0]
        
        self.cur.execute("""
            SELECT session_id, frequency FROM token_sessions 
            WHERE token_id = ? ORDER BY session_id
        """, (token_id,))
        
        evolution = []
        for session_id, freq in self.cur.fetchall():
            evolution.append({"session_id": session_id, "frequency": freq})
        
        return _ok(evolution)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────────
    
    def _close(self) -> Tuple[int, Any, Any]:
        """Close database connection."""
        self.conn.commit()
        self.conn.close()
        return _ok(True)
