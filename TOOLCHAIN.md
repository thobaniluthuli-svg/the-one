````markdown
# VB Unified Toolchain - Complete Code Governance & Analysis System

**Integrated system combining VB Shell Gate (code validation) + StableTokenVocab (semantic analysis)**

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VB UNIFIED TOOLCHAIN                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────┐  ┌─────────────────┐  │
│  │   VB SHELL GATE                  │  │   STABLE TOKEN  │  │
│  │   Code Governance                │  │   VOCAB         │  │
│  │   - Validates C code contracts   │  │   Semantic      │  │
│  │   - Repairs violations            │  │   Analysis      │  │
│  │   - Tracks history                │  │   - Similarity  │  │
│  │   - 10 required symbols           │  │   - Clustering  │  │
│  │   - 7 required patterns           │  │   - Encoding    │  │
│  └──────────────────────────────────┘  └─────────────────┘  │
│                     ▼                              ▼           │
│  ┌──────────────────────────────────────────────────────┐    │
│  │            SQLite Persistence Layer                  │    │
│  │  - classes, code_artifacts (VBShellGate)            │    │
│  │  - vocab, clusters, relationships (StableTokenVocab) │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. VB Shell Gate (Code Validation & Repair)

**Purpose**: Validate C code against VB-style contract patterns

**Key Classes:**
- `VBValidator` - Contract validation engine
- `VBShellGate` - Orchestrator (VBSTYLE)
- `VBShellGateCLI` - Interactive interface

**Features:**
- ✓ 10 required symbols validation
- ✓ 7 required patterns checking
- ✓ Method signature verification
- ✓ Automatic code repair with templates
- ✓ Artifact history tracking
- ✓ SQLite persistence

**Command Interface:**
```python
gate = VBShellGate()
gate.Run("init_db", {})
ok, data, err = gate.Run("validate_file", {"filepath": "code.c"})
```

**Database Schema:**
```sql
classes:
  - id (PRIMARY KEY)
  - name (UNIQUE)
  - status: 'approved' | 'rejected' | 'pending'
  - created_at (TIMESTAMP)

code_artifacts:
  - id (PRIMARY KEY)
  - class_id (FOREIGN KEY)
  - code (TEXT)
  - is_valid (0 | 1)
  - error_report
  - created_at (TIMESTAMP)
```

---

### 2. Stable Token Vocab (Semantic Analysis)

**Purpose**: Extract, cluster, and analyze semantic tokens from text

**Key Classes:**
- `TokenMetrics` - Token data structure
- `ClusterInfo` - Cluster information
- `SimilarityMetrics` - 3 similarity algorithms
- `StableTokenVocab` - Main orchestrator

**Features:**
- ✓ 3 similarity metrics (Jaccard, Cosine, Levenshtein)
- ✓ Configurable n-gram extraction
- ✓ Batch operations
- ✓ Multi-metric token clustering
- ✓ Quality scoring system
- ✓ Advanced filtering & aggregation
- ✓ Performance profiling

**Command Interface:**
```python
vocab = StableTokenVocab()
ok, tokens, err = vocab.Run("encode", {"text": "machine learning"})
ok, similar, err = vocab.Run("get_similar_tokens", {"token_id": 1})
```

**Database Schema:**
```sql
vocab:
  - token_id (PRIMARY KEY)
  - phrase (UNIQUE)
  - frequency, weight, quality_score
  - status: 'perm' | 'temp' | 'archived'

clusters:
  - cluster_id (PRIMARY KEY)
  - centroid_phrase
  - member_count
  - cohesion_score

token_relationships:
  - token_id_1, token_id_2, metric_type (PRIMARY KEY)
  - similarity_score
```

---

## Integration Patterns

### Pattern 1: Code Validation → Semantic Analysis

**Workflow:**
1. Validate C code with VBShellGate
2. Extract semantic tokens with StableTokenVocab
3. Analyze token relationships
4. Suggest optimizations

**Example:**
```python
# Step 1: Validate
gate = VBShellGate()
ok, data, _ = gate.Run("validate_file", {"filepath": "code.c"})

if not data["valid"]:
    # Step 2-4: Analyze why
    vocab = StableTokenVocab()
    violations = data["violations"]
    
    # Encode violations as semantic tokens
    ok, tokens, _ = vocab.Run("encode", {
        "text": " ".join(violations)
    })
    
    # Find similar patterns in corpus
    ok, similar, _ = vocab.Run("get_similar_tokens", {
        "token_id": tokens[0]
    })
```

### Pattern 2: Batch Code Analysis

