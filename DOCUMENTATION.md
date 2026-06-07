````markdown
# StableTokenVocab - Tokenizer System

**A stable token vocabulary system with clustering, persistence, and semantic analysis.**

## Overview

`StableTokenVocab` is a production-grade tokenizer built on VBSTYLE architecture that:

- **Encodes** text into stable, never-reshuffling token IDs
- **Decodes** token IDs back to original phrases
- **Persists** vocabulary across sessions using SQLite
- **Clusters** semantically similar phrases
- **Analyzes** token importance using 7 metrics (frequency, weight, contextual strength, cross-session reuse, compression ratio, information density)
- **Tracks** phrase evolution across sessions
- **Supports** import/export for corpus management

## Architecture

### VBSTYLE Design

- **Authority**: `token_vocab` (StableTokenVocab class)
- **Return Format**: `Tuple3 = (status: int, payload: Any, error: Tuple)`
- **Orchestration**: None (pure class, no external dependencies)
- **Schema**: SQL-driven (no hardcoded structures)

### Return Value Pattern

Every operation returns a 3-tuple:

```python
(status, payload, error)

# Success:
(1, result_data, None)

# Error:
(0, None, (error_code, error_message, metadata))
```

## Database Schema

### `vocab` Table
Core vocabulary storage with stable token IDs:

```sql
- token_id (INTEGER PRIMARY KEY) → Stable identifier
- phrase (TEXT UNIQUE) → The actual phrase text
- frequency (INTEGER) → How many times seen
- weight (REAL) → Computed importance score
- contextual_strength (REAL) → Contextual importance
- cross_session_reuse (INTEGER) → Sessions where phrase appears
- cluster_id (INTEGER) → Cluster assignment
- first_seen / last_seen (TIMESTAMP) → Lifecycle tracking
- decay_factor (REAL) → Temporal decay multiplier
- status (TEXT) → 'perm' | 'temp' | 'archived'
- phrase_hash (TEXT UNIQUE) → SHA256 for fast lookup
- rank (INTEGER) → Corpus-wide ranking
- compression_ratio (REAL) → Token ID length vs phrase length
- information_density (REAL) → Unique words vs total words
```

### `token_sessions` Table
Cross-session frequency tracking:

```sql
- token_id (INTEGER) → Reference to vocab
- session_id (TEXT) → Session identifier
- frequency (INTEGER) → Occurrences in this session
- PRIMARY KEY (token_id, session_id)
```

### `clusters` Table
Semantic clustering results:

```sql
- cluster_id (INTEGER PRIMARY KEY)
- centroid_phrase (TEXT) → Representative phrase
- member_count (INTEGER) → Phrases in cluster
- total_weight (REAL) → Sum of member weights
- intention_label (TEXT) → Auto-generated semantic label
- created (TIMESTAMP)
```

## API Reference

### Initialization

```python
from stable_token_vocab import StableTokenVocab

vocab = StableTokenVocab(
    mem=None,          # Optional: memory cache
    db=None,           # Optional: db connection
    param={
        "db_path": "stable_vocab_v3.db"  # Database file location
    }
)
```

### Core Operations

#### 1. Encode (Text → Token IDs)

```python
status, tokens, err = vocab.Run("encode", {
    "text": "machine learning is powerful"
})

# Result:
# status=1, tokens=[5, 6, 7, 8], err=None
```

**Process**:
1. Extract 3-grams from text
2. Look up or create stable token IDs
3. Update frequency and cross-session metrics
4. Apply ranking and threshold rules
5. Return token ID list

---

#### 2. Decode (Token IDs → Phrases)

```python
status, decoded, err = vocab.Run("decode", {
    "token_ids": [5, 6, 7, 8]
})

# Result:
# status=1, decoded="machine learning | learning is | is powerful", err=None
```

---

#### 3. Get Token Metadata

```python
status, metadata, err = vocab.Run("get_token_metadata", {
    "token_id": 5
})

# Result metadata contains:
# {
#   "phrase": "machine learning",
#   "token_id": 5,
#   "frequency": 12,
#   "weight": 28.5,
#   "status": "perm",
#   "rank": 3,
#   "sessions": ["a1b2c3d4", "e5f6g7h8"],
#   "compression_ratio": 2.67,
#   "information_density": 1.0,
#   ...
# }
```

