from collections.abc import Sequence
from pathlib import Path

import faiss
import numpy as np


class FaissVectorStore:

    def __init__(
        self,
        dimension: int,
        index_path: str,
    ):
        self.dimension = dimension
        self.index_path = Path(index_path)

        self.index_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.index = self._load_or_create()

    def _load_or_create(self) -> faiss.IndexIDMap: 
        if self.index_path.exists(): 
            index = faiss.read_index( 
                str(self.index_path), 
            ) 

            if not isinstance(index, faiss.IndexIDMap): 
                raise RuntimeError( 
                    "FAISS index must be an IndexIDMap. " 
                    "Delete the existing index and rebuild it." 
                ) 

            if index.d != self.dimension: 
                raise RuntimeError( 
                    "FAISS index dimension does not match " 
                    "the configured embedding dimension." 
                ) 
            return index 

        return faiss.IndexIDMap( 
            faiss.IndexFlatIP( 
                self.dimension, 
            ), 
        )
    

    def add(
        self,
        ids: Sequence[int],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        if not ids or not embeddings:
            return

        if len(ids) != len(embeddings): 
            raise ValueError( 
                "Number of IDs must match number of embeddings." 
            )

        vectors = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        vector_ids = np.asarray(
            ids,
            dtype=np.int64,
        )

        if vectors.ndim != 2: 
            raise ValueError( 
                "Embeddings must be a 2-dimensional sequence." 
            )

        if vectors.shape[1] != self.dimension:
            raise ValueError(
                "Embedding dimension does not match "
                "FAISS index dimension"
            )

        self.index.add_with_ids(
            vectors,
            vector_ids,
        )

        self.save()

    def search(
        self,
        embedding: Sequence[float],
        top_k: int = 5,
        allowed_ids: set[int] | None = None,
    ) -> list[tuple[int, float]]:

        if top_k <= 0 or self.index.ntotal == 0:
            return []

        vector = np.asarray(
            [embedding],
            dtype=np.float32,
        )

        if vector.shape[1] != self.dimension: 
            raise ValueError( 
                "Query embedding dimension does not match " 
                "FAISS index dimension." 
            )

        # IndexFlatIP does not support metadata filtering.
        # Search all vectors when authorization filtering is required.
        search_k = (
            self.index.ntotal
            if allowed_ids is not None
            else top_k
        )
        # print(f"search_k:{search_k}")
        scores, ids = self.index.search(
            vector,
            search_k,
        )

        results: list[tuple[int, float]] = []

        for chunk_id, score in zip(
            ids[0],
            scores[0],
        ):
            if chunk_id == -1:
                continue

            chunk_id = int(chunk_id)

            print(
                f"FAISS RESULT: chunk_id={chunk_id}, "
                f"allowed={chunk_id in allowed_ids if allowed_ids is not None else 'NO FILTER'}"
            )
            
            # Authorization filter
            if allowed_ids is not None and chunk_id not in allowed_ids:
                print(f"SKIPPING UNAUTHORIZED CHUNK: {chunk_id}")
                continue

            results.append(
                (
                    int(chunk_id),
                    float(score),
                )
            )

            if len(results) >= top_k:
                break


        return results

    def delete(
        self,
        ids: Sequence[int],
        ) -> None:
        if not ids:
            return

        vector_ids = np.asarray(
            ids,
            dtype=np.int64,
        )

        self.index.remove_ids(
            vector_ids,
        )

        self.save()

    def rebuild( 
            self, ids: Sequence[int], 
            embeddings: Sequence[Sequence[float]], 
        ) -> None: 
        if len(ids) != len(embeddings): 
            raise ValueError( "Number of IDs must match number of embeddings." ) 

        new_index = faiss.IndexIDMap( 
            faiss.IndexFlatIP( 
                self.dimension, 
            ), 
        ) 

        if ids: 
            vectors = np.asarray( 
                embeddings, 
                dtype=np.float32, 
            ) 

            vector_ids = np.asarray( 
                ids, 
                dtype=np.int64, 
            ) 

            if vectors.ndim != 2: 
                raise ValueError( 
                    "Embeddings must be a 2-dimensional sequence." 
                ) 

            if vectors.shape[1] != self.dimension: 
                raise ValueError( 
                    "Embedding dimension does not match " "FAISS index dimension." 
                ) 

            new_index.add_with_ids( vectors, vector_ids, ) 
            
            self.index = new_index 
            self.save() 


    def save(self) -> None: 
        faiss.write_index( 
            self.index, 
            str(self.index_path), 
        )