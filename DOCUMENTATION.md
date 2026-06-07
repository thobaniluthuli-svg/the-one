````markdown
# StableTokenVocab - Enhanced Tokenizer System

**Advanced stable token vocabulary with comprehensive similarity metrics, performance optimization, and semantic analysis.**

## What's New in Enhanced Version

### 🚀 Performance Enhancements
- **Multi-threaded Operations** - Thread-safe with `threading.RLock()`
- **Execution Profiling** - `@timing` decorator on all operations
- **Caching Layer** - TTL-based caching with `@cached_result`
- **Batch Operations** - Process multiple texts efficiently

### 🔬 Advanced Similarity Metrics
- **Jaccard Similarity** - Word-based overlap (0-1)
- **Cosine Similarity** - Character-level vector similarity
- **Levenshtein Distance** - Normalized edit distance

### 📊 Enhanced Data Structures
- **TokenMetrics** dataclass for type safety
- **ClusterInfo** dataclass with cohesion scoring
- **SimilarityMetrics** utility class with static methods

### 📈 New Database Columns
- `semantic_field` - Phrase categorization
- `quality_score` - Computed importance (0-1)
- `cohesion_score` - Cluster quality metric

### 🔧 New Commands (13 total)
1. `encode_batch` - Batch encode multiple texts
2. `get_similar_tokens` - Find similar tokens by metric
3. `get_token_relationships` - Comprehensive relationship info
4. `filter_tokens` - Multi-criteria filtering
5. `aggregate_stats` - Grouped statistics
6. `find_token_by_id` - Detailed token lookup
7. `get_cluster_members` - Inspect cluster contents
8. `validate_corpus` - Data integrity checks
9. `get_suggestions` - Smart merge suggestions
10. `merge_similar_tokens` - Auto-consolidation
11. `measure_performance` - Operation profiling
12. Plus 15 original commands

---

## Architecture

### VBSTYLE Design

```
Authority: token_vocab (StableTokenVocab class)
Return: Tuple3 = (status: int, payload: Any, error: Tuple)
Orchestration: none
Schema: SQL-driven, enhanced with new tables
```

### Enhanced Database Schema

#### `vocab` Table (Enhanced)
```sql
- token_id (PRIMARY KEY)
- phrase (UNIQUE)
- frequency, weight, contextual_strength
- cross_session_reuse, cluster_id
- status: 'perm' | 'temp' | 'archived'
- compression_ratio, information_density
→ semantic_field (NEW)
→ quality_score (NEW)
```

#### `token_sessions` Table
```sql
- token_id, session_id (PRIMARY KEY)
- frequency
```

#### `clusters` Table (Enhanced)
```sql
- cluster_id (PRIMARY KEY)
- centroid_phrase, member_count
- total_weight, intention_label
→ cohesion_score (NEW)
```

#### `token_relationships` Table (NEW)
```sql
- token_id_1, token_id_2, metric_type (PRIMARY KEY)
- similarity_score
```

#### `performance_metrics` Table (NEW)
```sql
- operation_name
- execution_time (seconds)
- timestamp
- parameters (JSON)
```

---

## Similarity Metrics

### Jaccard Similarity
**Definition**: Intersection / Union of word sets

```python
phrase1 = "machine learning"
phrase2 = "machine learning models"

# Words: {machine, learning} vs {machine, learning, models}
# Intersection: 2, Union: 3
# Jaccard = 2/3 = 0.667

score = SimilarityMetrics.jaccard_similarity(phrase1, phrase2)
# Returns: 0.667
```

**Use case**: Semantic phrase comparison

---

### Cosine Similarity
**Definition**: Dot product of normalized character vectors

```python
# Measures character-level similarity
score = SimilarityMetrics.cosine_similarity(phrase1, phrase2)
# Returns: 0.8-1.0 range (high for overlapping text)
```

**Use case**: Typo detection, spelling variants

---

