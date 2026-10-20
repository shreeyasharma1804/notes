### pg_vector extension

- Allows storing embeddings of any dimensions in the table
- I think, since the dimensions are variable, the actual table entry might contain a disk pointer to the embeddings locations (TOAST)

### Indexing

- Always create an index on the embedding column
- Hierarchical Navigable Small World
- The lowest level contains all the embeddings
- Skip lists are used with lengths reducing exponentially to maintain a o(log(n)) search complexity

### Cosine similarity

- Operator: <=>
- For 2 vectors (a_i, a_j) and (b_i, b_j) the cosine similarity is the cos(angle between the 2 vectors)
- Batch and queue inserts (Kafka → embedding worker → vector DB)
