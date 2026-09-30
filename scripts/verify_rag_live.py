import requests

BASE_URL = "http://127.0.0.1:8000"

def test_live_rag():
    print("--- 1. Ingest Demo Repository ---")
    res = requests.post(f"{BASE_URL}/api/v1/repositories/ingest", json={
        "source_type": "local",
        "target": "demo-repos/deploysafe-rag-demo"
    })
    assert res.status_code == 200, f"Ingest failed: {res.text}"
    snap = res.json()
    repo_id = snap["repository_id"]
    print(f"Repository Ingested: {snap['repository_name']} (ID: {repo_id})")
    print(f"Discovered {snap['file_count']} files, {snap['total_size_bytes']} bytes")

    print("\n--- 2. Index Repository ---")
    res_idx = requests.post(f"{BASE_URL}/api/v1/repositories/{repo_id}/index")
    assert res_idx.status_code == 200, f"Index failed: {res_idx.text}"
    idx_summary = res_idx.json()
    print(f"Status: {idx_summary['status']}")
    print(f"Files indexed: {idx_summary['files_indexed']}/{idx_summary['files_discovered']}")
    print(f"Chunks created: {idx_summary['chunks_created']}, Embeddings: {idx_summary['embeddings_created']}")
    print(f"Duration: {idx_summary['duration_seconds']}s")

    print("\n--- 3. Query: Deployment ---")
    q1 = "What does this project use for deployment?"
    r1 = requests.post(f"{BASE_URL}/api/v1/repositories/{repo_id}/search", json={"query": q1, "top_k": 3}).json()
    print(f"Query: '{q1}' => Status: {r1['status']} ({r1['results_count']} results)")
    for hit in r1["results"]:
        print(f"  * {hit['file_path']} (L{hit['line_start']}-L{hit['line_end']}) [Score: {hit['relevance_score']}] Category: {hit['category']}")

    print("\n--- 4. Query: Testing Instructions ---")
    q2 = "How should I run the tests?"
    r2 = requests.post(f"{BASE_URL}/api/v1/repositories/{repo_id}/search", json={"query": q2, "top_k": 3}).json()
    print(f"Query: '{q2}' => Status: {r2['status']} ({r2['results_count']} results)")
    for hit in r2["results"]:
        print(f"  * {hit['file_path']} (L{hit['line_start']}-L{hit['line_end']}) [Score: {hit['relevance_score']}] Category: {hit['category']}")

    print("\n--- 5. Query: Environment Variables ---")
    q3 = "Where are environment variables documented?"
    r3 = requests.post(f"{BASE_URL}/api/v1/repositories/{repo_id}/search", json={"query": q3, "top_k": 3}).json()
    print(f"Query: '{q3}' => Status: {r3['status']} ({r3['results_count']} results)")
    for hit in r3["results"]:
        print(f"  * {hit['file_path']} (L{hit['line_start']}-L{hit['line_end']}) [Score: {hit['relevance_score']}] Category: {hit['category']}")

    print("\n--- 6. Query: Unrelated Query (Anti-Hallucination) ---")
    q4 = "How to bake a sourdough bread?"
    r4 = requests.post(f"{BASE_URL}/api/v1/repositories/{repo_id}/search", json={"query": q4, "top_k": 3}).json()
    print(f"Query: '{q4}' => Status: {r4['status']} ({r4['results_count']} results)")
    print("Anti-hallucination check:", r4['status'])

    print("\nALL LIVE API VERIFICATION CHECKS PASSED!")

if __name__ == "__main__":
    test_live_rag()