### Levenshtein Distance
**Definition**: Minimum edits (insert/delete/substitute) normalized

```python
# Normalized to 0-1 (1 = identical)
score = SimilarityMetrics.levenshtein_distance(phrase1, phrase2)
# Returns: 1.0 - (edit_distance / max_length)
```

**Use case**: Fuzzy matching, spelling correction

---

## New API Commands

### 1. Batch Encoding

```python
status, results, err = vocab.Run("encode_batch", {
    "texts": [
        "first text here",
        "second text",
        "third text"
    ]
})

# Result:
# [
#   {"text": "...", "tokens": [1, 2, 3]},
#   {"text": "...", "tokens": [4, 5, 6]},
#   ...
# ]
```

**Performance**: Processes all texts in one operation

---

### 2. Get Similar Tokens

```python
status, similar, err = vocab.Run("get_similar_tokens", {
    "token_id": 42,
    "limit": 10,
    "metric": "jaccard"  # or "cosine" or "levenshtein"
})

# Result:
# [
#   {
#     "token_id": 43,
#     "phrase": "similar phrase",
#     "similarity": 0.85
#   },
#   ...
# ]
```

**Metrics**:
- `jaccard` - Word overlap (recommended for semantic)
- `cosine` - Character overlap
- `levenshtein` - Edit distance

---

### 3. Get Token Relationships

```python
status, relationships, err = vocab.Run("get_token_relationships", {
    "token_id": 42
})

# Result:
# {
#   "token_info": {
#     "phrase": "machine learning",
#     "frequency": 5,
#     "weight": 12.3,
#     ...
#   },
#   "relationships": [
#     {"token_id_1": 42, "token_id_2": 43, "similarity": 0.85, ...},
#     ...
#   ],
#   "cluster_members": [
#     {"token_id": 44, "phrase": "..."},
#     ...
#   ]
# }
```

---

### 4. Advanced Filtering

```python
status, filtered, err = vocab.Run("filter_tokens", {
    "min_frequency": 2,
    "max_frequency": 100,
    "min_weight": 5.0,
    "max_weight": 50.0,
    "status": "perm",
    "min_quality": 0.5,
    "cluster_id": 1,
    "limit": 100
})

# All filters are optional (use as needed)
```

**Filters**:
- `min_frequency` / `max_frequency`
- `min_weight` / `max_weight`
- `status` - 'perm', 'temp', or 'archived'
- `min_quality` - Quality score threshold (0-1)
- `cluster_id` - Specific cluster
- `limit` - Max results

---

### 5. Aggregate Statistics

```python
status, agg, err = vocab.Run("aggregate_stats", {
    "group_by": "status"  # or "cluster_id"
})

# Result (grouped by status):
# [
#   {
#     "status": "perm",
#     "count": 12,
#     "avg_frequency": 4.5,
#     "avg_weight": 15.2,
#     "avg_quality": 0.8,
#     "total_frequency": 54,
#     "total_weight": 182.4
#   },
#   ...
# ]
```

---

### 6. Find Token by ID

```python
status, token, err = vocab.Run("find_token_by_id", {
    "token_id": 42
})

# Result:
# {
#   "phrase": "machine learning",
#   "token_id": 42,
#   "frequency": 5,
#   "weight": 12.3,
#   "status": "perm",
#   "quality_score": 0.75,
#   "sessions": [
#     {"session_id": "abc123", "frequency": 3},
#     {"session_id": "def456", "frequency": 2}
#   ],
#   ...
# }
```

---

### 7. Get Cluster Members

```python
status, cluster, err = vocab.Run("get_cluster_members", {
    "cluster_id": 1
})

# Result:
# {
#   "cluster_id": 1,
#   "centroid_phrase": "machine learning",
#   "member_count": 5,
#   "total_weight": 42.3,
#   "intention_label": "machine_learning",
#   "cohesion_score": 0.82,
#   "members": [
#     {
#       "token_id": 42,
#       "phrase": "machine learning",
#       "frequency": 5,
#       "weight": 12.3,
#       "quality_score": 0.75
#     },
#     ...
#   ]
# }
```

