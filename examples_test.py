"""
Enhanced StableTokenVocab - Usage Examples with Advanced Features

Demonstrates all advanced functionality including:
- Batch encoding
- Similarity metrics
- Token relationships
- Advanced filtering
- Clustering with cohesion
- Performance profiling
- Data validation
"""

from stable_token_vocab import StableTokenVocab, SimilarityMetrics
import json


def main():
    print("=" * 80)
    print("ENHANCED STABLETOKENVOCAB - ADVANCED USAGE EXAMPLES")
    print("=" * 80)
    
    # ─────────────────────────────────────────────────────────────────────────
    # 1. Initialize with enhanced parameters
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[1] Initializing with enhanced parameters...")
    vocab = StableTokenVocab(param={
        "db_path": "enhanced_vocab.db",
        "ngram_sizes": [2, 3, 4],
        "similarity_threshold": 0.7,
        "enable_caching": True,
        "cache_ttl": 300,
        "use_threading": True
    })
    print(f"✓ Session ID: {vocab.session_id}")
    print(f"✓ N-gram sizes: {vocab.ngram_sizes}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 2. Batch encoding
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[2] Batch encoding multiple texts...")
    texts = [
        "machine learning algorithms are powerful",
        "deep learning neural networks excel",
        "machine learning models require data",
        "artificial intelligence transforms industries",
        "neural networks learn patterns",
    ]
    status, batch_results, err = vocab.Run("encode_batch", {"texts": texts})
    if status:
        for result in batch_results:
            if 'error' not in result:
                print(f"  ✓ {result['text'][:40]}... → {len(result['tokens'])} tokens")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 3. Get ranked tokens with quality scores
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[3] Top tokens by quality score...")
    status, ranked, err = vocab.Run("get_ranked_tokens", {"limit": 10})
    if status:
        print(f"✓ Top ranked tokens:")
        for i, token in enumerate(ranked[:5], 1):
            print(f"   {i}. '{token['phrase']}' (Quality: {token.get('quality_score', 0):.2f})")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 4. Similarity metrics demonstration
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[4] Similarity metrics comparison...")
    phrase1 = "machine learning"
    phrase2 = "machine learning models"
    phrase3 = "deep learning"
    
    jaccard_1_2 = SimilarityMetrics.jaccard_similarity(phrase1, phrase2)
    jaccard_1_3 = SimilarityMetrics.jaccard_similarity(phrase1, phrase3)
    cosine_1_2 = SimilarityMetrics.cosine_similarity(phrase1, phrase2)
    leven_1_2 = SimilarityMetrics.levenshtein_distance(phrase1, phrase2)
    
    print(f"✓ Comparing '{phrase1}' vs '{phrase2}':")
    print(f"   Jaccard: {jaccard_1_2:.3f}")
    print(f"   Cosine: {cosine_1_2:.3f}")
    print(f"   Levenshtein: {leven_1_2:.3f}")
    print(f"✓ Comparing '{phrase1}' vs '{phrase3}':")
    print(f"   Jaccard: {jaccard_1_3:.3f}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 5. Find similar tokens
    # ─────��───────────────────────────────────────────────────────────────────
    print("\n[5] Finding similar tokens...")
    if ranked and ranked[0]:
        token_id = ranked[0]['token_id']
        status, similar, err = vocab.Run("get_similar_tokens", {
            "token_id": token_id,
            "limit": 5,
            "metric": "jaccard"
        })
        if status:
            print(f"✓ Tokens similar to '{ranked[0]['phrase']}':")
            for sim_token in similar[:3]:
                print(f"   - '{sim_token['phrase']}' (Similarity: {sim_token['similarity']:.3f})")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 6. Get token relationships
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[6] Get comprehensive token relationships...")
    if ranked and ranked[0]:
        token_id = ranked[0]['token_id']
        status, relationships, err = vocab.Run("get_token_relationships", {
            "token_id": token_id
        })
        if status:
            print(f"✓ Token {token_id} relationships:")
            print(f"   - Info: '{relationships['token_info']['phrase']}'")
            print(f"   - Related tokens: {len(relationships['relationships'])}")
            if relationships['cluster_members']:
                print(f"   - Cluster members: {len(relationships['cluster_members'])}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 7. Advanced filtering
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[7] Advanced token filtering...")
    status, filtered, err = vocab.Run("filter_tokens", {
        "min_frequency": 2,
        "min_quality": 0.4,
        "status": "perm",
        "limit": 5
    })
    if status:
        print(f"✓ Found {len(filtered)} tokens matching filters:")
        for token in filtered[:3]:
            print(f"   - '{token['phrase']}' (Freq: {token['frequency']}, Quality: {token.get('quality_score', 0):.2f})")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 8. Aggregate statistics
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[8] Aggregated statistics by status...")
    status, agg_stats, err = vocab.Run("aggregate_stats", {"group_by": "status"})
    if status:
        print(f"✓ Statistics by status:")
        for stat in agg_stats:
            print(f"   - {stat['status']}: Count={stat['count']}, "
                  f"Avg Weight={stat['avg_weight']:.2f}, "
                  f"Total Freq={stat['total_frequency']}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 9. Build clusters with cohesion scoring
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[9] Building phrase clusters with cohesion...")
    status, clusters, err = vocab.Run("build_clusters", {"min_cluster_size": 2})
    if status:
        print(f"✓ Built {len(clusters)} clusters:")
        for cluster in clusters[:3]:
            print(f"   - Cluster {cluster['cluster_id']}: '{cluster['centroid_phrase']}'")
            print(f"     Members: {cluster['member_count']}, "
                  f"Cohesion: {cluster.get('cohesion_score', 0):.3f}, "
                  f"Label: {cluster['intention_label']}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 10. Get cluster members
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[10] Get detailed cluster members...")
    if clusters and clusters[0]:
        cluster_id = clusters[0]['cluster_id']
        status, cluster_info, err = vocab.Run("get_cluster_members", {
            "cluster_id": cluster_id
        })
        if status:
            print(f"✓ Cluster {cluster_id} members:")
            for member in cluster_info['members'][:3]:
                print(f"   - '{member['phrase']}' (Quality: {member.get('quality_score', 0):.2f})")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 11. Get suggestions for phrase improvement
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[11] Get suggestions for phrase...")
    status, suggestions, err = vocab.Run("get_suggestions", {
        "phrase": "machine learning"
    })
    if status:
        print(f"✓ Suggestions for 'machine learning':")
        for sugg in suggestions[:3]:
            print(f"   - '{sugg['phrase']}' ({sugg['suggestion']})")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 12. Validate corpus integrity
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[12] Validate corpus integrity...")
    status, validation, err = vocab.Run("validate_corpus", {})
    if status:
        print(f"✓ Corpus validation:")
        print(f"   - Orphaned sessions: {validation['orphaned_sessions']}")
        print(f"   - Invalid statuses: {validation['invalid_statuses']}")
        print(f"   - Inconsistent clusters: {validation['inconsistent_clusters']}")
        if validation['suggestions']:
            print(f"   - Suggestions: {', '.join(validation['suggestions'])}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 13. Merge similar tokens
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[13] Merge similar tokens (threshold=0.85)...")
    status, merge_result, err = vocab.Run("merge_similar_tokens", {"threshold": 0.85})
    if status:
        print(f"✓ Merge results:")
        print(f"   - Tokens merged: {merge_result['merged_count']}")
        if merge_result['merged_count'] > 0:
            print(f"   - Merge map: {merge_result['merge_map']}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 14. Performance profiling
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[14] Performance metrics...")
    status, perf_metrics, err = vocab.Run("measure_performance", {"operation": "all"})
    if status and perf_metrics:
        print(f"✓ Top operations by average time:")
        for metric in perf_metrics[:3]:
            print(f"   - {metric['operation_name']}: "
                  f"Avg={metric['avg_time']:.4f}s, "
                  f"Calls={metric['call_count']}, "
                  f"Max={metric['max_time']:.4f}s")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 15. Get comprehensive statistics
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[15] Comprehensive statistics...")
    status, stats, err = vocab.Run("get_stats", {})
    if status:
        print(f"✓ Corpus statistics:")
        print(f"   - Total tokens: {stats['total_tokens']}")
        print(f"   - Permanent: {stats['permanent_tokens']}")
        print(f"   - Temporary: {stats['temporary_tokens']}")
        print(f"   - Clusters: {stats['total_clusters']}")
        print(f"   - Sessions: {stats['total_sessions']}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 16. Export enhanced corpus
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[16] Exporting enhanced corpus...")
    status, result, err = vocab.Run("export_corpus", {
        "filepath": "enhanced_corpus_export.json"
    })
    if status:
        print(f"✓ Corpus exported to 'enhanced_corpus_export.json'")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 17. Close connection
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[17] Closing vocabulary system...")
    status, result, err = vocab.Run("close", {})
    if status:
        print(f"✓ Connection closed")
    
    print("\n" + "=" * 80)
    print("ALL ADVANCED EXAMPLES COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
