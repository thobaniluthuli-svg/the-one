"""
StableTokenVocab - Usage Examples & Tests

Demonstrates all functionality of the StableTokenVocab class via VBSTYLE interface.
"""

from stable_token_vocab import StableTokenVocab


def main():
    print("=" * 80)
    print("STABLETOKENVOCAB - USAGE EXAMPLES")
    print("=" * 80)
    
    # ─────────────────────────────────────────────────────────────────────────
    # 1. Initialize vocabulary system
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[1] Initializing StableTokenVocab...")
    vocab = StableTokenVocab(param={"db_path": "test_vocab.db"})
    print(f"✓ Session ID: {vocab.session_id}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 2. Encode text
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[2] Encoding text...")
    text1 = "machine learning is powerful for data science"
    status, tokens, err = vocab.Run("encode", {"text": text1})
    if status:
        print(f"✓ Text: {text1}")
        print(f"✓ Tokens: {tokens}")
    else:
        print(f"✗ Error: {err}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 3. Encode more text (to build frequency)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[3] Encoding more texts to build vocabulary...")
    texts = [
        "machine learning models are complex",
        "data science uses machine learning",
        "powerful algorithms for learning tasks",
        "machine learning is essential today"
    ]
    for text in texts:
        status, tokens, err = vocab.Run("encode", {"text": text})
        if status:
            print(f"  ✓ {text} -> {tokens}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 4. Decode token IDs
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[4] Decoding token IDs...")
    status, decoded, err = vocab.Run("decode", {"token_ids": tokens})
    if status:
        print(f"✓ Decoded: {decoded}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 5. Get ranked tokens
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[5] Getting top 10 ranked tokens...")
    status, ranked, err = vocab.Run("get_ranked_tokens", {"limit": 10})
    if status:
        print(f"✓ Top ranked tokens:")
        for i, token in enumerate(ranked, 1):
            print(f"   {i}. '{token['phrase']}' "
                  f"(ID: {token['token_id']}, Freq: {token['frequency']}, "
                  f"Weight: {token['weight']:.2f}, Status: {token['status']})")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 6. Get token metadata
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[6] Getting metadata for specific token...")
    if ranked:
        token_id = ranked[0]["token_id"]
        status, metadata, err = vocab.Run("get_token_metadata", {"token_id": token_id})
        if status:
            print(f"✓ Metadata for token {token_id} ('{metadata['phrase']}'):")
            print(f"   - Frequency: {metadata['frequency']}")
            print(f"   - Weight: {metadata['weight']:.2f}")
            print(f"   - Contextual Strength: {metadata['contextual_strength']:.2f}")
            print(f"   - Status: {metadata['status']}")
            print(f"   - Rank: {metadata['rank']}")
            print(f"   - Compression Ratio: {metadata['compression_ratio']:.2f}")
            print(f"   - Information Density: {metadata['information_density']:.2f}")
            print(f"   - Sessions: {metadata['sessions']}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 7. Search by phrase pattern
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[7] Searching for phrases containing 'machine'...")
    status, results, err = vocab.Run("search_by_phrase", {"pattern": "machine"})
    if status:
        print(f"✓ Found {len(results)} results:")
        for i, token in enumerate(results, 1):
            print(f"   {i}. '{token['phrase']}' (Freq: {token['frequency']}, Weight: {token['weight']:.2f})")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 8. Build clusters
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[8] Building phrase clusters...")
    status, clusters, err = vocab.Run("build_clusters", {"min_cluster_size": 2})
    if status:
        print(f"✓ Built {len(clusters)} clusters:")
        for i, cluster in enumerate(clusters, 1):
            print(f"   {i}. Centroid: '{cluster['centroid_phrase']}' "
                  f"(Label: {cluster['intention_label']}, "
                  f"Members: {cluster['member_count']}, "
                  f"Weight: {cluster['total_weight']:.2f})")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 9. Analyze threshold performance
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[9] Analyzing threshold performance...")
    if ranked:
        token_id = ranked[0]["token_id"]
        status, analysis, err = vocab.Run("analyze_threshold", {"token_id": token_id})
        if status:
            print(f"✓ Threshold analysis for token {token_id}:")
            for key, value in analysis.items():
                if isinstance(value, dict) and "pass" in value:
                    status_str = "✓ PASS" if value["pass"] else "✗ FAIL"
                    print(f"   {key}: {value['value']:.2f} / {value['threshold']:.2f} {status_str}")
            print(f"   Overall: {analysis['pass_count']}/7 rules passed - "
                  f"{'✓ PERMANENT' if analysis['overall_pass'] else '✗ TEMPORARY'}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 10. Get statistics
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[10] Getting vocabulary statistics...")
    status, stats, err = vocab.Run("get_stats", {})
    if status:
        print(f"✓ Statistics:")
        print(f"   - Total tokens: {stats['total_tokens']}")
        print(f"   - Permanent: {stats['permanent_tokens']}")
        print(f"   - Temporary: {stats['temporary_tokens']}")
        print(f"   - Total clusters: {stats['total_clusters']}")
        print(f"   - Total sessions: {stats['total_sessions']}")
        print(f"   - Current session: {stats['current_session']}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 11. Get threshold summary
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[11] Getting threshold summary...")
    status, summary, err = vocab.Run("get_threshold_summary", {})
    if status:
        print(f"✓ Threshold summary:")
        print(f"   - Permanent tokens: {summary['permanent_tokens']}")
        print(f"   - Temporary tokens: {summary['temporary_tokens']}")
        print(f"   - Archived tokens: {summary['archived_tokens']}")
        print(f"   - Active corpus size: {summary['corpus_size']}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 12. Track phrase evolution
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[12] Tracking phrase evolution...")
    phrase_to_track = "machine learning"
    status, evolution, err = vocab.Run("track_evolution", {"phrase": phrase_to_track})
    if status:
        print(f"✓ Evolution of '{phrase_to_track}':")
        for session in evolution:
            print(f"   - Session {session['session_id']}: {session['frequency']} occurrences")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 13. Export corpus
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[13] Exporting corpus to JSON...")
    status, result, err = vocab.Run("export_corpus", {"filepath": "corpus_export.json"})
    if status:
        print(f"✓ Corpus exported to 'corpus_export.json'")
    else:
        print(f"✗ Error: {err}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 14. Close connection
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[14] Closing vocabulary system...")
    status, result, err = vocab.Run("close", {})
    if status:
        print(f"✓ Connection closed")
    
    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