---

### 8. Validate Corpus

```python
status, validation, err = vocab.Run("validate_corpus", {})

# Result:
# {
#   "orphaned_sessions": 0,
#   "orphaned_relationships": 0,
#   "inconsistent_clusters": 0,
#   "invalid_statuses": 0,
#   "suggestions": [
#     "Clean up orphaned session entries",
#     "Fix invalid token statuses"
#   ]
# }
```

---

### 9. Get Suggestions

```python
status, suggestions, err = vocab.Run("get_suggestions", {
    "phrase": "machine learning"
})

# Result:
# [
#   {
#     "token_id": 43,
#     "phrase": "machine learning models",
#     "similarity": 0.85,
#     "suggestion": "Consider merging with 'machine learning models'"
#   },
#   {
#     "token_id": 44,
#     "phrase": "machine learning algorithm",
#     "similarity": 0.72,
#     "suggestion": "Related phrase"
#   },
#   ...
# ]
```

---

### 10. Merge Similar Tokens

```python
status, result, err = vocab.Run("merge_similar_tokens", {
    "threshold": 0.8  # Merge if similarity >= 0.8
})

# Result:
# {
#   "merged_count": 3,
#   "merge_map": {
#     45: 42,  # token 45 merged into 42
#     46: 42,
#     47: 43
#   }
# }
```

**Behavior**:
- Combines frequencies from merged tokens
- Updates cluster assignments
- Deletes source tokens
- Permanent operation (use with caution)

---

### 11. Measure Performance

```python
status, metrics, err = vocab.Run("measure_performance", {
    "operation": "all"  # or specific operation name
})

# Result (all operations):
# [
#   {
#     "operation_name": "_encode",
#     "avg_time": 0.0023,
#     "call_count": 45,
#     "max_time": 0.0089
#   },
#   {
#     "operation_name": "_build_clusters",
#     "avg_time": 0.1234,
#     "call_count": 2,
#     "max_time": 0.1456
#   },
#   ...
# ]
```

---

## Enhanced Features

### Thread Safety
All database operations use `threading.RLock()` for safe concurrent access:

```python
with self.lock:
    self.cur.execute(...)
    self.conn.commit()
```

### Quality Scoring
Each token gets a quality score (0-1) based on threshold passes:

```
quality_score = (passes / 7)

Thresholds:
- Frequency ≥ 3
- Weight ≥ 5.0
- Cross-session ≥ 2
- Rank in top 20%
- Contextual strength ≥ 1.0
- Compression ratio ≥ 2.0
- Information density ≥ 1.5
```

### Cluster Cohesion
Clusters now have a cohesion score measuring internal similarity:

```python
cohesion = mean_pairwise_similarity(cluster_members)
# Range: 0-1 (1 = perfectly cohesive)
```

### Configurable N-grams
Extract multiple n-gram sizes:

```python
vocab = StableTokenVocab(param={
    "ngram_sizes": [2, 3, 4]  # bigrams, trigrams, 4-grams
})
```

---

## Usage Example

```python
from stable_token_vocab import StableTokenVocab, SimilarityMetrics

# Initialize
vocab = StableTokenVocab(param={
    "db_path": "my_vocab.db",
    "ngram_sizes": [2, 3, 4],
    "similarity_threshold": 0.7
})

# Batch encode
texts = ["machine learning", "deep learning", "AI models"]
status, results, err = vocab.Run("encode_batch", {"texts": texts})

# Find similar
status, similar, err = vocab.Run("get_similar_tokens", {
    "token_id": 1,
    "limit": 5,
    "metric": "jaccard"
})

# Build clusters with cohesion
status, clusters, err = vocab.Run("build_clusters", {"min_cluster_size": 2})
for cluster in clusters:
    print(f"Cluster {cluster['cluster_id']}: "
          f"Cohesion={cluster['cohesion_score']:.2f}")

# Validate and merge
status, validation, err = vocab.Run("validate_corpus", {})
status, merged, err = vocab.Run("merge_similar_tokens", {"threshold": 0.85})

# Get stats
status, stats, err = vocab.Run("get_stats", {})
print(f"Total: {stats['total_tokens']}, "
      f"Permanent: {stats['permanent_tokens']}")

# Close
vocab.Run("close", {})
```