---

#### 4. Get Ranked Tokens

```python
status, ranked, err = vocab.Run("get_ranked_tokens", {
    "limit": 10,
    "status": "perm"  # Optional: filter by status
})

# Returns top 10 permanent tokens sorted by weight
```

---

#### 5. Search by Phrase Pattern

```python
status, results, err = vocab.Run("search_by_phrase", {
    "pattern": "machine"
})

# Returns all tokens matching LIKE '%machine%'
```

---

#### 6. Build Clusters

```python
status, clusters, err = vocab.Run("build_clusters", {
    "min_cluster_size": 3
})

# Result:
# [
#   {
#     "cluster_id": 1,
#     "centroid_phrase": "machine learning",
#     "member_count": 5,
#     "total_weight": 142.3,
#     "intention_label": "machine_learning"
#   },
#   ...
# ]
```

**Algorithm**:
- Filters permanent tokens with decay_factor > 0.3
- Calculates word overlap similarity (≥0.7 threshold)
- Groups similar phrases into clusters
- Assigns centroid as most weighted member

---

#### 7. Analyze Threshold

```python
status, analysis, err = vocab.Run("analyze_threshold", {
    "token_id": 5
})

# Result analyzes 7 rules:
# {
#   "frequency": {"value": 12, "threshold": 3, "pass": True},
#   "weight": {"value": 28.5, "threshold": 5.0, "pass": True},
#   "cross_session": {"value": 2, "threshold": 2, "pass": True},
#   "rank_percentile": {"value": 0.85, "threshold": 0.8, "pass": True},
#   "contextual_strength": {"value": 2.1, "threshold": 1.0, "pass": True},
#   "compression_ratio": {"value": 2.67, "threshold": 2.0, "pass": True},
#   "information_density": {"value": 1.0, "threshold": 1.5, "pass": False},
#   "pass_count": 6,
#   "overall_pass": True  # 6/7 >= 5 threshold
# }
```

**Thresholds** (token becomes "permanent" if 5+ pass):
- Frequency ≥ 3
- Weight ≥ 5.0
- Cross-session reuse ≥ 2
- Rank in top 20%
- Contextual strength ≥ 1.0
- Compression ratio ≥ 2.0
- Information density ≥ 1.5

---

#### 8. Get Statistics

```python
status, stats, err = vocab.Run("get_stats", {})

# Result:
# {
#   "total_tokens": 45,
#   "permanent_tokens": 12,
#   "temporary_tokens": 33,
#   "total_clusters": 3,
#   "total_sessions": 2,
#   "current_session": "a1b2c3d4",
#   "next_token_id": 46,
#   "next_cluster_id": 4
# }
```

---

#### 9. Get Threshold Summary

```python
status, summary, err = vocab.Run("get_threshold_summary", {})

# Result:
# {
#   "permanent_tokens": 12,
#   "temporary_tokens": 33,
#   "archived_tokens": 5,
#   "corpus_size": 45
# }
```

---

#### 10. Apply Decay

```python
status, result, err = vocab.Run("apply_decay", {})

# Multiplies decay_factor and weight by 0.95 for all tokens
# Used for temporal weighting
```

---

#### 11. Cleanup Temporary Tokens

```python
status, result, err = vocab.Run("cleanup_temp", {
    "min_age_days": 7
})

# Archives temporary tokens not seen in 7+ days
```

---

#### 12. Export Corpus

```python
status, result, err = vocab.Run("export_corpus", {
    "filepath": "corpus_export.json"
})

# Exports vocab, clusters, and sessions to JSON
```

---

#### 13. Import Corpus

```python
status, result, err = vocab.Run("import_corpus", {
    "filepath": "corpus_export.json"
})

# Restores vocab from JSON export
```

---

#### 14. Track Evolution

```python
status, evolution, err = vocab.Run("track_evolution", {
    "phrase": "machine learning"
})

# Result:
# [
#   {"session_id": "a1b2c3d4", "frequency": 5},
#   {"session_id": "e5f6g7h8", "frequency": 7}
# ]
```