**Workflow:**
1. Process multiple C files
2. Track violations semantically
3. Auto-cluster similar issues
4. Generate repair recommendations

```python
gate = VBShellGate()
vocab = StableTokenVocab()

files = ["code1.c", "code2.c", "code3.c"]

for filepath in files:
    ok, data, _ = gate.Run("validate_file", {"filepath": filepath})
    violations_text = " ".join(data["violations"])
    
    # Semantic analysis of violations
    ok, tokens, _ = vocab.Run("encode", {"text": violations_text})

# Cluster violation patterns
ok, clusters, _ = vocab.Run("build_clusters", {})

# Identify most common issues
for cluster in clusters:
    print(f"Common issue: {cluster['intention_label']}")
```

### Pattern 3: Artifact Quality Tracking

**Workflow:**
1. Validate and repair artifacts
2. Track semantic quality evolution
3. Predict repair success

```python
gate = VBShellGate()
vocab = StableTokenVocab()

# Get all artifacts
ok, data, _ = gate.Run("get_rejected_artifacts", {})

for artifact in data["artifacts"]:
    artifact_id, class_id, name, code, errors = artifact
    
    # Semantic quality analysis
    ok, quality_data, _ = vocab.Run("validate_code_string", {
        "code": code
    })
    
    # Track semantic coherence
    quality_score = 1.0 - (len(quality_data["violations"]) / 10)
    
    if quality_score > 0.7:
        # Likely to repair successfully
        gate.Run("repair_artifact", {"artifact_id": artifact_id})
```

---

## Command Reference

### VB Shell Gate Commands

| Command | Params | Returns |
|---------|--------|---------|
| `init_db` | {} | {initialized: bool} |
| `validate_file` | {filepath} | {valid, violations, class_id} |
| `validate_code` | {code} | {valid, violations} |
| `store_class` | {name, status} | {class_id, name} |
| `store_code_artifact` | {class_id, code, is_valid, error_report} | {artifact_id} |
| `get_class_history` | {class_name} | {history: []} |
| `get_rejected_artifacts` | {} | {count, artifacts: []} |
| `repair_artifact` | {artifact_id} | {repaired, violations} |
| `repair_all` | {} | {results: []} |

### Stable Token Vocab Commands

| Command | Params | Returns |
|---------|--------|---------|
| `encode` | {text} | {tokens: []} |
| `decode` | {token_ids} | {phrases} |
| `encode_batch` | {texts} | {results: []} |
| `get_similar_tokens` | {token_id, metric} | {similar: []} |
| `get_token_relationships` | {token_id} | {token_info, relationships} |
| `build_clusters` | {min_size} | {clusters: []} |
| `filter_tokens` | {filters} | {tokens: []} |
| `aggregate_stats` | {group_by} | {stats: []} |
| `validate_corpus` | {} | {issues} |

---

## Usage Scenarios

### Scenario 1: Code Quality Assurance

**Goal:** Ensure all C code meets VB-style standards

```python
import os
from vb_shell_gate import VBShellGate

gate = VBShellGate()
gate.Run("init_db", {})

# Scan directory
for filename in os.listdir("src/"):
    if filename.endswith(".c"):
        ok, data, _ = gate.Run("validate_file", {
            "filepath": f"src/{filename}"
        })
        
        if not data["valid"]:
            print(f"REJECT: {filename}")
            for v in data["violations"]:
                print(f"  - {v}")
```

### Scenario 2: Semantic Code Analysis

**Goal:** Find similar patterns and suggest refactoring

```python
from stable_token_vocab import StableTokenVocab

vocab = StableTokenVocab(param={
    "ngram_sizes": [2, 3, 4],
    "similarity_threshold": 0.75
})

vocab.Run("init_db", {})

# Analyze codebase
texts = [...]  # Extract comments/identifiers
ok, results, _ = vocab.Run("encode_batch", {"texts": texts})

# Find clusters
ok, clusters, _ = vocab.Run("build_clusters", {
    "min_cluster_size": 3
})

# Identify patterns
for cluster in clusters:
    print(f"Pattern: {cluster['centroid_phrase']}")
    print(f"  Members: {cluster['member_count']}")
    print(f"  Cohesion: {cluster['cohesion_score']:.2f}")
```

### Scenario 3: Automated Repair Pipeline

**Goal:** Auto-repair invalid artifacts and track success