---

## Performance Characteristics

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| encode | O(n) | n = word count |
| encode_batch | O(m*n) | m = texts, n = avg words |
| get_similar_tokens | O(k*p) | k = corpus, p = similarity calc |
| build_clusters | O(m²) | m = permanent tokens |
| merge_similar_tokens | O(m²) | Full pairwise comparison |
| validate_corpus | O(m) | Single scan |
| measure_performance | O(1) | DB aggregation |

---

## Best Practices

### 1. Batch Operations
Use `encode_batch` for processing multiple texts (faster):

```python
# Good ✓
status, results, err = vocab.Run("encode_batch", {"texts": texts})

# Slower ✗
for text in texts:
    vocab.Run("encode", {"text": text})
```

### 2. Choose Right Metric
- **Jaccard**: Semantic similarity (recommended)
- **Cosine**: Typo/variant detection
- **Levenshtein**: Exact matching

### 3. Cluster Before Merge
Always validate and inspect clusters before merging:

```python
status, clusters, err = vocab.Run("build_clusters", {})
status, suggestions, err = vocab.Run("get_suggestions", {"phrase": "..."})
status, merged, err = vocab.Run("merge_similar_tokens", {"threshold": 0.85})
```

### 4. Regular Validation
Check corpus integrity periodically:

```python
status, validation, err = vocab.Run("validate_corpus", {})
if validation['suggestions']:
    print(f"Issues found: {validation['suggestions']}")
```

### 5. Monitor Performance
Track operation performance:

```python
status, perf, err = vocab.Run("measure_performance", {"operation": "all"})
slowest = max(perf, key=lambda x: x['avg_time'])
print(f"Slowest: {slowest['operation_name']} ({slowest['avg_time']:.4f}s)")
```

---

## Advanced Configuration

```python
vocab = StableTokenVocab(param={
    "db_path": "vocab.db",
    "ngram_sizes": [2, 3],           # n-gram range
    "similarity_threshold": 0.7,      # Clustering threshold
    "enable_caching": True,           # Cache results
    "cache_ttl": 300,                 # 5 min cache
    "use_threading": True             # Thread safety
})
```

---

## Troubleshooting

### Slow Performance
1. Check `measure_performance` for bottlenecks
2. Use `encode_batch` for bulk operations
3. Reduce `ngram_sizes` for faster encoding

### Memory Issues
1. Export and reimport corpus (compact)
2. Archive old temporary tokens
3. Increase `cache_ttl` to reduce recomputation

### Inconsistent Data
1. Run `validate_corpus` check
2. Look at `suggestions` output
3. Use `merge_similar_tokens` judiciously

---

## Integration with Tokenizer Layers

This enhanced class covers multiple layers:

```
Layer 4: TOKEN IDENTITY + VOCABULARY
  ✓ Stable ID assignment
  ✓ Quality scoring
  
Layer 7: ENCODING / DECODING
  ✓ Batch encoding
  ✓ Import/export with relationships
  
Layer 8: CLUSTERING / SEMANTIC GROUPING
  ✓ Multi-metric similarity
  ✓ Cohesion scoring
  
Layer 5: FREQUENCY + WEIGHT
  ✓ Multi-factor weighting
  ✓ Quality metrics
```

---

**Version**: 2.0 Enhanced
**Created**: 2026-06-07
**Architecture**: VBSTYLE
**Status**: Production Ready

````