---

#### 15. Close Connection

```python
status, result, err = vocab.Run("close", {})

# Closes database connection
```

## Key Features

### 1. **Stable Token IDs**
- Once assigned, a token ID never changes
- Enabled by sequential ID assignment
- Guaranteed across sessions via SQLite

### 2. **Multi-Metric Weighting**
- **Frequency**: Raw occurrence count
- **Contextual Strength**: n-gram word count + occurrence count
- **Cross-Session Reuse**: Number of unique sessions
- **Compression Ratio**: Phrase length vs token ID length
- **Information Density**: Unique words vs total words

### 3. **Automatic Status Management**
- **Temporary**: New tokens, low metrics
- **Permanent**: Passes ≥5/7 threshold rules
- **Archived**: Old temporary tokens (>7 days)

### 4. **Semantic Clustering**
- Phrase similarity based on word overlap (≥0.7)
- Centroid selection by weight
- Auto-generated intention labels

### 5. **Session Awareness**
- Tracks occurrences per session
- Enables evolution tracking
- Cross-session reuse metrics

### 6. **Persistent Storage**
- SQLite backend (no external DB needed)
- Indexed for fast lookup
- Full import/export support

## Usage Example

```python
from stable_token_vocab import StableTokenVocab

# Initialize
vocab = StableTokenVocab(param={"db_path": "my_vocab.db"})

# Encode multiple texts
texts = [
    "machine learning is powerful",
    "data science with machine learning",
    "neural networks for deep learning"
]

for text in texts:
    status, tokens, err = vocab.Run("encode", {"text": text})
    print(f"Encoded: {text} → {tokens}")

# Get top tokens
status, top_tokens, err = vocab.Run("get_ranked_tokens", {"limit": 5})
for token in top_tokens:
    print(f"Token {token['token_id']}: '{token['phrase']}' "
          f"(Freq: {token['frequency']}, Status: {token['status']})")

# Build clusters
status, clusters, err = vocab.Run("build_clusters", {"min_cluster_size": 2})
print(f"Found {len(clusters)} clusters")

# Get stats
status, stats, err = vocab.Run("get_stats", {})
print(f"Total tokens: {stats['total_tokens']}, "
      f"Permanent: {stats['permanent_tokens']}")

# Close
vocab.Run("close", {})
```

## Tokenizer Architecture Context

This class implements the **Token Identity + Vocabulary Cluster** and **Token Encoding/Decoding Cluster** from the 10-layer tokenizer system:

```
Layer 4: TOKEN IDENTITY + VOCABULARY
  ├── TokenVocabulary (THIS CLASS)
  ├── TokenIDMapper
  ├── VocabularyRegistry
  ├── StableTokenStore
  └── TokenHasher

Layer 7: ENCODING / DECODING
  ├── TokenEncoder (_encode method)
  ├── TokenDecoder (_decode method)
  ├── SequenceSerializer (_export_corpus)
  └── TokenStreamParser (_import_corpus)

Layer 8: CLUSTERING / SEMANTIC GROUPING
  ├── TokenClusterer
  ├── SemanticGrouper
  └── CoOccurrenceClusterModel (_build_clusters)
```

## Performance Notes

- **Encoding**: O(n) where n = number of words
- **Lookup**: O(1) indexed on phrase and hash
- **Clustering**: O(m²) where m = permanent tokens
- **Memory**: Minimal, all data persisted to SQLite

## Error Handling

All operations return errors in tuple format:

```python
(0, None, (error_code, error_message, metadata))

# Example:
(0, None, ("NOT_FOUND", "Token 999 not found", None))
```

Error codes:
- `UNKNOWN_CMD`: Invalid command
- `NOT_FOUND`: Token/resource not found
- `INTERNAL`: Exception during execution

## Future Enhancements

- [ ] Configurable n-gram size
- [ ] Custom threshold rules
- [ ] Token similarity scoring
- [ ] Batch encoding/decoding
- [ ] Parallel clustering
- [ ] Distributed storage backend

---

**Created**: 2026-06-07
**Architecture**: VBSTYLE
**Persistence**: SQLite
````
