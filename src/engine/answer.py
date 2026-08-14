DEFAULT_MIN_SCORE = 0.3 # to calibrate

def answer_query(question, space, vsm, generation_provider, top_k=5, min_score=DEFAULT_MIN_SCORE):
    results = vsm.search(space, question, top_k=top_k)
    relevant_results = [r for r in results if r.score >= min_score]

    if not relevant_results:
        return {
            "answer": "I couldn't find relevant information in your documents for this question.",
            "sources": [],
        }

    context_parts = []
    sources = []
    for i, r in enumerate(relevant_results, start=1):
        context_parts.append(f"[{i}] {r.chunk.content}")
        sources.append({
            "id": i,
            "file": r.chunk.source_metadata.filepath,
            "score": r.score,
        })

    context = "\n\n".join(context_parts)

    # TODO: prompt is hardcoded here, move to a template/config
    prompt = f"""Answer the question using only the context below. Cite sources using [1], [2] etc. matching the context numbers. If the context doesn't contain the answer, say so clearly.

Context:
{context}

Question: {question}

Answer:"""

    answer_text = generation_provider.generate(prompt)

    return {
        "answer": answer_text,
        "sources": sources,
    }