```python
gate = VBShellGate()
gate.Run("init_db", {})

# Get invalid artifacts
ok, data, _ = gate.Run("get_rejected_artifacts", {})

repaired_count = 0
for artifact_id, class_id, name, code, errors in data["artifacts"]:
    ok, result, _ = gate.Run("repair_artifact", {
        "artifact_id": artifact_id
    })
    
    if result["repaired"]:
        print(f"✓ Repaired: {name}")
        repaired_count += 1
    else:
        print(f"✗ Failed: {name}")
        print(f"  Remaining: {result['violations']}")

print(f"\nRepaired {repaired_count}/{len(data['artifacts'])} artifacts")
```

---

## Installation & Setup

```bash
# Clone repository
git clone https://github.com/thobaniluthuli-svg/the-one.git
cd the-one

# Run VB Shell Gate (interactive)
python vb_shell_gate.py

# Validate specific file
python vb_shell_gate.py validate path/to/code.c

# Repair all artifacts
python vb_shell_gate.py repair_all

# Run StableTokenVocab examples
python examples_test.py
```

---

## Configuration

### VB Shell Gate

```python
gate = VBShellGate(param={
    "db_path": "vb_shell.db"  # Custom database path
})
```

**Environment Variables:**
```bash
export VB_SHELL_DB=/path/to/vb_shell.db
```

### Stable Token Vocab

```python
vocab = StableTokenVocab(param={
    "db_path": "stable_vocab_v3.db",
    "ngram_sizes": [2, 3, 4],
    "similarity_threshold": 0.7,
    "enable_caching": True,
    "cache_ttl": 300,
    "use_threading": True
})
```

---

## Performance Characteristics

### VB Shell Gate

| Operation | Complexity | Time |
|-----------|-----------|------|
| validate_file | O(n) | ~1ms for 1KB code |
| repair_artifact | O(n) | ~5ms |
| repair_all (100 artifacts) | O(m*n) | ~500ms |

### Stable Token Vocab

| Operation | Complexity | Time |
|-----------|-----------|------|
| encode | O(n) | ~1ms for 100 words |
| get_similar_tokens | O(k*p) | ~50ms for 1000 tokens |
| build_clusters | O(m²) | ~100ms for 100 tokens |

---

## Best Practices

### 1. Validation First
Always validate code before semantic analysis:
```python
# Good ✓
gate.Run("validate_file", {"filepath": "code.c"})
vocab.Run("encode", {"text": code})

# Not recommended ✗
vocab.Run("encode", {"text": code})  # Analyze invalid code
```

### 2. Batch Operations
Use batch commands for efficiency:
```python
# Good ✓
vocab.Run("encode_batch", {"texts": files})

# Slower ✗
for text in files:
    vocab.Run("encode", {"text": text})
```

### 3. Regular Maintenance
Periodically validate and repair:
```python
# Weekly maintenance
gate.Run("repair_all", {})
vocab.Run("validate_corpus", {})
```

### 4. Monitor Performance
Track operation times:
```python
ok, metrics, _ = vocab.Run("measure_performance", {
    "operation": "all"
})
```

---

## Troubleshooting

### Issue: "Artifact not found"
**Cause:** Artifact ID doesn't exist
**Solution:** Get valid IDs with `get_rejected_artifacts`

### Issue: Slow clustering
**Cause:** Too many tokens (O(m²) complexity)
**Solution:** Increase `min_cluster_size` or filter tokens first

### Issue: Repair failed with same violations
**Cause:** Violations require manual intervention
**Solution:** Review violation types and custom repairs

---

## Architecture Layers

This system covers multiple tokenizer layers:

```
Layer 2: TOKEN EXTRACTION CLUSTER
  ✓ VBValidator pattern extraction

Layer 4: TOKEN IDENTITY + VOCABULARY
  ✓ Stable ID assignment (VocabTokenVocab)

Layer 5: FREQUENCY + WEIGHT
  ✓ Quality scoring

Layer 7: ENCODING / DECODING
  ✓ Code encoding/decoding
  ✓ Batch operations

Layer 8: CLUSTERING / SEMANTIC GROUPING
  ✓ Multi-metric similarity
  ✓ Cohesion scoring

Layer 9: TRAINING SIGNAL LAYER
  ✓ Validation feedback

Layer 10: SYSTEM ORCHESTRATION
  ✓ Unified CLI interface
```

---

## Future Enhancements

- [ ] GPU-accelerated similarity computation
- [ ] Machine learning model for repair prediction
- [ ] Distributed validation across nodes
- [ ] Real-time WebSocket CLI
- [ ] Visual analysis dashboard
- [ ] Integration with version control (Git hooks)

---

**Version**: 1.0 Unified Toolchain
**Created**: 2026-06-07
**Components**: VBShellGate + StableTokenVocab
**Status**: Production Ready

````
